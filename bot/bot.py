import discord
import os
import aiohttp
import asyncio
from session_db import init_db, get_thread_session, create_thread_session, touch_thread_session

# Intents to allow message content
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Discord token from environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL', 'http://gemini-agent:8000/ask')

REQUEST_QUEUE: asyncio.Queue[dict] = asyncio.Queue()
COOLDOWN_SECONDS = 10


def _resolve_thread_id(message: discord.Message) -> str | None:
    if isinstance(message.channel, discord.Thread):
        return str(message.channel.id)
    return None


async def _send_chunked_reply(channel: discord.abc.Messageable, text: str):
    if len(text) > 2000:
        for i in range(0, len(text), 2000):
            await channel.send(text[i:i+2000])
    else:
        await channel.send(text)


async def _call_agent(prompt: str, session_id: str | None) -> tuple[dict | None, str | None]:
    payload = {'prompt': prompt, 'session_id': session_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, timeout=320) as resp:
            if resp.status != 200:
                return None, f"HTTP Error {resp.status} from API."
            data = await resp.json()
            if data.get('error'):
                return None, data['error']
            return data, None


async def _process_request(item: dict):
    """
    1リクエストを処理する．入力は，{'message': discord.Message, 'prompt': str, 'force_new': bool} の形式で `REQUEST_QUEUE` に入る。
    """
    message: discord.Message = item['message']
    prompt: str = item['prompt']
    force_new: bool = item['force_new']

    thread_id = _resolve_thread_id(message)
    if not thread_id:
        await message.channel.send("Error: この機能はDiscord thread内でのみ利用できます。")
        return

    try:
        existing = get_thread_session(thread_id)
    except Exception as e:
        await message.channel.send(f"Error: session mapping lookup failed: {str(e)}")
        return

    # --- 新規セッション開始の処理 ---
    if force_new:
        if existing:
            await message.channel.send("Error: このthreadには既にsessionが紐づいています。新規sessionは開始できません。")
            return

        async with message.channel.typing():
            data, error = await _call_agent(prompt=prompt, session_id=None)

        if error:
            await _send_chunked_reply(message.channel, f"Error from Gemini API: {error}")
            return

        session_id = data.get('session_id')
        if not session_id:
            await _send_chunked_reply(message.channel, "Error: 新規sessionのsession_idを取得できませんでした。")
            return

        try:
            create_thread_session(thread_id=thread_id, session_id=session_id, first_prompt=prompt)
            touch_thread_session(thread_id, status='active')
        except Exception as e:
            await _send_chunked_reply(message.channel, f"Error: session mapping save failed: {str(e)}")
            return

        response = data.get('response', 'Empty response.')
        await _send_chunked_reply(message.channel, response)
        return

    # --- 既存セッションでのやりとりの処理 ---
    if not existing:
        await message.channel.send("Error: このthreadにはsessionがありません。最初に `/new <prompt>` を実行してください。")
        return

    session_id = existing['session_id']

    async with message.channel.typing():
        data, error = await _call_agent(prompt=prompt, session_id=session_id)

    if error:
        await _send_chunked_reply(message.channel, f"Error from Gemini API: {error}")
        return

    try:
        touch_thread_session(thread_id, status='active')
    except Exception as e:
        await _send_chunked_reply(message.channel, f"Error: session mapping update failed: {str(e)}")
        return

    response = data.get('response', 'Empty response.')
    await _send_chunked_reply(message.channel, response)


async def _queue_worker():
    """
    Botへのリクエストを順番に処理するワーカー。リクエストは `REQUEST_QUEUE` に辞書形式で入る。
    例外が生じても，次のリクエスト処理に進むようにしている。
    """
    while True:
        item = await REQUEST_QUEUE.get()
        try:
            await _process_request(item)
        except Exception as e:
            message: discord.Message = item['message']
            await message.channel.send(f"Error while processing queue item: {str(e)}")
        finally:
            REQUEST_QUEUE.task_done()
            await asyncio.sleep(COOLDOWN_SECONDS)

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    init_db()
    if not hasattr(client, "queue_worker_started"):
        client.queue_worker_started = True
        client.loop.create_task(_queue_worker())

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 新規session開始
    if message.content.startswith('/new '):
        prompt = message.content[len('/new '):].strip()
        if not prompt:
            await message.channel.send("Error: `/new <prompt>` の形式で入力してください。")
            return
        await REQUEST_QUEUE.put({'message': message, 'prompt': prompt, 'force_new': True})
        await message.channel.send("Queue accepted: new session request")
        return

    # 既存sessionでのやりとり
    if message.content.startswith('/chat '):
        prompt = message.content[len('/chat '):].strip()
        if not prompt:
            await message.channel.send("Error: `/chat <prompt>` の形式で入力してください。")
            return
        await REQUEST_QUEUE.put({'message': message, 'prompt': prompt, 'force_new': False})
        await message.channel.send("Queue accepted: resume session request")
        return

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable is not set.")
    else:
        client.run(DISCORD_TOKEN)

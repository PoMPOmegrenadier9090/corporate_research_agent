import discord
import os
import aiohttp

# Intents to allow message content
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

# Discord token from environment
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
API_URL = os.getenv('API_URL', 'http://gemini-api:8000/ask')

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Trigger with !gemini
    if message.content.startswith('!gemini '):
        prompt = message.content[len('!gemini '):]
        
        # Botのステータス表示(入力中...)
        async with message.channel.typing():
            try:
                # agent側と通信するための非同期 http 通信のセッションを開く
                async with aiohttp.ClientSession() as session:
                    async with session.post(API_URL, json={'prompt': prompt}, timeout=3600) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data.get('error'):
                                response = f"Error from Gemini API: {data['error']}"
                            else:
                                response = data.get('response', 'Empty response.')
                        else:
                            response = f"HTTP Error {resp.status} from API."
            except Exception as e:
                response = f"An error occurred while connecting to API: {str(e)}"

        # Discord message limit is 2000 chars, so we chunk it if necessary
        if len(response) > 2000:
            for i in range(0, len(response), 2000):
                await message.channel.send(response[i:i+2000])
        else:
            await message.channel.send(response)

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable is not set.")
    else:
        client.run(DISCORD_TOKEN)

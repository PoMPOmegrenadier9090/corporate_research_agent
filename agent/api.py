import subprocess
import asyncio
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import config

app = FastAPI()


def build_gemini_command(prompt: str) -> list[str]:
    cmd = ["gemini", "--prompt", prompt]
    
    for key, value in config.GEMINI_CONFIG.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        elif value is not None:
            cmd.extend([f"--{key}", str(value)])
            
    return cmd

class PromptRequest(BaseModel):
    prompt: str

class PromptResponse(BaseModel):
    response: str
    error: str | None = None

@app.post("/ask", response_model=PromptResponse)
async def ask_gemini(request: PromptRequest):
    env = os.environ.copy()
    
    cmd = build_gemini_command(request.prompt)

    try:
        # 非同期でコマンドを実行し、stdout(結果)とstderr(思考ログ等)を分離
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env
        )

        # stderrをリアルタイムでdocker logsに出力するタスク
        async def stream_stderr():
            while True:
                line = await process.stderr.readline()
                if not line:
                    break
                print(line.decode('utf-8', errors='replace'), end="", flush=True)

        # stdoutを結果としてキャプチャするタスク
        async def capture_stdout():
            stdout_data = await process.stdout.read()
            return stdout_data.decode('utf-8', errors='replace').strip()

        stream_task = asyncio.create_task(stream_stderr())
        capture_task = asyncio.create_task(capture_stdout())

        # プロセスの終了を待機（タイムアウト付き）
        await asyncio.wait_for(process.wait(), timeout=3600)

        # 読み込みの完了を待機
        await stream_task
        response_text = await capture_task
        return_code = process.returncode
        
        if return_code == 0:
            if not response_text:
                response_text = "Gemini returned an empty response."
            return PromptResponse(response=response_text)
        else:
            return PromptResponse(response="", error=response_text.strip())

    except asyncio.TimeoutError:
        return PromptResponse(response="", error="Gemini CLI timed out (3600s).")
    except Exception as e:
        return PromptResponse(response="", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

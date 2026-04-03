import subprocess
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import config

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
        # コマンドの実行
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=3600
        )

        if result.returncode == 0:
            response_text = result.stdout.strip()
            if not response_text:
                response_text = "Gemini returned an empty response."
            return PromptResponse(response=response_text)
        else:
            return PromptResponse(response="", error=result.stderr.strip())

    except subprocess.TimeoutExpired:
        return PromptResponse(response="", error="Gemini CLI timed out.")
    except Exception as e:
        return PromptResponse(response="", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

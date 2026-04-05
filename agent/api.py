import asyncio
import os
import signal
import json
from fastapi import FastAPI
from pydantic import BaseModel
import config

app = FastAPI()


def build_gemini_command(prompt: str, session_id: str | None = None) -> list[str]:
    cmd = ["gemini", "--prompt", prompt]

    if session_id:
        cmd.extend(["--resume", session_id])
    
    for key, value in config.GEMINI_CONFIG.items():
        if isinstance(value, bool):
            if value:
                cmd.append(f"--{key}")
        elif value is not None:
            cmd.extend([f"--{key}", str(value)])
            
    return cmd

class PromptRequest(BaseModel):
    prompt: str
    session_id: str | None = None

class PromptResponse(BaseModel):
    response: str
    session_id: str | None = None
    error: str | None = None


def _extract_response_and_session_id(stdout_text: str) -> tuple[str, str | None]:
    try:
        payload = json.loads(stdout_text)
    except json.JSONDecodeError:
        return stdout_text.strip(), None

    if isinstance(payload, dict):
        session_id = (
            payload.get("session_id")
            or payload.get("sessionId")
            or payload.get("session", {}).get("id")
            or payload.get("metadata", {}).get("session_id")
        )

        response_text = (
            payload.get("response")
            or payload.get("content")
            or payload.get("text")
            or payload.get("output")
        )

        if response_text is None:
            response_text = stdout_text

        return str(response_text).strip(), str(session_id) if session_id else None

    return stdout_text.strip(), None


async def _run_gemini_once(prompt: str, session_id: str | None) -> tuple[bool, str, str | None]:
    env = os.environ.copy()
    cmd = build_gemini_command(prompt, session_id)

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
    )

    async def stream_stderr() -> str:
        chunks: list[str] = []
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace")
            chunks.append(decoded)
            print(decoded, end="", flush=True)
        return "".join(chunks)

    async def capture_stdout() -> str:
        stdout_data = await process.stdout.read()
        return stdout_data.decode("utf-8", errors="replace").strip()

    stderr_task = asyncio.create_task(stream_stderr())
    stdout_task = asyncio.create_task(capture_stdout())

    try:
        await asyncio.wait_for(process.wait(), timeout=300)
    except asyncio.TimeoutError:
        process.send_signal(signal.SIGINT)
        try:
            await asyncio.wait_for(process.wait(), timeout=10)
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()

        stderr_text = await stderr_task
        _ = await stdout_task
        timeout_error = "Gemini CLI timed out (300s). Sent SIGINT and terminated process."
        if stderr_text.strip():
            timeout_error = f"{timeout_error}\n{stderr_text.strip()}"
        return False, "", timeout_error

    stderr_text = await stderr_task
    stdout_text = await stdout_task
    return_code = process.returncode

    if return_code == 0:
        response_text, new_session_id = _extract_response_and_session_id(stdout_text)
        if not response_text:
            response_text = "Gemini returned an empty response."
        return True, response_text, new_session_id

    error_text = stdout_text.strip() or stderr_text.strip() or f"Gemini CLI failed with code {return_code}."
    return False, "", error_text

@app.post("/ask", response_model=PromptResponse)
async def ask_gemini(request: PromptRequest):
    try:
        ok, response_or_empty, session_or_error = await _run_gemini_once(
            prompt=request.prompt,
            session_id=request.session_id,
        )

        if ok:
            return PromptResponse(
                response=response_or_empty,
                session_id=session_or_error,
            )

        first_error = session_or_error or "Gemini CLI failed."

        # 同じsession_idで1回だけ再試行
        ok_retry, response_retry, session_retry_or_error = await _run_gemini_once(
            prompt=request.prompt,
            session_id=request.session_id,
        )

        if ok_retry:
            return PromptResponse(
                response=response_retry,
                session_id=session_retry_or_error,
            )

        final_error = session_retry_or_error or "Gemini CLI failed after retry."
        return PromptResponse(response="", error=f"first_attempt: {first_error}\nretry_attempt: {final_error}")

    except Exception as e:
        return PromptResponse(response="", error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

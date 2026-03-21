import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
FISH_URL   = os.getenv("FISH_URL",   "http://localhost:8080")
LLM_MODEL  = os.getenv("LLM_MODEL",  "qwen2.5:72b")

MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "opus": "audio/ogg",
    "pcm": "audio/pcm",
}

class SpeakRequest(BaseModel):
    prompt: str
    system_prompt: str = "You are a helpful assistant. Be concise."
    voice_reference_audio_b64: str = None
    voice_reference_text: str = None
    format: str = "mp3"
    speed: float = 1.0

@app.post("/speak")
async def speak(req: SpeakRequest):
    async with httpx.AsyncClient(timeout=120) as client:
        # 1. LLM
        llm_resp = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": LLM_MODEL,
                "stream": False,
                "messages": [
                    {"role": "system", "content": req.system_prompt},
                    {"role": "user",   "content": req.prompt}
                ]
            }
        )
        llm_resp.raise_for_status()
        generated_text = llm_resp.json()["message"]["content"]

        # 2. TTS
        tts_payload = {
            "text": generated_text,
            "format": req.format,
            "mp3_bitrate": 128,
            "streaming": False,
            "prosody": {"speed": req.speed, "volume": 0}
        }
        if req.voice_reference_audio_b64:
            tts_payload["references"] = [{
                "audio": req.voice_reference_audio_b64,
                "text": req.voice_reference_text or generated_text[:100]
            }]

        tts_resp = await client.post(f"{FISH_URL}/v1/tts", json=tts_payload)
        tts_resp.raise_for_status()

    media_type = MEDIA_TYPES.get(req.format, "audio/mpeg")
    return Response(content=tts_resp.content, media_type=media_type)

@app.get("/health")
async def health():
    return {"ollama": OLLAMA_URL, "fish": FISH_URL, "model": LLM_MODEL}

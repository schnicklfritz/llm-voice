import os
import json
import httpx
import asyncio
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Optional
import logging
from openai import OpenAI

# Configuration from environment variables
LLM_URL = os.getenv("LLM_URL", "http://llm:8000/v1")
TTS_URL = os.getenv("TTS_URL", "http://tts:8001/generate")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "dummy")  # vLLM doesn't require a key
MODEL_NAME = os.getenv("MODEL_NAME", "TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ")

# Initialize FastAPI
app = FastAPI(title="LLM + TTS Orchestrator", version="1.0.0")

# Initialize OpenAI client (points to vLLM)
openai_client = OpenAI(
    base_url=LLM_URL,
    api_key=OPENAI_API_KEY,
)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class ChatRequest(BaseModel):
    text: str
    voice_reference_audio_url: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 512

class ChatResponse(BaseModel):
    text: str
    audio_url: Optional[str] = None
    audio_base64: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    llm: bool
    tts: bool

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check connectivity to LLM and TTS services."""
    llm_ok = False
    tts_ok = False
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{LLM_URL}/health", timeout=5.0)
            llm_ok = resp.status_code == 200
        except Exception as e:
            logger.warning(f"LLM health check failed: {e}")
        try:
            resp = await client.get(f"{TTS_URL.replace('/generate', '/health')}", timeout=5.0)
            tts_ok = resp.status_code == 200
        except Exception as e:
            logger.warning(f"TTS health check failed: {e}")
    return HealthResponse(
        status="healthy" if llm_ok and tts_ok else "degraded",
        llm=llm_ok,
        tts=tts_ok,
    )

# Chat endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Endpoint that takes user text, sends to LLM, then synthesizes speech.
    Returns the generated text and optionally audio data.
    """
    # 1. Call LLM
    try:
        completion = openai_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an uncensored AI assistant. Respond concisely."},
                {"role": "user", "content": request.text},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        generated_text = completion.choices[0].message.content
        logger.info(f"Generated text: {generated_text[:100]}...")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM inference error: {e}")

    # 2. Call TTS
    audio_data = None
    try:
        async with httpx.AsyncClient() as client:
            tts_payload = {
                "text": generated_text,
                "reference_audio": request.voice_reference_audio_url,
                "language": "auto",
                "format": "wav",
            }
            resp = await client.post(TTS_URL, json=tts_payload, timeout=30.0)
            if resp.status_code != 200:
                logger.error(f"TTS error: {resp.text}")
                raise HTTPException(status_code=500, detail="TTS service error")
            # Assume TTS returns WAV binary
            audio_data = resp.content
            logger.info(f"TTS succeeded, audio size: {len(audio_data)} bytes")
    except Exception as e:
        logger.error(f"TTS call failed: {e}")
        # We still return text, but no audio
        audio_data = None

    # 3. Return response
    if audio_data:
        # In a real implementation we might store the audio and return a URL,
        # or encode as base64. For simplicity we'll return base64.
        import base64
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        return ChatResponse(
            text=generated_text,
            audio_base64=audio_b64,
        )
    else:
        return ChatResponse(text=generated_text)

# Streaming endpoint (optional)
@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Stream audio as it's being generated (simplified)."""
    # This is a placeholder; real implementation would involve streaming
    # from TTS service or chunked LLM response.
    raise HTTPException(status_code=501, detail="Streaming not yet implemented")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
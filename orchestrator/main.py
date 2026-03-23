import os
import re
import json
import httpx
from fastapi import FastAPI
from fastapi.responses import Response, StreamingResponse, HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
FISH_URL   = os.getenv("FISH_URL",   "http://localhost:8080")
LLM_MODEL  = os.getenv("LLM_MODEL",  "uncensored-model")

MEDIA_TYPES = {
    "mp3":  "audio/mpeg",
    "wav":  "audio/wav",
    "opus": "audio/ogg",
    "pcm":  "audio/pcm",
}

TONE_PROMPTS = {
    "casual":         "Speak in a relaxed, casual, conversational tone like talking to a close friend.",
    "formal":         "Speak in a composed, articulate, professional tone.",
    "unhinged":       "Speak in a chaotic, unpredictable, slightly unhinged tone. Tangents welcome.",
    "deadpan":        "Speak in a completely flat, deadpan tone. Deliver absurdity without cracking.",
    "dramatic":       "Speak with maximum theatrical drama. Every sentence is life or death.",
    "conspiratorial": "Speak in hushed, urgent tones like sharing forbidden knowledge.",
    "hype":           "Speak like an over-the-top infomercial host genuinely losing their mind with excitement.",
    "noir":           "Speak like a world-weary noir detective narrating a case gone wrong.",
}

INTENSITY_PROMPTS = {
    1: "Use emotion tags sparingly, only at the single most important moment.",
    2: "Use emotion tags occasionally to highlight a few key moments.",
    3: "Use emotion tags moderately throughout your response.",
    4: "Use emotion tags frequently and expressively throughout.",
    5: "Use emotion tags constantly and with extreme theatrical intensity on nearly every phrase. Go all out.",
}

LENGTH_PROMPTS = {
    "short":  "Keep your entire response under 50 words.",
    "medium": "Keep your response between 100 and 150 words.",
    "long":   "Keep your response between 250 and 300 words.",
}

BASE_PROMPT = """You are a vivid, expressive voice performer.
Annotate your response with Fish Speech S2 inline emotion tags to enhance delivery.
Use [square bracket] syntax with natural language descriptions at the word or phrase level.
Examples: [laughing] [whisper] [excited] [sad] [angry] [shouting] [sigh] [pause]
[chuckle] [voice breaking] [low voice] [emphasis] [inhale] [exhale] [shocked]
[audience laughter] [clearing throat] [singing] [echo] [panting] [delight]
[super happy] [barely audible] [voice cracking with emotion] [long pause] [nervous laugh]
[deep breath] [trembling voice] [monotone] [whimpering] [giggling] [dramatic pause]
[hushed] [breathless] [slow] [fast] [drawn out] [clipped] [staccato] [flowing]
[rhythmic] [rushed] [deliberate] [raspy] [breathy] [gravelly] [smooth] [nasal]
[resonant] [hollow] [thin voice] [full voice] [theatrical] [deadpan delivery]
[over the top] [understated] [dry] [sardonic] [wistful] [bitter] [nostalgic]
[conspiratorial] [yawning] [hiccup] [sniffling] [crying] [laughing through tears]
[catching breath] [swallowing] [clicking tongue] [energetic] [exhausted] [drowsy]
[alert] [sluggish] [frantic] [calm and collected] [pitch down] [pitch up]
[whisper quiet] [gradually louder] [gradually softer] [peak volume] [murmur]
You can also invent free-form descriptions — anything descriptive works.
Place tags immediately before the word or phrase they apply to.
{character}
{tone}
{intensity}
{length}
Never break character. Never add disclaimers or meta-commentary.
/no_think"""

CONFIG_PATH = "/app/config.json"

DEFAULT_CONFIG = {
    "default_length":    "short",
    "default_tone":      "casual",
    "default_intensity": 3,
    "think":             False
}

def get_config():
    try:
        with open(CONFIG_PATH) as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except:
        return DEFAULT_CONFIG


class Message(BaseModel):
    role: str
    content: str


class SpeakRequest(BaseModel):
    prompt: str
    mode: str = "conversational"
    tone: Optional[str] = None
    custom_tone: Optional[str] = None
    emotion_intensity: Optional[int] = None
    length: Optional[str] = None
    character: Optional[str] = None
    system_prompt: Optional[str] = None
    voice_reference_audio_b64: Optional[str] = None
    voice_reference_text: Optional[str] = None
    format: str = "mp3"
    speed: float = 1.0
    stream: bool = True
    messages: Optional[List[Message]] = None


def build_system_prompt(req: SpeakRequest, cfg: dict) -> str:
    if req.system_prompt:
        return req.system_prompt

    tone      = req.tone or cfg["default_tone"]
    intensity = req.emotion_intensity if req.emotion_intensity is not None else cfg["default_intensity"]
    length    = req.length or cfg["default_length"]

    tone_text      = req.custom_tone if req.custom_tone else TONE_PROMPTS.get(tone, TONE_PROMPTS["casual"])
    intensity_text = INTENSITY_PROMPTS.get(intensity, INTENSITY_PROMPTS[3])
    length_text    = LENGTH_PROMPTS.get(length, LENGTH_PROMPTS["short"])

    if req.mode == "story":
        tone_text = f"Tell a funny, vivid personal anecdote. Build to a punchline. {tone_text}"

    character_text = ""
    if req.character:
        character_text = f"Character definition: {req.character}"

    return BASE_PROMPT.format(
        character=character_text,
        tone=tone_text,
        intensity=intensity_text,
        length=length_text
    )


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("/app/ui.html", "r") as f:
        return f.read()


@app.get("/health")
async def health():
    cfg = get_config()
    return {"ollama": OLLAMA_URL, "fish": FISH_URL, "model": LLM_MODEL, "config": cfg}


@app.get("/config")
async def read_config():
    return get_config()


@app.post("/config")
async def write_config(cfg: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
    return {"status": "saved", "config": cfg}


@app.post("/speak")
async def speak(req: SpeakRequest):
    cfg    = get_config()
    system = build_system_prompt(req, cfg)

    # Build messages array — use conversation history if provided
    if req.messages:
        messages = [{"role": m.role, "content": m.content} for m in req.messages]
        # Inject system prompt as first message if not already there
        if not messages or messages[0]["role"] != "system":
            messages.insert(0, {"role": "system", "content": system})
    else:
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": req.prompt}
        ]

    async with httpx.AsyncClient(timeout=300) as client:
        # 1. LLM
        llm_resp = await client.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model":    LLM_MODEL,
                "stream":   False,
                "think":    cfg.get("think", False),
                "messages": messages
            }
        )
        llm_resp.raise_for_status()
        generated_text = llm_resp.json()["message"]["content"]

    # Strip thinking tags
    generated_text = re.sub(r'<think>.*?</think>', '', generated_text, flags=re.DOTALL).strip()

    # TTS payload
    tts_payload = {
        "text":        generated_text,
        "format":      req.format,
        "mp3_bitrate": 128,
        "streaming":   req.stream,
        "prosody":     {"speed": req.speed, "volume": 0}
    }
    if req.voice_reference_audio_b64:
        tts_payload["references"] = [{
            "audio": req.voice_reference_audio_b64,
            "text":  req.voice_reference_text or generated_text[:100]
        }]

    media_type = MEDIA_TYPES.get(req.format, "audio/mpeg")

    if req.stream:
        async def stream_audio():
            async with httpx.AsyncClient(timeout=300) as stream_client:
                async with stream_client.stream(
                    "POST", f"{FISH_URL}/v1/tts", json=tts_payload
                ) as r:
                    async for chunk in r.aiter_bytes():
                        yield chunk

        return StreamingResponse(stream_audio(), media_type=media_type)
    else:
        async with httpx.AsyncClient(timeout=300) as tts_client:
            tts_resp = await tts_client.post(f"{FISH_URL}/v1/tts", json=tts_payload)
            tts_resp.raise_for_status()
            return Response(content=tts_resp.content, media_type=media_type)

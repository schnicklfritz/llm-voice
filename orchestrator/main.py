# OLD (broken):
tts_payload = {"text": generated_text}

# NEW (Fish Speech v1/tts correct):
tts_payload = {
    "text": generated_text,
    "format": "wav", 
    "speed": 1.0,
    "volume": 1.0
}

# Voice cloning (if provided):
if hasattr(request, 'voice_reference_audio_b64') and request.voice_reference_audio_b64:
    tts_payload["references"] = [{
        "audio": request.voice_reference_audio_b64,
        "text": getattr(request, 'voice_reference_text', generated_text[:100])
    }]

resp = await client.post(f"{TTS_URL}", json=tts_payload, timeout=60)

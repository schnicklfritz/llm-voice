#!/usr/bin/env python3
"""
Integration test for the LLM + TTS orchestrator.
Requires all three services running (docker‑compose up).
"""

import sys
import json
import base64
import httpx
import tempfile
import os

# Configuration
LLM_URL = "http://localhost:8000/v1"
TTS_URL = "http://localhost:8001/generate"
ORCHESTRATOR_URL = "http://localhost:8002/chat"

def test_llm():
    """Test vLLM OpenAI‑compatible endpoint."""
    print("Testing LLM (vLLM)...")
    try:
        resp = httpx.get(f"{LLM_URL}/health", timeout=10)
        if resp.status_code == 200:
            print("  LLM health OK")
            return True
        else:
            print(f"  LLM health returned {resp.status_code}")
            return False
    except Exception as e:
        print(f"  LLM health error: {e}")
        return False

def test_tts():
    """Test Fish Speech TTS endpoint with a short text."""
    print("Testing TTS (Fish Speech)...")
    try:
        # Simple synthesis request (may fail without reference audio)
        payload = {
            "text": "Hello, this is a test.",
            "language": "en",
            "format": "wav"
        }
        resp = httpx.post(TTS_URL, json=payload, timeout=30)
        if resp.status_code == 200:
            print(f"  TTS success, audio size: {len(resp.content)} bytes")
            # Optionally save a sample
            with open("test_tts_sample.wav", "wb") as f:
                f.write(resp.content)
            print("  Sample saved as test_tts_sample.wav")
            return True
        else:
            print(f"  TTS error: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  TTS request error: {e}")
        return False

def test_orchestrator():
    """Test the orchestrator's /chat endpoint."""
    print("Testing orchestrator /chat...")
    try:
        payload = {
            "text": "Tell me a short joke.",
            "temperature": 0.7,
            "max_tokens": 100
        }
        resp = httpx.post(ORCHESTRATOR_URL, json=payload, timeout=60)
        if resp.status_code == 200:
            data = resp.json()
            print(f"  Orchestrator success: generated {len(data['text'])} characters")
            if "audio_base64" in data and data["audio_base64"]:
                audio = base64.b64decode(data["audio_base64"])
                with open("test_chat_audio.wav", "wb") as f:
                    f.write(audio)
                print("  Audio saved as test_chat_audio.wav")
            return True
        else:
            print(f"  Orchestrator error: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  Orchestrator request error: {e}")
        return False

def main():
    print("=== LLM + TTS Integration Test ===")
    all_ok = True

    # 1. LLM health
    if not test_llm():
        all_ok = False
        print("LLM test failed; skipping further tests.")
        sys.exit(1)

    # 2. TTS
    if not test_tts():
        all_ok = False
        print("TTS test failed; continuing anyway.")

    # 3. Orchestrator
    if not test_orchestrator():
        all_ok = False

    if all_ok:
        print("\nAll tests passed! The pipeline is functional.")
    else:
        print("\nSome tests failed. Check service logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
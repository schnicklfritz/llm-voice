# Voice-LLM Orchestrator (3-Pod QuickPod Swarm)

Minimal 3-pod voice-LLM system: LLM → TTS → Orchestrator.

## Architecture
LLM Pod (2x3090): vLLM Dolphin Mixtral → http://LLM_IP:8000/v1
TTS Pod (5060 Ti): Fish Speech → http://TTS_IP:8080/v1/tts
Orchestrator Pod (CPU): FastAPI → http://ORCH_IP:8002/chat


## QuickPod Deployment
1. Push images to Docker Hub
2. Deploy 3 pods using templates above
3. Copy PUBLIC_IPADDR from each pod
4. Test: `curl -X POST http://ORCH_IP:8002/chat -d '{"text": "Hello"}'`


## Local Testing
```bash
docker compose up -d
curl -X POST http://localhost:8002/chat -d '{"text": "Voice test"}'

Endpoints

POST /chat → {"text": "input"} → audio + text response


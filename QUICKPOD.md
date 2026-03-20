# Quickpod.io Deployment Guide

This guide explains how to deploy the three services (LLM, TTS, orchestrator) as separate GPU rentals on quickpod.io.

## Architecture Overview

Each service runs in its own quickpod.io pod with dedicated GPU(s):

1. **LLM Service** (`dolphin‑mixtral‑vllm`)
   - **GPU**: 2× RTX 3090 (or a single GPU with ≥24 GB VRAM)
   - **Image**: `yourusername/dolphin‑mixtral‑vllm:latest`
   - **Port**: 8000 (exposed publicly)

2. **TTS Service** (`fish‑speech‑tts`)
   - **GPU**: RTX 5060 Ti or any GPU with ≥8 GB VRAM
   - **Image**: `yourusername/fish‑speech‑tts:latest`
   - **Port**: 8001 (exposed publicly)

3. **Orchestrator Service** (`llm‑voice‑orchestrator`)
   - **GPU**: None (can run on CPU)
   - **Image**: `yourusername/llm‑voice‑orchestrator:latest`
   - **Port**: 8002 (exposed publicly)

The orchestrator calls the LLM and TTS services via their public IP addresses.

## Prerequisites

- Docker Hub repositories created (see [README.md](README.md#cicd-building-with-github-actions-and-docker-hub)).
- GitHub Actions workflow has built and pushed the images to Docker Hub.
- A quickpod.io account with credit.

## Step 1: Rent the LLM Pod

1. Go to [quickpod.io](https://quickpod.io) and click **"Rent a GPU"**.
2. Select **2× RTX 3090** (or a single GPU with enough VRAM for Mixtral 8x7B AWQ).
3. In the **"Docker Image"** field, enter:
   ```
   yourusername/dolphin‑mixtral‑vllm:latest
   ```
4. **Environment Variables** (optional but recommended):
   ```
   MODEL=TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ
   QUANTIZATION=awq
   GPU_MEMORY_UTILIZATION=0.9
   TENSOR_PARALLEL_SIZE=2
   MAX_MODEL_LEN=32768
   HOST=0.0.0.0
   PORT=8000
   ```
5. **Port Mapping**: Expose port `8000` (TCP).
6. Launch the pod. Wait for it to start and note its **public IP address** (e.g., `123.45.67.89`).

## Step 2: Rent the TTS Pod

1. Rent another GPU pod with **RTX 5060 Ti** (or any GPU with ≥8 GB VRAM).
2. Docker image:
   ```
   yourusername/fish‑speech‑tts:latest
   ```
3. Environment Variables:
   ```
   MODEL=fish-speech-s2-pro
   DEVICE=cuda
   HOST=0.0.0.0
   PORT=8001
   ```
4. Expose port `8001`.
5. Launch and note its public IP (e.g., `123.45.67.90`).

## Step 3: Rent the Orchestrator Pod (CPU)

1. Rent a **CPU‑only pod** (or a cheap GPU if you prefer).
2. Docker image:
   ```
   yourusername/llm‑voice‑orchestrator:latest
   ```
3. Environment Variables (**critical**):
   ```
   LLM_URL=http://<LLM‑IP>:8000/v1
   TTS_URL=http://<TTS‑IP>:8001/generate
   MODEL_NAME=TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ
   OPENAI_API_KEY=dummy
   HOST=0.0.0.0
   PORT=8002
   ```
   Replace `<LLM‑IP>` and `<TTS‑IP>` with the actual IPs from steps 1 and 2.
4. Expose port `8002`.
5. Launch the pod.

## Step 4: Test the Deployment

1. **Check LLM health**:
   ```bash
   curl http://<LLM‑IP>:8000/health
   ```
   Should return `{"status":"healthy"}`.

2. **Check TTS health**:
   ```bash
   curl http://<TTS‑IP>:8001/health
   ```
   (If the endpoint is not available, try a POST request to `/generate` with dummy text.)

3. **Check orchestrator health**:
   ```bash
   curl http://<ORCH‑IP>:8002/health
   ```
   Should return `{"status":"healthy","llm":true,"tts":true}`.

4. **Run a full chat**:
   ```bash
   curl -X POST http://<ORCH‑IP>:8002/chat \
     -H "Content-Type: application/json" \
     -d '{"text":"Hello, tell me a joke.", "temperature":0.7}' | jq .
   ```
   The response will contain the generated text and optionally `audio_base64`.

## Networking Considerations

- Each pod has its own public IP and firewall. Ensure the ports (8000, 8001, 8002) are open to inbound traffic (they are by default on quickpod.io).
- The orchestrator must be able to reach the LLM and TTS pods over the internet. Use the public IPs.
- If you want to restrict access, you can use quickpod.io’s built‑in firewall to allow only the orchestrator’s IP.

## Scaling

- **LLM**: For higher throughput, rent multiple LLM pods and put a load balancer in front.
- **TTS**: Similarly, scale horizontally by adding more TTS pods.
- **Orchestrator**: Deploy multiple orchestrator instances behind a load balancer (e.g., nginx).

## Cost Optimization

- Use **spot/preemptible** rentals for LLM and TTS to reduce cost.
- Shut down pods when not in use (quickpod.io charges per minute).
- Consider using a single GPU with more VRAM (e.g., RTX 4090) for the LLM if tensor‑parallel size 1 is acceptable.

## Troubleshooting

### "Connection refused" when orchestrator calls LLM/TTS
- Verify the LLM/TTS pods are running (`docker ps` inside the pod).
- Check that the pods’ public IPs are correct and ports are open.
- Ensure the orchestrator’s environment variables point to the correct IPs.

### LLM runs out of memory
- Reduce `GPU_MEMORY_UTILIZATION` to `0.8`.
- Set `TENSOR_PARALLEL_SIZE=1` and use a single GPU (rent a GPU with ≥26 GB VRAM, e.g., RTX 4090).

### TTS fails with "No reference audio"
Fish Speech may require a reference audio for zero‑shot TTS. Provide a short WAV file via the `voice_reference_audio_url` field in the orchestrator request.

### Slow response times
- The first request after pod startup includes model loading (several minutes).
- Subsequent requests should be faster.
- Consider using **warm pods** (keep them running) for production.

## Next Steps

- Implement a web UI (Gradio) that connects to the orchestrator.
- Add authentication to the API endpoints.
- Set up monitoring with Prometheus and Grafana.
- Automate pod provisioning with quickpod.io’s API.

---

For local development or single‑machine deployment, refer to [README.md](README.md).
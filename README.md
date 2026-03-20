# Docker Workflow: Uncensored LLM + Voice Cloning

This project provides a Docker‑based workflow for running an uncensored LLM (Dolphin Mixtral 8x7B) with voice cloning (Fish Speech) on a multi‑GPU setup, optimized for deployment on [quickpod.io](https://quickpod.io).

## Architecture

Three services run in separate containers:

1. **LLM Inference** (`vllm/vllm‑openai`) – serves Dolphin Mixtral 8x7B (AWQ quantized) via an OpenAI‑compatible API.
2. **Voice Cloning** (`fishaudio/fish‑speech`) – runs Fish Speech S2 Pro for zero‑shot/few‑shot TTS.
3. **Orchestrator** (custom FastAPI) – accepts user text, calls LLM, then TTS, and returns synthesized audio.

GPUs are allocated as follows:
- 2× RTX 3090 (indices `0,1`) for LLM (tensor‑parallel)
- 1× RTX 5060 Ti (index `2`) for TTS

## Prerequisites

- A quickpod.io instance with **3 GPUs** (2× RTX 3090 + 1× RTX 5060 Ti) or equivalent.
- NVIDIA drivers and **NVIDIA Container Toolkit** installed on the host (should be pre‑installed on quickpod.io).
- Docker and Docker Compose (v2+).
- At least 50 GB of free disk space for model caching.

## Quick Deployment

1. **Clone the repository** onto your quickpod.io instance:
   ```bash
   git clone <repository‑url>
   cd llm-voice
   ```

2. **Verify GPU visibility**:
   ```bash
   nvidia-smi -L
   ```
   Ensure three GPUs are listed. If the order differs from `0:3090, 1:3090, 2:5060Ti`, adjust `device_ids` in `docker‑compose.yml`.

3. **Build and start the services**:
   ```bash
   docker-compose up --detach --build
   ```
   The first run will download base images and cache model weights (may take 30‑60 minutes depending on network).

4. **Monitor startup logs**:
   ```bash
   docker-compose logs -f llm
   ```
   Wait until you see `"Uvicorn running on http://0.0.0.0:8000"` for LLM and similar messages for TTS.

5. **Run health checks**:
   ```bash
   chmod +x tests/test_health.sh
   ./tests/test_health.sh
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root to override defaults:

```env
# LLM model (AWQ quantized)
LLM_MODEL=TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ

# vLLM settings
GPU_MEMORY_UTILIZATION=0.9
TENSOR_PARALLEL_SIZE=2

# TTS settings (Fish Speech)
TTS_MODEL=fish-speech-s2-pro
```

### GPU Assignment

If your GPU indices differ, modify `docker‑compose.yml` under each service’s `deploy.reservations.devices` section. Use `device_ids` to pin specific GPUs:

```yaml
devices:
  - driver: nvidia
    device_ids: ["0", "1"]   # for LLM
    capabilities: [gpu]
```

### Model Caching

Model weights are cached in Docker volumes (`llm‑models`, `tts‑models`). To clear the cache:
```bash
docker-compose down -v
```

## Testing the Pipeline

After the services are up, run the integration test:

```bash
python3 tests/test_integration.py
```

This will:
1. Check LLM health.
2. Synthesize a test sentence with TTS (saves `test_tts_sample.wav`).
3. Call the orchestrator with a joke prompt and save the resulting audio (`test_chat_audio.wav`).

You can also manually query the orchestrator:

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, how are you?", "temperature": 0.7}' | jq .
```

The response includes the generated text and a `audio_base64` field containing a WAV file encoded in base64.

## Usage with Voice Cloning

Fish Speech supports zero‑shot voice cloning with a reference audio file. Place your reference audio (WAV format, 5‑30 seconds) in the `voices/` directory and pass its URL to the orchestrator:

```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is my cloned voice.",
    "voice_reference_audio_url": "file:///voices/my_voice.wav"
  }'
```

## Performance Notes

- **LLM Inference**: Dolphin Mixtral 8x7B AWQ requires ~26 GB VRAM. With two RTX 3090s (24 GB each) and tensor‑parallel size 2, the model fits comfortably.
- **TTS Inference**: Fish Speech S2 Pro uses ~6 GB VRAM, well within the RTX 5060 Ti’s 8 GB.
- **Latency**: First‑token latency ~1‑2 seconds, end‑to‑end audio generation ~5‑10 seconds depending on response length.
- **Throughput**: The orchestrator can handle multiple concurrent requests; consider scaling services independently if needed.

## Troubleshooting

### “Could not select device driver”

Ensure NVIDIA Container Toolkit is installed and the Docker daemon is configured with the `nvidia` runtime:

```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

If this fails, install the toolkit:
```bash
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Out of Memory (OOM) Errors

- Reduce `GPU_MEMORY_UTILIZATION` to `0.8` in the LLM service.
- Decrease `TENSOR_PARALLEL_SIZE` to `1` if only one GPU is available (requires a smaller model variant).
- For TTS, ensure no other processes are consuming VRAM on GPU 2.

### Model Download Failures

If the Hugging Face cache is inaccessible, pre‑download the AWQ model manually and mount it as a volume:

```bash
git lfs install
git clone https://huggingface.co/TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ ./models/llm
```

Then update the `llm` service volume mount to `./models/llm:/root/.cache/huggingface/hub`.

### TTS Returns “No reference audio”

Fish Speech may require a reference audio for zero‑shot TTS. Provide a short WAV file via `voice_reference_audio_url` or use few‑shot mode (see Fish Speech documentation).

## Monitoring

- **Service logs**: `docker‑compose logs -f <service>`
- **GPU utilization**: `nvidia‑smi` on the host.
- **API endpoints**:
  - LLM: `http://<host>:8000/v1/docs` (OpenAI‑compatible Swagger)
  - TTS: `http://<host>:8001/docs` (if Fish Speech provides)
  - Orchestrator: `http://<host>:8002/docs` (FastAPI auto‑generated docs)

## Scaling

To handle higher load, you can:
- Increase `max_parallel_requests` in vLLM via environment variable `MAX_PARALLEL_REQUESTS`.
- Run multiple TTS containers on different GPU devices (if additional GPUs are available).
- Place a load balancer (nginx, traefik) in front of the orchestrator.

## License

This project is provided as‑is under the MIT License. The Docker images used are subject to their respective licenses (vLLM, Fish Speech).

## References

- [vLLM Documentation](https://docs.vllm.ai)
- [Fish Speech GitHub](https://github.com/fishaudio/fish-speech)
- [Quickpod.io GPU Rental](https://quickpod.io)
- [Dolphin Mixtral 8x7B on Hugging Face](https://huggingface.co/cognitivecomputations/dolphin-2.9.2-mixtral-8x7b)
- [AWQ Quantization](https://github.com/mit-han-lab/llm-awq)
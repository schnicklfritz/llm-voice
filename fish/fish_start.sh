#!/bin/bash
mkdir -p /workspace
mkdir -p /workspace/checkpoints/s2-pro

echo "Downloading s2-pro model..."
/app/.venv/bin/huggingface-cli download fishaudio/s2-pro \
  --local-dir /workspace/checkpoints/s2-pro

echo "Starting Fish Speech server..."
cd /app && /app/.venv/bin/python tools/api_server.py \
  --listen 0.0.0.0:8080 \
  --llama-checkpoint-path /workspace/checkpoints/s2-pro \
  --decoder-checkpoint-path /workspace/checkpoints/s2-pro/codec.pth \
  --decoder-config-name modded_dac_vq &

echo "Done. Test: curl http://localhost:8080/v1/health"

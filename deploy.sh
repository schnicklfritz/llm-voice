#!/bin/bash
# Deployment script for LLM + TTS Docker workflow on quickpod.io
# Usage: ./deploy.sh [--skip-build]

set -e

cd "$(dirname "$0")"

SKIP_BUILD=false
if [[ "$1" == "--skip-build" ]]; then
    SKIP_BUILD=true
fi

echo "========================================"
echo "LLM + Voice Cloning Deployment"
echo "========================================"

# 1. Check GPU availability
echo "[1/6] Checking GPU availability..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi -L
    GPU_COUNT=$(nvidia-smi -L | wc -l)
    echo "Found $GPU_COUNT GPU(s)."
    if [ "$GPU_COUNT" -lt 3 ]; then
        echo "WARNING: At least 3 GPUs are recommended (2 for LLM, 1 for TTS)."
    fi
else
    echo "ERROR: nvidia-smi not found. NVIDIA drivers may not be installed."
    exit 1
fi

# 2. Check Docker and Docker Compose
echo "[2/6] Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed. Please install Docker first."
    exit 1
fi
if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: docker-compose is not installed. Please install Docker Compose."
    exit 1
fi
docker --version
docker-compose --version

# 3. Check NVIDIA Container Toolkit
echo "[3/6] Checking NVIDIA Container Toolkit..."
if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "WARNING: NVIDIA Container Toolkit may not be configured."
    echo "Trying to install NVIDIA Container Toolkit..."
    # Installation steps (Ubuntu/Debian)
    distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt-get update && sudo apt-get install -y nvidia-docker2
    sudo systemctl restart docker
    echo "NVIDIA Container Toolkit installed. Please re-run this script."
    exit 0
fi

# 4. Environment setup
echo "[4/6] Setting up environment..."
if [[ ! -f .env ]]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please review the .env file and adjust values if needed."
else
    echo ".env already exists, skipping."
fi

# 5. Build images (optional)
if [[ "$SKIP_BUILD" == false ]]; then
    echo "[5/6] Building Docker images (this may take a while)..."
    docker-compose build --parallel
else
    echo "[5/6] Skipping build (using cached images)..."
fi

# 6. Start services
echo "[6/6] Starting services with docker-compose..."
docker-compose up -d

echo ""
echo "========================================"
echo "Deployment complete!"
echo "========================================"
echo "Services:"
echo "  LLM (vLLM)          : http://localhost:8000"
echo "  TTS (Fish Speech)   : http://localhost:8001"
echo "  Orchestrator        : http://localhost:8002"
echo ""
echo "Check service logs:"
echo "  docker-compose logs -f llm"
echo ""
echo "Run health test:"
echo "  ./tests/test_health.sh"
echo ""
echo "Run integration test:"
echo "  python3 tests/test_integration.py"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
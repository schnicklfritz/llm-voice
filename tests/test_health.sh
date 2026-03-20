#!/bin/bash
# Health check for LLM + TTS orchestrator services
# Run after docker-compose up -d

set -e

echo "Testing service health..."

# LLM health (vLLM)
echo -n "LLM service (vLLM)... "
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "OK"
else
    echo "FAILED"
    exit 1
fi

# TTS health (Fish Speech)
echo -n "TTS service (Fish Speech)... "
if curl -s -f http://localhost:8001/health > /dev/null; then
    echo "OK"
else
    echo "FAILED (health endpoint may not exist, trying /generate)"
    # Try a simple POST to /generate with dummy data
    if curl -s -f -X POST http://localhost:8001/generate -H "Content-Type: application/json" -d '{"text":"test"}' > /dev/null; then
        echo "POST endpoint works"
    else
        echo "FAILED"
        exit 1
    fi
fi

# Orchestrator health
echo -n "Orchestrator service... "
if curl -s -f http://localhost:8002/health | grep -q '"status":"healthy"'; then
    echo "OK"
else
    echo "FAILED"
    exit 1
fi

echo "All services are healthy."
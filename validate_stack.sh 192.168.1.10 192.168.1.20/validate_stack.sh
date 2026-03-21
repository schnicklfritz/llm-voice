#!/bin/bash
# validate_stack.sh
# Usage: ./validate_stack.sh <OLLAMA_IP> <FISH_IP>

OLLAMA_IP=${1:?"Usage: $0 <OLLAMA_IP> <FISH_IP>"}
FISH_IP=${2:?"Usage: $0 <OLLAMA_IP> <FISH_IP>"}
OLLAMA_URL="http://${OLLAMA_IP}:11434"
FISH_URL="http://${FISH_IP}:8080"
PASS=0
FAIL=0

green() { echo -e "\033[32m✓ $1\033[0m"; }
red()   { echo -e "\033[31m✗ $1\033[0m"; }

check() {
    if [ $1 -eq 0 ]; then
        green "$2"
        PASS=$((PASS + 1))
    else
        red "$2"
        FAIL=$((FAIL + 1))
    fi
}

echo ""
echo "======================================="
echo " Stack Validator"
echo " Ollama : $OLLAMA_URL"
echo " Fish   : $FISH_URL"
echo "======================================="
echo ""

# --- OLLAMA CHECKS ---
echo "[ Ollama ]"

# Reachable
curl -sf --max-time 5 "$OLLAMA_URL" > /dev/null 2>&1
check $? "Ollama reachable"

# Model loaded
MODELS=$(curl -sf --max-time 5 "$OLLAMA_URL/api/tags" 2>/dev/null)
echo "$MODELS" | grep -q "uncensored-model"
check $? "uncensored-model exists"

# GPU loaded (not CPU)
PS_OUTPUT=$(curl -sf --max-time 5 "$OLLAMA_URL/api/ps" 2>/dev/null)
echo "$PS_OUTPUT" | grep -q "uncensored-model"
LOADED=$?
if [ $LOADED -eq 0 ]; then
    # Warm up if not already loaded
    green "Model warm in memory"
else
    echo "  (model not yet loaded into VRAM — sending warm-up prompt...)"
    curl -sf --max-time 60 "$OLLAMA_URL/api/chat" \
        -d '{"model":"uncensored-model","stream":false,"messages":[{"role":"user","content":"hi"}]}' \
        > /dev/null 2>&1
    check $? "Model warm-up prompt"
fi

# Inference test + timing
echo "  Running inference test..."
START=$(date +%s%3N)
RESPONSE=$(curl -sf --max-time 60 "$OLLAMA_URL/api/chat" \
    -d '{"model":"uncensored-model","stream":false,"messages":[{"role":"user","content":"Reply with one word: ready"}]}' \
    2>/dev/null)
END=$(date +%s%3N)
ELAPSED=$((END - START))
echo "$RESPONSE" | grep -q "content"
check $? "Ollama inference OK (${ELAPSED}ms)"

echo ""

# --- FISH SPEECH CHECKS ---
echo "[ Fish Speech ]"

# Reachable
curl -sf --max-time 5 "$FISH_URL" > /dev/null 2>&1
check $? "Fish Speech reachable"

# TTS test + timing
echo "  Running TTS test..."
START=$(date +%s%3N)
TTS_RESULT=$(curl -sf --max-time 60 "$FISH_URL/v1/tts" \
    -H "Content-Type: application/json" \
    -d '{"text":"ready","format":"mp3","mp3_bitrate":128,"streaming":false}' \
    -o /tmp/validate_tts_test.mp3 \
    -w "%{http_code}" 2>/dev/null)
END=$(date +%s%3N)
ELAPSED=$((END - START))
[ "$TTS_RESULT" = "200" ]
check $? "Fish TTS OK — HTTP $TTS_RESULT (${ELAPSED}ms)"

# Check output file has actual content
TTS_SIZE=$(wc -c < /tmp/validate_tts_test.mp3 2>/dev/null || echo 0)
[ "$TTS_SIZE" -gt 1000 ]
check $? "TTS output file valid (${TTS_SIZE} bytes)"

echo ""
echo "======================================="
echo " Results: ${PASS} passed, ${FAIL} failed"
echo "======================================="

if [ $FAIL -eq 0 ]; then
    green " Stack is healthy. Orchestrator is safe to start."
else
    red " Fix failures above before starting orchestrator."
fi

echo ""
rm -f /tmp/validate_tts_test.mp3
exit $FAIL

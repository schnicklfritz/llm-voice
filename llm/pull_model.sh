#!/bin/bash
MODEL=${1:-"huihui_ai/qwen3-abliterated:32b"}

echo "Pulling $MODEL..."
ollama pull $MODEL

echo "Creating optimized modelfile..."
cat > /tmp/Modelfile << EOF
FROM $MODEL
PARAMETER num_gpu 99
PARAMETER num_ctx 8192
EOF

ollama create uncensored-model -f /tmp/Modelfile
echo "Done. Test with: ollama run uncensored-model 'hello'"
```

---

**What each tool is for:**

| Package | Why |
|---|---|
| `apt-utils` | QuickPod validation, suppresses apt warnings |
| `curl` | API testing, health checks |
| `nano` | Quick file edits in pod |
| `wget` | Alternate downloader |
| `netcat-openbsd` | QuickPod validation, port checks |
| `iputils-ping` | Verify pod-to-pod connectivity |
| `net-tools` | `netstat`, `ifconfig` |
| `iproute2` | `ip addr` — get pod IP cleanly |
| `dnsutils` | `nslookup`, `dig` — DNS debugging |
| `lsof` | See what's using port 11434 if ollama won't start |
| `htop` | Watch VRAM/CPU during model load |

---

**QuickPod Template settings:**
```
Docker Image: yourdockerhub/ollama-uncensored:latest
Docker Options:
  --gpus all
  -p 11434:11434
  -e NVIDIA_VISIBLE_DEVICES=all
Launch Mode: Docker Entrypoint
Entrypoint: ollama serve

# GPU Allocation and Device Mapping

## Hardware Specification (Quickpod.io)
- 2× NVIDIA RTX 3090 (24 GB VRAM each) – for LLM inference
- 1× NVIDIA RTX 5060 Ti (8 GB VRAM) – for TTS voice cloning

## Docker GPU Device Mapping
In Docker Compose we use the `deploy.reservations.devices` syntax to assign GPUs to containers.

### Assumptions
1. The host's GPU indices are assigned by the NVIDIA driver in the order they appear in `nvidia-smi`.
2. We assume the two RTX 3090s are indices `0` and `1`, and the RTX 5060 Ti is index `2`.

### Verification
Run `nvidia-smi -L` on the host to list GPUs and their indices:

```bash
nvidia-smi -L
```

Expected output:
```
GPU 0: NVIDIA GeForce RTX 3090 (...)
GPU 1: NVIDIA GeForce RTX 3090 (...)
GPU 2: NVIDIA GeForce RTX 5060 Ti (...)
```

If the ordering differs, adjust the `count` and `device_ids` in the compose file.

## Container GPU Assignment

### LLM Service (`llm`)
- **GPUs**: two devices (indices 0 and 1)
- **vLLM tensor‑parallel size**: 2
- **VRAM requirement**: ~26 GB (Mixtral 8x7B AWQ)
- **Docker Compose configuration**:
  ```yaml
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 2
            capabilities: [gpu]
  ```
  This assigns any two available GPUs. To pin specific devices, use `device_ids` (requires Docker Compose spec 3.8+ with `device_ids` support). If pinning is needed, modify the configuration as follows:
  ```yaml
  devices:
    - driver: nvidia
      device_ids: ["0", "1"]
      capabilities: [gpu]
  ```

### TTS Service (`tts`)
- **GPU**: one device (index 2)
- **VRAM requirement**: ~6 GB (Fish Speech S2 Pro)
- **Docker Compose configuration**:
  ```yaml
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  ```
  To pin to GPU 2:
  ```yaml
  devices:
    - driver: nvidia
      device_ids: ["2"]
      capabilities: [gpu]
  ```

## NVIDIA Container Toolkit Setup
Ensure the host has the NVIDIA Container Toolkit installed and Docker configured to use the `nvidia` runtime.

### Installation (Ubuntu/Debian)
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

### Verify Runtime
```bash
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Quickpod.io Specific Notes
- Quickpod.io instances usually come with NVIDIA drivers and the Container Toolkit pre‑installed.
- The GPU ordering may vary; check with `nvidia-smi` before deployment.
- If the instance has more than three GPUs, you may need to set `NVIDIA_VISIBLE_DEVICES` environment variable in each service to isolate the correct GPUs.

## Testing GPU Visibility
Run a test container to verify GPU visibility for each service:

```bash
# Test LLM GPU visibility
docker run --rm --gpus '"device=0,1"' nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Test TTS GPU visibility
docker run --rm --gpus '"device=2"' nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
```

## Troubleshooting
- **Error "could not select device driver"**: NVIDIA Container Toolkit not installed.
- **GPU not visible inside container**: Check Docker runtime (`docker info | grep -i runtime`).
- **Out of memory**: Reduce `GPU_MEMORY_UTILIZATION` or `TENSOR_PARALLEL_SIZE` for LLM.
- **Incorrect GPU assignment**: Adjust `device_ids` or `count` in compose file.

## References
- [NVIDIA Container Toolkit Documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [Docker Compose GPU Support](https://docs.docker.com/compose/gpu-support/)
- [vLLM Tensor Parallel Configuration](https://docs.vllm.ai/en/latest/getting_started/installation.html#multi‑gpu)
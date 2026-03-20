# vLLM OpenAI-compatible inference server for Dolphin Mixtral 8x7B (AWQ)
# Based on official vLLM image with CUDA 12.1 and Python 3.10

FROM vllm/vllm-openai:latest

# Set environment variables for model configuration
ENV MODEL="TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ"
ENV QUANTIZATION="awq"
ENV GPU_MEMORY_UTILIZATION=0.9
ENV TENSOR_PARALLEL_SIZE=2
ENV MAX_MODEL_LEN=32768
ENV HOST="0.0.0.0"
ENV PORT="8000"

# The base image runs as root; we keep root for simplicity.
# If you need a non‑root user, uncomment the lines below and adjust.
# RUN useradd -m -u 1000 vllm && \
#     chown -R vllm:vllm /home/vllm
# USER vllm

# Expose the OpenAI API port
EXPOSE 8000

# Entrypoint is already set in base image; we just pass arguments
CMD ["--model", "${MODEL}", \
     "--quantization", "${QUANTIZATION}", \
     "--gpu-memory-utilization", "${GPU_MEMORY_UTILIZATION}", \
     "--tensor-parallel-size", "${TENSOR_PARALLEL_SIZE}", \
     "--max-model-len", "${MAX_MODEL_LEN}", \
     "--host", "${HOST}", \
     "--port", "${PORT}"]
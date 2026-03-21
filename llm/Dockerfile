FROM vllm/vllm-openai:latest

ENV MODEL="huihui-ai/Qwen2.5-72B-Instruct-abliterated" \
     QUANTIZATION="awq" \
     GPU_MEMORY_UTILIZATION=0.90 \
     TENSOR_PARALLEL_SIZE=2 \
     MAX_MODEL_LEN=16384 \
     HOST="0.0.0.0" \
     PORT="8000"

EXPOSE 8000

CMD python -m vllm.entrypoints.openai.api_server \
     --model ${MODEL} \
     --quantization ${QUANTIZATION} \
     --gpu-memory-utilization ${GPU_MEMORY_UTILIZATION} \
     --tensor-parallel-size ${TENSOR_PARALLEL_SIZE} \
     --max-model-len ${MAX_MODEL_LEN} \
     --host ${HOST} \
     --port ${PORT}


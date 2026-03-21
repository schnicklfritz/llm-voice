# FastAPI orchestrator service
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (for audio libraries)
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Create non-root user (disabled for compatibility)

# Environment variables
ENV LLM_URL="http://llm:8000/v1"
ENV TTS_URL="http://tts:8001/generate"
ENV MODEL_NAME="TheBloke/dolphin-2.9.2-mixtral-8x7b-AWQ"
ENV OPENAI_API_KEY="dummy"
ENV HOST="0.0.0.0"
ENV PORT="8002"

# Expose the orchestrator port
EXPOSE 8002

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
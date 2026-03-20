# Fish Speech TTS server with voice cloning
# Based on official image

FROM fishaudio/fish-speech:latest

# Set environment variables (adjust as needed)
ENV MODEL="fish-speech-s2-pro"
ENV DEVICE="cuda"
ENV PORT=8001
ENV HOST="0.0.0.0"

# The base image likely already runs as a non‑root user; we skip user creation.
# If you need to run as a specific user, adjust accordingly.

# Expose the HTTP API port
EXPOSE 8001

# The entrypoint is defined in the base image; we can override CMD if needed
# The default command runs the server; we just pass environment variables.
CMD ["serve", "--host", "${HOST}", "--port", "${PORT}"]
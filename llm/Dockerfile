FROM ollama/ollama:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    curl \
    nano \
    wget \
    netcat-openbsd \
    iputils-ping \
    net-tools \
    iproute2 \
    dnsutils \
    lsof \
    htop \
    && rm -rf /var/lib/apt/lists/*

COPY pull_model.sh /usr/local/bin/pull_model.sh
RUN chmod +x /usr/local/bin/pull_model.sh

EXPOSE 11434

CMD ["ollama", "serve"]

FROM fishaudio/fish-speech:server-cuda

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    nano \
    netcat-openbsd \
    iputils-ping \
    net-tools \
    iproute2 \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY fish_start.sh /usr/local/bin/fish_start.sh
RUN chmod +x /usr/local/bin/fish_start.sh

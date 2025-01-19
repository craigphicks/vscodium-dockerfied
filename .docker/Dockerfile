FROM ubuntu:24.04

# Install dependencies needed for VSCodium
RUN apt-get update && apt-get install -y \
    libasound2t64 \
    libatk1.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libsecret-1-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxkbfile1 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libcurl4 \
    xdg-utils \
    libwayland-client0 \
    libwayland-cursor0 \
    libwayland-egl1 \
    libwayland-server0 \
    mesa-utils \
    x11-utils \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set VSCodium version
ENV VSCODIUM_VERSION=1.96.3.25013

# Download and install VSCodium
RUN wget https://github.com/VSCodium/vscodium/releases/download/${VSCODIUM_VERSION}/codium_${VSCODIUM_VERSION}_amd64.deb \
    && apt-get update \
    && apt-get install -y ./codium_${VSCODIUM_VERSION}_amd64.deb \
    && rm codium_${VSCODIUM_VERSION}_amd64.deb \
    && rm -rf /var/lib/apt/lists/*

# Create directories and set permissions
RUN mkdir -p /workspace \
    && mkdir -p /home/ubuntu/.config/VSCodium \
    && mkdir -p /tmp/runtime-docker \
    && chown -R 1000:1000 /workspace /home/ubuntu /tmp/runtime-docker

WORKDIR /workspace

# uncomment load an example extension to show it can be done at build-time
# USER ubuntu
# RUN codium --install-extension ms-python.python

USER root
# Electron-based applications (like VSCodium) spawn multiple processes and deliberately 
# detach from their parent process group. This is typical behavior for Electron apps.
# So we need to wait until the main process exits before we can exit the container!!!
RUN echo '#!/bin/bash' > /usr/local/bin/start.sh && \
    echo 'set -e' >> /usr/local/bin/start.sh && \
    echo 'codium --no-sandbox --user-data-dir=/home/ubuntu/.config/VSCodium "$@"' >> /usr/local/bin/start.sh && \
    echo 'while pgrep -f "codium --no-sandbox" >/dev/null; do sleep 1; done' >> /usr/local/bin/start.sh && \
    chmod +x /usr/local/bin/start.sh

    
ENTRYPOINT ["/usr/local/bin/start.sh"]

FROM mcr.microsoft.com/vscode/devcontainers/base:debian

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN \
    apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        autoconf \
        bluez \
        cmake \
        ffmpeg \
        git \
        libavcodec-dev \
        libavdevice-dev \
        libavfilter-dev \
        libavformat-dev \
        libavutil-dev \
        libpcap-dev \
        libswresample-dev \
        libswscale-dev \
        libturbojpeg0 \
        libudev-dev \
        libxml2 \
        libyaml-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/alexxit/go2rtc:latest /usr/local/bin/go2rtc /bin/go2rtc
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

USER vscode

ENV VIRTUAL_ENV="/home/vscode/.local/ha-venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
ENV SHELL="/bin/bash"

RUN uv python install 3.13 && uv venv "$VIRTUAL_ENV"

RUN git clone --depth 1 https://github.com/home-assistant/hass-release ~/hass-release \
    && uv pip install -e ~/hass-release/

WORKDIR /workspaces

# Runbox Python Runner Image
# Minimal image for running and testing Python code

FROM python:3.11-slim

LABEL org.opencontainers.image.source="https://github.com/kaka-ruto/runbox"
LABEL org.opencontainers.image.description="Runbox Python execution environment"
LABEL org.opencontainers.image.version="0.1.0"

# Python environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install minimal system dependencies
# - iptables: network policy enforcement
# - dnsutils: DNS resolution for network allowlist
RUN apt-get update && apt-get install -y --no-install-recommends \
    iptables \
    dnsutils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python packages
# Minimal set for HTTP requests + testing
RUN pip install --no-cache-dir \
    requests==2.31.0 \
    pytest==8.0.0 \
    && rm -rf /root/.cache/pip

# Create non-root user for code execution
RUN useradd --create-home --shell /bin/bash --uid 1000 runner

# Create working directory
RUN mkdir -p /app && chown runner:runner /app
WORKDIR /app

# Default to showing version (overridden by executor)
CMD ["python", "--version"]

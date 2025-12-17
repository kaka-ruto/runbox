# Runbox Shell Runner Image
# Minimal image for running shell scripts

FROM alpine:3.19

LABEL org.opencontainers.image.source="https://github.com/anywaye/runbox"
LABEL org.opencontainers.image.description="Runbox Shell execution environment"
LABEL org.opencontainers.image.version="0.1.0"

# Install minimal tools
# - bash: shell interpreter
# - curl: HTTP client
# - jq: JSON processing
# - ca-certificates: HTTPS support
# - iptables: network policy
# - bind-tools: DNS resolution (dig, nslookup)
# - bats: Bash Automated Testing System
RUN apk add --no-cache \
    bash \
    curl \
    jq \
    ca-certificates \
    iptables \
    bind-tools \
    bats

# Create non-root user for code execution
RUN adduser -D -s /bin/bash -u 1000 runner

# Create working directory
RUN mkdir -p /app && chown runner:runner /app
WORKDIR /app

# Default to showing version (overridden by executor)
CMD ["bash", "--version"]

# Runbox Ruby Runner Image
# Minimal image for running and testing Ruby code

FROM ruby:3.2-slim

LABEL org.opencontainers.image.source="https://github.com/kaka-ruto/runbox"
LABEL org.opencontainers.image.description="Runbox Ruby execution environment"
LABEL org.opencontainers.image.version="0.1.0"

# Install build dependencies (needed for native gem extensions)
# Then install gems, then remove build tools to reduce attack surface
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    iptables \
    dnsutils \
    && gem install --no-document \
    faraday:2.9.0 \
    webmock:3.19.1 \
    && apt-get purge -y --auto-remove build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && rm -rf /usr/local/bundle/cache/*.gem

# Create non-root user for code execution
RUN useradd --create-home --shell /bin/bash --uid 1000 runner

# Create working directory
RUN mkdir -p /app && chown runner:runner /app
WORKDIR /app

# Default to showing version (overridden by executor)
CMD ["ruby", "--version"]

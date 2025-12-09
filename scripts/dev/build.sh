#!/bin/bash
# Build a single runbox image for local development
# Usage: ./scripts/dev/build.sh <language>

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

# Validate arguments
if [ $# -ne 1 ]; then
    log_error "Usage: $0 <language>"
    log_info "Example: $0 python"
    exit 1
fi

LANGUAGE=$1
validate_language "$LANGUAGE"

# Check Docker
check_docker

# Get version and platform
VERSION=$(get_image_version "$LANGUAGE")
PLATFORM=$(detect_platform)
IMAGE_NAME=$(get_ghcr_image_name "$LANGUAGE" "$VERSION")

log_info "Building $IMAGE_NAME for $PLATFORM"

# Build image (Docker will reuse layers from existing image with same tag)
log_info "Building image..."

docker build \
    --platform "$PLATFORM" \
    -t "$IMAGE_NAME" \
    "images/$LANGUAGE/"

# Prune dangling images
log_info "Pruning dangling images..."
docker image prune -f >/dev/null 2>&1

log_success "Built $IMAGE_NAME"

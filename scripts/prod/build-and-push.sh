#!/bin/bash
# Build and push a single runbox image to GHCR (multi-platform)
# Usage: ./scripts/prod/build-and-push.sh <language>

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

# Get version and SHA
VERSION=$(get_image_version "$LANGUAGE")
SHA=$(get_git_sha)
GHCR_IMAGE=$(get_ghcr_image_name "$LANGUAGE" "$VERSION")
GHCR_IMAGE_SHA="${GHCR_IMAGE}-sha-${SHA}"

log_info "Building and pushing $LANGUAGE image to GHCR"
log_info "Version: $VERSION"
log_info "SHA: $SHA"
log_info "Tags: $GHCR_IMAGE and $GHCR_IMAGE_SHA"

# Check if buildx is available
if ! docker buildx version >/dev/null 2>&1; then
    log_error "docker buildx is not available. Please install it first."
    exit 1
fi

# Build and push multi-platform image
log_info "Building multi-platform image (amd64, arm64)..."
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    -t "$GHCR_IMAGE" \
    -t "$GHCR_IMAGE_SHA" \
    --push \
    "images/$LANGUAGE/"

log_success "Pushed $GHCR_IMAGE"
log_success "Pushed $GHCR_IMAGE_SHA"

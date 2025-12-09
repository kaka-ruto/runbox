#!/bin/bash
# Clean up a specific runbox image
# Usage: ./scripts/dev/cleanup.sh <language>

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

# Get version
VERSION=$(get_image_version "$LANGUAGE")
IMAGE_NAME=$(get_local_image_name "$LANGUAGE" "$VERSION")

log_info "Cleaning up $IMAGE_NAME"

# Remove image
if docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    docker rmi "$IMAGE_NAME" 2>/dev/null || true
    log_success "Removed $IMAGE_NAME"
else
    log_warning "Image $IMAGE_NAME not found"
fi

# Prune dangling images
log_info "Pruning dangling images..."
docker image prune -f >/dev/null 2>&1

log_success "Cleanup completed for $LANGUAGE"

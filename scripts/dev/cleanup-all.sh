#!/bin/bash
# Clean up all runbox images
# Usage: ./scripts/dev/cleanup-all.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

# Check Docker
check_docker

log_info "Cleaning up all runbox images..."

# Remove all ghcr.io/kaka-ruto/runbox/* images
IMAGES=$(docker images --filter "reference=ghcr.io/kaka-ruto/runbox/*" -q)
if [ -n "$IMAGES" ]; then
    echo "$IMAGES" | xargs docker rmi -f 2>/dev/null || true
    log_success "Removed all runbox images"
else
    log_warning "No runbox images found"
fi

# Prune dangling images
log_info "Pruning dangling images..."
docker image prune -f >/dev/null 2>&1

log_success "Cleanup completed for all images"

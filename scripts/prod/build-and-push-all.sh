#!/bin/bash
# Build and push all runbox images to GHCR (multi-platform)
# Usage: ./scripts/prod/build-and-push-all.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

log_info "Building and pushing all runbox images to GHCR..."

FAILED=0

# Build and push each language sequentially
for LANGUAGE in $(get_all_languages); do
    echo ""
    if ! "$SCRIPT_DIR/build-and-push.sh" "$LANGUAGE"; then
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    log_success "All images built and pushed successfully"
    exit 0
else
    log_error "$FAILED image(s) failed to build/push"
    exit 1
fi

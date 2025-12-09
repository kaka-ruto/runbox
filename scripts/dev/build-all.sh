#!/bin/bash
# Build all runbox images for local development
# Usage: ./scripts/dev/build-all.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

log_info "Building all runbox images..."

# Build each language sequentially
for LANGUAGE in $(get_all_languages); do
    echo ""
    "$SCRIPT_DIR/build.sh" "$LANGUAGE"
done

echo ""
log_success "All images built successfully"

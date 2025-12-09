#!/bin/bash
# Build and test all runbox images
# Usage: ./scripts/dev/build-and-test-all.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

log_info "Building and testing all runbox images..."

# Build all
"$SCRIPT_DIR/build-all.sh"

echo ""

# Test all
"$SCRIPT_DIR/test-all.sh"

echo ""
log_success "All images built and tested successfully"

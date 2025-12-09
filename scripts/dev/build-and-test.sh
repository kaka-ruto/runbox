#!/bin/bash
# Build and test a single runbox image
# Usage: ./scripts/dev/build-and-test.sh <language>

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

log_info "Building and testing $LANGUAGE image..."

# Build
"$SCRIPT_DIR/build.sh" "$LANGUAGE"

echo ""

# Test
"$SCRIPT_DIR/test.sh" "$LANGUAGE"

echo ""
log_success "Build and test completed for $LANGUAGE"

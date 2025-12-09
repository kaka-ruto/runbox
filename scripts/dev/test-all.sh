#!/bin/bash
# Test all runbox images
# Usage: ./scripts/dev/test-all.sh

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source common functions
source "$SCRIPT_DIR/../lib/common.sh"

# Change to project root
cd "$PROJECT_ROOT"

log_info "Testing all runbox images..."

FAILED=0

# Test each language sequentially
for LANGUAGE in $(get_all_languages); do
    echo ""
    if ! "$SCRIPT_DIR/test.sh" "$LANGUAGE"; then
        FAILED=$((FAILED + 1))
    fi
done

echo ""
if [ $FAILED -eq 0 ]; then
    log_success "All tests passed"
    exit 0
else
    log_error "$FAILED test(s) failed"
    exit 1
fi

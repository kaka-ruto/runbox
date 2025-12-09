#!/bin/bash
# Test a single runbox image
# Usage: ./scripts/dev/test.sh <language>

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

log_info "Testing $IMAGE_NAME"

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    log_error "Image $IMAGE_NAME not found. Build it first with: ./scripts/dev/build.sh $LANGUAGE"
    exit 1
fi

# Run language-specific tests
TEST_SCRIPT="images/$LANGUAGE/test.sh"
if [ -f "$TEST_SCRIPT" ]; then
    bash "$TEST_SCRIPT" "$IMAGE_NAME"
else
    log_warning "No test script found at $TEST_SCRIPT"
    log_info "Running basic smoke test..."
    docker run --rm "$IMAGE_NAME" echo "Container starts successfully"
fi

log_success "Tests passed for $IMAGE_NAME"

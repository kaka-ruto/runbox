#!/bin/bash
# Smoke tests for Shell image
# Usage: ./images/shell/test.sh <image_name>

set -e

IMAGE=$1

if [ -z "$IMAGE" ]; then
    echo "Error: Image name required"
    exit 1
fi

echo "Running smoke tests for $IMAGE..."

# Test 1: Container starts and Bash works
echo -n "  ✓ Bash version: "
docker run --rm --user runner "$IMAGE" bash --version | head -n1

# Test 2: Tools are installed
echo -n "  ✓ Checking curl... "
docker run --rm --user runner "$IMAGE" curl --version >/dev/null && echo "OK"

echo -n "  ✓ Checking jq... "
docker run --rm --user runner "$IMAGE" jq --version >/dev/null && echo "OK"

# Test 3: Non-root user
echo -n "  ✓ User check: "
USER=$(docker run --rm --user runner "$IMAGE" whoami)
if [ "$USER" != "runner" ]; then
    echo "FAILED (expected 'runner', got '$USER')"
    exit 1
fi
echo "$USER"

# Test 4: Working directory
echo -n "  ✓ Working directory: "
PWD=$(docker run --rm --user runner "$IMAGE" pwd)
if [ "$PWD" != "/app" ]; then
    echo "FAILED (expected '/app', got '$PWD')"
    exit 1
fi
echo "$PWD"

# Test 5: Can execute a simple script
echo -n "  ✓ Script execution: "
OUTPUT=$(docker run --rm --user runner "$IMAGE" bash -c "echo 'Hello from Shell'")
if [ "$OUTPUT" != "Hello from Shell" ]; then
    echo "FAILED"
    exit 1
fi
echo "OK"

echo "All smoke tests passed for $IMAGE"

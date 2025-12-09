#!/bin/bash
# Smoke tests for Python image
# Usage: ./images/python/test.sh <image_name>

set -e

IMAGE=$1

if [ -z "$IMAGE" ]; then
    echo "Error: Image name required"
    exit 1
fi

echo "Running smoke tests for $IMAGE..."

# Test 1: Container starts and Python works
echo -n "  ✓ Python version: "
docker run --rm --user runner "$IMAGE" python --version

# Test 2: Packages are installed
echo -n "  ✓ Checking packages... "
docker run --rm --user runner "$IMAGE" python -c "import requests; import pytest" && echo "OK"

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
OUTPUT=$(docker run --rm --user runner "$IMAGE" python -c "print('Hello from Python')")
if [ "$OUTPUT" != "Hello from Python" ]; then
    echo "FAILED"
    exit 1
fi
echo "OK"

echo "All smoke tests passed for $IMAGE"

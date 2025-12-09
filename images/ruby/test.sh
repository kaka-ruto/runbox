#!/bin/bash
# Smoke tests for Ruby image
# Usage: ./images/ruby/test.sh <image_name>

set -e

IMAGE=$1

if [ -z "$IMAGE" ]; then
    echo "Error: Image name required"
    exit 1
fi

echo "Running smoke tests for $IMAGE..."

# Test 1: Container starts and Ruby works
echo -n "  ✓ Ruby version: "
docker run --rm --user runner "$IMAGE" ruby --version

# Test 2: Gems are installed
echo -n "  ✓ Checking gems... "
docker run --rm --user runner "$IMAGE" ruby -e "require 'faraday'; require 'webmock'" && echo "OK"

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
OUTPUT=$(docker run --rm --user runner "$IMAGE" ruby -e "puts 'Hello from Ruby'")
if [ "$OUTPUT" != "Hello from Ruby" ]; then
    echo "FAILED"
    exit 1
fi
echo "OK"

echo "All smoke tests passed for $IMAGE"

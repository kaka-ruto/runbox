#!/bin/bash
# Common functions for runbox build and test scripts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}❌${NC} $1"
}

# Detect platform architecture
detect_platform() {
    case "$(uname -m)" in
        arm64|aarch64)
            echo "linux/arm64"
            ;;
        x86_64|amd64)
            echo "linux/amd64"
            ;;
        *)
            log_error "Unsupported architecture: $(uname -m)"
            exit 1
            ;;
    esac
}

# Get image version from VERSION file
get_image_version() {
    local language=$1
    local version_file="images/$language/VERSION"
    
    if [ -f "$version_file" ]; then
        cat "$version_file"
    else
        log_error "VERSION file not found for $language image at $version_file"
        exit 1
    fi
}

# Validate language argument
validate_language() {
    local language=$1
    case "$language" in
        python|ruby|shell)
            return 0
            ;;
        *)
            log_error "Invalid language: $language"
            log_info "Valid languages: python, ruby, shell"
            exit 1
            ;;
    esac
}

# Get all supported languages
get_all_languages() {
    echo "python ruby shell"
}

# Get GHCR image name
get_ghcr_image_name() {
    local language=$1
    local version=$2
    echo "ghcr.io/anywaye/runbox/$language:$version"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Get git commit SHA (short)
get_git_sha() {
    git rev-parse --short HEAD 2>/dev/null || echo "unknown"
}

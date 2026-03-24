# Runbox Image Build Scripts

This directory contains scripts for building and testing runbox container images.

## Directory Structure

```
scripts/
├── dev/                    # Development scripts (local builds)
│   ├── build.sh           # Build a single image
│   ├── build-all.sh       # Build all images
│   ├── test.sh            # Test a single image
│   ├── test-all.sh        # Test all images
│   ├── build-and-test.sh  # Build and test a single image
│   ├── build-and-test-all.sh  # Build and test all images
│   ├── cleanup.sh         # Clean up a single image
│   └── cleanup-all.sh     # Clean up all images
│
├── prod/                   # Production scripts (GHCR builds)
│   ├── build-and-push.sh  # Build and push a single image
│   └── build-and-push-all.sh  # Build and push all images
│
└── lib/
    └── common.sh          # Shared functions
```

## Development Workflow

### Build a Single Image

```bash
./scripts/dev/build.sh python
./scripts/dev/build.sh ruby
./scripts/dev/build.sh shell
```

This will:
- Build the image for your native architecture (arm64 or amd64)
- Tag as `runbox-<language>:<version>` (e.g., `runbox-python:3.11`)
- **Leverage Docker layer caching** for fast rebuilds (unchanged layers are reused)
- Prune dangling images (old untagged images from previous builds)

**Performance:** First build takes ~60-90s, subsequent builds with no changes take ~1-2s thanks to layer caching!

### Build All Images

```bash
./scripts/dev/build-all.sh
```

Builds all three images sequentially.

### Test a Single Image

```bash
./scripts/dev/test.sh python
./scripts/dev/test.sh ruby
./scripts/dev/test.sh shell
```

Runs smoke tests to verify:
- Container starts successfully
- Runtime version is correct
- Required packages/tools are installed
- Non-root user is configured
- Working directory is `/app`
- Can execute simple scripts

### Test All Images

```bash
./scripts/dev/test-all.sh
```

Tests all three images and reports overall success/failure.

### Build and Test (Combined)

```bash
# Single image
./scripts/dev/build-and-test.sh python

# All images
./scripts/dev/build-and-test-all.sh
```

Convenience scripts that build and test in one command.

### Clean Up Images

```bash
# Clean up a single image
./scripts/dev/cleanup.sh python

# Clean up all runbox images
./scripts/dev/cleanup-all.sh
```

Removes images and prunes dangling images.

**When to use cleanup:**
- **Force fresh build**: When you want to rebuild from scratch without layer caching (e.g., to test the build process)
- **Free disk space**: When you want to remove all runbox images
- **Troubleshooting**: When cached layers might be causing issues

**Note:** During normal development, you don't need to run cleanup scripts. The build process automatically prunes dangling images while preserving layer caching for fast rebuilds.

## Production Workflow

### Build and Push to GHCR

**Prerequisites:**
- Docker buildx installed
- Authenticated to GHCR (`docker login ghcr.io`)

```bash
# Single image
./scripts/prod/build-and-push.sh python

# All images
./scripts/prod/build-and-push-all.sh
```

This will:
- Build multi-platform images (linux/amd64 and linux/arm64)
- Tag with version: `ghcr.io/kaka-ruto/runbox-<language>:<version>`
- Tag with SHA: `ghcr.io/kaka-ruto/runbox-<language>:<version>-sha-<commit>`
- Push both tags to GHCR

### GitHub Actions

Images are automatically built and pushed to GHCR when:
- Dockerfiles are changed and pushed to `main`
- `images/shell/VERSION` is changed and pushed to `main`
- Manually triggered via GitHub Actions UI

To manually trigger:
1. Go to Actions tab in GitHub
2. Select "Build and Push Images" workflow
3. Click "Run workflow"
4. Choose language (or "all")

## Image Versioning

Images are tagged based on the runtime version:

- **Python**: Extracted from `FROM python:X.Y` in Dockerfile
  - Example: `runbox-python:3.11`
- **Ruby**: Extracted from `FROM ruby:X.Y` in Dockerfile
  - Example: `runbox-ruby:3.2`
- **Shell**: Read from `images/shell/VERSION` file (bash version)
  - Example: `runbox-shell:5.2`

## Architecture Support

### Local Development
- Builds for your native architecture only (arm64 on M1 Mac, amd64 on Intel)
- Fast builds, no emulation

### Production (GHCR)
- Builds for both linux/amd64 and linux/arm64
- Uses Docker buildx for multi-platform builds

## Troubleshooting

### "Docker is not running"
Start Docker Desktop and try again.

### "Image not found" when testing
Build the image first: `./scripts/dev/build.sh <language>`

### "docker buildx is not available"
Install Docker buildx:
```bash
docker buildx install
```

### Permission denied
Make scripts executable:
```bash
chmod +x scripts/dev/*.sh scripts/prod/*.sh
```

## Examples

```bash
# Typical development workflow
./scripts/dev/build-and-test.sh python
./scripts/dev/build-and-test.sh ruby
./scripts/dev/build-and-test.sh shell

# Or all at once
./scripts/dev/build-and-test-all.sh

# Clean up when done
./scripts/dev/cleanup-all.sh

# Push to production (after testing locally)
./scripts/prod/build-and-push.sh python
```

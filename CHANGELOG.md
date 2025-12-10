# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **`new_dependencies` parameter** in `/v1/run` endpoint: Install dependencies on-the-fly before code execution
  - Python: Uses `pip install --no-cache-dir`
  - Ruby: Uses `gem install --no-document`
  - Shell: Uses `apk add --no-cache`
- **`packages` field** in run response: Returns updated package list when dependencies are installed
  - Only included when `new_dependencies` were provided
  - Dictionary of package names to versions

### Example

```json
POST /v1/run
{
  "container_id": "runbox-project-123-python",
  "files": [{"path": "main.py", "content": "import requests; print(requests.__version__)"}],
  "entrypoint": "main.py",
  "new_dependencies": ["requests==2.31.0"]
}

Response:
{
  "success": true,
  "exit_code": 0,
  "stdout": "2.31.0\n",
  "stderr": "",
  "execution_time_ms": 1234,
  "timeout_exceeded": false,
  "packages": {
    "pip": "23.0.1",
    "requests": "2.31.0",
    ...
  }
}
```

## [1.0.0] - 2025-12-10

### Breaking Changes

- **New API workflow**: Two-step `/v1/setup` + `/v1/run` workflow
- `/v1/run` endpoint signature changed:
  - Now requires `container_id` instead of `identifier` and `language`
  - Removed `memory` and `network_allow` parameters (moved to `/v1/setup`)
- Run response no longer includes `container_id` and `cached` fields (now in setup response)

### Added

- **`/v1/setup` endpoint**: Creates or reuses a container and returns environment information
  - Returns `container_id`, `cached`, and `environment_snapshot`
  - `environment_snapshot` includes OS, runtime, and package information
- **Environment introspection**: Detailed container environment information
  - OS name and version
  - Runtime name and version
  - Installed packages with versions

### Changed

- Renamed internal `CodeExecutor` to `CodeRunner`
- Renamed `execute()` methods to `run()`
- Improved error handling with specific error types

## [0.1.0] - 2024-12-01

### Added

- Initial release
- `/v1/run` endpoint for executing code in isolated containers
- Support for Python, Ruby, and Shell languages
- Container reuse via identifiers
- Environment variables, timeouts, memory limits, network allowlisting
- `/v1/containers/{identifier}` DELETE endpoint for cleanup
- `/v1/health` endpoint for health checks
- Comprehensive error handling
- API key authentication

## README.md

# Runbox

A fast, secure, and simple API for running code in isolated containers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Features

- 🚀 **Fast**: Per-identifier persistent containers for instant repeat executions
- 🔒 **Secure**: Network allowlisting, resource limits, isolated execution
- 🌐 **Multi-language**: Python, Ruby, Shell out of the box
- ⚙️ **Configurable**: Timeouts, memory limits, network policies per request
- 🧹 **Self-cleaning**: Automatic cleanup of idle containers
- 🔍 **Environment Introspection**: Get OS, runtime, and package info before running code

## Development Setup

### Prerequisites
- Python 3.11+
- Docker Desktop running

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/anywaye/runbox.git
cd runbox

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/core/test_runner.py -v

# Run with coverage
pytest tests/ --cov=src/runbox --cov-report=html
```

## Quick Start

### Using Docker Compose

```bash
git clone https://github.com/anywaye/runbox.git
cd runbox
cp runbox.example.yml runbox.yml
docker-compose up
```

### Step 1: Set Up a Container

First, call `/setup` to create a container and get environment info:

```bash
curl -X POST http://localhost:8080/v1/setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "identifier": "my-session",
    "language": "python"
  }'
```

Response:

```json
{
  "container_id": "runbox-my-session-python",
  "cached": false,
  "environment_snapshot": {
    "os_name": "debian",
    "os_version": "12",
    "runtime_name": "python",
    "runtime_version": "3.11.6",
    "packages": {
      "pip": "23.0.1",
      "requests": "2.31.0",
      "pytest": "8.0.0"
    }
  }
}
```

### Step 2: Run Code

Then, use the `container_id` to run code:

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "container_id": "runbox-my-session-python",
    "files": [{"path": "main.py", "content": "print(\"Hello, Runbox!\")"}],
    "run_command": "python main.py"
  }'
```

Response:

```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Hello, Runbox!\n",
  "stderr": "",
  "execution_time_ms": 45,
  "timeout_exceeded": false
}
```

### Installing Dependencies On-The-Fly

Install new dependencies before running code:

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "container_id": "runbox-my-session-python",
    "files": [{"path": "main.py", "content": "import requests; print(requests.__version__)"}],
    "run_command": "python main.py",
    "new_dependencies": ["requests==2.31.0", "pytest"]
  }'
```

Response includes updated package list:

```json
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
    "pytest": "7.4.0"
  }
}
```

**Supported package managers:**
- Python: `pip install --no-cache-dir`
- Ruby: `gem install --no-document`
- Shell: `apk add --no-cache`

## Documentation

- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [API Reference](docs/api-reference.md)
- [Security](docs/security.md)
- [Deployment](docs/deployment/)

## Client Libraries

- [runbox-rb](https://github.com/anywaye/runbox-rb) - Ruby client
- [runbox-py](https://github.com/anywaye/runbox-py) - Python client

## License

MIT License - see [LICENSE](LICENSE) for details.

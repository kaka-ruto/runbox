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
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/core/test_executor.py -v

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

### Run Some Code

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "identifier": "my-session",
    "language": "python",
    "files": [{"path": "main.py", "content": "print(\"Hello, Runbox!\")"}],
    "entrypoint": "main.py"
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
  "container_id": "runbox-my-session-python",
  "cached": false
}
```

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

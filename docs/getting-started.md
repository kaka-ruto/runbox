# Getting Started

Get Runbox running in 5 minutes.

## Prerequisites

- Docker installed and running
- Python 3.11+ (for development) or just Docker (for deployment)

## Quick Start with Docker

1. **Clone the repository**

```bash
git clone https://github.com/anywaye/runbox.git
cd runbox
```

2. **Configure**

```bash
cp runbox.example.yml runbox.yml
# Edit runbox.yml to set your API key
```

3. **Start Runbox**

```bash
docker-compose up -d
```

4. **Test it**

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

## Local Development

1. **Create virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. **Install dependencies**

```bash
pip install -e ".[dev]"
```

3. **Run the server**

```bash
export RUNBOX_API_KEY=dev-key
runbox
```

4. **Run tests**

```bash
pytest
```

## Next Steps

- [Configuration](configuration.md) - Customize settings
- [API reference](api-reference.md) - Learn the API
- [Deployment](deployment.md) - Deploy to production

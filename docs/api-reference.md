# API Reference

## Authentication

All endpoints except `/v1/health` require authentication.

Include your API key in the `Authorization` header:

```
Authorization: Bearer your-api-key
```

## Endpoints

### POST /v1/run

Execute code in a sandboxed container.

**Request Body**

| Field           | Type    | Required | Description                                      |
| --------------- | ------- | -------- | ------------------------------------------------ |
| `identifier`    | string  | Yes      | Unique identifier for container reuse            |
| `language`      | string  | Yes      | Programming language (`python`, `ruby`, `shell`) |
| `files`         | array   | Yes      | Files to write before execution                  |
| `entrypoint`    | string  | Yes      | File to execute                                  |
| `env`           | object  | No       | Environment variables                            |
| `timeout`       | integer | No       | Timeout in seconds (default: 30, max: 300)       |
| `memory`        | string  | No       | Memory limit (default: "256m")                   |
| `network_allow` | array   | No       | Allowed network destinations                     |

**File Object**

| Field     | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| `path`    | string | File path relative to working directory |
| `content` | string | File content                            |

**Response**

| Field               | Type    | Description                               |
| ------------------- | ------- | ----------------------------------------- |
| `success`           | boolean | Whether execution succeeded (exit code 0) |
| `exit_code`         | integer | Process exit code                         |
| `stdout`            | string  | Standard output                           |
| `stderr`            | string  | Standard error                            |
| `execution_time_ms` | integer | Execution time in milliseconds            |
| `container_id`      | string  | Container identifier                      |
| `cached`            | boolean | Whether container was reused              |
| `timeout_exceeded`  | boolean | Whether execution timed out               |

**Example**

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "identifier": "project-123",
    "language": "python",
    "files": [
      {"path": "main.py", "content": "print(\"Hello!\")"}
    ],
    "entrypoint": "main.py",
    "timeout": 30,
    "network_allow": ["api.stripe.com"]
  }'
```

### DELETE /v1/containers/{identifier}

Force cleanup all containers for an identifier.

**Response**

| Field     | Type  | Description                   |
| --------- | ----- | ----------------------------- |
| `deleted` | array | List of deleted container IDs |

### GET /v1/health

Health check endpoint. Does not require authentication.

**Response**

| Field     | Type   | Description                |
| --------- | ------ | -------------------------- |
| `status`  | string | Service status ("healthy") |
| `version` | string | Service version            |

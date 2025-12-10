# API Reference

## Authentication

All endpoints except `/v1/health` require authentication.

Include your API key in the `Authorization` header:

```
Authorization: Bearer your-api-key
```

## Endpoints

### POST /v1/setup

Set up a container and get environment information. This should be called first before running code.

**Request Body**

| Field           | Type    | Required | Description                                      |
| --------------- | ------- | -------- | ------------------------------------------------ |
| `identifier`    | string  | Yes      | Unique identifier for container reuse            |
| `language`      | string  | Yes      | Programming language (`python`, `ruby`, `shell`) |
| `env`           | object  | No       | Environment variables to set                     |
| `timeout`       | integer | No       | Default timeout in seconds (default: 30)         |
| `memory`        | string  | No       | Memory limit (default: "256m")                   |
| `network_allow` | array   | No       | Allowed network destinations                     |

**Response**

| Field                  | Type    | Description                               |
| ---------------------- | ------- | ----------------------------------------- |
| `container_id`         | string  | Container ID to use in /run calls         |
| `cached`               | boolean | Whether container was reused              |
| `environment_snapshot` | object  | Environment information (see below)       |

**Environment Snapshot Object**

| Field             | Type   | Description                               |
| ----------------- | ------ | ----------------------------------------- |
| `os_name`         | string | Operating system name (e.g., "debian")    |
| `os_version`      | string | Operating system version (e.g., "12")     |
| `runtime_name`    | string | Runtime name (e.g., "python", "ruby")     |
| `runtime_version` | string | Runtime version (e.g., "3.11.6")          |
| `packages`        | object | Map of package names to versions          |

**Example**

```bash
curl -X POST http://localhost:8080/v1/setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "identifier": "project-123",
    "language": "python"
  }'
```

**Response**

```json
{
  "container_id": "runbox-project-123-python",
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

---

### POST /v1/run

Run code in a container that was set up via `/setup`.

**Request Body**

| Field          | Type    | Required | Description                                      |
| -------------- | ------- | -------- | ------------------------------------------------ |
| `container_id` | string  | Yes      | Container ID from /setup response                |
| `files`        | array   | Yes      | Files to write before running                    |
| `entrypoint`   | string  | Yes      | File to run                                      |
| `env`          | object  | No       | Runtime environment variables                    |
| `timeout`      | integer | No       | Timeout in seconds (default: 30, max: 300)       |

**File Object**

| Field     | Type   | Description                             |
| --------- | ------ | --------------------------------------- |
| `path`    | string | File path relative to working directory |
| `content` | string | File content                            |

**Response**

| Field               | Type    | Description                               |
| ------------------- | ------- | ----------------------------------------- |
| `success`           | boolean | Whether run succeeded (exit code 0)       |
| `exit_code`         | integer | Process exit code                         |
| `stdout`            | string  | Standard output                           |
| `stderr`            | string  | Standard error                            |
| `execution_time_ms` | integer | Execution time in milliseconds            |
| `timeout_exceeded`  | boolean | Whether run timed out                     |

**Example**

```bash
curl -X POST http://localhost:8080/v1/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "container_id": "runbox-project-123-python",
    "files": [
      {"path": "main.py", "content": "print(\"Hello!\")"}
    ],
    "entrypoint": "main.py",
    "timeout": 30
  }'
```

**Response**

```json
{
  "success": true,
  "exit_code": 0,
  "stdout": "Hello!\n",
  "stderr": "",
  "execution_time_ms": 42,
  "timeout_exceeded": false
}
```

---

### DELETE /v1/containers/{identifier}

Force cleanup all containers for an identifier.

**Response**

| Field     | Type  | Description                   |
| --------- | ----- | ----------------------------- |
| `deleted` | array | List of deleted container IDs |

**Example**

```bash
curl -X DELETE http://localhost:8080/v1/containers/project-123 \
  -H "Authorization: Bearer your-api-key"
```

---

### GET /v1/health

Health check endpoint. Does not require authentication.

**Response**

| Field     | Type   | Description                |
| --------- | ------ | -------------------------- |
| `status`  | string | Service status ("healthy") |
| `version` | string | Service version            |

---

## Error Responses

All error responses have the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Common Status Codes**

| Code | Description                           |
| ---- | ------------------------------------- |
| 400  | Bad request (invalid parameters)      |
| 401  | Unauthorized (missing/invalid API key)|
| 404  | Not found (container doesn't exist)   |
| 422  | Validation error                      |
| 500  | Internal server error                 |

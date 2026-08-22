# CodeFlow Engine - API Documentation

Complete API reference for the CodeFlow Engine REST API and WebSocket endpoints.

---

## Base URL

```
Production: https://app.codeflow.celladoresystems.com
Development: http://localhost:8000
```

---

## Authentication

### API Key Authentication

Most endpoints require an API key passed in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://app.codeflow.celladoresystems.com/api/status
```

### GitHub App Authentication

For GitHub App endpoints, authentication is handled via OAuth flow.

---

## API Endpoints

### Health & Status

#### `GET /health`

Health check endpoint.

**Query Parameters:**
- `detailed` (boolean, optional): Return detailed health info (default: `false`)

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.1",
  "database": "connected",
  "redis": "connected",
  "uptime_seconds": 3600.5
}
```

**Example:**
```bash
curl https://app.codeflow.celladoresystems.com/health
curl https://app.codeflow.celladoresystems.com/health?detailed=true
```

---

### Dashboard API

#### `GET /api/status`

Get dashboard status and statistics.

**Authentication:** Required (API Key)

**Response:**
```json
{
  "uptime_seconds": 3600.5,
  "uptime_formatted": "1h 0m 0s",
  "total_checks": 150,
  "total_issues": 45,
  "success_rate": 0.98,
  "average_processing_time": 2.5,
  "quality_stats": {
    "fast": {
      "count": 100,
      "avg_time": 1.5
    },
    "comprehensive": {
      "count": 50,
      "avg_time": 5.0
    }
  }
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" https://app.codeflow.celladoresystems.com/api/status
```

---

#### `GET /api/metrics`

Get metrics data for dashboard charts.

**Authentication:** Required (API Key)

**Response:**
```json
{
  "processing_times": [
    {"timestamp": "2025-01-15T10:00:00Z", "time": 2.5},
    {"timestamp": "2025-01-15T10:05:00Z", "time": 2.3}
  ],
  "issue_counts": [
    {"timestamp": "2025-01-15T10:00:00Z", "count": 5},
    {"timestamp": "2025-01-15T10:05:00Z", "count": 3}
  ],
  "quality_mode_usage": {
    "fast": 100,
    "comprehensive": 50,
    "ai_enhanced": 25
  }
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" https://app.codeflow.celladoresystems.com/api/metrics
```

---

#### `GET /api/history`

Get activity history with pagination.

**Authentication:** Required (API Key)

**Query Parameters:**
- `limit` (integer, optional): Maximum records to return (1-100, default: 50)
- `offset` (integer, optional): Number of records to skip (default: 0)

**Response:**
```json
[
  {
    "timestamp": "2025-01-15T10:00:00Z",
    "mode": "fast",
    "files_checked": 10,
    "issues_found": 5,
    "processing_time": 2.5,
    "success": true
  }
]
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" \
  "https://app.codeflow.celladoresystems.com/api/history?limit=20&offset=0"
```

---

#### `POST /api/quality-check`

Run a quality check on specified files or directory.

**Authentication:** Required (API Key)  
**Rate Limit:** 10 requests per minute per IP

**Request Body:**
```json
{
  "mode": "fast",
  "files": ["src/main.py", "src/utils.py"],
  "directory": ""
}
```

**Quality Modes:**
- `ultra-fast`: Minimal checks, fastest
- `fast`: Standard checks, fast
- `smart`: Intelligent selection of checks
- `comprehensive`: All checks, thorough
- `ai_enhanced`: AI-powered analysis

**Response:**
```json
{
  "success": true,
  "total_issues_found": 5,
  "processing_time": 2.5,
  "mode": "fast",
  "files_checked": 10,
  "issues_by_tool": {
    "ruff": 3,
    "mypy": 2
  },
  "simulated": false,
  "error": null,
  "details": {
    "issues": [...]
  }
}
```

**Example:**
```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"mode": "fast", "files": ["src/main.py"]}' \
  https://app.codeflow.celladoresystems.com/api/quality-check
```

**Error Responses:**
- `400`: Bad request (invalid parameters)
- `403`: Forbidden (file access denied)
- `429`: Rate limit exceeded (Retry-After header included)

---

#### `GET /api/config`

Get current dashboard configuration.

**Authentication:** Required (API Key)

**Response:**
```json
{
  "quality_mode": "fast",
  "auto_fix": false,
  "notifications_enabled": true
}
```

**Example:**
```bash
curl -H "X-API-Key: your-api-key" https://app.codeflow.celladoresystems.com/api/config
```

---

#### `POST /api/config`

Save dashboard configuration.

**Authentication:** Required (API Key)

**Request Body:**
```json
{
  "quality_mode": "comprehensive",
  "auto_fix": true,
  "notifications_enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration saved"
}
```

**Example:**
```bash
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"quality_mode": "comprehensive", "auto_fix": true}' \
  https://app.codeflow.celladoresystems.com/api/config
```

---

### Comment Filter API

#### `GET /api/comment-filter/settings`

Get comment filter settings.

**Authentication:** Required (API Key)

**Response:**
```json
{
  "enabled": true,
  "allowed_commenters": ["user1", "user2"],
  "block_all_others": false
}
```

---

#### `POST /api/comment-filter/settings`

Update comment filter settings.

**Authentication:** Required (API Key)

**Request Body:**
```json
{
  "enabled": true,
  "block_all_others": false
}
```

---

#### `GET /api/comment-filter/commenters`

List allowed commenters.

**Authentication:** Required (API Key)

**Query Parameters:**
- `limit` (integer, optional): Maximum records (default: 50)
- `offset` (integer, optional): Skip records (default: 0)

**Response:**
```json
[
  {
    "username": "user1",
    "added_at": "2025-01-15T10:00:00Z"
  }
]
```

---

#### `POST /api/comment-filter/commenters`

Add allowed commenter.

**Authentication:** Required (API Key)

**Request Body:**
```json
{
  "username": "newuser"
}
```

---

#### `DELETE /api/comment-filter/commenters/{username}`

Remove allowed commenter.

**Authentication:** Required (API Key)

**Example:**
```bash
curl -X DELETE \
  -H "X-API-Key: your-api-key" \
  https://app.codeflow.celladoresystems.com/api/comment-filter/commenters/user1
```

---

### GitHub App API

#### `GET /github-app/install`

GitHub App installation page.

**Response:** HTML page for app installation

---

#### `GET /github-app/callback`

OAuth callback handler.

**Query Parameters:**
- `code`: OAuth authorization code
- `state`: CSRF protection token

---

#### `POST /github-app/webhook`

GitHub webhook endpoint.

**Headers:**
- `X-GitHub-Event`: Event type (e.g., `pull_request`, `issue_comment`)
- `X-Hub-Signature-256`: Webhook signature

**Request Body:** GitHub webhook payload

---

### API Root

#### `GET /api`

API information endpoint.

**Response:**
```json
{
  "message": "CodeFlow Engine API",
  "version": "1.0.1",
  "dashboard": "available",
  "github_app": "available"
}
```

---

## WebSocket API

### Connection

```javascript
const ws = new WebSocket('wss://app.codeflow.celladoresystems.com/ws?api_key=your-api-key');
```

### Events

#### Quality Check Progress

```json
{
  "type": "quality_check_progress",
  "data": {
    "file": "src/main.py",
    "progress": 0.5,
    "status": "analyzing"
  }
}
```

#### Quality Check Complete

```json
{
  "type": "quality_check_complete",
  "data": {
    "success": true,
    "issues_found": 5,
    "processing_time": 2.5
  }
}
```

---

## Rate Limiting

### Limits

- **Quality Check Endpoint**: 10 requests per minute per IP
- **Other Endpoints**: 60 requests per minute per IP

### Headers

When rate limited, the response includes:
- `Retry-After`: Seconds to wait before retrying
- `X-RateLimit-Limit`: Request limit
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

### Example

```bash
# Rate limited response
HTTP/1.1 429 Too Many Requests
Retry-After: 30
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1705320000
```

---

## Error Codes

### HTTP Status Codes

| Code | Description |
|------|-------------|
| `200` | Success |
| `400` | Bad Request (invalid parameters) |
| `401` | Unauthorized (missing/invalid API key) |
| `403` | Forbidden (access denied) |
| `404` | Not Found |
| `429` | Too Many Requests (rate limited) |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

### Error Response Format

```json
{
  "detail": "Error message description",
  "error_code": "INVALID_PARAMETER",
  "timestamp": "2025-01-15T10:00:00Z"
}
```

---

## Request/Response Examples

### Complete Quality Check Flow

```bash
# 1. Check health
curl https://app.codeflow.celladoresystems.com/health

# 2. Get status
curl -H "X-API-Key: your-api-key" https://app.codeflow.celladoresystems.com/api/status

# 3. Run quality check
curl -X POST \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "fast",
    "files": ["src/main.py", "src/utils.py"]
  }' \
  https://app.codeflow.celladoresystems.com/api/quality-check

# 4. Get history
curl -H "X-API-Key: your-api-key" \
  "https://app.codeflow.celladoresystems.com/api/history?limit=10"
```

### Python Example

```python
import requests

API_BASE = "https://app.codeflow.celladoresystems.com"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}

# Run quality check
response = requests.post(
    f"{API_BASE}/api/quality-check",
    headers=headers,
    json={
        "mode": "fast",
        "files": ["src/main.py"]
    }
)

result = response.json()
print(f"Issues found: {result['total_issues_found']}")
```

### JavaScript Example

```javascript
const API_BASE = 'https://app.codeflow.celladoresystems.com';
const API_KEY = 'your-api-key';

async function runQualityCheck(files) {
  const response = await fetch(`${API_BASE}/api/quality-check`, {
    method: 'POST',
    headers: {
      'X-API-Key': API_KEY,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      mode: 'fast',
      files: files
    })
  });
  
  return await response.json();
}
```

---

## OpenAPI/Swagger Specification

The API includes automatic OpenAPI documentation:

- **Swagger UI**: `https://app.codeflow.celladoresystems.com/docs`
- **ReDoc**: `https://app.codeflow.celladoresystems.com/redoc`
- **OpenAPI JSON**: `https://app.codeflow.celladoresystems.com/openapi.json`

---

## SDKs and Client Libraries

### Python

```bash
pip install codeflow-engine
```

```python
from codeflow_engine import CodeFlowClient

client = CodeFlowClient(api_key="your-api-key")
result = client.quality_check(files=["src/main.py"], mode="fast")
```

### JavaScript/TypeScript

```bash
npm install @codeflow/sdk
```

```typescript
import { CodeFlowClient } from '@codeflow/sdk';

const client = new CodeFlowClient({ apiKey: 'your-api-key' });
const result = await client.qualityCheck({
  files: ['src/main.ts'],
  mode: 'fast'
});
```

---

## Additional Resources

- [Architecture Documentation](../architecture/ARCHITECTURE.md)
- [Deployment Guide](../deployment/DEPLOYMENT_GUIDE.md)
- [Environment Variables](../deployment/ENVIRONMENT_VARIABLES.md)

---

## Support

For API questions or issues:
- GitHub Issues: [codeflow-engine/issues](https://github.com/JustAGhosT/codeflow-engine/issues)
- API Documentation: `/docs` endpoint
- Email: support@codeflow.io


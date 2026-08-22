# CodeFlow Engine - Environment Variables Reference

Complete reference for all environment variables used by CodeFlow Engine.

---

## Quick Reference

| Variable             | Required | Default                    | Description                                  |
| -------------------- | -------- | -------------------------- | -------------------------------------------- |
| `DATABASE_URL`       | Yes\*    | -                          | PostgreSQL connection string                 |
| `REDIS_URL`          | No       | `redis://localhost:6379/0` | Redis connection string                      |
| `GITHUB_TOKEN`       | Yes\*    | -                          | GitHub Personal Access Token                 |
| `CODEFLOW_ENV`       | No       | `development`              | Environment (development/staging/production) |
| `CODEFLOW_LOG_LEVEL` | No       | `INFO`                     | Logging level (DEBUG/INFO/WARNING/ERROR)     |

\* Required for production deployments

---

## Core Configuration

### Environment Settings

#### `CODEFLOW_ENV`

**Type:** String  
**Required:** No  
**Default:** `development`  
**Values:** `development`, `testing`, `staging`, `production`

Sets the application environment. Affects logging, debugging, and security settings.

```bash
CODEFLOW_ENV=production
```

#### `CODEFLOW_LOG_LEVEL`

**Type:** String  
**Required:** No  
**Default:** `INFO`  
**Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

Controls the verbosity of logging output.

```bash
CODEFLOW_LOG_LEVEL=DEBUG
```

#### `CODEFLOW_HOST`

**Type:** String  
**Required:** No  
**Default:** `0.0.0.0`

Host address to bind the server.

```bash
CODEFLOW_HOST=0.0.0.0
```

#### `CODEFLOW_PORT`

**Type:** Integer  
**Required:** No  
**Default:** `8000`

Port number for the HTTP server.

```bash
CODEFLOW_PORT=8080
```

---

## Database Configuration

### `DATABASE_URL`

**Type:** String (PostgreSQL connection string)  
**Required:** Yes (for production)  
**Default:** None

PostgreSQL database connection string.

**Format:**

```text
postgresql://[user[:password]@][host][:port][/database][?param1=value1&...]
```

**Examples:**

```bash
# Local development
DATABASE_URL=postgresql://codeflow:password@localhost:5432/codeflow

# Azure Database for PostgreSQL
DATABASE_URL=postgresql://codeflow:password@codeflow-postgres.postgres.database.azure.com:5432/codeflow?sslmode=require

# With connection pool settings
DATABASE_URL=postgresql://user:pass@host:5432/db?pool_size=10&max_overflow=20
```

**Connection Pool Options:**

- `pool_size`: Number of connections in pool (default: 10)
- `max_overflow`: Maximum overflow connections (default: 20)
- `pool_timeout`: Timeout for getting connection (default: 30)
- `pool_recycle`: Recycle connections after seconds (default: 3600)

---

## Redis Configuration

### `REDIS_URL`

**Type:** String (Redis connection string)  
**Required:** No  
**Default:** `redis://localhost:6379/0`

Redis cache connection string.

**Format:**

``` text
redis://[password@]host[:port][/database][?param1=value1&...]
rediss://[password@]host[:port][/database][?param1=value1&...]  # SSL
```

**Examples:**

```bash
# Local development
REDIS_URL=redis://localhost:6379/0

# With password
REDIS_URL=redis://:password@localhost:6379/0

# Azure Cache for Redis (SSL)
REDIS_URL=rediss://codeflow-redis.redis.cache.windows.net:6380?ssl=true&password=your_key

# With database number
REDIS_URL=redis://localhost:6379/1
```

**Alternative Variables:**

- `REDIS_HOST`: Redis host (default: `localhost`)
- `REDIS_PORT`: Redis port (default: `6379`)
- `REDIS_DB`: Database number (default: `0`)
- `REDIS_PASSWORD`: Redis password
- `REDIS_SSL`: Enable SSL (default: `false`)

---

## GitHub Configuration

### `GITHUB_TOKEN`

**Type:** String (GitHub Personal Access Token)  
**Required:** Yes (for GitHub integration)  
**Default:** None

GitHub Personal Access Token for API authentication.

**Token Format:**

- Classic: `ghp_...`
- Fine-grained: `github_pat_...`

```bash
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### `GITHUB_APP_ID`

**Type:** Integer  
**Required:** No  
**Default:** None

GitHub App ID for app-based authentication (alternative to token).

```bash
GITHUB_APP_ID=123456
```

### `GITHUB_PRIVATE_KEY`

**Type:** String (PEM format)  
**Required:** No (required if using App ID)  
**Default:** None

GitHub App private key for app-based authentication.

```bash
GITHUB_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n..."
```

### `GITHUB_BASE_URL`

**Type:** String  
**Required:** No  
**Default:** `https://api.github.com`

GitHub API base URL (for GitHub Enterprise).

```bash
GITHUB_BASE_URL=https://github.example.com/api/v3
```

### `GITHUB_TIMEOUT`

**Type:** Integer (seconds)  
**Required:** No  
**Default:** `30`

Timeout for GitHub API requests.

```bash
GITHUB_TIMEOUT=60
```

---

## LLM Provider Configuration

### OpenAI

#### `OPENAI_API_KEY`

**Type:** String  
**Required:** No (required for OpenAI features)  
**Default:** None

OpenAI API key.

```bash
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### `OPENAI_BASE_URL`

**Type:** String  
**Required:** No  
**Default:** `https://api.openai.com/v1`

OpenAI API base URL (for custom endpoints).

```bash
OPENAI_BASE_URL=https://api.openai.com/v1
```

#### `OPENAI_DEFAULT_MODEL`

**Type:** String  
**Required:** No  
**Default:** `gpt-4`

Default OpenAI model to use.

```bash
OPENAI_DEFAULT_MODEL=gpt-4-turbo
```

### Anthropic

#### `ANTHROPIC_API_KEY`

**Type:** String  
**Required:** No (required for Anthropic features)  
**Default:** None

Anthropic API key.

```bash
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### `ANTHROPIC_BASE_URL`

**Type:** String  
**Required:** No  
**Default:** `https://api.anthropic.com`

Anthropic API base URL.

```bash
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

#### `ANTHROPIC_DEFAULT_MODEL`

**Type:** String  
**Required:** No  
**Default:** `claude-3-sonnet-20240229`

Default Anthropic model.

```bash
ANTHROPIC_DEFAULT_MODEL=claude-3-opus-20240229
```

### Other LLM Providers

#### `MISTRAL_API_KEY`

#### `GROQ_API_KEY`

#### `PERPLEXITY_API_KEY`

#### `TOGETHER_API_KEY`

Similar structure to OpenAI/Anthropic.

---

## Security Configuration

### `SECRET_KEY`

**Type:** String  
**Required:** Yes (for production)  
**Default:** None

Secret key for encryption and signing. Must be at least 32 characters.

```bash
SECRET_KEY=your-secret-key-at-least-32-characters-long
```

### `JWT_SECRET`

**Type:** String  
**Required:** No  
**Default:** None

Secret key for JWT token signing.

```bash
JWT_SECRET=your-jwt-secret-key
```

### `JWT_EXPIRY`

**Type:** Integer (seconds)  
**Required:** No  
**Default:** `3600`

JWT token expiration time.

```bash
JWT_EXPIRY=7200
```

### `CORS_ALLOWED_ORIGINS`

**Type:** Comma-separated list  
**Required:** No (required for production)  
**Default:** `[]`

Allowed origins for CORS.

```bash
CORS_ALLOWED_ORIGINS=https://codeflow.celladoresystems.com
```

### `RATE_LIMIT_PER_MINUTE`

**Type:** Integer  
**Required:** No  
**Default:** `60`

API rate limit per minute.

```bash
RATE_LIMIT_PER_MINUTE=100
```

---

## Monitoring Configuration

### `SENTRY_DSN`

**Type:** String  
**Required:** No  
**Default:** None

Sentry DSN for error tracking.

```bash
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

### `APPINSIGHTS_INSTRUMENTATION_KEY`

**Type:** String  
**Required:** No  
**Default:** None

Azure Application Insights instrumentation key.

```bash
APPINSIGHTS_INSTRUMENTATION_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

### `JAEGER_ENDPOINT`

**Type:** String  
**Required:** No  
**Default:** None

Jaeger tracing endpoint.

```bash
JAEGER_ENDPOINT=http://jaeger:14268/api/traces
```

### `ENABLE_METRICS`

**Type:** Boolean  
**Required:** No  
**Default:** `true`

Enable Prometheus metrics endpoint.

```bash
ENABLE_METRICS=true
```

### `METRICS_PORT`

**Type:** Integer  
**Required:** No  
**Default:** `8000`

Port for metrics endpoint.

```bash
METRICS_PORT=9090
```

---

## Workflow Configuration

### `WORKFLOW_MAX_CONCURRENT`

**Type:** Integer  
**Required:** No  
**Default:** `10`

Maximum concurrent workflow executions.

```bash
WORKFLOW_MAX_CONCURRENT=20
```

### `WORKFLOW_TIMEOUT`

**Type:** Integer (seconds)  
**Required:** No  
**Default:** `300`

Workflow execution timeout.

```bash
WORKFLOW_TIMEOUT=600
```

### `WORKFLOW_RETRY_ATTEMPTS`

**Type:** Integer  
**Required:** No  
**Default:** `3`

Number of retry attempts for failed workflows.

```bash
WORKFLOW_RETRY_ATTEMPTS=5
```

---

## AI Linting Configuration

### `AI_LINTING_ENABLED`

**Type:** Boolean  
**Required:** No  
**Default:** `true`

Enable AI-powered linting fixer.

```bash
AI_LINTING_ENABLED=true
```

### `AI_LINTING_DEFAULT_PROVIDER`

**Type:** String  
**Required:** No  
**Default:** `openai`

Default LLM provider for AI linting.

```bash
AI_LINTING_DEFAULT_PROVIDER=anthropic
```

### `AI_LINTING_MAX_WORKERS`

**Type:** Integer  
**Required:** No  
**Default:** `4`

Maximum worker threads for AI linting.

```bash
AI_LINTING_MAX_WORKERS=8
```

### `AI_LINTING_MAX_FIXES_PER_RUN`

**Type:** Integer  
**Required:** No  
**Default:** `10`

Maximum fixes per linting run.

```bash
AI_LINTING_MAX_FIXES_PER_RUN=20
```

---

## Integration Configuration

### Linear

#### `LINEAR_API_KEY`

**Type:** String  
**Required:** No  
**Default:** None

Linear API key for issue creation.

```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Slack

#### `SLACK_BOT_TOKEN`

**Type:** String  
**Required:** No  
**Default:** None

Slack bot token for notifications.

```bash
SLACK_BOT_TOKEN=xoxb-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

#### `SLACK_WEBHOOK_URL`

**Type:** String  
**Required:** No  
**Default:** None

Slack webhook URL for notifications.

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxxxx/xxxxx/xxxxx
```

### Axolo

#### `AXOLO_API_KEY`

**Type:** String  
**Required:** No  
**Default:** None

Axolo API key for integration.

```bash
AXOLO_API_KEY=axolo_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Volume Control Configuration

### `VOLUME_DEFAULT_PR`

**Type:** Integer  
**Required:** No  
**Default:** `500`

Default volume for PR analysis.

```bash
VOLUME_DEFAULT_PR=800
```

### `VOLUME_DEFAULT_DEV`

**Type:** Integer  
**Required:** No  
**Default:** `500`

Default volume for development analysis.

```bash
VOLUME_DEFAULT_DEV=500
```

### `VOLUME_DEFAULT_CHECKIN`

**Type:** Integer  
**Required:** No  
**Default:** `500`

Default volume for check-in analysis.

```bash
VOLUME_DEFAULT_CHECKIN=300
```

---

## Environment-Specific Examples

### Development

```bash
CODEFLOW_ENV=development
CODEFLOW_LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://codeflow:password@localhost:5432/codeflow
REDIS_URL=redis://localhost:6379/0
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Production

```bash
CODEFLOW_ENV=production
CODEFLOW_LOG_LEVEL=INFO
DATABASE_URL=postgresql://codeflow:password@postgres.example.com:5432/codeflow?sslmode=require
REDIS_URL=rediss://redis.example.com:6380?ssl=true&password=xxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SECRET_KEY=your-secret-key-at-least-32-characters-long
CORS_ALLOWED_ORIGINS=https://codeflow.celladoresystems.com
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
```

---

## Loading Order

Environment variables are loaded in this order:

1. System environment variables
2. `.env` file (if exists)
3. Environment-specific config files (`environments/production.yaml`)
4. Default values

Variables are case-insensitive and can use underscores or hyphens.

---

## Validation

All environment variables are validated on startup. Invalid values will cause the application to fail with a clear error message.

---

## Security Best Practices

1. **Never commit secrets** to version control
2. **Use secret management** (Azure Key Vault, AWS Secrets Manager, etc.)
3. **Rotate secrets regularly**
4. **Use different secrets** for each environment
5. **Restrict access** to production secrets
6. **Use least privilege** for API keys
7. **Enable SSL/TLS** for database and Redis connections in production

---

## Additional Resources

- [Configuration Documentation](../config/CONFIGURATION.md)
- [Deployment Guide](./DEPLOYMENT_GUIDE.md)
- [Security Best Practices](../security/SECURITY.md)

---

## Support

For issues or questions:

- GitHub Issues: [codeflow-engine/issues](https://github.com/JustAGhosT/codeflow-engine/issues)
- Documentation: [README.md](../../README.md)

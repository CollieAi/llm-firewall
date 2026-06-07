---
description: >-
  How to run CollieAi locally for development — set up Python, Docker
  (PostgreSQL, Redis, ClickHouse), environment variables, migrations, the API
  server, and the background worker.
icon: nas
---

# Local development

This guide walks you through running CollieAi locally for development purposes.

## Prerequisites

* **Python 3.11+**
* **Docker and Docker Compose** (latest stable)
* **Git**

## Setup

{% stepper %}
{% step %}
#### Clone and Create Virtual Environment

```bash
git clone <repository-url>
cd Claude

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```
{% endstep %}

{% step %}
#### Environment Variables

Create a `.env` file in the project root with the following settings:

```bash
# PostgreSQL (individual fields — there is no DATABASE_URL setting)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=collieai
POSTGRES_PASSWORD=collieai_dev_pass
POSTGRES_DB=collieai

# Redis (individual fields — there is no REDIS_URL setting)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=collieai_redis_pass
REDIS_DB=0

# ClickHouse
CLICKHOUSE_HOST=localhost
CLICKHOUSE_PORT=8123
CLICKHOUSE_USER=collieai
CLICKHOUSE_PASSWORD=collieai_clickhouse_pass
CLICKHOUSE_DATABASE=collieai_logs

# ML Models (for prompt injection & language detection)
HF_TOKEN=your_huggingface_token_here

# Model preloading (default: true)
# Set to false for faster startup during development
PRELOAD_MODELS=true

# Optional: Fernet key for encrypting provider tokens at rest
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# Leave empty to store tokens in plaintext (fine for local dev)
PROVIDER_TOKEN_ENCRYPTION_KEY=

# Billing (disabled by default for self-hosted / local dev)
# To enable Stripe billing, set BILLING_ENABLED=true and provide Stripe keys.
# See .env.example for the full list of STRIPE_* variables.
BILLING_ENABLED=false
```
{% endstep %}

{% step %}
#### Start Database Services

Start PostgreSQL, Redis, and ClickHouse using Docker Compose:

```bash
docker compose up -d postgres redis clickhouse
```

Verify all services are running and healthy:

```bash
docker compose ps
```
{% endstep %}

{% step %}
#### Run Database Migrations

Apply all database migrations before starting the application:

```bash
alembic upgrade head
```

{% hint style="info" %}
If you already have tables from a previous setup, stamp the current state first: `alembic stamp head`
{% endhint %}
{% endstep %}

{% step %}
#### Start the API Server

Run the FastAPI application with hot reload:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

| Endpoint   | URL                                                        |
| ---------- | ---------------------------------------------------------- |
| API        | [http://localhost:8000](http://localhost:8000/)            |
| Swagger UI | [http://localhost:8000/docs](http://localhost:8000/docs)   |
| ReDoc      | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
{% endstep %}

{% step %}
#### Start the Background Worker

In a **separate terminal**, activate the virtual environment and start the worker:

```bash
source .venv/bin/activate
python -m app.worker.main
```

The worker processes Redis queues for async filtering, webhook delivery, and alert evaluation.
{% endstep %}
{% endstepper %}

## Verification

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:

```json
{"status": "healthy", "service": "CollieAI", "version": "..."}
```

### Queue Depths

```bash
curl http://localhost:8000/api/v1/health/queues
```

Expected response:

```json
{
  "status": "ok",
  "queues": {
    "inbound_filtering": 0,
    "outbound_filtering": 0,
    "webhook_delivery": 0,
    "alert_evaluation": 0
  }
}
```

Non-zero values indicate pending jobs. Consistently growing queues may indicate the worker is not running or is falling behind.

### ML Models Status

```bash
curl http://localhost:8000/api/v1/health/models
```

Expected response (when `PRELOAD_MODELS=true`):

```json
{
  "status": "ok",
  "models": {
    "language_detection": {"loaded": true, "model_path": "~/.cache/fasttext/lid.176.ftz"},
    "lightweight_classifiers": {"loaded_models": ["model1", "model2"]},
    "generative": {"loaded_models": ["Qwen/Qwen2.5-0.5B-Instruct"]}
  }
}
```

If `language_detection.loaded` is `false`, [language detection rules](../security-rules/text-processing/language-detection.md) will silently fail open.

## Frontend

The frontend is a React + Vite application located in the `frontend/` directory:

```bash
cd frontend
npm install
npm run dev
```

The development server starts at [http://localhost:5173](http://localhost:5173/) and proxies API requests to the backend automatically.

## Stopping Services

1. Press `Ctrl+C` in the API server terminal.
2. Press `Ctrl+C` in the worker terminal.
3. Stop database containers:

```bash
docker compose down
```

To also remove volumes and delete all data:

```bash
docker compose down -v
```

## Troubleshooting

### Port Already in Use

If port 8000 is occupied, use a different port:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### Database Connection Issues

1.  Verify containers are running:

    ```bash
    docker compose ps
    ```
2.  Check PostgreSQL logs:

    ```bash
    docker compose logs postgres
    ```
3.  Test the connection directly:

    ```bash
    docker compose exec postgres psql -U collieai -d collieai -c "SELECT 1"
    ```

### Redis Connection Issues

Test the Redis connection:

```bash
docker compose exec redis redis-cli -a collieai_redis_pass ping
```

Expected response: `PONG`

### Worker Not Processing Jobs

1.  Check that Redis queues have items:

    ```bash
    docker compose exec redis redis-cli -a collieai_redis_pass LLEN collieai:inbound_filtering
    ```
2. Verify the worker is connected to Redis (check worker terminal for connection logs).
3. Ensure the API and worker use the same Redis credentials in their `.env` files.

### ML Models Not Loading

1. Verify `PRELOAD_MODELS=true` is set in your `.env` file.
2. Check that `HF_TOKEN` is valid -- gated models require a HuggingFace token with accepted license agreements.
3. Ensure the machine has network access to `huggingface.co`. Models are downloaded on first startup and cached locally.
4.  Check API server logs for model loading errors:

    ```bash
    # Look for lines containing "model" in the server output
    ```
5. If you do not need ML-based rules during development, set `PRELOAD_MODELS=false` for faster startup. Rules that depend on ML models will silently fail open.

## Development Tips

### Verbose Logging

Enable debug-level logs for more detail:

```bash
export LOG_LEVEL=DEBUG
```

Then restart the API server or worker.

### Database Shell

Access PostgreSQL directly:

```bash
docker compose exec postgres psql -U collieai -d collieai
```

### Redis CLI

Access Redis directly:

```bash
docker compose exec redis redis-cli -a collieai_redis_pass
```

### ClickHouse Shell

Access ClickHouse directly:

```bash
docker compose exec clickhouse clickhouse-client --user collieai --password collieai_clickhouse_pass
```

## Worker Configuration

The background worker supports the following environment variables:

| Variable                     | Default | Description                                                                                                                                                                 |
| ---------------------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `WORKER_CONCURRENCY`         | `10`    | Number of consumer coroutines per worker process. Each one races on all four queues (input / output / playground filtering + delivery) via multi-key BRPOP.                 |
| `WORKER_QUEUE_POLL_INTERVAL` | `0.1`   | Queue polling interval in seconds.                                                                                                                                          |
| `REDIS_POOL_SIZE`            | `40`    | Hard cap on Redis connections per worker process. **Must satisfy** `REDIS_POOL_SIZE >= WORKER_CONCURRENCY + 20` — the worker refuses to boot otherwise. Bump both together. |

Add these to your `.env` file or export them in the worker terminal before starting.

> **Note:** if you raise `WORKER_CONCURRENCY`, raise `REDIS_POOL_SIZE` in lockstep. The worker enforces the relationship at startup with a clear error message naming both knobs.

---
description: >-
  CollieAi Health API — liveness and readiness probes, ML model status, and
  async queue depths via /api/v1/health endpoints for monitoring and Kubernetes.
icon: stethoscope
---

# Health

Health check endpoints for monitoring application status and dependencies. For an external uptime monitor use [`GET /api/v1/health/status`](#get-api-v1-health-status): it is the one endpoint that answers `503` when something is wrong. The others return `200 OK` and report state in the response body; they carry a `timestamp` (Unix seconds).

***

## GET /api/v1/health

Basic liveness check. Returns `200` if the application is running. Does not test dependencies.

**URL:** `https://app.collieai.io/api/v1/health`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health
```

### Response -- `200 OK`

```json
{
  "status": "healthy",
  "service": "CollieAI",
  "version": "1.0.1",
  "timestamp": 1737021000.123
}
```

***

## GET /api/v1/health/status

Strict status for external monitoring. Returns `200` only when everything enabled on the host works — Postgres, Redis, ClickHouse, the inference runners and, where streaming moderation runs, the guard runner (its model must be loaded). Otherwise `503`, so a plain uptime check sees an outage by the status code.

The answer comes within about 3 seconds even when a dependency hangs (that dependency then reads `false`). Each API process checks at most once every 5 seconds, so polling every 30–60 seconds is plenty.

`version` is the CollieAi release; `revision` identifies the exact build running. A change of `revision` means a new release was deployed — useful to tell whether an error spike started with a deploy.

**URL:** `https://app.collieai.io/api/v1/health/status`

**Auth:** None

### Example Request

```bash
curl -i https://app.collieai.io/api/v1/health/status
```

### Response -- `200 OK`

```json
{
  "status": "ok",
  "components": {
    "postgres": true,
    "redis": true,
    "clickhouse": true,
    "inference": true,
    "guard": true
  },
  "version": "1.0.1",
  "revision": "6f14f8983b1c"
}
```

### Response -- `503 Service Unavailable`

```json
{
  "status": "degraded",
  "components": {
    "postgres": true,
    "redis": true,
    "clickhouse": true,
    "inference": true,
    "guard": false
  },
  "version": "1.0.1",
  "revision": "6f14f8983b1c"
}
```

`guard` is present only on hosts that run the guard runner.

***

## GET /api/v1/health/ready

Readiness probe. Checks infrastructure dependencies (Postgres, Redis, ClickHouse) and, when `INFERENCE_BACKEND=http`, reports inference-runner state as a separate diagnostic. `status` reflects infrastructure only — a dead inference runner does **not** flip readiness to `not_ready` (ML rules fail open).

**URL:** `https://app.collieai.io/api/v1/health/ready`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/ready
```

### Response -- `200 OK`

```json
{
  "status": "ready",
  "service": "CollieAI",
  "version": "1.0.1",
  "checks": {
    "postgres": true,
    "redis": true,
    "clickhouse": true
  },
  "inference": { "ready": true },
  "timestamp": 1737021000.123
}
```

`status` is `"ready"` when all `checks` are `true`, otherwise `"not_ready"` (still HTTP `200`). `inference` carries runner diagnostics: `ready` plus which runners are enabled and ready.

***

## GET /api/v1/health/live

Minimal liveness check for a Kubernetes liveness probe. Returns `200` if the process is running.

**URL:** `https://app.collieai.io/api/v1/health/live`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/live
```

### Response -- `200 OK`

```json
{
  "status": "alive"
}
```

***

## GET /api/v1/health/models

ML model status. Reports which models are downloaded on disk (models load lazily in the worker, so this checks the shared model cache).

**URL:** `https://app.collieai.io/api/v1/health/models`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/models
```

### Response -- `200 OK`

```json
{
  "status": "ok",
  "models": {
    "language_detection": {
      "loaded": true,
      "default_model_id": "fasttext/lid.176.ftz",
      "models": {
        "fasttext/lid.176.ftz": { "downloaded": true }
      }
    },
    "lightweight_classifiers": {
      "loaded_models": ["codeintegrity-ai/promptguard"]
    },
    "generative": {
      "loaded_models": []
    }
  },
  "timestamp": 1737021000.123
}
```

`loaded_models` lists the model IDs found in the cache; it is empty when none are downloaded.

***

## GET /api/v1/health/queues

Redis queue depths for async-job and webhook monitoring. A growing `inbound_filtering` queue means jobs are waiting longer in `processing_inbound`.

**URL:** `https://app.collieai.io/api/v1/health/queues`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/queues
```

### Response -- `200 OK`

```json
{
  "status": "healthy",
  "queues": {
    "inbound_filtering": 0,
    "outbound_filtering": 2,
    "log_events": 0,
    "webhook_delivery": 1,
    "webhook_retry": 0,
    "webhook_dead_letter": 0
  },
  "total_pending": 3,
  "timestamp": 1737021000.123
}
```

`status` is `"healthy"` when `total_pending` (inbound + outbound + webhook_delivery + webhook_retry) is under 100, otherwise `"backlogged"`.

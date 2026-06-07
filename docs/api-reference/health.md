---
description: >-
  CollieAi Health API — liveness and readiness probes, ML model status, and
  async queue depths via /api/v1/health endpoints for monitoring and Kubernetes.
icon: stethoscope
---

# Health

Health check endpoints for monitoring application status and dependencies.

***

## GET /api/v1/health

Basic liveness probe. Returns `200` if the application is running.

**URL:** `https://app.collieai.io/api/v1/health`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health
```

### Response -- `200 OK`

```json
{
  "status": "ok",
  "service": "collieai",
  "version": "1.5.0"
}
```

***

## GET /api/v1/health/ready

Readiness probe. Checks all critical dependencies (database, Redis, ClickHouse).

**URL:** `https://app.collieai.io/api/v1/health/ready`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/ready
```

### Response -- `200 OK` (all healthy)

```json
{
  "status": "ok",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2},
    "redis": {"status": "ok", "latency_ms": 1},
    "clickhouse": {"status": "ok", "latency_ms": 5}
  }
}
```

### Response -- `503 Service Unavailable` (dependency unhealthy)

```json
{
  "status": "degraded",
  "checks": {
    "database": {"status": "ok", "latency_ms": 2},
    "redis": {"status": "error", "error": "Connection refused"},
    "clickhouse": {"status": "ok", "latency_ms": 5}
  }
}
```

***

## GET /api/v1/health/live

Kubernetes liveness probe. Lightweight check that returns `200` if the process is alive. Does not check external dependencies.

**URL:** `https://app.collieai.io/api/v1/health/live`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/live
```

### Response -- `200 OK`

```json
{
  "status": "ok"
}
```

***

## GET /api/v1/health/models

ML models status. Reports loaded state of all models used for rule evaluation.

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
  "language_detection": {
    "loaded": true
  },
  "lightweight_classifiers": {
    "loaded_models": ["prompt_injection", "toxicity", "relevance"]
  },
  "generative": {
    "loaded_models": ["gpt-4o-mini"]
  }
}
```

### Response -- `503 Service Unavailable` (model not loaded)

```json
{
  "status": "degraded",
  "language_detection": {
    "loaded": false,
    "error": "Failed to load model weights"
  },
  "lightweight_classifiers": {
    "loaded_models": ["prompt_injection"]
  },
  "generative": {
    "loaded_models": []
  }
}
```

***

## GET /api/v1/health/queues

Queue depths for async jobs monitoring.

**URL:** `https://app.collieai.io/api/v1/health/queues`

**Auth:** None

### Example Request

```bash
curl https://app.collieai.io/api/v1/health/queues
```

### Response -- `200 OK`

```json
{
  "status": "ok",
  "queues": {
    "inbound_filtering": 0,
    "outbound_filtering": 2,
    "webhook_delivery": 1,
    "webhook_retry": 0,
    "webhook_dead_letter": 0
  },
  "total_pending": 3
}
```

---
description: >-
  CollieAi Analytics API — project-scoped KPIs, time-series, threat breakdown,
  top rules, and   streaming-engine metrics over 24h/7d/30d windows via
  /api/v1/analytics.
icon: magnifying-glass-chart
---

# Analytics

Analytics endpoints back the dashboard's KPI cards, charts, top-rules table, and the Streaming engine section. All responses are project-scoped and use the same `range` window (`24h`, `7d`, `30d`).

## GET /api/v1/analytics

Headline KPIs (requests, blocks, errors, tokens, latency percentiles, rule firings), time-series buckets, threat breakdown, top rules, and alert event count for the current window plus the comparable previous window.

**URL:** `https://app.collieai.io/api/v1/analytics`

**Auth:** Session cookie

### Query Parameters

| Parameter    | Type   | Required | Description                                                                                                                                     |
| ------------ | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `project_id` | string | Yes      | Project to scope the query to.                                                                                                                  |
| `range`      | string | No       | `"24h"` (default), `"7d"`, or `"30d"`. Drives both the window and the bucket granularity (hour / 6h / day).                                     |
| `scope`      | string | No       | `"all"` (default), `"dropin"`, `"async"`, or `"filtering"`. Filters request\_logs by event shape so cards don't mix incomparable traffic types. |

### Response — `200 OK`

```json
{
  "window": {
    "from": "2026-05-23T22:00:00+00:00",
    "to":   "2026-05-24T22:00:00+00:00",
    "previous_from": "2026-05-22T22:00:00+00:00",
    "previous_to":   "2026-05-23T22:00:00+00:00"
  },
  "scope": "all",
  "kpi": {
    "total_requests": 12345,
    "blocked_requests": 12,
    "error_requests": 3,
    "total_tokens": 4567890,
    "input_tokens": 1234567,
    "output_tokens": 3333323,
    "cache_write_tokens": 0,
    "cache_read_tokens": 0,
    "avg_duration_ms": 412.7,
    "p95_duration_ms": 1890.0,
    "rule_firings": 8,
    "unique_rules_triggered": 3
  },
  "previous_kpi": { "...": "same shape as kpi" },
  "time_series": [
    {
      "bucket": "2026-05-24T12:00:00",
      "total": 532,
      "blocked": 1,
      "monitoring": 0,
      "errors": 0,
      "block_rate": 0.19,
      "monitor_rate": 0.0,
      "error_rate": 0.0,
      "p50_ms": 380,
      "p95_ms": 1900,
      "p99_ms": 4100,
      "p50_inbound_ms": 4,
      "p95_inbound_ms": 12,
      "p99_inbound_ms": 18,
      "p50_outbound_ms": 18,
      "p95_outbound_ms": 42,
      "p99_outbound_ms": 88,
      "p50_provider_ms": 360,
      "p95_provider_ms": 1880,
      "p99_provider_ms": 4080,
      "p50_proxy_ms": 380,
      "p95_proxy_ms": 1900,
      "p99_proxy_ms": 4100,
      "p50_queue_ms": 0,
      "p95_queue_ms": 0,
      "p99_queue_ms": 0,
      "inbound_latency_count": 532,
      "outbound_latency_count": 531,
      "provider_latency_count": 531,
      "proxy_latency_count": 531,
      "queue_latency_count": 0
    }
  ],
  "threat_breakdown": [
    {"category": "passed",     "count": 12330},
    {"category": "blocked",    "count": 12},
    {"category": "monitoring", "count": 0},
    {"category": "error",      "count": 3}
  ],
  "threat_categories_time_series": [
    {"bucket": "2026-05-24T12:00:00", "rule_type": "regex", "firings": 4}
  ],
  "top_rules": [
    {
      "rule_id": "rule_abc",
      "rule_name": "SSN detector",
      "policy_name": "PII output",
      "direction": "outbound",
      "decision": "mask",
      "monitoring": false,
      "trigger_count": 8,
      "last_triggered": "2026-05-24T21:42:11+00:00"
    }
  ],
  "alert_events_count": 0
}
```

### Error Responses

| Status | Description                                              |
| ------ | -------------------------------------------------------- |
| `401`  | Not authenticated                                        |
| `404`  | Project not found or not owned by the authenticated user |

## GET /api/v1/analytics/streaming

Streaming engine KPIs for the window. Backed by the columns added in ClickHouse migration `09-streaming-kpis.sql`. Returns the static aggregations the dashboard's Streaming engine card renders.

**URL:** `https://app.collieai.io/api/v1/analytics/streaming`

**Auth:** Session cookie

### Query Parameters

| Parameter    | Type   | Required | Description                                                                  |
| ------------ | ------ | -------- | ---------------------------------------------------------------------------- |
| `project_id` | string | Yes      | Project to scope the query to.                                               |
| `range`      | string | No       | `"24h"` (default), `"7d"`, or `"30d"`. Same window contract as `/analytics`. |

### Response — `200 OK`

```json
{
  "window": {
    "from": "2026-05-23T22:00:00+00:00",
    "to":   "2026-05-24T22:00:00+00:00"
  },
  "kpi": {
    "total_requests": 12345,
    "total_streaming_engine_requests": 11200,
    "streaming_delivery_count": 7400,
    "buffered_delivery_count": 3800,
    "streaming_share_pct": 66.07,
    "mid_stream_block_rate_pct": 0.11,
    "client_disconnect_rate_pct": 0.04,
    "upstream_error_rate_pct": 0.02,
    "postflight_block_count": 4,
    "done_count": 11185,
    "max_held_chars_p50": 32,
    "max_held_chars_p95": 128,
    "max_held_chars_p99": 384,
    "chars_emitted_before_block_p50": 0,
    "chars_emitted_before_block_p95": 96,
    "chars_emitted_before_block_p99": 256
  },
  "close_reasons": [
    {"reason": "done",                   "count": 11185},
    {"reason": "client_disconnect",      "count": 5},
    {"reason": "postflight_rule_block",  "count": 4},
    {"reason": "streaming_rule_block",   "count": 8},
    {"reason": "upstream_error",         "count": 2}
  ]
}
```

### KPI field semantics

| Field                                                  | Meaning                                                                                                                                                                                 |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `total_requests`                                       | Every row in the window, regardless of delivery.                                                                                                                                        |
| `total_streaming_engine_requests`                      | Rows where the streaming engine ran (`delivery != ''`). Denominator for `streaming_share_pct` and `upstream_error_rate_pct`.                                                            |
| `streaming_delivery_count` / `buffered_delivery_count` | Per-delivery counts within the engine-served subset.                                                                                                                                    |
| `streaming_share_pct`                                  | `streaming_count / engine_total`. The fraction of engine-served traffic that actually streamed incrementally.                                                                           |
| `mid_stream_block_rate_pct`                            | `streaming_rule_block / streaming_count`. How often the engine fired a block on a streaming request — those are the cases where the client saw partial content before policy caught up. |
| `client_disconnect_rate_pct`                           | `client_disconnect / streaming_count`. Streaming requests where the client closed the connection before completion.                                                                     |
| `upstream_error_rate_pct`                              | `upstream_error / engine_total`. Engine-served requests that errored mid-stream.                                                                                                        |
| `max_held_chars_p50/95/99`                             | Distribution of peak chars buffered by the engine per request (latency proxy — higher = more added latency).                                                                            |
| `chars_emitted_before_block_p50/95/99`                 | Distribution of safe chars delivered to the client before a streaming block fired (security proxy).                                                                                     |

### Error Responses

| Status | Description                                              |
| ------ | -------------------------------------------------------- |
| `401`  | Not authenticated                                        |
| `404`  | Project not found or not owned by the authenticated user |

## GET /api/v1/analytics/streaming/timeseries

Bucketed counterpart to `/analytics/streaming`. Same data, one row per bucket. Powers the dashboard's stacked-area close-reasons chart. Empty buckets are zero-filled by ClickHouse — every bucket in the window appears in `buckets[]` even if no traffic landed in it.

**URL:** `https://app.collieai.io/api/v1/analytics/streaming/timeseries`

**Auth:** Session cookie

### Query Parameters

| Parameter    | Type   | Required | Description                                                                           |
| ------------ | ------ | -------- | ------------------------------------------------------------------------------------- |
| `project_id` | string | Yes      | Project to scope the query to.                                                        |
| `range`      | string | No       | `"24h"` (default; `hour` buckets), `"7d"` (`6h` buckets), or `"30d"` (`day` buckets). |

### Response — `200 OK`

```json
{
  "window": {
    "from": "2026-05-23T22:00:00+00:00",
    "to":   "2026-05-24T22:00:00+00:00"
  },
  "bucket_granularity": "hour",
  "buckets": [
    {
      "bucket": "2026-05-23T22:00:00",
      "streaming_count": 310,
      "buffered_count": 160,
      "engine_total": 470,
      "done_count": 468,
      "streaming_block_count": 1,
      "postflight_block_count": 1,
      "upstream_error_count": 0,
      "client_disconnect_count": 0,
      "max_held_chars_p50": 30,
      "max_held_chars_p95": 122,
      "max_held_chars_p99": 360
    }
  ]
}
```

`bucket_granularity` is announced explicitly so chart consumers can label the X-axis without re-deriving from `range`.

### Error Responses

| Status | Description                                              |
| ------ | -------------------------------------------------------- |
| `401`  | Not authenticated                                        |
| `404`  | Project not found or not owned by the authenticated user |

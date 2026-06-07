---
description: >-
  CollieAi Jobs API — create async filtering jobs, poll status, submit LLM
  responses, and stream filtered chunks for your own model via POST /v1/jobs and
  related endpoints.
icon: briefcase-arrow-right
---

# Jobs

Asynchronous request processing. Create a job to evaluate content against policy rules, with optional LLM forwarding and webhook delivery.

***

## POST /v1/jobs

Create a new async job.

**URL:** `https://app.collieai.io/v1/jobs`

**Auth:** Bearer token (API key `clai_xxx`)

### Request Body

| Field                | Type    | Required | Description                                                                                   |
| -------------------- | ------- | -------- | --------------------------------------------------------------------------------------------- |
| `message`            | string  | No       | Shorthand for a single user message. Mutually exclusive with `message_input`/`message_output` |
| `message_input`      | string  | No       | Input message to evaluate against input rules                                                 |
| `message_output`     | string  | No       | Output message to evaluate against output rules                                               |
| `webhook_url`        | string  | Yes      | URL to receive the job result via POST                                                        |
| `metadata`           | object  | No       | Arbitrary key-value pairs attached to the job                                                 |
| `expires_in_seconds` | integer | No       | Job TTL in seconds. Default: 86400 (24h)                                                      |
| `inbound_only`       | boolean | No       | Only run input rules, skip LLM forwarding. Default: `false`                                   |

### Field Behavior

| Scenario                           | Input Rules | LLM Call | Output Rules              |
| ---------------------------------- | ----------- | -------- | ------------------------- |
| `message` only                     | Evaluated   | Yes      | Evaluated on LLM response |
| `message_input` only               | Evaluated   | Yes      | Evaluated on LLM response |
| `message_output` only              | Skipped     | No       | Evaluated                 |
| `message_input` + `message_output` | Evaluated   | No       | Evaluated                 |
| `inbound_only: true` + `message`   | Evaluated   | No       | Skipped                   |

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message_input": "Summarize the quarterly earnings report",
    "webhook_url": "https://your-app.com/webhooks/collie",
    "metadata": {
      "user_id": "user_123",
      "session_id": "sess_abc"
    }
  }'
```

### Response -- `202 Accepted`

```json
{
  "job_id": "job_abc123def456",
  "status": "pending",
  "webhook_secret": "whsec_abc123",
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-16T10:30:00Z"
}
```

### Error Responses

| Status | Description                                                        |
| ------ | ------------------------------------------------------------------ |
| `400`  | Invalid request (e.g. both `message` and `message_input` provided) |
| `401`  | Missing or invalid API key                                         |
| `422`  | Validation error                                                   |

***

## GET /v1/jobs/{job\_id}

Retrieve job status and results.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `job_id`  | string | The job identifier |

### Example Request

```bash
curl https://app.collieai.io/v1/jobs/job_abc123def456 \
  -H "Authorization: Bearer clai_your_api_key"
```

### Response -- `200 OK`

```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "created_at": "2025-01-15T10:30:00Z",
  "completed_at": "2025-01-15T10:30:05Z",
  "expires_at": "2025-01-16T10:30:00Z",
  "metadata": {
    "user_id": "user_123",
    "session_id": "sess_abc"
  },
  "inbound_result": {
    "decision": "pass",
    "rules_evaluated": 3,
    "rules_triggered": [],
    "latency_ms": 120
  },
  "outbound_result": {
    "decision": "pass",
    "rules_evaluated": 4,
    "rules_triggered": [],
    "latency_ms": 85
  },
  "webhook_delivery": {
    "url": "https://your-app.com/webhooks/collie",
    "status": "delivered",
    "response_code": 200,
    "delivered_at": "2025-01-15T10:30:06Z"
  }
}
```

### Job Statuses

| Status              | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `pending`           | Created, waiting to be processed                        |
| `processing`        | Currently being evaluated                               |
| `awaiting_response` | Input rules passed, waiting for LLM response submission |
| `completed`         | All processing finished                                 |
| `failed`            | Processing encountered an error                         |
| `expired`           | Job exceeded its TTL                                    |

### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Missing or invalid API key |
| `404`  | Job not found              |

***

## POST /v1/jobs/{job\_id}/response

Submit an LLM response for a job in `awaiting_response` status. CollieAI evaluates the response against output rules.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/response`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `job_id`  | string | The job identifier |

### Request Body

| Field      | Type   | Required | Description                          |
| ---------- | ------ | -------- | ------------------------------------ |
| `response` | string | Yes      | The LLM response content to evaluate |

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs/job_abc123def456/response \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "The quarterly earnings show revenue of $2.5B..."
  }'
```

### Response -- `202 Accepted`

```json
{
  "job_id": "job_abc123def456",
  "status": "processing"
}
```

### Error Responses

| Status | Description                              |
| ------ | ---------------------------------------- |
| `400`  | Job is not in `awaiting_response` status |
| `401`  | Missing or invalid API key               |
| `404`  | Job not found                            |

***

## POST /v1/jobs/{job\_id}/chunks

Submit one chunk of an upstream-model stream for filtering. Use this when **you own the model** (your own LLM call, a self-hosted model, or a non-OpenAI provider) and you want CollieAi to filter the streaming output as it's produced. Pair it with `GET /v1/jobs/{job_id}/stream` to surface the filtered chunks to your end user.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/chunks`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description                                    |
| --------- | ------ | ---------------------------------------------- |
| `job_id`  | string | The job identifier returned by `POST /v1/jobs` |

### Request Body

| Field      | Type    | Required | Description                                                                                                                                                                     |
| ---------- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sequence` | integer | Yes      | Monotonic per-job chunk index, starting at `0`. Each subsequent chunk MUST be `N+1`. Repeating the last sequence is treated as an idempotent retry.                             |
| `content`  | string  | Yes      | Text chunk from the upstream model. Empty string is valid (e.g. for a `sequence=N` chunk whose only purpose is to mark `is_final=true`).                                        |
| `is_final` | boolean | No       | `true` on the last chunk of the stream. Triggers the engine's final flush and marks the session terminal. Further submits return `409 chunk_session_finished`. Default `false`. |

### Idempotency

Submitting the same `sequence` twice with the **same** body returns the same response (cached on the server). Submitting the same `sequence` with a **different** body returns `409 chunk_idempotency_conflict` — sequences are tied to a body for the lifetime of the session. To send different content, use a new sequence number.

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs/job_abc123def456/chunks \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": 0,
    "content": "The quarterly earnings ",
    "is_final": false
  }'
```

### Response -- `200 OK`

```json
{
  "sequence": 0,
  "accepted": true,
  "emits": [
    {
      "content": "The quarterly ",
      "blocked": false,
      "final": false,
      "triggered_rules": []
    }
  ],
  "finished": false
}
```

| Field      | Type    | Description                                                                                                                                                      |
| ---------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sequence` | integer | Echo of the submitted sequence.                                                                                                                                  |
| `accepted` | boolean | Always `true` on a `200` response. Errors return the standard `{"error": {...}}` envelope instead.                                                               |
| `emits`    | array   | Filtered safe chunks. May be empty if the upstream chunk is fully held back in the engine's stable-window buffer. Forward `content` to your end user in order.   |
| `finished` | boolean | `true` once the session is terminal (final flush completed OR a rule fired a block). After `finished=true`, further submits return `409 chunk_session_finished`. |

Each emit:

| Field             | Type    | Description                                                                                                  |
| ----------------- | ------- | ------------------------------------------------------------------------------------------------------------ |
| `content`         | string  | Safe text to forward to your end user. Masked content already has placeholders applied.                      |
| `blocked`         | boolean | `true` when a rule fired a block. The emit is the terminal emit; the session is finished.                    |
| `final`           | boolean | `true` for the terminal sentinel emit (sent after `is_final=true` drains the buffer, or for a blocked emit). |
| `triggered_rules` | array   | Rule audit entries that fired on this emit (rule id, name, decision, etc.).                                  |

### Error Responses

All errors use the OpenAI-compatible `{"error": {"message", "type", "code"}}` envelope.

| Status | Code                          | Description                                                                                                                                                                      |
| ------ | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `400`  | `chunk_streaming_unsupported` | The project's active policy can't be served by the streaming engine (`streaming_mode = "buffered"`, multi-rule policy, or `STREAMING_MODES_ENABLED=false` on the host).          |
| `401`  | -                             | Missing or invalid API key.                                                                                                                                                      |
| `404`  | -                             | Job not found or not owned by the API key's project.                                                                                                                             |
| `409`  | `chunk_sequence_conflict`     | `sequence` is not the next expected value (gap, or re-submitting an old sequence after later ones were accepted). Response includes `expected_sequence` and `received_sequence`. |
| `409`  | `chunk_idempotency_conflict`  | `sequence` was previously submitted with different content. Use a new sequence number to send different content.                                                                 |
| `409`  | `chunk_session_finished`      | A prior chunk had `is_final=true` or a rule fired a block. Create a new job to start a new stream.                                                                               |
| `409`  | `chunk_concurrent_submit`     | Another submit for the same job is in-flight. Submissions for one job must be serial; wait for the prior response.                                                               |
| `409`  | `chunk_policy_changed`        | The project's policy changed mid-stream. Create a new job to use the updated policy.                                                                                             |
| `409`  | `chunk_session_unrecoverable` | A prior commit left the job's stream in a state that can't be repaired. Create a new job.                                                                                        |
| `504`  | `chunk_filter_timeout`        | Filtering exceeded the per-chunk budget. Retry the same sequence with backoff.                                                                                                   |

***

## GET /v1/jobs/{job\_id}/stream

Server-Sent Events (SSE) stream of the filtered chunks produced by `POST /v1/jobs/{job_id}/chunks`. Subscribers see emits the API has accepted; in-flight or failed submits are never published. Useful for delivering filtered output to a browser or another client while your backend handles the chunk submission.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/stream`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description                                    |
| --------- | ------ | ---------------------------------------------- |
| `job_id`  | string | The job identifier returned by `POST /v1/jobs` |

### Request Headers

| Header          | Required | Description                                                                                                                                             |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Last-Event-ID` | No       | Standard SSE resume token — the ID of the last event the client saw. Subscribers resume from the next event. Absent → full backlog replay from chunk 0. |

### Example Request

```bash
curl -N https://app.collieai.io/v1/jobs/job_abc123def456/stream \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Accept: text/event-stream"
```

### Response -- `200 OK` (`Content-Type: text/event-stream`)

Each filtered emit is delivered as a `chunk` event with a stable stream ID for resume support:

```
id: 1-0
event: chunk
data: {"sequence": 0, "content": "The quarterly ", "blocked": false, "final": false, "triggered_rules": []}

id: 2-0
event: chunk
data: {"sequence": 1, "content": "earnings show ", "blocked": false, "final": false, "triggered_rules": []}

id: 3-0
event: chunk
data: {"sequence": 2, "content": "", "blocked": false, "final": true, "triggered_rules": []}

event: end
data: {"reason": "final"}
```

| Field             | Type    | Description                                                                             |
| ----------------- | ------- | --------------------------------------------------------------------------------------- |
| `sequence`        | integer | The chunk-submission sequence this emit came from. Multiple emits can share a sequence. |
| `content`         | string  | Safe text to render to the end user.                                                    |
| `blocked`         | boolean | `true` when a rule fired a block. Terminal for the stream.                              |
| `final`           | boolean | `true` for the terminal sentinel emit on `is_final=true` chunks.                        |
| `triggered_rules` | array   | Rule audit entries that fired on this emit.                                             |

The stream always closes with a single `end` event:

| `reason`                | Meaning                                                                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `final`                 | Normal end of stream — the last chunk submitted with `is_final=true` was processed.                                                                       |
| `blocked`               | A rule fired a block and terminated the stream.                                                                                                           |
| `session_finished`      | The session was already terminal when the SSE consumer connected (e.g. SSE opened late, after the producer finished).                                     |
| `session_unrecoverable` | The job's chunk stream entered a state that can't be repaired. The customer's backend should create a new job.                                            |
| `idle_timeout`          | No new emits arrived within the idle window and the session is not terminal. The consumer should reconnect with `Last-Event-ID` if the job is still live. |
| `upstream_error`        | The SSE reader hit an internal error reading the chunk stream. Reconnect with `Last-Event-ID`.                                                            |

Keepalive comments (`: keepalive\n\n`) are sent periodically when no new emits arrive, so reverse proxies don't idle-close the TCP connection. Treat them as no-ops.

### Error Responses

| Status | Description                                         |
| ------ | --------------------------------------------------- |
| `401`  | Missing or invalid API key                          |
| `404`  | Job not found or not owned by the API key's project |

***

## GET /v1/jobs

List jobs for the authenticated project.

**URL:** `https://app.collieai.io/v1/jobs`

**Auth:** Bearer token (API key `clai_xxx`)

### Query Parameters

| Parameter       | Type    | Required | Description                                                                                       |
| --------------- | ------- | -------- | ------------------------------------------------------------------------------------------------- |
| `page`          | integer | No       | Page number, starting from 1. Default: 1                                                          |
| `page_size`     | integer | No       | Items per page, 1-100. Default: 20                                                                |
| `status_filter` | string  | No       | Filter by status (`pending`, `processing`, `awaiting_response`, `completed`, `failed`, `expired`) |

### Example Request

```bash
curl "https://app.collieai.io/v1/jobs?page=1&page_size=10&status_filter=completed" \
  -H "Authorization: Bearer clai_your_api_key"
```

### Response -- `200 OK`

```json
{
  "jobs": [
    {
      "job_id": "job_abc123def456",
      "status": "completed",
      "created_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:30:05Z",
      "metadata": {
        "user_id": "user_123"
      }
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Missing or invalid API key |
| `422`  | Invalid query parameters   |

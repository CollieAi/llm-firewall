---
description: >-
  How CollieAi Async Job webhooks work — event types, payload format,
  HMAC-SHA256   signature verification, replay protection, and retry behavior.
icon: webhook
---

# Webhooks

CollieAi delivers filtering results to your application via webhooks. Each webhook is an HTTP POST request to the `webhook_url` you specified when [creating the job](creating-jobs.md).

***

## Webhook Events

| Event                   | Description                                                             |
| ----------------------- | ----------------------------------------------------------------------- |
| `job.inbound_complete`  | Input filtering finished. The filtered content is in `data.filtered`.   |
| `job.inbound_blocked`   | Input content was blocked by a policy rule.                             |
| `job.outbound_complete` | Output filtering finished. The filtered response is in `data.filtered`. |
| `job.outbound_blocked`  | Output content was blocked by a policy rule.                            |

***

## Payload Format

### job.input\_complete

```json
{
  "event": "job.inbound_complete",
  "job_id": "job_abc123def456",
  "timestamp": "2026-02-23T10:30:01Z",
  "metadata": {"user_id": "user_123", "session_id": "sess_456"},
  "data": {
    "filtered": "Tell me about network security",
    "original_length": 35,
    "filtered_length": 35,
    "rules_applied": 3
  }
}
```

### job.output\_complete

```json
{
  "event": "job.outbound_complete",
  "job_id": "job_abc123def456",
  "timestamp": "2026-02-23T10:30:12Z",
  "metadata": {"user_id": "user_123", "session_id": "sess_456"},
  "data": {
    "filtered": "Here are common network security practices...",
    "original_length": 512,
    "filtered_length": 498,
    "rules_applied": 5
  }
}
```

### job.input\_blocked

```json
{
  "event": "job.inbound_blocked",
  "job_id": "job_abc123def456",
  "timestamp": "2026-02-23T10:30:01Z",
  "metadata": {"user_id": "user_123"},
  "data": {
    "reason": "Content violates policy: prohibited topic",
    "rule_name": "dangerous-content-filter"
  }
}
```

### job.output\_blocked

```json
{
  "event": "job.outbound_blocked",
  "job_id": "job_abc123def456",
  "timestamp": "2026-02-23T10:30:12Z",
  "metadata": {"user_id": "user_123"},
  "data": {
    "reason": "Response contains prohibited content",
    "rule_name": "output-safety-filter"
  }
}
```

***

## Security Headers

Every webhook request includes the following headers:

| Header                 | Description                                        |
| ---------------------- | -------------------------------------------------- |
| `X-CollieAI-Signature` | HMAC-SHA256 signature of the payload               |
| `X-CollieAI-Timestamp` | Unix timestamp (seconds) when the webhook was sent |
| `X-CollieAI-Job-Id`    | The job ID this webhook belongs to                 |

***

## Signature Verification

Always verify webhook signatures to confirm the request came from CollieAI and was not tampered with.

The signature is computed as:

```
HMAC-SHA256(webhook_secret, "{timestamp}.{raw_body}")
```

Where `timestamp` is the value of `X-CollieAI-Timestamp` and `raw_body` is the raw request body string.

### Python

```python
import hmac
import hashlib
import time


def verify_signature(
    payload: str,
    signature: str,
    timestamp: str,
    secret: str,
    tolerance_seconds: int = 300,
) -> bool:
    # Check timestamp is within tolerance (replay protection)
    current_time = int(time.time())
    if abs(current_time - int(timestamp)) > tolerance_seconds:
        return False

    # Compute expected signature
    message = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(expected, signature)
```

### Node.js

```javascript
const crypto = require("crypto");

function verifySignature(payload, signature, timestamp, secret, toleranceSeconds = 300) {
  // Check timestamp is within 5 minutes
  const currentTime = Math.floor(Date.now() / 1000);
  if (Math.abs(currentTime - parseInt(timestamp)) > toleranceSeconds) {
    return false;
  }

  // Compute expected signature
  const message = `${timestamp}.${payload}`;
  const expected = crypto
    .createHmac("sha256", secret)
    .update(message)
    .digest("hex");

  // Constant-time comparison
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}
```

***

## Replay Protection

CollieAI includes a Unix timestamp in the `X-CollieAI-Timestamp` header. Reject any webhook where the timestamp is more than **5 minutes** from your server's current time. This prevents replay attacks where an attacker resends a captured webhook payload. Always check the timestamp **before** computing the signature.

***

## Retry Policy

If your endpoint does not return an HTTP 2xx response, CollieAI retries the webhook with exponential backoff:

| Attempt   | Delay      |
| --------- | ---------- |
| 1st retry | 2 seconds  |
| 2nd retry | 4 seconds  |
| 3rd retry | 8 seconds  |
| 4th retry | 16 seconds |
| 5th retry | 32 seconds |

After 5 failed retries, the job status moves to `failed`. You can check the job status via [polling](job-lifecycle.md#polling) if webhook delivery is unreliable.

***

## Endpoint Requirements

Your webhook endpoint must:

* **Return HTTP 2xx** to acknowledge receipt. Any other status code triggers a retry.
* **Respond within 30 seconds.** Requests that take longer are treated as failures.
* **Be idempotent.** Due to retries, you may receive the same webhook more than once. Use the `job_id` and event type to deduplicate.
* **Verify the signature.** Always validate `X-CollieAI-Signature` before processing the payload.

***

## Full Webhook Handler Example

A complete FastAPI webhook handler with signature verification and idempotency:

```python
import hmac
import hashlib
import json
import time
import logging

from fastapi import FastAPI, Request, HTTPException

app = FastAPI()
logger = logging.getLogger(__name__)

# In production, store secrets in a database keyed by job_id
WEBHOOK_SECRETS: dict[str, str] = {}

# Track processed events for idempotency (use a database in production)
processed_events: set[str] = set()


def verify_collieai_signature(
    payload: str, timestamp: str, signature: str, secret: str
) -> bool:
    """Verify CollieAI webhook signature with replay protection."""
    try:
        ts = int(timestamp)
    except (ValueError, TypeError):
        return False

    if abs(int(time.time()) - ts) > 300:
        return False

    message = f"{timestamp}.{payload}"
    expected = hmac.new(
        secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


@app.post("/webhooks/collieai")
async def handle_webhook(request: Request):
    # 1. Read raw body and headers
    body = await request.body()
    raw_body = body.decode("utf-8")
    signature = request.headers.get("X-CollieAI-Signature", "")
    timestamp = request.headers.get("X-CollieAI-Timestamp", "")
    job_id = request.headers.get("X-CollieAI-Job-Id", "")

    # 2. Look up webhook secret for this job
    secret = WEBHOOK_SECRETS.get(job_id)
    if not secret:
        raise HTTPException(status_code=401, detail="Unknown job")

    # 3. Verify signature (includes replay protection)
    if not verify_collieai_signature(raw_body, timestamp, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # 4. Parse payload
    payload = json.loads(raw_body)
    event = payload["event"]

    # 5. Idempotency check
    event_key = f"{job_id}:{event}"
    if event_key in processed_events:
        return {"status": "already_processed"}
    processed_events.add(event_key)

    # 6. Handle events
    if event == "job.inbound_complete":
        filtered_content = payload["data"]["filtered"]
        logger.info(f"Input passed for {job_id}")
        # Send filtered_content to your LLM, then submit response:
        # POST /v1/jobs/{job_id}/response

    elif event == "job.inbound_blocked":
        reason = payload["data"]["reason"]
        logger.warning(f"Input blocked for {job_id}: {reason}")
        # Notify user that their message was rejected

    elif event == "job.outbound_complete":
        filtered_response = payload["data"]["filtered"]
        logger.info(f"Output passed for {job_id}")
        # Deliver filtered_response to the end user

    elif event == "job.outbound_blocked":
        reason = payload["data"]["reason"]
        logger.warning(f"Output blocked for {job_id}: {reason}")
        # Return a fallback message to the user

    return {"status": "ok"}
```

***

## Testing Webhooks

During development, use [webhook.site](https://webhook.site) to inspect webhook payloads without deploying a server:

1. Go to [webhook.site](https://webhook.site) and copy your unique URL.
2. Use that URL as `webhook_url` when creating a job.
3. Inspect the incoming requests to see payload structure and headers.

For local development, tools like [ngrok](https://ngrok.com) can expose your local server to receive live webhooks.

***

## Next Steps

* [Job Lifecycle](job-lifecycle.md) -- understand status transitions and expiration behavior
* [Creating Jobs](creating-jobs.md) -- endpoint reference and code examples

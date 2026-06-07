---
description: >-
  How to create CollieAi Async Jobs — submit content to POST /v1/jobs for
  asynchronous   input and output filtering, with results delivered to your
  webhook.
icon: diagram-successor
---

# Creating jobs

Submit content for asynchronous filtering by creating a job. CollieAi processes the content against your configured rules and delivers results to your webhook URL.

## Create a Job

```http
POST /v1/jobs
```

### Authentication

Include your API key in the `Authorization` header:

```http
Authorization: Bearer clai_xxx
```

### Request Body

| Field                | Type    | Required | Description                                              |
| -------------------- | ------- | -------- | -------------------------------------------------------- |
| `message`            | string  | No\*     | Content for input filtering (legacy mode)                |
| `message_input`      | string  | No\*     | User message for input rules                             |
| `message_output`     | string  | No\*     | AI response for output rules                             |
| `webhook_url`        | string  | Yes      | HTTPS URL where filtered results are delivered           |
| `metadata`           | object  | No       | Custom key-value pairs passed through to webhooks        |
| `expires_in_seconds` | integer | No       | Job expiration time (default: 3600, max: 604800)         |
| `inbound_only`       | boolean | No       | Mark job complete after input filtering (default: false) |

\* At least one message field is required.

### Field Combination Behavior

| Fields Provided                        | Input Filtering    | Output Filtering | Webhooks Delivered                     |
| -------------------------------------- | ------------------ | ---------------- | -------------------------------------- |
| `message`                              | Yes (legacy rules) | No               | `job.inbound_complete`                 |
| `message_input`                        | Yes                | No               | `job.inbound_complete`                 |
| `message_output`                       | No                 | Yes              | `job.outbound_complete`                |
| `message_input` + `message_output`     | Yes                | Yes              | Both, in order                         |
| `message_input` + `inbound_only: true` | Yes                | No               | `job.inbound_complete` (job completes) |

### Response

**202 Accepted**

```json
{
  "job_id": "job_abc123def456",
  "status": "processing_inbound",
  "webhook_secret": "whsec_a1b2c3d4e5f6...",
  "created_at": "2026-02-23T10:30:00Z",
  "expires_at": "2026-02-23T11:30:00Z"
}
```

{% hint style="warning" %}
**Important:** Store the `webhook_secret` from the response. You need it to [verify webhook signatures](webhooks.md). It is only returned once at job creation.
{% endhint %}

***

## Examples

### Legacy Mode

Filter input content using the `message` field. This mode exists for backward compatibility.

{% tabs %}
{% tab title="cURL" %}
```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How do I make a dangerous chemical compound?",
    "webhook_url": "https://yourapp.com/webhooks/collieai"
  }'
```
{% endtab %}
{% endtabs %}

### Separate Mode (Input Only)

Filter a user message before sending it to your LLM.

{% tabs %}
{% tab title="cURL" %}
```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "message_input": "Explain how to bypass security systems",
    "webhook_url": "https://yourapp.com/webhooks/collieai",
    "metadata": {
      "user_id": "user_123",
      "session_id": "sess_456"
    }
  }'
```
{% endtab %}
{% endtabs %}

### Combined Mode (Input + Output)

Filter both user input and AI output in a single request. Useful for logging pipelines or post-processing.

{% tabs %}
{% tab title="cURL" %}
```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "message_input": "Tell me about network security",
    "message_output": "Here are common network security practices...",
    "webhook_url": "https://yourapp.com/webhooks/collieai",
    "expires_in_seconds": 7200
  }'
```
{% endtab %}
{% endtabs %}

### Python Example

```python
import httpx

COLLIEAI_API_KEY = "clai_xxx"
BASE_URL = "https://app.collieai.io"


async def create_filtering_job(user_message: str, webhook_url: str) -> dict:
    """Create an input filtering job and return job details."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/v1/jobs",
            headers={"Authorization": f"Bearer {COLLIEAI_API_KEY}"},
            json={
                "message_input": user_message,
                "webhook_url": webhook_url,
                "metadata": {"source": "chat-app"},
                "expires_in_seconds": 3600,
            },
        )
        response.raise_for_status()
        job = response.json()

        # Store the webhook_secret -- you need it to verify deliveries
        webhook_secret = job["webhook_secret"]
        print(f"Job created: {job['job_id']}")

        return job
```

***

## Check Job Status

Poll a job to check its current status.

```http
GET /v1/jobs/{job_id}
```

```bash
curl https://app.collieai.io/v1/jobs/job_abc123def456 \
  -H "Authorization: Bearer clai_xxx"
```

**Response:**

```json
{
  "job_id": "job_abc123def456",
  "status": "awaiting_response",
  "message_input": "Tell me about network security",
  "filtered_input": "Tell me about network security",
  "metadata": {
    "source": "chat-app"
  },
  "created_at": "2026-02-23T10:30:00Z",
  "expires_at": "2026-02-23T11:30:00Z"
}
```

See [Job Lifecycle](job-lifecycle.md) for all possible status values.

***

## Submit LLM Response

After receiving the `job.inbound_complete` webhook, call your LLM and submit its response for output filtering.

```http
POST /v1/jobs/{job_id}/response
```

```bash
curl -X POST https://app.collieai.io/v1/jobs/job_abc123def456/response \
  -H "Authorization: Bearer clai_xxx" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "Here are common network security practices..."
  }'
```

**Response:**

```json
{
  "job_id": "job_abc123def456",
  "status": "processing_outbound"
}
```

CollieAi filters the response through your output rules and delivers the result via the `job.outbound_complete` webhook.

{% hint style="info" %}
**Note:** This endpoint is only available when the job status is `awaiting_response`. If the job was created with `inbound_only: true` or `message_output` was provided in the initial request, this endpoint returns an error.
{% endhint %}

***

## List Jobs

Retrieve a paginated list of your jobs.

```http
GET /v1/jobs?page=1&page_size=20
```

```bash
curl "https://app.collieai.io/v1/jobs?page=1&page_size=20" \
  -H "Authorization: Bearer clai_xxx"
```

**Response:**

```json
{
  "jobs": [
    {
      "job_id": "job_abc123def456",
      "status": "completed",
      "created_at": "2026-02-23T10:30:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

***

## Next Steps

* [Webhooks](webhooks.md) -- understand the payload format and verify signatures
* [Job Lifecycle](job-lifecycle.md) -- status transitions, expiration, and best practices

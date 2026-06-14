---
description: >-
  How CollieAi projects isolate workloads — each project has its own API keys,
  active policy, rate limits, and data retention, so you can run multiple AI
  apps with separate security configs.
icon: diagram-project
---

# Projects

A project is an isolated context within CollieAi. Each project has its own API keys, settings, and active policy. Use projects to separate workloads -- for example, a production chatbot, a staging environment, and an internal copilot can each be their own project with distinct security configurations.

{% hint style="info" %}
**Key points**

* A project is an isolated context in CollieAi with its own API keys, settings, and one active policy.
* Use projects to separate workloads — for example production, staging, and an internal copilot.
* Each project sets its own rate limit (RPM) and data retention for logs and request bodies.
  * Switching a project's active policy takes effect instantly, which enables A/B testing and instant rollback.
{% endhint %}

## Creating a project

When you create a project, CollieAi automatically:

1. Assigns your **default policy** as the project's active policy. (If you have not starred a default policy, one is created for you.)
2. Creates an **API key** for the project so you can start sending requests immediately.

```bash
curl -X POST https://app.collieai.io/api/v1/projects \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-chatbot",
    "description": "Customer-facing AI assistant"
  }'
```

**Response:**

```json
{
  "id": "a1b2c3d4-...",
  "name": "production-chatbot",
  "description": "Customer-facing AI assistant",
  "active_policy_id": "e5f6a7b8-...",
  "filter_all_messages": true,
  "api_key": {
    "id": "k1l2m3n4-...",
    "name": "production-chatbot-key",
    "prefix": "clai_AbCd..."
  },
  "created_at": "2026-02-23T10:00:00Z"
}
```

{% hint style="warning" %}
The full API key value is only shown at creation time. Store it securely -- you cannot retrieve it later.
{% endhint %}

## Project settings

### filter\_all\_messages

Controls how CollieAi processes multi-turn conversations:

| Value            | Behavior                                                                                              |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `false` (default) | Only the **last message** in the conversation is filtered. Previous messages are forwarded unchanged. |
| `true`            | **All messages** in the conversation are filtered on every request.                                  |

By default only the latest message is filtered, for performance. Set to `true` for stronger protection (a user cannot sneak PII into earlier turns), at the cost of more processing on long conversations.

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "filter_all_messages": true
  }'
```

## Rate limiting

Control how many requests per minute (RPM) each project can make. This protects against runaway costs and upstream rate limit errors.

The rate limit applies to **all request-processing endpoints** for the project:

* `POST /v1/chat/completions` — sync chat proxy
* `POST /v1/jobs` — async job creation
* `POST /v1/jobs/{id}/response` — async response submission

All endpoints share the same counter, so a project configured with 60 RPM allows 60 total requests per minute across both sync and async usage.

| Setting          | Type            | Default            | Description                 |
| ---------------- | --------------- | ------------------ | --------------------------- |
| `rate_limit_rpm` | integer or null | `null` (unlimited) | Maximum requests per minute |

### Setting a rate limit

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{"rate_limit_rpm": 60}'
```

### Removing a rate limit

Set `rate_limit_rpm` to `null` to allow unlimited requests:

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{"rate_limit_rpm": null}'
```

### Rate limit response

When the limit is exceeded, CollieAI returns HTTP 429 with an OpenAI-compatible error:

```json
{
  "error": {
    "message": "Rate limit exceeded. Max 60 requests per minute. Try again in 12s.",
    "type": "rate_limit_exceeded",
    "code": 429
  }
}
```

Response headers on every request (when rate limiting is configured):

| Header                  | Description                             |
| ----------------------- | --------------------------------------- |
| `X-RateLimit-Limit`     | Configured RPM                          |
| `X-RateLimit-Remaining` | Requests remaining in current window    |
| `X-RateLimit-Reset`     | Unix timestamp when the window resets   |
| `Retry-After`           | Seconds to wait (only on 429 responses) |

## Data retention

Each project controls how long its log data lives. Two settings:

* **`body_retention_hours`** (default `48`) — how long `request_body` and `response_body` are kept before being nulled.
* **`log_retention_days`** (default `90`) — how long the rest of the log row is kept before being deleted.

Bodies are higher-sensitivity evidence; metadata is the audit trail. The split lets you keep bodies short (for confidentiality) while keeping metadata long (for compliance).

The invariant `body_retention_hours ≤ log_retention_days × 24` is enforced. Changes apply to **new logs only** — existing rows keep their original expiry.

See [Data Retention](data-retention.md) for full details, recommended values by use case, and special-case behavior.

## Active policy

Every project has exactly one **active policy** that determines which rules apply to incoming and outgoing messages. You can switch the active policy at any time -- the change takes effect immediately for all subsequent requests.

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "active_policy_id": "f9a8b7c6-..."
  }'
```

This is useful for:

* **A/B testing policies** -- switch between two policies and compare trigger rates.
* **Instant rollback** -- if a new policy causes issues, switch back to the previous one in a single API call.
* **Environment progression** -- use a lenient policy in staging and a strict one in production.

See [Policies](policies.md) for details on creating and managing policies.

## Deleting a project

Deleting a project is a **hard delete**. The project and its API keys are permanently removed. However, policies and rules linked to the project are **preserved** -- they are unlinked, not deleted. This means:

* The policy that was active on the project remains available for use on other projects.
* Rules within that policy are not affected.
* Provider tokens are user-scoped and are not affected by project deletion.

```bash
curl -X DELETE https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..."
```

{% hint style="warning" %}
This action cannot be undone. All API keys associated with the project will stop working immediately.
{% endhint %}

## API reference

### List all projects

```bash
curl https://app.collieai.io/api/v1/projects \
  -H "Authorization: Bearer clai_..."
```

### Get a project

```bash
curl https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..."
```

### Create a project

```bash
curl -X POST https://app.collieai.io/api/v1/projects \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-project",
    "description": "Optional description"
  }'
```

### Update a project

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "renamed-project",
    "filter_all_messages": true,
    "active_policy_id": "new-policy-uuid"
  }'
```

### Delete a project

```bash
curl -X DELETE https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..."
```

## Next steps

* [Policies](policies.md) -- create and manage the rule collections assigned to projects.
* [API Keys](../getting-started/api-keys.md) -- manage API keys within a project.
* [Provider Tokens](provider-tokens.md) -- configure the LLM provider keys used by the proxy.
* [Security Rules](../security-rules/overview.md) -- learn about the 9 rule types available in policies.

### Frequently asked questions

**How do I run multiple AI apps with different security settings in CollieAi?** Create a separate CollieAi project for each app. Each project is isolated with its own API keys, active policy, rate limit, and data retention, so a production chatbot, a staging environment, and an internal copilot can each have distinct security configurations.

**What happens to my policies and rules if I delete a project?** Deleting a project is a hard delete that removes the project and its API keys, but the linked policies and rules are preserved and unlinked, so they remain available for use on other projects. Provider tokens are user-scoped and unaffected.

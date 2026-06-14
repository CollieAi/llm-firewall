---
description: >-
  The CollieAi API reference — base URL, API key and session authentication,
  OpenAI-compatible   error format, rate limits, pagination, and every proxy,
  async, resource, and account endpoint.
icon: gear-complex-api
---

# Overview

This section documents every endpoint in the CollieAi API.

{% hint style="info" %}
**Key points**

* The CollieAi API base URL is `https://app.collieai.io` (replace it with your own URL when self-hosting).
* `/v1/...` endpoints use API key (Bearer) auth; `/api/v1/...` dashboard endpoints use a session cookie.
* All errors follow an OpenAI-compatible shape with `message`, `type`, and `code`.
* List endpoints are paginated with `page` and `page_size` (max 100).
{% endhint %}

## Base URL

```
https://app.collieai.io
```

If you are self-hosting, replace this with your own deployment URL.

## Authentication

CollieAI uses two authentication methods depending on the endpoint:

| Endpoint prefix | Auth method            | Description                                                                           |
| --------------- | ---------------------- | ------------------------------------------------------------------------------------- |
| `/v1/...`       | API key (Bearer token) | Used by your application to proxy LLM requests and manage resources programmatically. |
| `/api/v1/...`   | Session cookie         | Used by the CollieAi dashboard. Requires a logged-in session.                         |

### API Key Authentication

Pass your CollieAi API key in the `Authorization` header:

```
Authorization: Bearer clai_your_api_key_here
```

API keys are prefixed with `clai_` and scoped to a single project. See [API Keys](../getting-started/api-keys.md) for details.

### Session Authentication

Session cookies are set automatically when you sign in to the dashboard. No manual header is needed for browser-based requests.

## Error Format

All errors follow an OpenAI-compatible shape:

```json
{
  "error": {
    "message": "A human-readable description of what went wrong.",
    "type": "error_type",
    "code": 400
  }
}
```

### Common Error Types

| Type                    | Code | Description                                                      |
| ----------------------- | ---- | ---------------------------------------------------------------- |
| `invalid_request_error` | 400  | The request body is malformed or missing required fields.        |
| `policy_violation`      | 400  | A security rule with a **block** decision matched the content.   |
| `authentication_error`  | 401  | Missing, invalid, or expired API key or session.                 |
| `forbidden_error`       | 403  | The authenticated user does not have permission for this action. |
| `not_found_error`       | 404  | The requested resource does not exist.                           |
| `validation_error`      | 422  | One or more fields failed validation.                            |
| `rate_limit_exceeded`   | 429  | Too many requests. Back off and retry.                           |
| `billing_limit`         | 429  | Monthly plan quota exceeded (see Rate Limiting).                 |
| `internal_error`        | 500  | An unexpected server error occurred.                             |

## Rate Limiting

API requests are subject to two types of rate limits:

* **Per-project burst limit (RPM):** Configurable requests-per-minute limit for each project. Returns `429` with `type: "rate_limit_exceeded"`.
* **Monthly usage limit:** Based on your subscription plan (Free: 20,000 calls/month, Growth: 250,000 included). Returns `429` with `type: "billing_limit"` when exceeded.

The `Retry-After` header indicates how many seconds to wait before retrying. Monthly usage includes a grace buffer -- requests are blocked at 110% of the limit, not exactly 100%.

## Pagination

List endpoints support pagination with two query parameters:

| Parameter   | Default | Description                             |
| ----------- | ------- | --------------------------------------- |
| `page`      | 1       | The page number (1-indexed).            |
| `page_size` | 20      | Number of items per page (maximum 100). |

Paginated responses include metadata:

```json
{
  "items": [],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

## Endpoints

### Proxy

* [Chat Completions](chat-completions.md) -- OpenAI-compatible chat completions endpoint.

### Async

* [Jobs](jobs.md) -- Create and manage async processing jobs.

### Resources

* [Projects](projects.md) -- Create and manage projects.
* [Policies](policies.md) -- Create and manage policies within a project.
* [Rules](rules.md) -- Add, update, and remove rules from policies.
* [API Keys](api-keys.md) -- Generate and manage API keys for a project.
* [Provider Tokens](provider-tokens.md) -- Store and manage LLM provider credentials.
* [Dictionaries](dictionaries.md) -- Upload and manage term dictionaries for matching rules.
* [Alerts](alerts.md) -- Configure and manage monitoring alerts.

### Account

* [Auth](auth.md) -- Sign in, sign out, and manage sessions.
* [Health](health.md) -- Server health check.
* [Admin](admin.md) -- Administrative operations (user management, system resources).
* [Billing](billing.md) -- Subscription management, usage info, Stripe checkout and portal.

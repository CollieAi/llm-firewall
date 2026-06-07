---
description: >-
  How CollieAi API keys work — create, use, rotate, and deactivate clai_ keys
  that   authenticate your application's proxy and Jobs API requests, scoped to
  one project.
icon: rectangle-api
---

# API keys

API keys authenticate your application when it makes requests to CollieAi's proxy or Jobs API. Every key is prefixed with `clai_` so you can identify CollieAi keys at a glance.

## How do API keys work?

* Each key belongs to **one project**. Requests made with that key are scoped to the project's policies, rules, and provider tokens.
* The full key is returned **only once**, at creation time. After that, CollieAi stores a hashed version and shows a masked display form (e.g., `clai_AbCd...xYz`).
* Keys are passed as a Bearer token in the `Authorization` header.

## Creating a Key

### Via the Dashboard

1. Open your project in the CollieAi dashboard.
2. Navigate to **API Keys**.
3. Click **Create Key**.
4. Give the key a descriptive name (e.g., `backend-prod`, `staging-test`).
5. Click **Create** and copy the full key immediately.

### Via the API

You can also create keys programmatically. See the [API Keys endpoint reference](../api-reference/api-keys.md) for details.

## Using a Key

Pass the key as a Bearer token in the `Authorization` header:

```
Authorization: Bearer clai_your_api_key_here
```

With the OpenAI Python SDK or any OpenAI-compatible client:

```python
from openai import OpenAI

client = OpenAI(
    api_key="clai_AbCSSs2IjKlMnOpQrStUvWxYz01328901234",
    base_url="https://app.collieai.io/v1",
)
```

Or with curl:

```bash
curl https://app.collieai.io/v1/chat/completions \
  -H "Authorization: Bearer clai_AbCdEfAdDWxYz012345678901234" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Project Association

Every API key belongs to exactly one project. When a request arrives, CollieAi:

1. Looks up the key and verifies it is active and not expired.
2. Resolves the project the key belongs to.
3. Loads the project's active policy and rules.
4. Uses the project's provider token to forward requests to the LLM.

If you need different rule sets for different environments or applications, create separate projects and generate a key for each.

## What are the best practices for API keys?

* **Never commit keys to version control.** Use environment variables or a secrets manager instead.
* **Use descriptive names.** Names like `backend-prod-v2` make it easy to audit which services use which keys.
* **Rotate keys regularly.** Create a new key, update your application, then deactivate the old one.
* **Set expiration dates** for keys used in short-lived environments (CI, demos, testing).
* **One key per service.** If multiple services call CollieAi, give each its own key so you can revoke independently.

## Deactivating a Key

When a key is no longer needed or may have been compromised:

1. Open the project in the dashboard.
2. Go to **API Keys**.
3. Find the key and click **Deactivate**.

Deactivated keys are rejected immediately on the next request - no delay. Make sure your application has switched to a new key before deactivating the old one.

## See Also

* [Authentication](authentication.md) -- Overview of all auth methods.
* [API Reference: API Keys](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/api-reference) -- Full endpoint documentation for key management.

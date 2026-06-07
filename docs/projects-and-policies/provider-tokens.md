---
description: >-
  How CollieAi provider tokens work — store your OpenAI, Anthropic, Azure
  OpenAI, or Google Gemini API keys, encrypted at rest, so your app only needs a
  CollieAi key to reach the upstream model.
icon: square-binary
---

# Provider tokens

Provider tokens are the API keys for your LLM provider — OpenAI, Anthropic, Azure OpenAI, or Google Gemini. CollieAi stores these tokens and uses them when proxying requests to the upstream model, so your application only needs a CollieAi API key.

{% hint style="info" %}
**Key points**

* Provider tokens are your upstream LLM API keys (OpenAI, Anthropic, Azure OpenAI, Google Gemini) stored in CollieAi.
* They are user-scoped, so you configure a key once and all your projects use it via your default token.
* Tokens are encrypted at rest with Fernet (AES-128-CBC + HMAC-SHA256) when an encryption key is configured.
* Your application only needs a `clai_` CollieAi key — it never handles the raw provider key.
{% endhint %}

## How they work

When a request arrives at the CollieAi proxy:

1. CollieAi authenticates the request using the `clai_` API key.
2. Input security rules are applied.
3. The (possibly modified) message is forwarded to the LLM provider using your stored provider token.
4. Output security rules are applied to the response.
5. The filtered response is returned to your application.

Your application never needs direct access to the provider's API key -- it only needs the CollieAi API key.

## User-scoped, not per-project

Provider tokens are **user-scoped**. They belong to your account and are available across all of your projects. When CollieAi proxies a request, it uses your **default token** for the relevant provider, regardless of which project the request belongs to.

This means:

* You configure your OpenAI key once, and all projects use it.
* You do not need to duplicate provider keys across projects.
* If you rotate your OpenAI key, you update it in one place.

## Default token

You can have multiple provider tokens (for example, separate keys for different billing accounts or providers), but one must be marked as **default**. The default token is used for all proxy requests.

```bash
curl -X POST https://app.collieai.io/api/v1/tokens \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai-production",
    "provider": "openai",
    "api_key": "sk-...",
    "is_default": true
  }'
```

Marking a new token as default automatically un-defaults the previous one for that provider.

## Encryption at rest

When the `PROVIDER_TOKEN_ENCRYPTION_KEY` environment variable is set, CollieAi encrypts all stored provider tokens using **Fernet** (AES-128-CBC + HMAC-SHA256). This ensures that tokens are encrypted at rest in the database and can only be decrypted by the running application with the correct key.

| Configuration                              | Behavior                                                             |
| ------------------------------------------ | -------------------------------------------------------------------- |
| `PROVIDER_TOKEN_ENCRYPTION_KEY` is set     | Tokens are encrypted before storage and decrypted on use.            |
| `PROVIDER_TOKEN_ENCRYPTION_KEY` is not set | Tokens are stored in plaintext. Suitable for local development only. |

{% hint style="info" %}
**Recommendation:** Always set `PROVIDER_TOKEN_ENCRYPTION_KEY` in production environments. See [Self-Hosting](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/self-hosting) for configuration details.
{% endhint %}

## Supported providers

| Provider      | Value       | Notes                                   |
| ------------- | ----------- | --------------------------------------- |
| OpenAI        | `openai`    | Standard OpenAI API keys (`sk-...`)     |
| Anthropic     | `anthropic` | Claude Messages API keys (`sk-ant-...`) |
| Azure OpenAI  | `azure`     | Azure-specific endpoint and key         |
| Google Gemini | `gemini`    | Google AI API keys                      |

## API reference

### List all tokens

Returns all tokens for the authenticated user. Token values are **masked** in list responses -- only the last 4 characters are shown.

```bash
curl https://app.collieai.io/api/v1/tokens \
  -H "Authorization: Bearer clai_..."
```

**Response:**

```json
[
  {
    "id": "t1a2b3c4-...",
    "name": "openai-production",
    "provider": "openai",
    "api_key_last4": "Ab1C",
    "is_default": true,
    "created_at": "2026-02-23T10:00:00Z"
  }
]
```

### Create a token

```bash
curl -X POST https://app.collieai.io/api/v1/tokens \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai-staging",
    "provider": "openai",
    "api_key": "sk-...",
    "is_default": false
  }'
```

### Update a token

```bash
curl -X PATCH https://app.collieai.io/api/v1/tokens/{token_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai-production-rotated",
    "api_key": "sk-new-key-...",
    "is_default": true
  }'
```

### Delete a token

```bash
curl -X DELETE https://app.collieai.io/api/v1/tokens/{token_id} \
  -H "Authorization: Bearer clai_..."
```

{% hint style="warning" %}
**Warning:** Deleting the default token will cause proxy requests to fail until a new default is set.
{% endhint %}

## Best practices

| Practice                               | Why                                                                                                                                                                         |
| -------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Enable encryption in production**    | Set `PROVIDER_TOKEN_ENCRYPTION_KEY` to protect tokens at rest. Plaintext storage is acceptable only for local development.                                                  |
| **Rotate tokens regularly**            | Update your provider keys periodically. Use the PATCH endpoint to swap in a new key without downtime.                                                                       |
| **Use descriptive names**              | Name tokens by purpose and environment (e.g., `openai-production`, `azure-staging`) so you can identify them at a glance.                                                   |
| **Use separate keys for dev and prod** | Create distinct provider tokens for development and production environments. This isolates billing and makes it easier to rotate keys without affecting production traffic. |
| **Avoid sharing provider keys**        | Each CollieAi user should have their own provider tokens. Do not share raw provider API keys between users.                                                                 |
| **Monitor usage**                      | Check your provider's billing dashboard to ensure tokens are only used through CollieAi as expected.                                                                        |

## Next steps

* [Projects](projects.md) -- the environments that use provider tokens for proxying.
* [Proxy Integration](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/proxy-integration) -- how requests flow through CollieAi to the LLM.
* [Self-Hosting](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/self-hosting) -- configure encryption and other production settings.

### Frequently asked questions

**Which LLM providers can I connect to CollieAi?** You can store provider tokens for OpenAI, Anthropic (Claude), Azure OpenAI, and Google Gemini. CollieAi uses your default token for each provider when proxying requests, so your application only needs a CollieAi API key.

**Are my provider API keys stored securely in CollieAi?** Yes. When an encryption key is configured, CollieAi encrypts provider tokens at rest with Fernet (AES-128-CBC + HMAC-SHA256), masks them in API responses (last 4 characters only), and never exposes them to your application.

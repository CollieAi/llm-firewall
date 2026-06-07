---
description: >-
  CollieAi Provider Tokens API — add, list, update, and delete encrypted
  upstream LLM API keys   (OpenAI, Anthropic, and more) via /api/v1/tokens.
icon: cloudscale
---

# Provider tokens

Provider tokens store your LLM provider API keys (OpenAI, Anthropic, etc.) in CollieAi. The proxy uses these tokens to forward requests to upstream providers.

## GET /api/v1/tokens

List all provider tokens for the authenticated user. API key values are masked.

**URL:** `https://app.collieai.io/api/v1/tokens`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/api/v1/tokens \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
[
  {
    "id": "tok_abc123",
    "name": "OpenAI Production",
    "provider": "openai",
    "key_masked": "sk-...abc1",
    "is_default": true,
    "created_at": "2025-01-10T08:00:00Z",
    "updated_at": "2025-01-10T08:00:00Z"
  },
  {
    "id": "tok_def456",
    "name": "Anthropic Key",
    "provider": "anthropic",
    "key_masked": "sk-ant-...def4",
    "is_default": false,
    "created_at": "2025-01-12T09:00:00Z",
    "updated_at": "2025-01-12T09:00:00Z"
  }
]
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

## POST /api/v1/tokens

Add a new provider token.

**URL:** `https://app.collieai.io/api/v1/tokens`

**Auth:** Session cookie or Bearer token

### Request Body

| Field        | Type    | Required | Description                                              |
| ------------ | ------- | -------- | -------------------------------------------------------- |
| `provider`   | string  | Yes      | Provider identifier (`openai`, `anthropic`, etc.)        |
| `api_key`    | string  | Yes      | The provider API key value                               |
| `name`       | string  | No       | Display name for the token                               |
| `is_default` | boolean | No       | Set as default token for this provider. Default: `false` |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/tokens \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_key": "sk-abc123...",
    "name": "OpenAI Production",
    "is_default": true
  }'
```

### Response — `201 Created`

```json
{
  "id": "tok_new789",
  "name": "OpenAI Production",
  "provider": "openai",
  "is_default": true,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

> The API key value is stored encrypted and is never returned in API responses.

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `422`  | Validation error  |

## PATCH /api/v1/tokens/{token\_id}

Update a provider token's name or default status.

**URL:** `https://app.collieai.io/api/v1/tokens/{token_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter  | Type   | Description          |
| ---------- | ------ | -------------------- |
| `token_id` | string | The token identifier |

### Request Body

| Field        | Type    | Description                            |
| ------------ | ------- | -------------------------------------- |
| `name`       | string  | New display name                       |
| `is_default` | boolean | Set as default token for this provider |

### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/tokens/tok_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenAI Production (Updated)",
    "is_default": true
  }'
```

### Response — `200 OK`

```json
{
  "id": "tok_abc123",
  "name": "OpenAI Production (Updated)",
  "provider": "openai",
  "is_default": true,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Token not found   |
| `422`  | Validation error  |

## DELETE /api/v1/tokens/{token\_id}

Delete a provider token. If this was the default token for the provider, no default will be set.

**URL:** `https://app.collieai.io/api/v1/tokens/{token_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter  | Type   | Description          |
| ---------- | ------ | -------------------- |
| `token_id` | string | The token identifier |

### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/tokens/tok_abc123 \
  -H "Authorization: Bearer <token>"
```

### Response — `204 No Content`

No response body.

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Token not found   |

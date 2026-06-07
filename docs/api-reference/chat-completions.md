---
description: >-
  CollieAi chat completions API — the OpenAI-compatible POST
  /v1/chat/completions endpoint that   auto-routes gpt-* to OpenAI and claude-*
  to Anthropic, plus GET /v1/models.
icon: message
---

# Chat completions

## POST /v1/chat/completions

Create a chat completion through the CollieAi proxy. OpenAI-compatible request format. CollieAi auto-routes to the right upstream provider based on the `model` field:

* `gpt-*`, `o1-*`, `o3-*`, `o4-*`, `chatgpt-*`, `text-embedding-*`, `dall-e-*` → **OpenAI**
* `claude-*`, `claude.*` → **Anthropic** (translated to and from the Messages API)

If your project has an Anthropic provider token configured, sending `model="claude-sonnet-4-6"` Just Works — same request shape, same response shape, no client changes. Some OpenAI-only features (`n > 1`, `logprobs`, `response_format`, tool calling, vision) are rejected with `400 unsupported_for_provider` against `claude-*` models so behavior never silently differs from what you requested. See [Anthropic SDK Integration](../proxy-integration/anthropic-sdk-integration.md) for the full compatibility matrix.

Prefer Anthropic's native request shape? Use [`/v1/messages`](messages.md) instead.

**URL:** `https://app.collieai.io/v1/chat/completions`

**Auth:** Bearer token (API key `clai_xxx`)

### Request Body

| Field               | Type             | Required | Description                                                |
| ------------------- | ---------------- | -------- | ---------------------------------------------------------- |
| `model`             | string           | Yes      | Model identifier (e.g. `gpt-4o`, `claude-3-opus-20240229`) |
| `messages`          | array            | Yes      | Array of message objects                                   |
| `temperature`       | number           | No       | Sampling temperature, 0-2. Default: 1                      |
| `max_tokens`        | integer          | No       | Maximum tokens to generate                                 |
| `stream`            | boolean          | No       | Stream partial responses via SSE. Default: `false`         |
| `top_p`             | number           | No       | Nucleus sampling threshold. Default: 1                     |
| `frequency_penalty` | number           | No       | Penalize repeated tokens, -2.0 to 2.0. Default: 0          |
| `presence_penalty`  | number           | No       | Penalize tokens already present, -2.0 to 2.0. Default: 0   |
| `stop`              | string or array  | No       | Up to 4 sequences where generation stops                   |
| `tools`             | array            | No       | List of tool/function definitions                          |
| `tool_choice`       | string or object | No       | Controls tool usage (`auto`, `none`, or specific tool)     |
| `response_format`   | object           | No       | Force output format (e.g. `{"type": "json_object"}`)       |
| `seed`              | integer          | No       | Seed for deterministic sampling                            |
| `user`              | string           | No       | End-user identifier for abuse tracking                     |

### Message Format

| Field          | Type            | Required | Description                                                |
| -------------- | --------------- | -------- | ---------------------------------------------------------- |
| `role`         | string          | Yes      | One of `system`, `user`, `assistant`, `tool`               |
| `content`      | string or array | Yes      | Message content (string or content parts array)            |
| `name`         | string          | No       | Optional participant name                                  |
| `tool_calls`   | array           | No       | Tool calls made by the assistant                           |
| `tool_call_id` | string          | No       | ID of the tool call this message responds to (`tool` role) |

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/chat/completions \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "What is CollieAI?"}
    ],
    "temperature": 0.7,
    "max_tokens": 500
  }'
```

### Response -- `200 OK`

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1709000000,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "CollieAI is an AI firewall and governance platform..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 42,
    "total_tokens": 67
  }
}
```

The response body is 100% OpenAI-compatible. CollieAI metadata is returned via response headers (see below).

### CollieAI Headers

Responses that reach the proxy pipeline (status 200, 400 policy violations, 429 rate limits, and upstream errors) include these headers. Early rejections (401 auth, 403 IP block, 422 validation) do not, since the request never entered the proxy.

| Header                 | Type    | Description                                                                                                                                                                                          |
| ---------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `X-Collie-Duration-Ms` | integer | Proxy processing time in milliseconds. For non-streaming this is the full round-trip; for streaming it reflects setup time (auth + input filtering) since headers are sent before the stream begins. |
| `X-Collie-Proxied-At`  | integer | Unix timestamp when the request was processed                                                                                                                                                        |
| `X-Collie-Api-Version` | string  | API version (currently `v1`)                                                                                                                                                                         |

### Streaming

When `stream: true`, the response uses Server-Sent Events (SSE):

```
data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709000000,"model":"gpt-4o","choices":[{"index":0,"delta":{"role":"assistant","content":"Collie"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709000000,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"AI"},"finish_reason":null}]}

data: {"id":"chatcmpl-abc123","object":"chat.completion.chunk","created":1709000000,"model":"gpt-4o","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

### Error Responses

| Status | Code                  | Description                            |
| ------ | --------------------- | -------------------------------------- |
| `400`  | `content_blocked`     | Input message blocked by policy rule   |
| `400`  | `response_blocked`    | Output response blocked by policy rule |
| `401`  | `invalid_api_key`     | Missing or invalid API key             |
| `429`  | `rate_limit_exceeded` | Too many requests                      |
| `502`  | `upstream_error`      | Upstream LLM provider error            |

```json
{
  "error": {
    "message": "Request blocked by rule: PII Detection",
    "type": "content_blocked",
    "code": 400
  }
}
```

## GET /v1/models

List all models available through the CollieAI proxy for the authenticated project.

**URL:** `https://app.collieai.io/v1/models`

**Auth:** Bearer token (API key `clai_xxx`)

### Example Request

```bash
curl https://app.collieai.io/v1/models \
  -H "Authorization: Bearer clai_your_api_key"
```

### Response -- `200 OK`

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model",
      "created": 1709000000,
      "owned_by": "openai"
    },
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "created": 1709000000,
      "owned_by": "openai"
    },
    {
      "id": "claude-3-opus-20240229",
      "object": "model",
      "created": 1709000000,
      "owned_by": "anthropic"
    }
  ]
}
```

### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Missing or invalid API key |

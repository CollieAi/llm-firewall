---
description: >-
  CollieAi native Anthropic Messages API — the POST /v1/messages endpoint that
  matches api.anthropic.com verbatim for Claude, with CollieAi auth, filtering,
  and audit logging.
icon: claude
---

# Messages (native Anthropic)

## POST /v1/messages

Create a Claude completion through CollieAi using Anthropic's native Messages API shape. Use this route when your application is already built against the Anthropic SDK — request and response bodies match `api.anthropic.com/v1/messages` verbatim, with CollieAi's auth, rate limiting, content filtering, and audit logging layered on top.

For OpenAI-shape clients, use [`/v1/chat/completions`](chat-completions.md) instead — that route translates between OpenAI and Anthropic shapes automatically when the model is `claude-*`.

**URL:** `https://app.collieai.io/v1/messages`

**Auth:** Bearer token (API key `clai_xxx`)

**Required:** an Anthropic provider token configured in the dashboard.

### Request Body

| Field            | Type             | Required | Description                                                                                                                                |
| ---------------- | ---------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `model`          | string           | Yes      | Must be a `claude-*` model. Non-Anthropic models return `400 wrong_endpoint`.                                                              |
| `messages`       | array            | Yes      | Conversation history. Each item has `role` (`user`/`assistant`) and `content` (string or **text** content blocks). See restrictions below. |
| `max_tokens`     | integer          | Yes      | Required by Anthropic. Maximum tokens to generate.                                                                                         |
| `system`         | string \| array  | No       | System prompt. String form recommended. If array, each block must be `type: "text"`.                                                       |
| `temperature`    | number           | No       | 0.0 - 1.0.                                                                                                                                 |
| `top_p`          | number           | No       | 0.0 - 1.0.                                                                                                                                 |
| `top_k`          | integer          | No       | Sample from top-K tokens.                                                                                                                  |
| `stop_sequences` | array of strings | No       | Up to 4 sequences where generation stops.                                                                                                  |
| `stream`         | boolean          | No       | Stream events via SSE. Default `false`.                                                                                                    |
| `metadata`       | object           | No       | Arbitrary metadata, forwarded to Anthropic.                                                                                                |

Unrecognized top-level fields are forwarded to Anthropic unchanged so body-level betas and new features work without an SDK upgrade. Three Anthropic-SDK reserved kwargs — `extra_body`, `extra_headers`, `extra_query` — are explicitly rejected because they're SDK-level escape hatches that would inject content past CollieAi's filter, prompt-size cap, and audit logging. Note: CollieAi cannot filter or count content the proxy doesn't recognize as text — see restrictions below.

### v1 restrictions

To guarantee that filtering, prompt-size caps, and audit logging apply to every request — the same promise that `/v1/chat/completions` makes — the native route currently accepts **text content only**. The following fields and content block types are rejected with `400 unsupported_for_provider`, matching the rejection set on `/v1/chat/completions` when the model is `claude-*`:

| Rejected                                       | Why                                                                                                                   |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `tools`                                        | Tool schemas would bypass prompt-size caps (often thousands of tokens). Coming in a later release.                    |
| `tool_choice`                                  | Same.                                                                                                                 |
| `image` content blocks                         | Image data isn't visible to the text-based filter. Vision support deferred.                                           |
| `tool_use` content blocks (assistant messages) | Tool-call args aren't currently filterable.                                                                           |
| `tool_result` content blocks (user messages)   | Tool output text isn't currently walked by the filter; in agentic flows it often carries the most sensitive data.     |
| `document` content blocks                      | PDF data isn't filterable.                                                                                            |
| `thinking` content blocks                      | Extended-thinking content isn't currently filterable.                                                                 |
| `extra_body`, `extra_headers`, `extra_query`   | Anthropic-SDK escape hatches that would merge into the upstream request after CollieAi's inspection. Always rejected. |

Schema also enforces well-formedness on accepted shapes: `messages` cannot be empty, each message needs a `user`/`assistant` role and non-empty `content`, and `text` blocks must carry a non-empty string `text` field. Malformed shapes return `422 validation_error` before any side effects (no quota consumption, no upstream call).

If your application needs any of the deferred features above, please reach out — we're tracking demand to prioritize.

### Example: Non-streaming

```bash
curl -X POST https://app.collieai.io/v1/messages \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [
      {"role": "user", "content": "Hello, Claude!"}
    ]
  }'
```

Response:

```json
{
  "id": "msg_01ABC...",
  "type": "message",
  "role": "assistant",
  "model": "claude-sonnet-4-6",
  "content": [
    {"type": "text", "text": "Hello! How can I help?"}
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 12,
    "output_tokens": 8,
    "cache_creation_input_tokens": 0,
    "cache_read_input_tokens": 0
  }
}
```

### Example: Streaming

Set `"stream": true`. Response uses Anthropic's typed-event SSE format (`message_start`, `content_block_delta`, `message_delta`, `message_stop`):

```
event: message_start
data: {"type": "message_start", "message": {...}}

event: content_block_start
data: {"type": "content_block_start", "index": 0, "content_block": {"type": "text", "text": ""}}

event: content_block_delta
data: {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hi"}}

...
```

### Error Responses

| Status | Code                       | Cause                                                                                                                                                                                                            |
| ------ | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 400    | `wrong_endpoint`           | Model is not `claude-*`. Use `/v1/chat/completions` for OpenAI models.                                                                                                                                           |
| 400    | `configuration_error`      | No Anthropic provider token configured.                                                                                                                                                                          |
| 400    | `unsupported_for_provider` | Request uses a feature listed in [v1 restrictions](messages.md#v1-restrictions) — tools, vision, tool\_use/tool\_result/document/thinking blocks, etc.                                                           |
| 400    | `policy_violation`         | Content blocked by a configured rule.                                                                                                                                                                            |
| 400    | `billing_limit`            | Prompt exceeds the plan's `max_prompt_tokens` cap, or the user is past their monthly call limit.                                                                                                                 |
| 422    | `validation_error`         | Malformed request shape — empty `messages`, missing/invalid `role` or `content`, non-string `text` in a text block, SDK escape-hatch fields, etc. Returned before any side effects (no quota, no upstream call). |
| 429    | `rate_limit_exceeded`      | Project RPM limit hit, or upstream rate-limited.                                                                                                                                                                 |
| 5xx    | `anthropic_error`          | Upstream Anthropic error, status code passed through.                                                                                                                                                            |

### Filtering and audit

Native `/v1/messages` accepts text content only (see [v1 restrictions](messages.md#v1-restrictions)) — both string-shaped and `[{"type": "text", "text": "..."}]`-list-shaped content. Input filtering runs on each message's text content; output filtering runs on the assembled response text before it reaches the client. If a rule masks content, the masked text is emitted in a single synthetic text block; the original token counts from upstream are preserved in the response so client-side billing reconciliation matches Anthropic's invoice.

Every request is logged to `request_logs` with `endpoint="/v1/messages"` and `provider="anthropic"`. Anthropic-specific prompt-caching counters (`cache_creation_input_tokens`, `cache_read_input_tokens`) are stored in dedicated columns for cache-hit-rate analytics, and their values are also summed into `prompt_tokens` so subscription billing matches what Anthropic charges. On blocked or masked responses, the audit log records the masked text (or empty for blocked) rather than the original content.

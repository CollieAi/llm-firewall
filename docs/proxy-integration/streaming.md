---
description: >-
  How CollieAi streams LLM responses — real-time SSE streaming with output
  guardrails enforced on the stream, in both incremental and buffered modes, for
  OpenAI and Anthropic.
icon: signal-stream
---

# Streaming

CollieAi supports Server-Sent Events (SSE) streaming, matching the OpenAI and Anthropic streaming formats. Your existing streaming code works without modification — just point it at CollieAi.

{% hint style="info" %}
**Key points**

* CollieAi supports real-time SSE streaming and enforces output security rules on the stream itself.
* There are two delivery paths: incremental (near-real-time) and buffered (after full generation plus filtering).
* The wire format is identical to the upstream provider — OpenAI-compatible on `/v1/chat/completions`, Anthropic-native on `/v1/messages`.
* You set the streaming mode (`auto`, `incremental`, `buffered`) per project, and CollieAi never silently overrides it.
{% endhint %}

{% hint style="info" %}
**Using a non-OpenAI/Anthropic model?** This page covers streaming through the drop-in proxy. If you're calling your own model (self-hosted, open-source, multi-provider router) and want filtered streaming output, push chunks into a job instead — see [Customer-owned streaming](../async-jobs/customer-owned-streaming.md).
{% endhint %}

How quickly the first token reaches your client depends on your project's **streaming mode** and the security rules in the project's active policy. There are two delivery paths:

1. **Incremental streaming** — safe text is released to your client as the upstream model generates it. Rules run on a sliding window so violations are caught mid-stream. This is what you get for projects on `streaming_mode = "auto"` (the default for new projects) or `"incremental"`, _when every active output rule supports streaming_.
2. **Buffered streaming** — CollieAi accumulates the upstream model's full response, applies output rules to the complete text, then replays the result to your client in SSE format. This is what you get on `streaming_mode = "buffered"`, OR on `auto`/`incremental` projects where any active rule needs full context to make a decision (for example LLM-detection rules, language detection, or multi-rule policies that haven't been cleared for cascading streaming yet).

In both cases the wire format is identical — your client doesn't need to know which path served the request. The difference is **first-token latency**: incremental is near-real-time, buffered is delayed by the full upstream generation time plus the time to apply your output rules.

## Choosing a streaming mode

The mode lives on the project, not the request. Set it via the dashboard or [`PATCH /api/v1/projects/{project_id}`](../api-reference/projects.md):

```json
{"streaming_mode": "auto"}
```

| Mode                                | When to choose                                                                                                                                                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `auto` _(default for new projects)_ | You want incremental streaming when CollieAi can prove it's safe, buffered otherwise. The right default for most apps.                                                                                                                         |
| `incremental`                       | Same behavior as `auto` today. Keep this if you want to be explicit that you're opting into streaming (and to make a future "auto with traffic heuristics" change opt-in only).                                                                |
| `buffered`                          | You want CollieAi to always buffer-then-replay. Use this if your app is latency-insensitive and you'd rather not deal with mid-stream blocks (a block on incremental can fire after some safe text has already been delivered to your client). |

If you're not sure which mode you're on, the project's [Analytics page](../monitoring/analytics.md) shows a **Streaming engine** card with delivery mix per window.

## Enabling streaming on a request

Set `stream: true` exactly as you would against OpenAI or Anthropic. CollieAi doesn't introduce a new flag.

```bash
curl -X POST "https://app.collieai.io/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer clai_your_api_key_here" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Tell me a short story."}],
    "stream": true
  }'
```

## SSE format

The wire format mirrors whichever upstream provider you're calling — CollieAi does not introduce a custom envelope. The same delivery path (incremental or buffered) is used for both providers, but the byte sequence is provider-specific. Pick the section that matches your route.

### `/v1/chat/completions` (OpenAI-compatible)

Each chunk is delivered as a `data:` line in standard SSE format, with `[DONE]` as the terminator:

```
data: {"id":"chatcmpl-9a1b2c","object":"chat.completion.chunk","created":1709145600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"role":"assistant","content":""},"finish_reason":null}]}

data: {"id":"chatcmpl-9a1b2c","object":"chat.completion.chunk","created":1709145600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":"Once"},"finish_reason":null}]}

data: {"id":"chatcmpl-9a1b2c","object":"chat.completion.chunk","created":1709145600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{"content":" upon"},"finish_reason":null}]}

data: {"id":"chatcmpl-9a1b2c","object":"chat.completion.chunk","created":1709145600,"model":"gpt-4o-mini","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

The first chunk typically contains the `role` field in `delta`. Subsequent chunks contain incremental `content`. The final chunk has an empty `delta` and a `finish_reason` of `"stop"`. The stream ends with `data: [DONE]`.

### `/v1/messages` (Anthropic-native)

Anthropic's SSE format is **typed**: every chunk carries an `event:` name in addition to the `data:` payload, and there's **no `[DONE]` terminator** — the stream ends with `message_stop`. Six event types appear in a normal stream:

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_01","role":"assistant","content":[],"model":"claude-sonnet-4-5","stop_reason":null,"usage":{"input_tokens":10,"output_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Once"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" upon"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":2}}

event: message_stop
data: {"type":"message_stop"}
```

Periodic `event: ping` frames may appear mid-stream as keepalives. Consume them as no-ops.

## Python streaming example

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a short story about a brave dog."}
    ],
    stream=True
)

for chunk in stream:
    content = chunk.choices[0].delta.content
    if content:
        print(content, end="", flush=True)

print()  # Newline after the stream completes
```

## How does incremental streaming works

When your project's mode is `auto` or `incremental` AND every active output rule supports streaming, CollieAi runs rules on a **sliding window** as text arrives:

```mermaid
flowchart TD
    A["Client request"] --> B["Input filtering (before the stream starts)"]
    B --> C["Upstream model streams tokens"]
    C --> D["CollieAi sliding-window engine"]
    D --> E["Safe stable prefix (released)"]
    D --> F["Unstable suffix (held back)"]
    E --> G["Client"]
```

The engine holds back a small suffix (the "unstable window") so rules can detect patterns that straddle chunk boundaries. The held-back suffix size depends on the rule type — typically 64–512 characters. As the window grows past the unstable region, safe text is released to your client.

If a rule fires on the stable window:

* **Mask** — the matched region is replaced with the rule's placeholder (e.g. `[EMAIL_REDACTED]`) before the affected chunk is released. Some safe text may have already reached your client before the match was detected; CollieAi never recalls already-sent bytes.
* **Block** — the stream emits a single error chunk and closes. Any safe text already released to your client stays — your application has to handle the early termination.

## How does buffered streaming works

When your project's mode is `buffered`, OR when a rule in the policy can't be evaluated on a streaming window (e.g. LLM-detection rules need the full text), CollieAi accumulates the upstream response, applies rules to the complete text, then replays the result:

```mermaid
flowchart TD
    A["Client request"] --> B["Input filtering (before the stream starts)"]
    B --> C["Upstream model streams tokens"]
    C --> D["CollieAi buffers full response"]
    D --> E["Apply output rules"]
    E --> F["Allowed"]
    E --> G["Masked"]
    E --> H["Blocked"]
    F --> F2["Re-stream original chunks"]
    G --> G2["Re-stream with masked content"]
    H --> H2["Send error chunk and close stream"]
```

In buffered mode the first token reaches your client **after** the full upstream generation and rule evaluation, so first-token latency equals the upstream generation time plus the filter time. Once filtering is complete, the buffered chunks are delivered rapidly.

### When does a project on `auto` get buffered anyway?

* Any active output rule requires full context (LLM detection, language detection, lightweight model).
* The policy has multiple output rules (cascading streaming semantics aren't shipped yet — multi-rule policies always buffer).
* A streaming-eligible rule's configuration falls outside its safe-window guarantee (regex pattern with unbounded quantifier, AhoCorasick dictionary with a term longer than the rule's window, URL rule with `block_encoded_patterns=true`, base64 rule with `min_length` greater than its window).
* `STREAMING_MODES_ENABLED` is `false` on the host (self-hosted opt-out).

In all of these cases your project's `streaming_mode` is honored — there's no silent override. You get buffered behavior because that's what the policy can safely deliver. The dashboard's Streaming engine card surfaces both delivery paths so you can see which way your traffic actually went.

### Blocked response during streaming

If an output rule blocks the response, the stream emits a single error frame and closes. The shape is provider-specific — same OpenAI/Anthropic split as the success case above.

**`/v1/chat/completions`** (OpenAI-compatible) — error chunk followed by `[DONE]`:

```
data: {"error":{"message":"Response blocked by security policy","type":"policy_violation","code":"response_blocked"}}

data: [DONE]
```

The OpenAI SDKs raise an `APIError` when they encounter the error chunk.

**`/v1/messages`** (Anthropic-native) — typed `event: error` frame, **no `[DONE]`**:

```
event: error
data: {"type":"error","error":{"type":"policy_violation","message":"Response blocked by security policy"}}
```

The Anthropic SDK raises an `APIError` when it encounters the error event. There's no terminator frame — the connection closes after the error event. Clients that wait for a `message_stop` to consider the stream complete should ALSO treat `event: error` as terminal.

On the incremental path, this error can arrive **after** some safe text has already been delivered to your client. Plan your UI so a stream that begins rendering can still surface a policy block — for example, by attaching the final error to a dedicated UI affordance rather than assuming "stream started ⇒ stream completed."

## Best practices

* **Set appropriate client timeouts.** On the buffered path, first-token latency equals the full upstream generation time plus filter time. Set your client timeout to at least the expected generation time plus 10–15 seconds. For long outputs, consider 60–120 seconds. On the incremental path, the first token arrives in milliseconds, but the overall timeout should still cover the full generation in case the policy hits a buffered fallback.
* **Handle stream errors gracefully.** A stream can be interrupted by a policy violation at any point. Always wrap your streaming loop in a try/except (Python) or try/catch (Node.js) block. See [Error Handling](error-handling.md) for details.
* **Use buffered mode if mid-stream blocks complicate your UX.** If your app can't easily surface a policy block after some text has already rendered, set `streaming_mode = "buffered"` so the block (if any) fires before your client sees any content. The latency trade-off is the cost.
* **Test with your output rules enabled.** The delivery path depends on which rules are active. Test in your development environment with the same policy you run in production so you don't get a different delivery profile on launch.
* **Consider `stream_options` for token usage.** If you need token usage information in streaming mode, pass `stream_options: {"include_usage": true}` in your request. The final chunk will include a `usage` field.

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True,
    stream_options={"include_usage": True}
)
```

## Streaming vs non-streaming comparison

| Aspect                   | Non-streaming                        | Streaming (buffered)                          | Streaming (incremental)                                |
| ------------------------ | ------------------------------------ | --------------------------------------------- | ------------------------------------------------------ |
| Wire format              | Single JSON response                 | SSE chunks (`data:` lines)                    | SSE chunks (`data:` lines)                             |
| Time to first token      | After full generation + filtering    | After full generation + filtering             | Within milliseconds of the upstream's first token      |
| Delivery after filtering | All at once                          | Chunk by chunk (rapid replay)                 | Continuous, with a small held-back suffix              |
| Mid-stream blocks        | Not applicable                       | Block fires before any content reaches client | Block can fire after some safe text has reached client |
| Client compatibility     | Any HTTP client                      | SSE-capable client required                   | SSE-capable client required                            |
| Best for                 | Short responses, simple integrations | Long responses where UX needs all-or-nothing  | Long responses where time-to-first-token matters       |

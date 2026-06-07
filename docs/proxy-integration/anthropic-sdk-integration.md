---
description: >-
  Connect Anthropic's Claude to CollieAi — use the native Messages API
  (/v1/messages) or the OpenAI-compatible endpoint with claude-* models, secured
  by the same guardrails.
icon: claude
---

# Anthropic SDK Integration

CollieAi proxies Anthropic's Claude models through two surfaces:

* **`/v1/chat/completions`** — OpenAI-compatible. Use this when migrating an OpenAI-based app to Claude with a single line change. CollieAi translates between OpenAI and Anthropic shapes automatically.
* **`/v1/messages`** — Native Anthropic Messages API. Use this when your app already uses the Anthropic SDK directly.

Both surfaces apply the same authentication, rate limiting, content filtering, and audit logging.

{% hint style="info" %}
Using OpenAI models instead? See [OpenAI SDK Integration](openai-sdk-integration.md) — CollieAi applies the same security pipeline across every provider.
{% endhint %}

## Add an Anthropic provider token

1. Open the dashboard at [https://app.collieai.io](https://app.collieai.io).
2. Go to **Provider Tokens → Add token**.
3. Select **Anthropic (Claude)** as the provider, paste your `sk-ant-...` key, give it a name, and mark it as default.

CollieAi never logs your API key in plaintext — it's encrypted at rest with Fernet.

## Option A — Native Anthropic SDK (recommended)

Use the Anthropic SDK exactly as you would against `api.anthropic.com`, but point `base_url` at CollieAi. CollieAi mounts `/v1/messages` with the same shape Anthropic does and accepts the API key from the SDK's default `x-api-key` header — **no header overrides needed.**

{% tabs %}
{% tab title="Python" %}
```bash
pip install anthropic
```

```python
from anthropic import Anthropic

client = Anthropic(
    base_url="https://app.collieai.io",
    api_key="clai_your_api_key_here",
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ],
)
print(message.content[0].text)
```
{% endtab %}

{% tab title="Node.js" %}
```bash
npm install @anthropic-ai/sdk
```

```javascript
import Anthropic from "@anthropic-ai/sdk";

const client = new Anthropic({
  baseURL: "https://app.collieai.io",
  apiKey: "clai_your_api_key_here",
});

const message = await client.messages.create({
  model: "claude-sonnet-4-6",
  max_tokens: 1024,
  messages: [{ role: "user", content: "Hello, Claude!" }],
});
console.log(message.content[0].text);
```
{% endtab %}

{% tab title="cURL" %}
```bash
curl https://app.collieai.io/v1/messages \
  -H "Authorization: Bearer clai_your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello, Claude!"}]
  }'
```
{% endtab %}
{% endtabs %}

## Option B — OpenAI SDK targeting Claude models

Already on the OpenAI SDK? Keep your client, just send a `claude-*` model name. CollieAi will route to Anthropic and translate the response back to OpenAI shape.

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here",
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",  # <-- claude-* models route to Anthropic
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

## Streaming

Both routes support streaming. The native `/v1/messages` route forwards Anthropic's event-typed SSE format; the OpenAI-compatible route emits OpenAI-shape SSE chunks.

```python
# Native Anthropic streaming
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

## Supported features (v1)

| Feature                        | `/v1/chat/completions` (claude-\* model) | `/v1/messages` (native)       |
| ------------------------------ | ---------------------------------------- | ----------------------------- |
| Text generation                | ✅                                        | ✅                             |
| Streaming                      | ✅                                        | ✅                             |
| System prompts                 | ✅ (auto-extracted from messages)         | ✅ (top-level `system` field)  |
| Stop sequences                 | ✅ (`stop` → `stop_sequences`)            | ✅                             |
| Temperature / top\_p           | ✅                                        | ✅                             |
| Prompt caching                 | ✅ (counts surface in usage metrics)      | ✅                             |
| Tool calling                   | ❌ — coming in a later release            | ❌ — coming in a later release |
| Vision (image input)           | ❌ — coming in a later release            | ❌ — coming in a later release |
| `n > 1` (multiple completions) | ❌ — Anthropic doesn't support            | n/a                           |
| `logprobs`                     | ❌ — Anthropic doesn't support            | n/a                           |
| `response_format` (JSON mode)  | ❌ — use prompt-based guidance instead    | n/a                           |

Unsupported fields are rejected on BOTH surfaces with `400 unsupported_for_provider` rather than silently dropped — your code won't surprise you with mismatched semantics, and you get identical errors whether you call `/v1/chat/completions` or `/v1/messages`. On the native route the rejection also covers non-text content blocks (`image`, `tool_use`, `tool_result`, `document`, `thinking`) because CollieAi's filter and prompt-size cap operate on text. See [v1 restrictions on /v1/messages](../api-reference/messages.md#v1-restrictions) for the full list.

## Supported models

CollieAi recognizes any model name starting with `claude-` (or `claude.`) as Anthropic. The curated list returned by `GET /v1/models` includes:

* `claude-opus-4-7`
* `claude-opus-4-6`
* `claude-sonnet-4-6`
* `claude-haiku-4-5-20251001`
* `claude-3-5-sonnet-20241022`
* `claude-3-5-haiku-20241022`
* `claude-3-opus-20240229`

Other Claude variants (Bedrock, custom deployments) work too as long as the name starts with `claude-`.

### Frequently asked questions

**Can I use Claude with CollieAi?** Yes. CollieAi proxies Anthropic's Claude models through two surfaces — the native Messages API at `/v1/messages` and the OpenAI-compatible `/v1/chat/completions` endpoint with a `claude-*` model name — both secured by the same guardrails.

**Do I need to change my Anthropic SDK code to use CollieAi?** No. You use the Anthropic SDK exactly as you would against api.anthropic.com and only point `base_url` at CollieAi. CollieAi accepts the SDK's default `x-api-key` header, so no header overrides are needed.

**Can I keep the OpenAI SDK while calling Claude through CollieAi?** Yes. Keep your OpenAI client and send a `claude-*` model name; CollieAi routes the request to Anthropic and translates the response back to OpenAI shape.

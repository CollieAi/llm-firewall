---
description: >-
  How the CollieAi proxy integration works — a drop-in, provider-agnostic proxy
  that filters every LLM request and response, OpenAI-compatible and
  Anthropic-native.
icon: gear
---

# Proxy integration overview

CollieAi acts as a **drop-in, provider-agnostic proxy** between your application and your LLM provider. Change two configuration values — your base URL and API key — and every request is automatically filtered through your project's security policies before it reaches the model. CollieAi is OpenAI-compatible and also supports Anthropic's native Messages API, so there are no code changes, no new dependencies, and no refactoring.

{% hint style="info" %}
**Key points**

* CollieAi is a drop-in, provider-agnostic proxy — change your `base_url` and API key, with no other code changes.
* It is OpenAI-compatible and supports Anthropic's native Messages API, and routes to OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, or self-hosted models.
* Every request is filtered on both input and output against your project's security rules.
* Full SSE streaming is supported, with output rules still enforced on the stream.
{% endhint %}

## How does the CollieAi proxy work?

<figure><img src="../.gitbook/assets/1.png" alt=""><figcaption></figcaption></figure>

1. **Authenticate** - CollieAi validates your `clai_` API key and resolves the associated project.
2. **Input filtering** - User messages are checked against all active input rules (PII masking, prompt injection detection, keyword blocking, etc.).
3. **Forward to the provider** - The filtered request is sent to your chosen provider (OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, or a self-hosted model) using your project's provider token.
4. **Output filtering** - The model's response is checked against all active output rules.
5. **Return response** - A standard OpenAI-compatible (or Anthropic-native) response is returned to your application.

## What are the benefits of the drop-in proxy?

* **Zero code changes.** The request and response format is identical to the OpenAI and Anthropic APIs. Just update `base_url` and `api_key`.
* **Works with OpenAI and Anthropic SDKs.** Official OpenAI Python and Node.js SDKs, the Anthropic SDK, and any HTTP client that speaks the OpenAI or Anthropic protocol.
* **Full streaming (SSE) support.** Streaming works exactly as it does with the provider's API. Output rules are still enforced on the stream.
* **Multi-tenant.** Each API key maps to a project with its own set of rules and provider tokens.
* **Transparent filtering.** Both input (user to model) and output (model to user) content is filtered automatically.

## Quick Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

That is the entire integration. Everything else - PII redaction, prompt injection blocking, keyword filtering - happens automatically based on the rules configured in your CollieAi project.

## Response Metadata

CollieAi metadata is returned via response headers, keeping the response body 100% OpenAI-compatible:

| Header                 | Type    | Description                                                                                                                                                                                          |
| ---------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `X-Collie-Duration-Ms` | integer | Proxy processing time in milliseconds. For non-streaming this is the full round-trip; for streaming it reflects setup time (auth + input filtering) since headers are sent before the stream begins. |
| `X-Collie-Proxied-At`  | integer | Unix timestamp when the request was processed.                                                                                                                                                       |
| `X-Collie-Api-Version` | string  | API version (currently `v1`).                                                                                                                                                                        |

These headers are included on responses that reach the proxy pipeline (200, 400 policy blocks, 429 rate limits, upstream errors). Early rejections before the proxy runs (401 auth, 403 IP block, 422 validation) do not include them. They do not interfere with standard OpenAI SDK parsing.

## Message Filtering Scope

The **filter\_all\_messages** project setting controls which messages in the conversation are evaluated by input rules:

| Setting           | Behavior                                                                                                                                             |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `true`            | All messages in the `messages` array are filtered. Use this for maximum coverage when the full conversation history is submitted on each request.    |
| `false` (default) | Only the last message in the `messages` array is filtered. This is more efficient when earlier messages have already been checked on prior requests. |

This setting can be configured per-project in the CollieAI dashboard.

## Drop-in proxy vs async jobs: which should you use?

CollieAi offers two integration modes. Choose the one that fits your architecture.

|                        | Drop-in Proxy                                                             | Async Jobs                                                        |
| ---------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| **How it works**       | Change `base_url` to CollieAi; we proxy to your provider                  | Submit content via the Jobs API; receive results via webhook      |
| **Latency**            | Synchronous -- response in real time                                      | Asynchronous -- results delivered later                           |
| **Who calls the LLM?** | CollieAi proxies the call to your provider for you                        | You call your own LLM and submit content for filtering            |
| **Streaming**          | Full SSE streaming support                                                | Not applicable                                                    |
| **Integration effort** | Minimal -- two config changes                                             | Requires a webhook endpoint to receive results                    |
| **Best for**           | Chat applications, real-time assistants, any OpenAI or Anthropic SDK user | Batch processing, custom LLM providers, high-throughput pipelines |

**Use the drop-in proxy when** you want the fastest path to protection. If you are already calling OpenAI or Anthropic, you can be up and running in minutes.

**Use async jobs when** you need to bring your own model, process content in bulk, or integrate filtering into an event-driven architecture.

## Next Steps

* [OpenAI SDK Integration](openai-sdk-integration.md) -- Complete setup guide for Python, Node.js, cURL, and function calling
* [Streaming](streaming.md) -- How streaming works with CollieAI, including output filtering behavior
* [Error Handling](error-handling.md) -- Error format, policy violation responses, and troubleshooting

### Frequently asked questions

**How do I integrate CollieAi as a proxy?** You integrate CollieAi by changing two values in your existing OpenAI or Anthropic SDK — the `base_url` and the API key. No other code changes, dependencies, or refactoring are required.

**Which SDKs and providers does the CollieAi proxy support?** The CollieAi proxy is OpenAI-compatible and supports Anthropic's native Messages API. Through these protocols it routes to OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models.

**Does the CollieAi proxy support streaming?** Yes. CollieAi supports full server-sent events (SSE) streaming exactly as the provider does, and output security rules are still enforced on the stream by the streaming guard.

**Does CollieAi change the response format?** No. CollieAi keeps the response body fully OpenAI-compatible (or Anthropic-native) and returns its own metadata through `X-Collie-*` response headers, so standard SDK parsing is unaffected.

**When should I use the drop-in proxy instead of async jobs?** Use the drop-in proxy for real-time, synchronous use cases like chat and assistants, where CollieAi calls the provider for you. Use async jobs when you call your own model, process content in bulk, or work in an event-driven architecture.

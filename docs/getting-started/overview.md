---
description: >-
  How to get started with CollieAi, an AI firewall and LLM security gateway —
  secure your LLM app, block prompt injection, and redact PII in about five
  minutes.
icon: rocket-launch
---

# Getting started with CollieAi

CollieAi is an AI firewall (LLM security gateway) that sits between your application and your LLM provider. Every request and response passes through a configurable filtering pipeline that detects and redacts PII, blocks prompt injection and jailbreaks, filters URLs, and more — without changing how your application talks to the model.

{% hint style="info" %}
**Key points**

* CollieAi is a drop-in, provider-agnostic proxy — switch by changing one `base_url`. It works with any major LLM provider through an OpenAI-compatible API and Anthropic's native Messages API.
* It secures OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models (vLLM, Ollama, LocalAI).
* Two integration paths: a real-time drop-in proxy, and async jobs for batch or long-running work.
* You need a CollieAi account and a provider API key to send your first secured request.
{% endhint %}

<figure><img src="../.gitbook/assets/1 (2).png" alt=""><figcaption></figcaption></figure>

## What do you need to get started?

Before you begin, make sure you have:

* [x] **A CollieAi account** - Sign up at [app.collieai.io](https://app.collieai.io/) using Google OAuth or email/password.
* [x] **A provider API key** - You need an API key from your LLM provider — OpenAI, Anthropic, Google Gemini, Azure OpenAI, AWS Bedrock, or a self-hosted endpoint. CollieAi proxies your requests using this key.

## Three Ways to Integrate

<table data-card-size="large" data-view="cards"><thead><tr><th></th><th></th><th></th></tr></thead><tbody><tr><td><h4><i class="fa-right-to-bracket" style="color:$primary;">:right-to-bracket:</i></h4></td><td><strong><a href="../proxy-integration/overview.md">Drop-in Proxy</a></strong></td><td>The fastest path. Point your OpenAI or Anthropic SDK (or any OpenAI-compatible client) at CollieAi by changing the <code>base_url</code>.<br><br>Your existing code works as-is - CollieAi transparently applies security rules and forwards requests to the provider.<br><br>Best for: real-time chat, streaming responses, low-latency use cases.</td></tr><tr><td><h4><i class="fa-rotate" style="color:$primary;">:rotate:</i></h4></td><td><strong><a href="../async-jobs/overview.md">Async Jobs</a></strong></td><td>Submit a request and receive a callback when the result is ready.<br><br>Useful for batch processing, long-running prompts, or workflows where you do not need an immediate response.<br><br>Best for: background processing, batch pipelines, webhook-driven architectures.</td></tr><tr><td><h4><i class="fa-code" style="color:$primary;">:code:</i></h4></td><td><strong><a href="../sdks/overview.md">SDKs</a></strong></td><td>Language-native clients for Python, Node, and .NET. Run your own model and stream back only CollieAi-released text - the SDK owns the chunk protocol and input moderation, so you never touch the raw endpoints.<br><br>Best for: customer-owned streaming, safe token-by-token UX from your own backend.</td></tr></tbody></table>

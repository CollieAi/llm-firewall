---
description: >-
  CollieAi is an AI firewall and LLM security gateway — a drop-in,
  OpenAI-compatible proxy that blocks prompt injection and redacts PII across
  OpenAI, Anthropic Claude, Google Gemini, and Azure OpenAI.
icon: paw
---

# CollieAi

CollieAi is an AI firewall (LLM security gateway) **—** a drop-in proxy that intercepts API calls to large language models, applies configurable security rules to both input and output, and routes requests to your chosen LLM provider.

CollieAi is **OpenAI-compatible** and supports **Anthropic's native Messages API** — change one line of code and your existing OpenAI or Anthropic SDK calls flow through CollieAi. Through these protocols it secures OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models (vLLM, Ollama, LocalAI).



{% tabs %}
{% tab title="Point your SDK at CollieAi and secure any LLM provider — one line" %}
```python
# Before — direct call to OpenAI
client = OpenAI(api_key="sk-...")

# After — change base_url, full protection
client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_project_key",
)
```
{% endtab %}
{% endtabs %}

<button type="button" class="button primary" data-action="ask" data-icon="gitbook-assistant">Ask a question…</button>

<a href="getting-started/quick-start.md" class="button primary" data-icon="rocket-launch">Quick Start</a><a href="https://app.collieai.io" class="button primary" data-icon="right-to-bracket">Try for Free</a><a href="api-reference/overview.md" class="button secondary">API Reference</a>

## Key Features

* **Drop-in proxy for any LLM provider** - Point your existing OpenAI or Anthropic SDK at CollieAi by changing the `base_url`. No other code changes needed.
* **Security Rules Pipeline** - Define input and output rules that inspect, mask, or block content before it reaches the model or your users.
* **PII Detection** - Identify and redact personally identifiable information (PII) in real time using regex patterns, structured ID validation, and dictionary matching.
* **Prompt Injection Blocking** - Stop prompt injection and jailbreak attempts in real time with a lightweight ML classifier and LLM-based detection.
* **Async Jobs** - Submit long-running requests and receive results via webhooks when they complete.
* **Monitoring and Analytics** - View request logs, track usage analytics, and configure alerts from a single dashboard.
* **Multi-Tenancy** - Organize work into projects, each with its own policies, rules, API keys, and provider tokens.
* **Free & Growth Plans** - Start for free with 20,000 API calls/month and all features included. Upgrade to Growth for production-scale volume and priority support.

## Getting Started

<table data-view="cards"><thead><tr><th></th><th></th><th></th></tr></thead><tbody><tr><td><h4><i class="fa-rocket-launch" style="color:$primary;">:rocket-launch:</i></h4></td><td><h3><a href="./getting-started/overview.md">Getting started</a></h3></td><td>Sign up, create a project, send your first secured request</td></tr><tr><td><h4><i class="fa-plug-circle-plus" style="color:$primary;">:plug-circle-plus:</i></h4></td><td><h3><a href="./proxy-integration/overview.md">Proxy Integration</a></h3></td><td>Connect the OpenAI or Anthropic SDK and route to OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, or self-hosted models — with streaming and error handling</td></tr><tr><td><h4><i class="fa-arrows-retweet" style="color:$primary;">:arrows-retweet:</i></h4></td><td><h3><a href="./async-jobs/overview.md">Async Jobs</a></h3></td><td>View request logs, usage analytics, and configure alerts</td></tr></tbody></table>

## Explore

<table data-view="cards"><thead><tr><th></th><th></th><th></th></tr></thead><tbody><tr><td><h4><i class="fa-square-a-lock" style="color:$primary;">:square-a-lock:</i></h4></td><td><h3><a href="./security-rules/overview.md">Security Rules</a></h3></td><td>Configure PII masking, threat blocking, and text processing</td></tr><tr><td><h4><i class="fa-diagram-subtask" style="color:$primary;">:diagram-subtask:</i></h4></td><td><h3><a href="./projects-and-policies/overview.md">Projects &#x26; Policies</a></h3></td><td>Organize workloads with projects, policies, and provider tokens</td></tr><tr><td><h4><i class="fa-display-chart-up-circle-currency" style="color:$primary;">:display-chart-up-circle-currency:</i></h4></td><td><h3><a href="./monitoring/overview.md">Monitoring</a></h3></td><td>View request logs, usage analytics, and configure alerts</td></tr></tbody></table>

### Frequently asked questions

**What is CollieAi?** CollieAi is an AI firewall (LLM security gateway) — a drop-in, OpenAI-compatible proxy that blocks prompt injection and redacts PII in real time before requests reach the model or responses reach your users.

**Which LLM providers does CollieAi support?** CollieAi secures OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models (vLLM, Ollama, LocalAI). It exposes an OpenAI-compatible API and an Anthropic-native Messages API, so existing SDK calls flow through unchanged.

**How does CollieAi stop prompt injection?** CollieAi detects prompt injection and jailbreak attempts with a lightweight ML classifier plus LLM-based detection, and blocks or masks malicious input before it reaches the model.

**Does CollieAi redact PII?** Yes. CollieAi identifies and redacts personally identifiable information (PII) using regex patterns, structured ID validation, and dictionary matching, on both input and output.

**How much does CollieAi cost?** CollieAi is free for 20,000 API calls per month with the full guardrail stack. The Growth plan is $49/month and includes 250,000 requests, then $0.001 per additional request — an AI firewall for well under $500/month.

**Can I self-host CollieAi?** Yes. CollieAi can be self-hosted, where billing is disabled by default and you get unlimited projects and API calls with no usage limits.

---
description: >-
  Language-native CollieAi SDKs for Python, Node, and .NET — customer-owned
  streaming and pre-generation input moderation without touching the raw chunk
  protocol.
icon: code
---

# SDKs

The CollieAi SDKs are language-native clients for **customer-owned streaming** and **input moderation**. You run your own model; the SDK checks the prompt before generation and streams back only CollieAi-released text — it owns the chunk protocol (sequence numbers, retries, idempotency, finalization), so you never touch the [raw chunk endpoints](../async-jobs/customer-owned-streaming.md).

All three SDKs share the same API shape and are validated by a cross-language conformance suite, so behavior is consistent across languages.

## Choose your language

<table data-view="cards"><thead><tr><th></th><th></th><th></th></tr></thead><tbody><tr><td><h4><i class="fa-python" style="color:$primary;">:python:</i></h4></td><td><strong><a href="python-sdk.md">Python SDK</a></strong></td><td><code>pip install collieai</code><br><br>Async-first client built on httpx + pydantic.</td></tr><tr><td><h4><i class="fa-node-js" style="color:$primary;">:node-js:</i></h4></td><td><strong><a href="node-sdk.md">Node SDK</a></strong></td><td><code>npm install @collieai/sdk</code><br><br>Zero-runtime-dependency TypeScript client.</td></tr><tr><td><h4><i class="fa-microsoft" style="color:$primary;">:microsoft:</i></h4></td><td><strong><a href="dotnet-sdk.md">.NET SDK</a></strong></td><td><code>dotnet add package CollieAi.Client</code><br><br>.NET 8 client with dependency-injection support.</td></tr></tbody></table>

## When to use an SDK

Use an SDK when you run your own model and want safe, token-by-token streaming from your own backend — without implementing the chunk protocol or webhooks yourself. For a real-time drop-in proxy, see [Proxy Integration](../proxy-integration/overview.md); for webhook-based batch work, see [Async Jobs](../async-jobs/overview.md).

---
icon: node-js
---

# Node SDK

The `@collieai/sdk` Node/TypeScript SDK is the recommended way to do
customer-owned streaming from a Node backend. You run your own model; the SDK
checks the prompt before you call it and lets you stream back **only
CollieAi-released text** — never raw model output. It owns the chunk protocol
(sequence numbers, retries, idempotency, finalization), so you don't touch the
[raw chunk endpoints](../async-jobs/customer-owned-streaming.md). It mirrors the
[Python SDK](python-sdk.md) — same event model, same typed errors — and has
**zero runtime dependencies** (it uses the global `fetch`; Node ≥ 18).

{% hint style="warning" %}
**Forward `event.text`, never the raw model delta.** The whole point of the SDK
is that your users only ever see text CollieAi has released. The examples below
keep the raw provider stream inside the `rawStreamFactory`; you only forward SDK
events.
{% endhint %}

## Install

```bash
npm install @collieai/sdk
```

## Construct the client

```ts
import { CollieClient } from "@collieai/sdk";

const collie = new CollieClient({
  apiKey: "clai_...",
  baseUrl: "https://app.collieai.io",
  projectId: "project_123",
});
```

## Check an input before calling your LLM

```ts
const result = await collie.moderate.input({
  prompt: userPrompt,
  conversationId,          // optional: groups a conversation
  correlationId: turnId,   // optional: pins one turn
});

if (result.blocked) return result.blockMessage ?? "Input blocked by policy.";
```

A policy block is a normal result (`result.blocked === true`), not an error.
No webhook is required — the SDK polls for you.

## Analyze context alongside the prompt

Pass `context` to analyze the data you're about to send the model — retrieved
documents, tool output, a record — alongside the prompt. Structured `context`
travels as JSON; `contextFormat` (`"auto"` | `"json"` | `"text"`) is an optional
hint for a raw string.

```ts
const result = await collie.moderate.input({
  prompt: userPrompt,
  context: { transaction: { memo: retrievedMemo } },
});

const ctx = result.context;
if (ctx && ctx.status !== "clean" && ctx.status !== "not_provided") {
  console.log(ctx.status, ctx.triggeringPointer, ctx.triggeringRuleType); // path, never a value
}
if (result.blocked) return result.blockMessage ?? "Blocked by policy.";
// result.blockedBy is "prompt" | "context" | "none"
```

`result.context` carries the closed `status` enum, the triggering JSON Pointer +
rule, and degraded markers; the pointer is a **path, never a value**. The same
`context` works on `protectStream` / `protectBuffered` when input checking is
enabled. See [Context analysis](../security-rules/context-analysis.md).

{% hint style="info" %}
Until context analysis is enabled (host flag **and** policy switch), `context` is
inert — a safe no-op.
{% endhint %}

## Stream safely (Express)

`protectStream` checks the input, calls your LLM **only if it passes**, batches
the output, and yields only safe events. Pass a *factory* (a function returning a
fresh async iterable; it may accept the SDK-provided `AbortSignal`), not an
already-started stream — the SDK calls it once, after the check.

By default it streams optimistically — if the policy can't stream, the first
push throws `ChunkStreamingUnsupported`. To choose the UX *before* generating,
use [preflight](#choose-the-ux-up-front-preflight) or pass `requireStreaming: true`.

```ts
import express from "express";
import OpenAI from "openai";
import { CollieClient } from "@collieai/sdk";

const collie = new CollieClient({ apiKey: process.env.COLLIEAI_API_KEY! });
const openai = new OpenAI();
const app = express();
app.use(express.json());

async function* openaiDeltas(prompt: string, signal?: AbortSignal) {
  const stream = await openai.chat.completions.create(
    {
      model: "gpt-4o-mini",
      messages: [{ role: "user", content: prompt }],
      stream: true,
    },
    signal ? { signal } : undefined,
  );
  try {
    for await (const part of stream as AsyncIterable<any>) {
      const delta = part.choices?.[0]?.delta?.content;
      if (delta) yield delta;
    }
  } finally {
    stream.controller?.abort(); // stop generation if abandoned early
  }
}

app.post("/chat", async (req, res) => {
  res.setHeader("content-type", "text/plain");
  for await (const event of collie.streaming.protectStream({
    input: req.body.prompt,
    rawStreamFactory: (signal) => openaiDeltas(req.body.prompt, signal),
  })) {
    if (event.type === "delta") res.write(event.text);
    else if (event.type === "blocked" || event.type === "input_blocked") {
      res.write(event.blockMessage ?? "Blocked by policy.");
      break;
    }
  }
  res.end();
});
```

That's the whole integration. You never touch chunk sequence numbers, retries,
or batching. The same loop works in a Next.js App Router route handler —
return a `ReadableStream` that enqueues `event.text`.

{% hint style="info" %}
**Provider adapters.** Instead of writing `openaiDeltas` by hand, use the
packaged factory (the provider SDK stays an optional peer dependency):

```ts
import { openaiFactory } from "@collieai/sdk/adapters/openai";
// or: import { anthropicFactory } from "@collieai/sdk/adapters/anthropic";

const factory = openaiFactory(openai, {
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: prompt }],
});
for await (const event of collie.streaming.protectStream({ input: prompt, rawStreamFactory: factory })) {
  // ...
}
```

The factory opens the provider stream lazily (only after the input check
passes) and closes it on early exit.
{% endhint %}

## Choose the UX up front (preflight)

Ask whether the policy can stream **before** calling the LLM, and branch into a
token-stream UI or a "checking response…" UI:

```ts
const cap = await collie.streaming.preflight(); // cached until cap.validUntil

if (cap.recommendedClientBehavior === "stream") {
  // protectStream → token-stream UI
} else if (cap.recommendedClientBehavior === "buffer_then_show") {
  const result = await collie.streaming.protectBuffered({
    input: userPrompt,
    rawStreamFactory: (signal) => openaiDeltas(userPrompt, signal),
  });
  // "checking response…", then show result
} else {
  throw new Error(cap.reasonDetail ?? cap.reason ?? "policy unavailable"); // fail_fast
}
```

Prefer not to branch yourself? Pass `requireStreaming: true` to `protectStream`:
it preflights first and throws `BufferedFallbackRequired` (policy must buffer)
or a `PreflightError` (can't be served) **before** calling your LLM.

## Buffered fallback

When a policy can't stream, check the whole response at once — same input gate
and factory contract, but it returns a single result instead of events:

```ts
const result = await collie.streaming.protectBuffered({
  input: userPrompt,
  rawStreamFactory: (signal) => openaiDeltas(userPrompt, signal),
});
return result.blocked ? result.blockMessage : result.filteredText;
```

## Relay safe output to a browser (SSE)

When your backend submits chunks for a job, it can also **subscribe** to that
job's CollieAi SSE stream and relay safe events to a browser — with automatic
reconnect. `session.streamEvents()` yields the same typed events as
`protectStream`, plus `interrupted` on idle-timeout / disconnect.

```ts
import { toSse } from "@collieai/sdk";

for await (const event of session.streamEvents()) {  // auto-resumes from Last-Event-ID
  if (event.type === "interrupted") continue;        // reconnecting; nothing to forward
  res.write(toSse(event));                           // SSE bytes for text/event-stream
  if (event.type === "blocked" || event.type === "finished") break;
}
```

On a dropped connection or server idle-timeout the SDK reconnects from the last
seen event id and **deduplicates replayed frames**, so a delta is never shown
twice. To handle resume yourself, pass `autoResume: false` — iteration then
stops at the first `interrupted` event, whose `lastEventId` you pass back to
`streamEvents({ lastEventId })` later.

### Let a browser subscribe directly (stream tokens)

To skip the backend relay, mint a short-lived, job-scoped **stream token** and
hand it to the browser — your API key stays server-side:

```ts
// Backend: mint and return a token for the browser.
const st = await session.mintStreamToken();
return { url: st.url, expiresIn: st.expiresIn };
```

```javascript
// Browser: subscribe with the token in the query string.
const es = new EventSource(url); // .../v1/jobs/{id}/stream?stream_token=...
es.addEventListener("chunk", (e) => {
  const chunk = JSON.parse(e.data);
  if (chunk.content) append(chunk.content);
  if (chunk.blocked) {
    append(chunk.block_message ?? "Blocked by policy.");
    es.close();
  }
});
es.addEventListener("end", () => es.close());
```

{% hint style="info" %}
**Token scope & delegation.** A stream token is read-only and valid only for its
one job's stream — it can't submit chunks or call any other endpoint, and it
can't be used for a different job. *Minting* is fully authenticated (active user
+ IP allowlist, via your API key); the token is then a **delegated capability**
that the browser redeems from its own IP, so it is *not* re-checked against the
IP allowlist. Keep the API key server-side; give the browser only the token, and
re-mint before it expires. Operators can disable browser tokens entirely with
`STREAM_TOKEN_ENABLED=false` (then use the backend relay above).
{% endhint %}

{% hint style="warning" %}
**The token is a credential in the URL.** Treat the full `?stream_token=...` URL
as secret: serve it over HTTPS, don't log it, and redact `stream_token` at your
proxy/access-log layer. A direct browser `EventSource` to CollieAi is
**cross-origin** — your site's origin must be in the API's CORS allowlist, or
use the backend relay above instead.
{% endhint %}

## Errors

Catch typed errors instead of parsing strings. All extend `CollieError`.
Policy blocks are **events** (`type: "blocked"` / `"input_blocked"`), not
errors.

| Error | When | What to do |
|---|---|---|
| `ChunkRetryExhausted` | transient failures exceeded the retry budget | retry the turn, or fall back to a non-streaming path |
| `ChunkPolicyChanged` | policy changed mid-stream | start a new stream/session (it picks up the new policy) |
| `ChunkSessionUnrecoverable` | the stream entered an unrepairable state | start a new stream/session |
| `ChunkQuotaExceeded` | rate-limited with no usable `Retry-After` | back off and retry later |
| `ChunkStreamingUnsupported` | the policy can't be served by the streaming engine | use `protectBuffered` instead |
| `BufferedFallbackRequired` | `requireStreaming: true` but the policy must buffer | switch to `protectBuffered` |
| `ProjectNotFound` / `StreamingFeatureDisabled` / `PlanNotEntitled` / `UnknownRuleType` / `PolicyNotStreamable` (`PreflightError`) | preflight says the policy can't be served | fix project/policy configuration |
| `ProviderStreamFactoryRequired` | passed a started stream (or non-async-iterable) instead of a factory | pass a factory returning a fresh async iterable: `(signal) => myStream(signal)` |
| `ConcurrentSessionUseError` | overlapping `push()` calls on one low-level session | serialize submits per session |
| `ModerationError` | `moderate.input` job failed/expired or timed out | retry the input check |
| `CollieConnectionError` | transport failure (timeout, connection refused) | retry; check connectivity to `baseUrl` |
| `CollieApiError` | unexpected HTTP error or malformed response (`code === "invalid_response"`) | inspect `statusCode`/`code`; retry or report |

## Retry behavior

The SDK retries the **same** chunk sequence on transient failures (network
timeouts, `503`, `504 chunk_filter_timeout`, `429` with a usable `Retry-After`)
with exponential backoff + jitter — default base 250 ms, max 4 s, 3 attempts per
chunk, 10 s ceiling (`new CollieClient({ retryMaxPerChunkS: ... })`). A retried
chunk never produces a duplicate visible delta.

## Advanced: low-level session

If you need to drive batching yourself, use the session directly. It does
**not** check the input — call `moderate.input(...)` first.

```ts
const check = await collie.moderate.input({ prompt: userPrompt });
if (check.blocked) return check.blockMessage ?? "Input blocked by policy.";

const session = collie.streaming.session({ input: userPrompt });
await session.open();
try {
  for await (const rawDelta of yourLlmStream()) {
    const result = await session.push(rawDelta);
    for (const emit of result.emits) forward(emit.text); // forward ONLY safe emits
    if (result.finished) break;
  }
  await session.finish();
} finally {
  await session.close();
}
```

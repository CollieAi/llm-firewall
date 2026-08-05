---
icon: python
---

# Python SDK

The `collieai` Python SDK is the recommended way to do customer-owned
streaming. You run your own model; the SDK checks the prompt before you call it
and lets you stream back **only CollieAi-released text** — never raw model
output. It owns the chunk protocol (sequence numbers, retries, idempotency,
finalization), so you don't touch the [raw chunk endpoints](../async-jobs/customer-owned-streaming.md).

{% hint style="warning" %}
**Forward `SafeDelta.text`, never the raw model delta.** The whole point of the
SDK is that your users only ever see text CollieAi has released. The examples
below keep the raw provider stream inside the `raw_stream_factory`; you only
yield SDK events.
{% endhint %}

## Install

```bash
pip install collieai
```

## Construct the client

```python
from collieai import AsyncCollie

collie = AsyncCollie(
    api_key="clai_...",
    base_url="https://app.collieai.io",
    project_id="project_123",
)
```

One pooled HTTP connection set is reused across calls. Close it with
`await collie.aclose()` when done, or use it as an async context manager.

## Check an input before calling your LLM

```python
result = await collie.moderate.input(
    prompt=user_prompt,
    conversation_id=conversation_id,   # optional: groups a conversation
    correlation_id=chat_turn_id,       # optional: pins one turn
)

if result.blocked:
    return result.block_message or "Input blocked by policy."
```

A policy block is a normal result (`result.blocked is True`), not an exception.
No webhook is required — the SDK polls for you.

## Analyze context alongside the prompt

Pass `context` to analyze the data you're about to send the model — retrieved
documents, tool output, a record — alongside the prompt, so an injection hidden in
that data is caught too. Structured `context` travels as JSON; `context_format`
(`"auto"` | `"json"` | `"text"`) is an optional hint for a raw string.

```python
result = await collie.moderate.input(
    prompt=user_prompt,
    context={"transaction": {"memo": retrieved_memo}},
)

if result.context and result.context.status in ("monitored", "blocked", "degraded"):
    print(result.context.status,
          result.context.triggering_pointer,     # e.g. "/transaction/memo" — a path, never a value
          result.context.triggering_rule_type)

if result.blocked:
    # result.blocked_by is "prompt" or "context"
    return result.block_message or "Blocked by policy."
```

`result.context` carries the closed `status` enum, the triggering JSON Pointer +
rule, and degraded-coverage markers; the pointer is a **path, never a value**. The
same `context` works on `protect_stream` / `protect_buffered` when input checking
is enabled. See [Context analysis](../security-rules/context-analysis.md).

{% hint style="info" %}
Until context analysis is enabled (the deployment's host flag **and** the policy
switch), `context` is inert — a safe no-op (`status` `disabled` / `not_provided`).
{% endhint %}

## Check an output produced outside a wrapper

`protect_stream` / `protect_buffered` already moderate the streamed answer. Use
`moderate.output` for assistant text that never went through a wrapper —
proactive notifications, escalation messages, any side channel. Don't route
such text through `moderate.input`: that evaluates it with **input** rules, so
output-safety and masking rules silently never run, and injection detectors can
false-block assistant-style imperatives ("You need to submit…").

```python
result = await collie.moderate.output(
    response=assistant_text,
    conversation_id=conversation_id,   # optional
    correlation_id=notification_id,    # optional
)

if result.blocked:
    return  # don't send it
# `is not None`, NOT `or`: an empty filtered_text is a real mask result
# (a rule may replace the whole match with "") — `or` would send the
# original, unmasked text.
safe = result.filtered_text if result.filtered_text is not None else assistant_text
send(safe)
```

`filtered_text` carries the **masked** output — send it, not the original, or
masking rules silently do nothing. `moderate.output` takes no `context`:
context is an input surface; for context-aware output filtering use
`protect_buffered` / `protect_stream`.

## Stream safely (FastAPI)

`protect_stream` checks the input, calls your LLM **only if it passes**, batches
the output, and yields only safe events. Pass a *factory* (a zero-arg callable
returning your stream), not an already-started stream — the SDK calls it once,
after the check.

By default it streams optimistically — if the policy can't stream, the first
push raises `ChunkStreamingUnsupported`. To choose the UX *before* generating,
use [preflight](#choose-the-ux-up-front-preflight) or pass `require_streaming=True`.

```python
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI
from collieai import AsyncCollie, SafeDelta, Blocked, InputBlocked

collie = AsyncCollie(api_key=os.environ["COLLIEAI_API_KEY"], project_id="project_123")
openai_client = AsyncOpenAI()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await collie.aclose()          # release the SDK's pooled connections
    await openai_client.close()    # ...and OpenAI's


app = FastAPI(lifespan=lifespan)


async def openai_deltas(prompt: str):
    stream = await openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    try:
        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    finally:
        await stream.close()   # stop generation if the stream is abandoned early


@app.post("/chat")
async def chat(body: dict):
    prompt = body["prompt"]

    async def events():
        async for event in collie.streaming.protect_stream(
            input=prompt, raw_stream_factory=lambda: openai_deltas(prompt),
        ):
            if isinstance(event, SafeDelta):
                yield event.text
            elif isinstance(event, (Blocked, InputBlocked)):
                yield event.block_message or "Blocked by policy."
                return

    return StreamingResponse(events(), media_type="text/plain")
```

That's the whole integration. You never touch chunk sequence numbers, retries,
or batching.

{% hint style="info" %}
**Provider adapters.** Instead of writing `openai_deltas` by hand, install an
extra and use the packaged factory:

```python
from collieai.adapters.openai import openai_factory       # pip install "collieai[openai]"
# or: from collieai.adapters.anthropic import anthropic_factory  # "collieai[anthropic]"

factory = openai_factory(openai_client, model="gpt-4o-mini",
                         messages=[{"role": "user", "content": prompt}])
async for event in collie.streaming.protect_stream(input=prompt, raw_stream_factory=factory):
    ...
```

The factory opens the provider stream lazily (only after the input check passes)
and closes it on early exit.
{% endhint %}

## Choose the UX up front (preflight)

Ask whether the policy can stream **before** calling the LLM, and branch into a
token-stream UI or a "checking response…" UI:

```python
cap = await collie.streaming.preflight()   # cached until cap.valid_until

if cap.recommended_client_behavior == "stream":
    async for event in collie.streaming.protect_stream(
        input=user_prompt, raw_stream_factory=lambda: openai_deltas(user_prompt),
    ):
        ...   # token-stream UI
elif cap.recommended_client_behavior == "buffer_then_show":
    result = await collie.streaming.protect_buffered(
        input=user_prompt, raw_stream_factory=lambda: openai_deltas(user_prompt),
    )
    ...       # "checking response…", then show result
else:
    raise RuntimeError(cap.reason_detail or cap.reason)   # fail_fast
```

Prefer not to branch yourself? Pass `require_streaming=True` to `protect_stream`:
it preflights first and raises `BufferedFallbackRequired` (policy must buffer)
or a `PreflightError` (can't be served) **before** calling your LLM.

### Which rule is responsible — `cap.rules`

`cap.rules` explains the verdict rule by rule. Each entry carries
`execution_role`, the role that rule plays in a streaming request:

| `execution_role` | meaning |
| --- | --- |
| `enforce_streaming` | blocks or masks **as tokens arrive** |
| `enforce_postflight` | blocks or masks, but needs the **whole** response first — a policy containing one always buffers |
| `stream_observed` | monitor-only; observed **as tokens arrive** while the text streams through untouched |
| `postflight_observed` | monitor-only; observed after the response completes |
| `null` | the rule could not be planned at all (e.g. an unrecognised type) |

```python
blockers = [r for r in cap.rules if r.execution_role == "enforce_postflight"]
if blockers:
    print("buffered because:", ", ".join(r.rule_name for r in blockers))
```

{% hint style="info" %}
`streaming_supported` is `False` for **every** monitor rule, so it cannot tell a
`stream_observed` rule from a `postflight_observed` one. Use `execution_role`
when you need that distinction — typically while running a policy in monitor
mode before turning on blocking.
{% endhint %}

Three things `execution_role` does not tell you. It is **per-rule** and ignores
policy-level gates, so a rule can say `stream_observed` while the request still
buffers — `cap.mode` remains the answer to "does this request stream at all".
It reflects your project's current streaming setting, so a project set to
`buffered` reports full-context roles throughout. And it reflects the **server
that answered**: on current servers a monitor-only policy streams — monitor
rules observe the text as it passes and their findings appear in your CollieAi
audit log only, never in the chunk responses your users see. A server that has
not been upgraded yet still buffers any policy containing a monitor rule and
answers `cap.mode = "buffered"`, `cap.reason = "monitor_mode"`; the SDK
handles both, and `cap.mode` is always the delivery verdict. The roles are
what let you see, ahead of time, whether monitor→enforce will be a config flip
or a re-integration.

Treat the value as an open string: compare against the names you know and fall
through on anything else, so a role added later doesn't break your branch.


## Buffered fallback

When a policy can't stream, check the whole response at once — same input gate
and factory contract, but it returns a single result instead of events:

```python
result = await collie.streaming.protect_buffered(
    input=user_prompt, raw_stream_factory=lambda: openai_deltas(user_prompt),
)
return result.block_message if result.blocked else result.filtered_text
```

## Relay safe output to a browser (SSE)

When your backend submits chunks for a job, it can also **subscribe** to that
job's CollieAi SSE stream and relay safe events to a browser — with automatic
reconnect. `session.stream_events()` yields the same typed events as
`protect_stream`, plus `StreamInterrupted` on idle-timeout / disconnect.

```python
from collieai import SafeDelta, Blocked, Finished, StreamInterrupted, to_sse

async def relay():
    async for event in session.stream_events():     # auto-resumes from Last-Event-ID
        if isinstance(event, StreamInterrupted):
            continue                                 # reconnecting; nothing to forward
        yield to_sse(event)                          # framework-friendly SSE bytes
        if isinstance(event, (Blocked, Finished)):
            return
```

On a dropped connection or server idle-timeout the SDK reconnects from the last
seen event id and **deduplicates replayed frames**, so a delta is never shown
twice. To handle resume yourself, pass `auto_resume=False` — iteration then stops
at the first `StreamInterrupted`, whose `last_event_id` you pass back to
`stream_events(last_event_id=...)` later.

`to_sse(event)` re-encodes an event as an SSE frame you can write straight to
your own `text/event-stream` response.

### Let a browser subscribe directly (stream tokens)

To skip the backend relay, mint a short-lived, job-scoped **stream token** and
hand it to the browser — your API key stays server-side. The token authorizes
read-only SSE access to **one** job's stream and expires quickly; re-mint before
it lapses.

```python
# Backend: mint and return a token for the browser.
st = await session.mint_stream_token()
return {"url": st.url, "expires_in": st.expires_in}
```

```javascript
// Browser: subscribe with the token in the query string.
const es = new EventSource(url);   // .../v1/jobs/{id}/stream?stream_token=...
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
IP allowlist. Keep the API key server-side; give the browser only the token.
Operators can disable browser tokens entirely with `STREAM_TOKEN_ENABLED=false`
(then use backend relay).
{% endhint %}

{% hint style="warning" %}
**The token is a credential in the URL.** Treat the full `?stream_token=...` URL
as secret: serve it over HTTPS, don't log it, and redact `stream_token` at your
proxy/access-log layer.

**CORS.** A direct browser `EventSource` to CollieAi is **cross-origin**, so your
site's origin must be in the API's CORS allowlist (`CORS_ORIGINS`). If you can't
configure that, use the **backend relay** above instead — it's same-origin and
needs no CORS setup.
{% endhint %}

## Errors

Catch typed exceptions instead of parsing strings. All inherit from
`CollieError`.

| Exception | When | What to do |
|---|---|---|
| `InputBlocked` *(event)* / `Blocked` *(event)* | input or output blocked by policy | show `block_message`; not an error — it's a terminal event from `protect_stream` |
| `ChunkRetryExhausted` | transient failures exceeded the retry budget | retry the turn, or fall back to a non-streaming path |
| `ChunkPolicyChanged` | policy changed mid-stream | start a new stream/session (it picks up the new policy) |
| `ChunkSessionUnrecoverable` | the stream entered an unrepairable state | start a new stream/session |
| `ChunkQuotaExceeded` | rate-limited with no usable `Retry-After` | back off and retry later |
| `ChunkStreamingUnsupported` | the policy can't be served by the streaming engine | use `protect_buffered` instead |
| `ChunkResolutionUnavailable` | `503 chunk_resolution_unavailable` — the server couldn't **resolve** the policy (a dependency outage, not a policy shape) | nothing at first: the SDK retries it automatically; if the outage outlasts the retry budget it is the `__cause__` of `ChunkRetryExhausted` |
| `BufferedFallbackRequired` | `require_streaming=True` but the policy must buffer | switch to `protect_buffered` |
| `ProjectNotFound` / `StreamingFeatureDisabled` / `PlanNotEntitled` / `UnknownRuleType` / `PolicyNotStreamable` *(`PreflightError`)* | preflight says the policy can't be served | fix project/policy configuration; other reason codes (e.g. `rule_unplannable`, `resolution_error:<cause>`) surface as the base `PreflightError` — treat the code as an open string |
| `ProviderStreamFactoryRequired` | passed a started stream (or non-async-iterable) instead of a factory | pass a zero-arg callable: `lambda: my_stream()` |
| `ConcurrentSessionUseError` | overlapping `push()` calls on one low-level session | serialize submits per session |
| `ModerationError` | a `moderate.input` / `moderate.output` job failed/expired or timed out | retry the check |
| `CollieConnectionError` | transport failure (timeout, connection refused) | retry; check connectivity to `base_url` |
| `CollieAPIError` | unexpected HTTP error or malformed response (`code="invalid_response"`) | inspect `status_code`/`code`; retry or report |

## Retry behavior

The SDK retries the **same** chunk sequence on transient failures (network
timeouts, `503` — including the typed `chunk_resolution_unavailable` —
`504 chunk_filter_timeout`, `429` with a usable `Retry-After`)
with exponential backoff + jitter — default base 250 ms, max 4 s, 3 attempts per
chunk, 10 s ceiling (`AsyncCollie(retry_max_per_chunk_s=...)`). A retried chunk
never produces a duplicate visible delta.

## Failure policy: fail-closed by default

When retries are exhausted the SDK **fails closed** — it raises and releases no
text. There is no fail-open switch: shipping unchecked model output is a risk
decision only you can make, so it has to be your explicit code, not a default.

Two things decide what that code should do.

**1. Where you caught it.** `raw_stream_factory` is a deferred factory: the SDK
calls it exactly once, *after* the input check passes and the session exists. So
if CollieAi is unreachable, the failure lands before your LLM ever ran — nothing
was generated, nothing reached the user, and passing through is a clean choice.
A failure *mid-stream* is different: some text is already on screen and the
engine is holding more, so re-running the model would duplicate output. Track it
with one flag.

**2. Not every `CollieError` is an outage.** `ChunkStreamingUnsupported` means
the policy demands buffered checking, and `ChunkRetryExhausted` means a
mid-stream abort. Catching the base class and passing through would bypass a
policy that deliberately asked to inspect the whole answer. Catch the transport
failures — `CollieConnectionError` and `CollieAPIError` with a 5xx — and nothing
else.

```python
from collieai.errors import (
    BufferedFallbackRequired, ChunkStreamingUnsupported,
    CollieAPIError, CollieConnectionError, CollieError,
)

started = False

def factory():
    return customer_llm(prompt)          # zero-arg: returns an async iterable

try:
    async for ev in collie.streaming.protect_stream(
        input=prompt, raw_stream_factory=factory
    ):
        if ev.type == "delta":
            started = True
            await write(ev.text)
        elif ev.type == "input_blocked":
            await write(ev.block_message or "Request rejected."); return
        elif ev.type == "blocked":
            await write(ev.block_message or "Response rejected."); return

# Fail-open ONLY on infrastructure failure AND only before the first delta.
except CollieConnectionError:
    if not (FAIL_OPEN_ALLOWED and not started):
        raise
    async for delta in customer_llm(prompt):     # your own LLM, unfiltered
        await write(delta)
except CollieAPIError as e:
    if not (FAIL_OPEN_ALLOWED and not started
            and e.status_code is not None and e.status_code >= 500):
        raise
    async for delta in customer_llm(prompt):
        await write(delta)

# Policy demands buffered checking -- an instruction, not an outage. The
# `started` guard avoids re-emitting an answer the user has already partly seen.
# NOTE: protect_buffered re-invokes your LLM — a second, billable generation.
except (BufferedFallbackRequired, ChunkStreamingUnsupported):
    if started:
        await write("Could not verify the response. Please try again.")
    else:
        r = await collie.streaming.protect_buffered(
            input=prompt, raw_stream_factory=factory
        )
        await write((r.block_message or "Response rejected.") if r.blocked
                    else (r.filtered_text or ""))

# Everything else, including a mid-stream abort.
except CollieError:
    await write("Could not verify the response. Please try again.")
```

`asyncio.CancelledError` does not inherit `CollieError`, so a client disconnect
never triggers fail-open.

If you need fail-open **mid-stream** too, you must tee the provider stream: wrap
your LLM iterable so deltas also accumulate in a local buffer, then on failure
emit `buffer[already_written_chars:]` and continue raw. Without the tee the text
the engine was still holding is lost and the answer has a hole in the middle.

Whatever you choose, make fail-open **observable**: log every occurrence and put
it behind a flag you can turn off. A silent `except` means an outage can leave
you serving unchecked model output for hours with everything looking healthy.

## Advanced: low-level session

If you need to drive batching yourself, use the session directly. It does
**not** check the input — call `moderate.input(...)` first.

```python
check = await collie.moderate.input(prompt=user_prompt)
if check.blocked:
    return check.block_message or "Input blocked by policy."

async with collie.streaming.session(input=user_prompt) as session:
    async for raw_delta in your_llm_stream():
        result = await session.push(raw_delta)
        for emit in result.emits:
            yield emit.text          # forward ONLY safe emits
        if result.finished:
            break
    await session.finish()
```

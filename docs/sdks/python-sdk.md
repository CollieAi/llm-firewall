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
| `BufferedFallbackRequired` | `require_streaming=True` but the policy must buffer | switch to `protect_buffered` |
| `ProjectNotFound` / `StreamingFeatureDisabled` / `PlanNotEntitled` / `UnknownRuleType` / `PolicyNotStreamable` *(`PreflightError`)* | preflight says the policy can't be served | fix project/policy configuration |
| `ProviderStreamFactoryRequired` | passed a started stream (or non-async-iterable) instead of a factory | pass a zero-arg callable: `lambda: my_stream()` |
| `ConcurrentSessionUseError` | overlapping `push()` calls on one low-level session | serialize submits per session |
| `ModerationError` | `moderate.input` job failed/expired or timed out | retry the input check |
| `CollieConnectionError` | transport failure (timeout, connection refused) | retry; check connectivity to `base_url` |
| `CollieAPIError` | unexpected HTTP error or malformed response (`code="invalid_response"`) | inspect `status_code`/`code`; retry or report |

## Retry behavior

The SDK retries the **same** chunk sequence on transient failures (network
timeouts, `503`, `504 chunk_filter_timeout`, `429` with a usable `Retry-After`)
with exponential backoff + jitter — default base 250 ms, max 4 s, 3 attempts per
chunk, 10 s ceiling (`AsyncCollie(retry_max_per_chunk_s=...)`). A retried chunk
never produces a duplicate visible delta.

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

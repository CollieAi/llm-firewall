---
icon: microsoft
---

# .NET SDK

The `CollieAi.Client` .NET 8 SDK is the recommended way to do customer-owned
streaming from a .NET backend. You run your own model; the SDK checks the
prompt before you call it and lets you stream back **only CollieAi-released
text** — never raw model output. It owns the chunk protocol (sequence numbers,
retries, idempotency, finalization), so you don't touch the
[raw chunk endpoints](../async-jobs/customer-owned-streaming.md). It mirrors
the [Python](python-sdk.md) and [Node](node-sdk.md) SDKs — same event model,
same typed errors.

{% hint style="warning" %}
**Forward `SafeDelta.Text`, never the raw provider delta.** The whole point of
the SDK is that your users only ever see text CollieAi has released. The
examples below keep the raw provider stream inside the `RawStreamFactory`; you
only forward SDK events.
{% endhint %}

## Install

```bash
dotnet add package CollieAi.Client
```

## Construct the client

### ASP.NET Core (dependency injection)

```csharp
builder.Services.AddCollieAi(options =>
{
    options.ApiKey = builder.Configuration["CollieAi:ApiKey"]!;
    options.BaseUrl = new Uri("https://app.collieai.io");
    options.ProjectId = "project_123";
});

// then inject ICollieClient anywhere
public sealed class ChatService(ICollieClient collie) { /* ... */ }
```

{% hint style="info" %}
`AddCollieAi` registers a named `HttpClient` (`"CollieAi.Client"`) through
`IHttpClientFactory` — attach your own logging/tracing handlers to that named
client if you need them, but **do not** add retry, circuit-breaker, or timeout
handlers: they conflict with the SDK's own retry + idempotency semantics on the
chunk endpoints.
{% endhint %}

### Console / worker (direct)

```csharp
await using var collie = new CollieClient(new CollieClientOptions
{
    ApiKey = Environment.GetEnvironmentVariable("COLLIEAI_API_KEY")!,
    BaseUrl = new Uri("https://app.collieai.io"),
    ProjectId = "project_123",
});
```

`CollieClient` is `IAsyncDisposable` — dispose with `await using` so the owned
HTTP resources are released.

## Check an input before calling your LLM

```csharp
var input = await collie.Moderation.CheckInputAsync(new InputModerationRequest
{
    Prompt = userPrompt,
    ConversationId = conversationId,   // optional: groups a conversation
    CorrelationId = chatTurnId,        // optional: pins one turn
});

if (input.Blocked)
    return input.BlockMessage ?? "Input blocked by policy.";

// If your input policy MASKS, send the FILTERED prompt to your model —
// null-check, never string emptiness: "" is a legitimate full wipe.
var promptForModel = input.FilteredText ?? userPrompt;
```

A policy block is a normal result (`Blocked = true`), not an exception.
No webhook is required — the SDK polls for you. `FilteredText` is the
post-mask prompt: the raw values a mask rule removed must never reach your
model, so `promptForModel` — not `userPrompt` — goes into your LLM call.
When the wrapper's own gate masks a prompt, `ProtectStreamAsync` /
`ProtectBufferedAsync` throw `MaskedInputException` before your factory
runs; the recipe is to gate manually as above, build the factory over
`result.FilteredText`, and pass `InputResult = result` (keep
`CheckInput` at its default `true` — combining `InputResult` with
`CheckInput = false` is a contradiction and throws
`ArgumentException`; in 2.0 it was silently ignored).

## Analyze context alongside the prompt

Set `Context` to analyze the data you're about to send the model — retrieved
documents, tool output, a record — alongside the prompt. It travels as JSON with
your keys preserved; `ContextFormat` (`"auto"` / `"json"` / `"text"`) is an
optional hint for a raw string.

```csharp
var input = await collie.Moderation.CheckInputAsync(new InputModerationRequest
{
    Prompt = userPrompt,
    Context = new Dictionary<string, object>
    {
        ["transaction"] = new Dictionary<string, object> { ["memo"] = retrievedMemo },
    },
});

if (input.Context is { Status: not "clean" and not "not_provided" } ctx)
    Console.WriteLine($"{ctx.Status} {ctx.TriggeringPointer} {ctx.TriggeringRuleType}"); // path, never a value

if (input.Blocked)
    return input.BlockMessage ?? "Blocked by policy.";   // input.BlockedBy: "prompt" | "context" | "none"
```

`input.Context` carries the closed `Status` string, the triggering JSON Pointer +
rule, and degraded markers; the pointer is a **path, never a value**. `Context`
works the same on `ProtectStreamAsync` / `ProtectBufferedAsync` when input checking
is enabled. See [Context analysis](../security-rules/context-analysis.md).

{% hint style="info" %}
Until context analysis is enabled (host flag **and** policy switch), `Context` is
inert — a safe no-op.
{% endhint %}

## Check an output produced outside a wrapper

`ProtectStreamAsync` / `ProtectBufferedAsync` already moderate the streamed
answer. Use `CheckOutputAsync` for assistant text that never went through a
wrapper — proactive notifications, escalation messages, any side channel. Don't
route such text through `CheckInputAsync`: that evaluates it with **input**
rules, so output-safety and masking rules silently never run, and injection
detectors can false-block assistant-style imperatives ("You need to submit…").

```csharp
var result = await collie.Moderation.CheckOutputAsync(new OutputModerationRequest
{
    Response = assistantText,
    ConversationId = conversationId, // optional
    CorrelationId = notificationId,  // optional
});

if (result.Blocked) return;               // don't send it
Send(result.FilteredText ?? assistantText); // masking applies here
```

`FilteredText` carries the **masked** output — send it, not the original, or
masking rules silently do nothing. `OutputModerationRequest` has no `Context`:
context is an input surface; for context-aware output filtering use
`ProtectBufferedAsync` / `ProtectStreamAsync`.

Both moderation requests accept an optional `TimeoutS` — a wall-clock budget
in seconds for polling the verdict (it starts after the job-create POST,
which `CollieClientOptions.Timeout` bounds separately). On expiry you get the
same `ModerationException` as any died-without-verdict outcome.

## Stream safely (ASP.NET minimal API)

`ProtectStreamAsync` checks the input, calls your LLM **only if it passes**,
batches the output, and yields only safe events. The `RawStreamFactory` runs
**exactly once**, after the check — chunk retries never re-invoke it. It
receives a `CancellationToken` that the SDK cancels on teardown; forward it to
your provider so paid generation stops promptly.

```csharp
using System.Runtime.CompilerServices;

app.MapPost("/chat", async (ChatRequest body, ICollieClient collie,
                            HttpResponse response, CancellationToken ct) =>
{
    response.ContentType = "text/plain";

    await foreach (var ev in collie.Streaming.ProtectStreamAsync(new ProtectStreamRequest
    {
        Input = body.Prompt,
        RawStreamFactory = token => MyLlmDeltas(body.Prompt, token),
    }, ct))
    {
        switch (ev)
        {
            case SafeDelta d:
                await response.WriteAsync(d.Text, ct);
                break;
            case InputBlocked ib:
                await response.WriteAsync(ib.BlockMessage ?? "Input blocked by policy.", ct);
                return;
            case Blocked b:
                await response.WriteAsync(b.BlockMessage ?? "Blocked by policy.", ct);
                return;
        }
    }
});

// Your provider stream, wrapped as IAsyncEnumerable<string> text deltas.
// Honor the token: the SDK cancels it on block/early exit.
static async IAsyncEnumerable<string> MyLlmDeltas(
    string prompt, [EnumeratorCancellation] CancellationToken ct)
{
    await foreach (var update in myLlm.StreamTextAsync(prompt, ct))
        if (!string.IsNullOrEmpty(update.Text))
            yield return update.Text;
}
```

That's the whole integration. You never touch chunk sequence numbers, retries,
or batching.

{% hint style="info" %}
**No packaged provider adapters (yet).** Unlike the Python and Node SDKs, the
.NET SDK ships without OpenAI/Anthropic adapter helpers — you wrap your
provider's streaming API as an `IAsyncEnumerable<string>` yourself, as above.
This keeps your provider configuration and API-key management fully in your
hands; adapters may be added based on demand.
{% endhint %}

## Choose the UX up front (preflight)

By default `ProtectStreamAsync` streams optimistically; a policy that can't
stream surfaces as `ChunkStreamingUnsupportedException` on the first push. To
decide the UX **before** generation, set `RequireStreaming = true` (preflights
and throws `BufferedFallbackRequiredException` when the policy buffers), or
branch yourself:

```csharp
var cap = await collie.Streaming.PreflightAsync(new StreamingPreflightRequest());

if (cap.RecommendedClientBehavior == RecommendedClientBehavior.Stream)
{
    // ProtectStreamAsync → token-stream UI
}
else if (cap.RecommendedClientBehavior == RecommendedClientBehavior.BufferThenShow)
{
    var result = await collie.Streaming.ProtectBufferedAsync(new ProtectBufferedRequest
    {
        Input = userPrompt,
        RawStreamFactory = token => MyLlmDeltas(userPrompt, token),
    });
    // "checking response…", then show result
}
else
{
    throw new InvalidOperationException(cap.ReasonDetail ?? cap.Reason); // fail_fast
}
```

### Which rule is responsible — `cap.Rules`

`cap.Rules` explains the verdict rule by rule. Each entry carries
`ExecutionRole`, the role that rule plays in a streaming request:

| `ExecutionRole` | meaning |
| --- | --- |
| `enforce_streaming` | blocks or masks **as tokens arrive** |
| `enforce_postflight` | blocks or masks, but needs the **whole** response first — a policy containing one always buffers |
| `stream_observed` | monitor-only; observed **as tokens arrive** while the text streams through untouched |
| `postflight_observed` | monitor-only; observed after the response completes |
| `null` | the rule could not be planned at all (e.g. an unrecognised type) |

```csharp
var blockers = cap.Rules
    .Where(r => r.ExecutionRole == "enforce_postflight")
    .Select(r => r.RuleName)
    .ToList();

if (blockers.Count > 0)
    Console.WriteLine($"buffered because: {string.Join(", ", blockers)}");
```

{% hint style="info" %}
`StreamingSupported` is `false` for **every** monitor rule, so it cannot tell a
`stream_observed` rule from a `postflight_observed` one. Use `ExecutionRole`
when you need that distinction — typically while running a policy in monitor
mode before turning on blocking.
{% endhint %}

Three things `ExecutionRole` does not tell you. It is **per-rule** and ignores
policy-level gates, so a rule can say `stream_observed` while the request still
buffers — `cap.Mode` remains the answer to "does this request stream at all".
It reflects your project's current streaming setting, so a project set to
`buffered` reports full-context roles throughout. And it reflects the **server
that answered**: on current servers a monitor-only policy streams — monitor
rules observe the text as it passes and their findings appear in your CollieAi
audit log only, never in the chunk responses your users see. A server that has
not been upgraded yet still buffers any policy containing a monitor rule and
answers `cap.Mode = "buffered"`, `cap.Reason = "monitor_mode"`; the SDK
handles both, and `cap.Mode` is always the delivery verdict. The roles are
what let you see, ahead of time, whether monitor→enforce will be a config flip
or a re-integration.

It is a `string` rather than an enum on purpose: compare against the names you
know and fall through on anything else, so a role added later doesn't break
your branch.


## Buffered fallback

Same input gate and factory contract, but the whole response is checked at
once and you get a single result instead of events:

```csharp
var result = await collie.Streaming.ProtectBufferedAsync(new ProtectBufferedRequest
{
    Input = userPrompt,
    RawStreamFactory = token => MyLlmDeltas(userPrompt, token),
});
return result.Blocked ? result.BlockMessage : result.FilteredText;
```

One difference from `ProtectStreamAsync` matters if you reuse an input
result: on the streaming path a passed `InputResult` carrying a `JobId`
becomes, against a 2.1+ server, a **server-verified, expiring, single-use
claim** (the `input_gate_*` 409s can surface; without a `JobId` or on an
older server the session runs claimless and re-filters the input in its
own async pass — the pre-2.1 shape: billed, and the verdict can land
after streaming has started); on the
buffered path it is a **trusted-client reuse** — the server
neither verifies nor consumes it, and no `input_gate_*` error can occur.
Because nothing server-side checks freshness there, obtain the result in the
same turn, from the same client and project, immediately before the call —
never cache or reuse it.

## Relay safe output to a browser (SSE)

A session can **subscribe** to its job's CollieAi SSE stream and relay safe
events — with automatic reconnect. `StreamEventsAsync()` yields the same typed
events as `ProtectStreamAsync`, plus `StreamInterrupted` on idle-timeout /
disconnect (the SDK auto-resumes from the last event id and deduplicates
replayed frames, so a delta is never shown twice).

```csharp
await foreach (var ev in session.StreamEventsAsync(cancellationToken: ct))
{
    if (ev is StreamInterrupted) continue;     // reconnecting; nothing to forward
    await WriteSseAsync(response, ev, ct);     // your event → SSE frame mapping
    if (ev is Blocked or Finished) break;
}
```

### Let a browser subscribe directly (stream tokens)

Mint a short-lived, job-scoped **stream token** and hand it to the browser —
your API key stays server-side. The token authorizes read-only SSE access to
one job's stream and expires quickly; re-mint before it lapses.

```csharp
var token = await session.MintStreamTokenAsync();
return Results.Ok(new { url = token.Url, expiresIn = token.ExpiresIn });
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
**The token is a credential in the URL.** Treat the full `?stream_token=...`
URL as secret: serve it over HTTPS, don't log it, and redact `stream_token` at
your proxy/access-log layer. A direct browser `EventSource` to CollieAi is
**cross-origin** — your site's origin must be in the API's CORS allowlist, or
use the backend relay above instead.
{% endhint %}

## Errors

Catch typed exceptions instead of parsing strings. All inherit from
`CollieException`. Policy blocks are **events** (`Blocked` / `InputBlocked`),
not exceptions.

| Exception | When | What to do |
|---|---|---|
| `ChunkRetryExhaustedException` | transient failures exceeded the retry budget | retry the turn, or fall back to a non-streaming path |
| `ChunkPolicyChangedException` | policy changed mid-stream | start a new stream/session (it picks up the new policy) |
| `ChunkSessionUnrecoverableException` | the stream entered an unrepairable state | start a new stream/session |
| `ChunkQuotaExceededException` | rate-limited with no usable `Retry-After` | back off and retry later |
| `ChunkStreamingUnsupportedException` | the policy can't be served by the streaming engine | use `ProtectBufferedAsync` instead |
| `ChunkResolutionUnavailableException` | `503 chunk_resolution_unavailable` — the server couldn't **resolve** the policy (a dependency outage, not a policy shape) | nothing at first: the SDK retries it automatically; if the outage outlasts the retry budget it is the `InnerException` of `ChunkRetryExhaustedException` |
| `BufferedFallbackRequiredException` | `RequireStreaming = true` but the policy must buffer | switch to `ProtectBufferedAsync` |
| `ProjectNotFoundException` / `StreamingFeatureDisabledException` / `PlanNotEntitledException` / `UnknownRuleTypeException` / `PolicyNotStreamableException` (`PreflightException`) | preflight says the policy can't be served | fix project/policy configuration; other reason codes (e.g. `rule_unplannable`, `resolution_error:<cause>`) surface as the base `PreflightException` — treat the code as an open string |
| `ProviderStreamFactoryRequiredException` | the factory returned null / an unusable stream | return a fresh `IAsyncEnumerable<string>` from the factory |
| `ConcurrentSessionUseException` | overlapping `PushAsync` calls on one session | serialize submits per session |
| `ModerationException` | a `CheckInputAsync` / `CheckOutputAsync` job failed/expired or timed out | retry the check |
| `MaskedInputException` | the wrapper's own input gate MASKED the prompt — streaming would send the unmasked original to your model | gate manually with `CheckInputAsync`, build the factory over `result.FilteredText` (`""` is a legitimate full wipe), pass `InputResult = result` |
| `CollieConnectionException` | transport failure (timeout, connection refused) | retry; check connectivity to `BaseUrl` |
| `CollieApiException` | unexpected HTTP error or malformed response (`Code == "invalid_response"`) | inspect `StatusCode`/`Code`; retry or report |

## Retry behavior

The SDK retries the **same** chunk sequence on transient failures (network
timeouts, `503` — including the typed `chunk_resolution_unavailable` —
`504 chunk_filter_timeout`, `429` with a usable `Retry-After`)
with exponential backoff + jitter — default base 250 ms, max 4 s, 3 attempts
per chunk, 10 s ceiling (configurable on `CollieClientOptions`). A retried
chunk never produces a duplicate visible delta.

## Failure policy: fail-closed by default

When retries are exhausted the SDK **fails closed** — it raises and releases no
text. There is no fail-open switch: shipping unchecked model output is a risk
decision only you can make, so it has to be your explicit code, not a default.

Two things decide what that code should do.

**1. Where you caught it.** `RawStreamFactory` is a deferred factory: the SDK
calls it exactly once, *after* the input check passes and the session exists. So
if CollieAi is unreachable, the failure lands before your LLM ever ran — nothing
was generated, nothing reached the user, and passing through is a clean choice.
A failure *mid-stream* is different: some text is already on screen and the
engine is holding more, so re-running the model would duplicate output. Track it
with one flag.

**2. Not every `CollieException` is an outage.** `ChunkStreamingUnsupportedException`
means the policy demands buffered checking, and `ChunkRetryExhaustedException`
means a mid-stream abort. Catching the base type and passing through would
bypass a policy that deliberately asked to inspect the whole answer. Catch the
transport failures — `CollieConnectionException` and `CollieApiException` with a
5xx — and nothing else.

```csharp
bool started = false;
try {
    await foreach (var ev in collie.Streaming.ProtectStreamAsync(req, ct)) {
        switch (ev) {
            case SafeDelta d:     started = true; await Write(d.Text); break;
            case InputBlocked ib: await Write(ib.BlockMessage ?? "Request rejected."); return;
            case Blocked b:       await Write(b.BlockMessage ?? "Response rejected."); return;
        }
    }
}
// Fail-open ONLY on infrastructure failure AND only before the first delta.
catch (CollieConnectionException) when (FailOpenAllowed && !started) {
    await PassThrough();                        // your own LLM, unfiltered
}
catch (CollieApiException e) when (FailOpenAllowed && !started && e.StatusCode >= 500) {
    await PassThrough();
}
// Policy demands buffered checking -- an instruction, not an outage. !started
// guards against re-emitting an answer the user has already partly seen.
catch (BufferedFallbackRequiredException)  when (!started) { await BufferedPath(); }
catch (ChunkStreamingUnsupportedException) when (!started) { await BufferedPath(); }
// Everything else, including a mid-stream abort.
catch (CollieException) {
    await Write("Could not verify the response. Please try again.");
}

// The full answer is checked before anything reaches the user.
// NOTE: this re-invokes your LLM — the first stream was already started and
// partially consumed, so this is a second, billable generation.
async Task BufferedPath() {
    var r = await collie.Streaming.ProtectBufferedAsync(new ProtectBufferedRequest {
        Input = msg,
        RawStreamFactory = token => CustomerLlm.StreamAsync(msg, token),
    }, ct);
    await Write(r.Blocked ? (r.BlockMessage ?? "Response rejected.") : r.FilteredText ?? "");
}
```

`OperationCanceledException` does not inherit `CollieException`, so a client
disconnect never triggers fail-open.

If you need fail-open **mid-stream** too, you must tee the provider stream: wrap
your LLM enumerable so deltas also accumulate in a local buffer, then on failure
emit `buffer[alreadyWrittenChars..]` and continue raw. Without the tee the text
the engine was still holding is lost and the answer has a hole in the middle.

Whatever you choose, make fail-open **observable**: log every occurrence and put
it behind a flag you can turn off. A silent catch means an outage can leave you
serving unchecked model output for hours with everything looking healthy.

## Advanced: low-level session

If you need to drive batching yourself, use the session directly. It does
**not** check the input — call `CheckInputAsync(...)` first.

```csharp
var check = await collie.Moderation.CheckInputAsync(new InputModerationRequest { Prompt = userPrompt });
if (check.Blocked)
    return check.BlockMessage ?? "Input blocked by policy.";

// The split that matters when your input policy masks:
// - the SESSION gets the ORIGINAL prompt (it must byte-match the gate);
// - your MODEL gets the FILTERED prompt ("" is a legitimate full wipe).
var promptForModel = check.FilteredText ?? userPrompt;

// InputJobId: proves the prompt was just gated, so the server skips
// re-filtering it on the session job (one input pass per turn).
await using var session = await collie.Streaming.CreateSessionAsync(
    new StreamingSessionRequest { Input = userPrompt, InputJobId = check.JobId });

await foreach (var rawDelta in YourLlmStream(promptForModel))
{
    var result = await session.PushAsync(rawDelta);
    foreach (var emit in result.Emits)
        Forward(emit.Text);              // forward ONLY safe emits
    if (result.Finished) break;
}
await session.FinishAsync();
```

Manual sessions do not auto-retry the claim protocol: `input_gate_stale`
means the policy changed since your gate ran — re-run `CheckInputAsync`
(with the same context, if any) and open a new session with the fresh job
id; `input_gate_unverifiable` means retry without the gate reference;
`input_gate_claimed` means that gate was already consumed.
`ProtectStreamAsync` handles all of this for you — but ONLY when it runs its own gate: with an external `InputResult` (this very recipe) the typed errors surface to YOUR code by design, since the wrapper cannot re-check a context it never saw.

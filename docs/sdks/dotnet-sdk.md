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
```

A policy block is a normal result (`Blocked = true`), not an exception.
No webhook is required — the SDK polls for you.

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
| `BufferedFallbackRequiredException` | `RequireStreaming = true` but the policy must buffer | switch to `ProtectBufferedAsync` |
| `ProjectNotFoundException` / `StreamingFeatureDisabledException` / `PlanNotEntitledException` / `UnknownRuleTypeException` / `PolicyNotStreamableException` (`PreflightException`) | preflight says the policy can't be served | fix project/policy configuration |
| `ProviderStreamFactoryRequiredException` | the factory returned null / an unusable stream | return a fresh `IAsyncEnumerable<string>` from the factory |
| `ConcurrentSessionUseException` | overlapping `PushAsync` calls on one session | serialize submits per session |
| `ModerationException` | `CheckInputAsync` job failed/expired or timed out | retry the input check |
| `CollieConnectionException` | transport failure (timeout, connection refused) | retry; check connectivity to `BaseUrl` |
| `CollieApiException` | unexpected HTTP error or malformed response (`Code == "invalid_response"`) | inspect `StatusCode`/`Code`; retry or report |

## Retry behavior

The SDK retries the **same** chunk sequence on transient failures (network
timeouts, `503`, `504 chunk_filter_timeout`, `429` with a usable `Retry-After`)
with exponential backoff + jitter — default base 250 ms, max 4 s, 3 attempts
per chunk, 10 s ceiling (configurable on `CollieClientOptions`). A retried
chunk never produces a duplicate visible delta.

## Advanced: low-level session

If you need to drive batching yourself, use the session directly. It does
**not** check the input — call `CheckInputAsync(...)` first.

```csharp
var check = await collie.Moderation.CheckInputAsync(new InputModerationRequest { Prompt = userPrompt });
if (check.Blocked)
    return check.BlockMessage ?? "Input blocked by policy.";

await using var session = await collie.Streaming.CreateSessionAsync(
    new StreamingSessionRequest { Input = userPrompt });

await foreach (var rawDelta in YourLlmStream(userPrompt))
{
    var result = await session.PushAsync(rawDelta);
    foreach (var emit in result.Emits)
        Forward(emit.Text);              // forward ONLY safe emits
    if (result.Finished) break;
}
await session.FinishAsync();
```

---
description: >-
  Analyze the data you send to the model alongside the prompt — retrieved
  documents, tool output, records — so an injection hidden in that data is caught,
  not just one in the user's prompt.
icon: layer-group
---

# Context analysis

## What is context analysis in CollieAi?

Most checks look at the user's **prompt**. But modern apps feed the model far more
than the prompt: retrieved documents (RAG), tool/function output, prior messages,
a database record being summarized. That **context** is often attacker-influenced
— a poisoned document can carry "ignore previous instructions…" that the user
never typed.

**Context analysis** adds a **second input surface**: the structured data (or raw
text) you're about to send the model is analyzed *alongside* the prompt, reusing
your policy's enabled **input detection rules**. A threat hidden in the context is
detected and blocked just like one in the prompt.

{% hint style="warning" %}
**Where it applies.** Context analysis runs on the **input check** of the
SDK / async-jobs path — `moderate.input`, the `protect_stream` / `protect_buffered`
wrappers, and `POST /v1/jobs`. It is **not supported on the proxy routes**
(`/v1/chat/completions`, `/v1/messages`) — don't send `context` there; use the
SDK / async-job input-check surface instead.
{% endhint %}

{% hint style="info" %}
**Key points**

* Context is a **second input surface**, analyzed with your policy's enabled
  input detectors — not a new rule type.
* Structured context (an object/array) is analyzed **per field**, so a block
  tells you the exact **JSON Pointer** of the offending field (a path like
  `/transaction/memo`, never the value).
* The result distinguishes a **prompt** block from a **context** block
  (`blocked_by`), and reports a closed **status** (`clean` / `monitored` /
  `blocked` / `degraded` / …).
* Enable it **per policy**; it's a single switch with sensible defaults.
{% endhint %}

## Enabling it

Open your policy and turn on the **Context Analysis** panel. Four controls:

| Control | What it does |
|---|---|
| **Analyze context** | On / off for this policy. |
| **Format** | How to parse a raw-string context: **Auto** (default), **JSON**, or **Text**. Structured context is always JSON. |
| **Rules** | **Use all compatible input rules** (default), or **Choose specific rules** to narrow which detectors run. Normalization always runs first. |
| **On threat** | **Block** the request, or **Monitor** (audit only — observe before enforcing). |

Only your policy's **enabled, input-direction** detectors that are compatible with
context run — regex, dictionaries, structured IDs, URL filtering, base64, and the
ML/LLM classifiers. Output-only rules and the Streaming Guard don't apply to
context, and `allow` / transformation rules don't act on it. **Normalization**
always runs first (lowercasing, unicode folding); choosing **specific rules**
narrows the *detectors*, not normalization.

A rule set to **mask** behaves differently in context, because you can't redact an
injection out of the data you're about to send the model:

* a **security classifier** (`lightweight_model` / `llm_detection`) mask
  **escalates to a block**;
* any **other** mask rule is **audit-only** — recorded, but it doesn't block.

The panel warns you per rule when a mask would behave this way.

## Sending context from the SDK

Pass `context` to the input check. Structured data travels as JSON; an optional
`context_format` hint applies only to raw strings.

{% tabs %}
{% tab title="Python" %}
```python
result = await collie.moderate.input(
    prompt="summarize the attached document",
    context={"doc": retrieved_document},
)

if result.context and result.context.status == "blocked":
    print(result.context.triggering_pointer)  # e.g. "/doc" — a path, never a value

if result.blocked:
    # result.blocked_by is "prompt" or "context"
    return result.block_message or "Blocked by policy."
```
{% endtab %}

{% tab title="Node" %}
```ts
const result = await collie.moderate.input({
  prompt: "summarize the attached document",
  context: { doc: retrievedDocument },
});

if (result.context?.status === "blocked") console.log(result.context.triggeringPointer);
if (result.blocked) return result.blockMessage ?? "Blocked by policy.";
// result.blockedBy is "prompt" | "context" | "none"
```
{% endtab %}

{% tab title=".NET" %}
```csharp
var input = await collie.Moderation.CheckInputAsync(new InputModerationRequest
{
    Prompt = "summarize the attached document",
    Context = new Dictionary<string, object> { ["doc"] = retrievedDocument },
});

if (input.Context is { Status: "blocked" } ctx)
    Console.WriteLine(ctx.TriggeringPointer);   // path, never a value
if (input.Blocked) return input.BlockMessage ?? "Blocked by policy.";
```
{% endtab %}
{% endtabs %}

The same `context` argument works on the streaming wrappers (`protect_stream` /
`protect_buffered`) when the input check runs.

## Reading the verdict

The input result gains a typed `context` sub-result and a `blocked_by` field:

* **`status`** — the closed enum: `not_provided`, `disabled`, `not_run`, `clean`,
  `monitored`, `blocked`, `degraded`.
* **`blocked_by`** — `prompt`, `context`, or `none`, so you know which surface
  blocked.
* **triggering JSON Pointer** + **rule** — *where* and *which detector* fired.
  The pointer is a **path** (e.g. `/transaction/memo`), never the value at it.
* **degraded markers** — see below.

{% hint style="warning" %}
**`degraded` means coverage was incomplete.** If context was too large, malformed,
or a model detector was briefly unavailable, the verdict is `degraded` — scanning
didn't cover the whole context, so a `clean`/`monitored` result there can't be
fully trusted. Watch the degraded rate (it's a first-class metric in Analytics and
an alertable threshold). `degraded` does **not** block the request.
{% endhint %}

## Observability

* **Logs** — each analyzed request shows its context verdict; filter by status and
  search by the triggering pointer or rule.
* **Analytics** — a **Context** section with the context block-rate and the
  coverage-degraded rate (distinct from the prompt-channel block rate).
* **Alerts** — `context_block_rate` and `context_degraded_rate` are alert metrics;
  set a threshold on the degraded rate so incomplete coverage never erodes silently.

{% hint style="info" %}
**Availability — two gates.** Detection runs only when **both** are on: the
deployment's **host feature flag** (operator-controlled) **and** the policy's
**Context Analysis** switch. With either off, sending `context` is a safe no-op —
the status is `disabled` (or `not_provided`) and behavior is unchanged.
{% endhint %}

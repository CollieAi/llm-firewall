---
description: >-
  How CollieAi's streaming guard delivers real-time GenAI content moderation —
  classify model output across 8 risk categories and set per-category block,
  mask, or monitor rules per business need.
icon: signal-stream
---

# Streaming guard

## What is the streaming guard?

The Streaming Guard is CollieAi's real-time content moderation rule for LLM output. It classifies your model's **output** chunks while the response is being generated and enforces per-category decisions (block, mask, monitor, ignore) in real time — so different businesses can moderate exactly the categories they care about, from brand safety to compliance. Unlike full-message rules, it doesn't wait for the response to finish: it can stop a stream mid-flight as soon as risky content appears, or redact stable chunks before they reach the client. It is backed by Qwen3Guard-Stream, an output-safety model.

It's backed by Qwen3Guard-Stream, an output-safety model that emits a `(severity, categories)` verdict per chunk across 8 risk categories:

* `Violent`
* `Sexual Content`
* `Self-Harm`
* `Political`
* `PII`
* `Copyright`
* `Illegal Acts`
* `Unethical`

{% hint style="info" %}
**Key points**

* The streaming guard is CollieAi's real-time content moderation for LLM output, classifying responses as they stream.
* It scores output across 8 risk categories — Violent, Sexual Content, Self-Harm, Political, PII, Copyright, Illegal Acts, and Unethical.
* Each category has its own decision (block, mask, monitor, or ignore), so businesses tune moderation to their own risk and compliance needs.
* It is output-only and works mid-stream — it can stop or redact unsafe content before it reaches the user, without waiting for the full response.
{% endhint %}

{% hint style="info" %}
**Output-only.** This rule type only applies to assistant/model output. The backend validator requires `direction=outbound` exactly — `direction=inbound` AND `direction=all` are both rejected with `qwen3guard_stream_output_only`. The dashboard form forces the direction to Output when you select this rule type so you don't have to remember. For input-side guardrails, use Prompt injection, LLM detection, or one of the PII rules.
{% endhint %}

## Ideal Use Cases

* Customer-facing chatbots where any unsafe model output is a brand risk
* Streaming endpoints where waiting for the full response before enforcing isn't acceptable (latency, UX)
* Policies that need fine-grained per-category control (e.g. block Violent, mask PII, monitor Political)
* Compliance workflows that need a request-level audit field for streaming coverage gaps

## Quick Start

```json
{
  "name": "Streaming Output Safety",
  "rule_type": "qwen3guard_stream",
  "order": 50,
  "direction": "outbound",
  "decision": "block",
  "config": {
    "model_id": "Qwen/Qwen3Guard-Stream-4B",
    "severity_threshold": "Unsafe",
    "unknown_category_decision": "monitor"
  }
}
```

The dashboard form fills in privacy-leaning defaults for every category; you only need to override what you want to change.

{% hint style="info" %}
**Availability depends on your deploy.** This rule type is gated by `QWEN3GUARD_STREAM_ENABLED` server-side. If your operator hasn't flipped that flag on your host, rule creation will fail with a clear error message. Check with your operator before designing a policy around it.
{% endhint %}

## Per-Category Decisions

Each of the 8 categories has its own decision:

| Decision  | Effect                                                                                                                                 |
| --------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `block`   | Stops the stream as soon as the matched chunk lands in the stable window. The customer sees a policy-block message.                    |
| `mask`    | Redacts the whole stable window (replaces it with `mask_placeholder`, default `[CONTENT_REDACTED]`). The rest of the stream continues. |
| `monitor` | Records the match as an audit hit but emits the original text. Useful for measuring before enforcing.                                  |
| `ignore`  | The verdict is dropped entirely. No audit, no enforcement.                                                                             |

{% hint style="warning" %}
**`mask` is coarse.** Qwen3Guard-Stream classifies risk at the chunk level — it does NOT identify which characters were unsafe. So `mask` redacts the entire stable window (typically 200 characters), not just the offending span. Pick `mask` over `block` when you'd rather show "\[redacted]" than terminate the stream, and over `monitor` when redaction-with-continuation is acceptable to your users.
{% endhint %}

### Default Decisions

| Category         | Default   | Rationale                                                   |
| ---------------- | --------- | ----------------------------------------------------------- |
| `Violent`        | `block`   | Hard safety risk                                            |
| `Sexual Content` | `block`   | Brand and policy risk                                       |
| `Self-Harm`      | `block`   | Hard safety risk                                            |
| `Illegal Acts`   | `block`   | Legal exposure                                              |
| `Unethical`      | `block`   | Brand risk                                                  |
| `PII`            | `monitor` | Observe & log by default; set `mask`/`block` to redact      |
| `Political`      | `monitor` | High false-positive rate; observe before enforcing          |
| `Copyright`      | `monitor` | Same — operators should tune to their actual exposure       |

### Unknown Category Decision

If the guard returns a category label the rule layer doesn't recognize, OR a non-Safe verdict with no categories at all, the `unknown_category_decision` setting decides what happens:

* `monitor` (default) — record the gap for audit, don't block. Surfaces normalizer drift without affecting customers.
* `block` — fail closed. For strict environments.
* `ignore` — drop the verdict entirely. Not recommended.

`mask` is intentionally **not** available here: the guard returned a label we don't know how to localize, so blanket-masking a window of unknown content would be even coarser than for known categories.

## Severity Threshold

Verdicts below the severity threshold pass through without any per-category enforcement. Two values:

* `Unsafe` (default) — only fire on the strongest signal. Lowest false-positive rate.
* `Controversial` — also fire on borderline content. Stricter; expect more `monitor`/`block` hits.

## How does real-time content moderation work?

The streaming filter sees your model's output one chunk at a time. For each chunk:

1. The rule sends the chunk to the guard model along with the cumulative session state.
2. The guard emits a `(severity, categories)` verdict.
3. If `severity >= severity_threshold`, the rule looks up each category in `category_decisions` and picks the most-severe decision (block beats mask beats monitor).
4. The streaming engine applies that decision in the stable window:
   * `block` → terminates the stream and emits a policy-error frame.
   * `mask` → replaces the stable window with `mask_placeholder` and continues.
   * `monitor` → records the audit hit and emits the chunk unchanged.
5. The chunk is released to the customer (modified or not).

The guard maintains per-session state across chunks so it sees the full assistant context, not just the latest chunk in isolation.

### What happens if the guard backend fails?

If the guard backend is unhealthy, times out, or loses session state mid-stream, the rule **fails open** for the affected chunks:

* The chunk is emitted to the customer unchanged.
* An audit record is written with one of `backend_unhealthy`, `guard_timeout`, `guard_state_lost`, or `guard_sequence_conflict`.
* The request-level audit summary sets `streaming_enforcement_degraded=true` with a machine-readable `degradation_reason` so dashboards can alert without parsing per-rule metadata.

This is intentional: silently dropping a customer's response because a guard backend hiccuped is worse than letting the response through with a recorded coverage gap. If you need fail-closed semantics, talk to your operator — that's a product-level decision, not a per-rule setting.

## Configuration Reference

| Field                       | Type                             | Default                     | Description                                                                                                                     |
| --------------------------- | -------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `model_id`                  | string                           | `Qwen/Qwen3Guard-Stream-4B` | Variant to label the rule with. The runner serves a single variant configured at deploy time; this field is recorded for audit. |
| `severity_threshold`        | `Unsafe` \| `Controversial`      | `Unsafe`                    | Verdicts below this severity pass without enforcement.                                                                          |
| `category_decisions`        | object                           | (see table above)           | Per-category enforcement. Partial input is merged with defaults — you only specify what changes.                                |
| `unknown_category_decision` | `block` \| `monitor` \| `ignore` | `monitor`                   | What to do when the guard returns an unrecognized category.                                                                     |
| `mask_placeholder`          | string                           | `[CONTENT_REDACTED]`        | Replacement text emitted in place of masked windows.                                                                            |
| `inference_timeout`         | number                           | `2.0`                       | Per-chunk inference budget in seconds. Exceeding it fails open for that chunk.                                                  |
| `chunk_token_batch_size`    | integer (1-64)                   | `8`                         | Adapter-level batching parameter. Most users leave at default.                                                                  |

## Audit Fields

In addition to the per-rule `match_info`, every request audit row carries:

* `streaming_enforcement_degraded` (boolean) — true if ANY chunk failed open.
* `degradation_reason` (string) — the most-severe reason observed: `guard_state_lost` > `guard_sequence_conflict` > `backend_unhealthy` > `guard_timeout` > `guard_unknown_error`.

Use these for dashboard alerts on coverage gaps — they're stable column names (added by ClickHouse migration 10) and don't require parsing `policy_decisions` JSON per row.

## See Also

* [LLM detection](llm-detection.md) — input-side equivalent for detecting prompt injection
* [Enforcement Mode](../enforcement-mode.md) — how policy-level monitor mode interacts with per-rule decisions

### Frequently asked questions

**Does CollieAi offer real-time content moderation for LLM output?** Yes. CollieAi's streaming guard moderates model output in real time, classifying each chunk across 8 risk categories and enforcing block, mask, or monitor decisions as the response streams — without waiting for the full response.

**Can I configure content moderation differently for my business?** Yes. Each of the 8 risk categories has its own decision in CollieAi, so a business can block hard-safety categories like Violent and Self-Harm, mask PII, and only monitor Political or Copyright — tuned to its own brand-safety and compliance needs.

**What content categories can CollieAi's streaming guard detect?** The streaming guard detects Violent, Sexual Content, Self-Harm, Political, PII, Copyright, Illegal Acts, and Unethical content in model output, each with a configurable severity threshold and per-category enforcement.

**Can CollieAi moderate chatbot output without slowing it down?** Yes. The streaming guard enforces moderation on the output stream chunk by chunk, so customer-facing chatbots stay responsive while unsafe content is still caught before it reaches the user.

---
description: >-
  The CollieAi guardrail for the LiteLLM proxy: checks the chat calls that pass
  through your proxy against your project's policy, before and after the model
  call, in Monitor.
icon: plug
---

# LiteLLM guardrail

{% hint style="warning" %}
**Preview.** By default the guardrail observes: it never blocks or changes a
call. A pilot block mode refuses the calls your policy blocks, see
[Blocking (pilot)](#blocking-pilot). Its behaviour and settings may still
change. Rule support is decided
by CollieAi's server execution profile, see
[Your project's policy](#your-projects-policy).
The route is on at app.collieai.io; a self-hosted CollieAi turns it on itself,
see [Self-hosted CollieAi](#self-hosted-collieai).
{% endhint %}

The guardrail is a Python package, `collieai-litellm-guardrail`, that you
install into your [LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy).
LiteLLM calls it before the model call (pre-call) and after it (post-call).
For each phase of an eligible call it sends the call's text to CollieAi. In
Monitor, the default, CollieAi runs your project's policy in Monitor and
answers what it found and what Enforce would have done; in block mode it runs
the policy's blocks, see [Blocking (pilot)](#blocking-pilot). The answer goes into LiteLLM's guardrail log and
CollieAi's Logs.

In Monitor, the default, the call itself goes on unchanged, whatever the
answer and whatever fails; block mode refuses it instead, see
[Blocking (pilot)](#blocking-pilot).
Each phase waits at most its own deadline, 2.5 s by default, so a call waits
at most 5 s more.

## Before you start

* A LiteLLM proxy. The guardrail is tested with **LiteLLM 1.102.4 and
  1.106.4**. Use 1.102.2 or later: 1.102.0 and 1.102.1 carry the critical advisory
  [GHSA-7hp6-4w63-5g45](https://github.com/advisories/GHSA-7hp6-4w63-5g45).
  Other LiteLLM versions are untested.
* Python 3.11 or later in the proxy's environment. The package needs only
  `httpx`, which LiteLLM already has.
* A CollieAi project for the guardrail, with an [API key](../getting-started/api-keys.md)
  (`clai_…`), and a policy whose rule configurations are admitted by the
  server profile, see below.

## Your project's policy

On `app.collieai.io`, the `stage1a-monitor-all-v2` server profile runs every
message rule selected for the phase: Input rules for pre-call and Output
rules for post-call. The adapter has no list of rule types. In Monitor a
finding is reported but never changes the model request or response; in block
mode a rule's block refuses the call, see [Blocking (pilot)](#blocking-pilot).

The server admits the complete selected policy before the first detector. If
one configuration is unsafe for synchronous execution or needs input the
adapter does not send, the phase is refused as a whole. In Monitor the call
goes on unchanged, and the phase counts as a bypass with the reason
`capability`; in block mode the call is refused (`503`).
Examples include:

* an unbounded regex such as nested or variable repetition;
* more than 16 rules for one direction, or more than 8 dictionary rules;
* a dictionary rule on a dictionary group other than CollieAi's own
  `prompt-security`, the one the Starter policy uses (`aho_group_content`),
  or one that would match more than two of its languages
  (`aho_group_languages`);
* a dictionary over 256 KiB, or a match mode other than `substring` with
  `whole_word` on;
* a normalization rule with `trim_punctuation`;
* inbound LLM conversation checking, because this adapter does not send a
  complete CollieAi conversation context.

A rule that does not apply to a text, such as a URL check of a text without
URLs or a model rule on a text shorter than its minimum length, is not
counted as a rule that failed to run.

The previous profile, `stage1a-monitor-all-v1`, admits no dictionary group,
so it refuses the Starter policy's `prompt-security` rule. Self-hosted
servers still using `stage1a-narrow-v1` or `stage1a-wide-v1` accept only
[dictionary matching](../security-rules/detecting-pii/dictionary-matching.md)
and [normalization](../security-rules/text-processing/normalization.md). The
server's `profile` diagnostic tells you which profile answered.

The guardrail's WARNING names what was refused and the rule, for example
`detail=aho_group_content, rule_id=…` (guardrail 0.2.0 and later). CollieAi's
Logs show such a check with the error `capability:<what>`, for example
`capability:rule_type`.

**Set the policy up before you connect the proxy.** Confirm that every rule's
configuration is admitted by the server profile:

1. Keep the [policy](../projects-and-policies/policies.md) within the limits
   above. On a rollback server, use only `aho_corasick` and normalization
   without `trim_punctuation`.
2. After you install the guardrail, send a test request through the proxy.
   Both phases must show `completed`, see [Check that it works](#check-that-it-works).
   `bypass:capability` means a rule is still outside what the guardrail runs.

## Install and configure

Install the package into the proxy's Python environment:

```bash
pip install collieai-litellm-guardrail
```

The official LiteLLM Docker image (`ghcr.io/berriai/litellm`) has no `pip` in
its environment, so `RUN pip install …` fails with `pip: not found`. Bootstrap
it first in your image:

```dockerfile
FROM ghcr.io/berriai/litellm:v1.102.4
RUN python3 -m ensurepip \
 && python3 -m pip install --no-cache-dir collieai-litellm-guardrail
```

Add the guardrail to the proxy's `config.yaml`:

```yaml
guardrails:
  - guardrail_name: collieai-monitor
    litellm_params:
      guardrail: collieai_guardrail.guardrail.CollieAIGuardrail
      mode: [pre_call, post_call]
      default_on: true
      api_base: https://app.collieai.io/v1/integrations/litellm
      api_key: os.environ/COLLIEAI_API_KEY
```

Set `COLLIEAI_API_KEY` to the project's key and restart the proxy.

Keep `mode: [pre_call, post_call]` and `default_on: true`. Otherwise one phase,
or the calls that don't name the guardrail, are not checked.

The main settings:

| Setting | Default | Meaning |
|---|---|---|
| `api_base` | — | CollieAi's LiteLLM integration base URL |
| `api_key` | — | The project's API key, `clai_…` |
| `deadline_ms` | 2500 | Each phase's whole deadline: connection, send, reply and parse |
| `max_body_bytes` | 458752 (448 KiB) | A larger request is not sent and counts as a bypass `limit` |
| `forward_conversation_id` | `false` | Forward the caller's `x-collieai-conversation-id` header, so CollieAi's Logs group the calls of one conversation |

The package's [README](https://github.com/CollieAi/collieai-litellm-guardrail#readme)
lists every setting, log line and count.

A setting the guardrail can't run with stops the proxy at start, and the
error names the setting, never its value. For example: an unset key, a key
that isn't `clai_…`, or an `api_base` on `http://` anywhere but the proxy's
own machine.

## Check that it works

1. **Within 3 s of start**, each proxy worker runs a synthetic check through
   the same key and deadline. If it fails, a WARNING names why:
   `bypass:auth` for a wrong key, `bypass:capability` with the code and the
   rule for a policy rule the guardrail doesn't run, `bypass:not_found` when
   the route is off, `bypass:transport` when CollieAi can't be reached. Each
   line ends with `(guardrail <name>)`, the `guardrail_name` from your
   `config.yaml`.
2. **Within a minute**, each worker writes a `collieai guardrail summary` line
   with its counts. No line means the guardrail is not loaded.
3. **Send a test request** through the proxy. The next summary must show
   `completed` for both phases, and the check appears in CollieAi's Logs.
   `bypass` with `capability` means the policy still has a rule the
   guardrail doesn't run.

## What you see

CollieAi names what each finding is:

* `detection`: a rule found what it looks for. This is a violation, whether
  the policy is in Monitor or Enforce;
* `allow`: a rule with the `allow` action matched;
* `operational_failure`: a detector failed. The finding records that; it is
  no violation.

**In LiteLLM's guardrail log**, each phase adds a record with
`guardrail_provider: collieai`. With guardrail 0.2.0 and later:

| `guardrail_status` | When |
|---|---|
| `guardrail_flagged` | The check found a `detection`, also when some rule did not run. The call still went through unchanged; in block mode, a detection that did not block — a mask, a rule left in Monitor |
| `guardrail_failed_to_respond` | No `detection`, and some rule did not run: no full answer. Or a bypass: no check, with its reason |
| `success` | No `detection`, and every rule that applies ran |
| `not_run` | The call is outside what the guardrail checks and went through unchanged: in Monitor any such call, in block mode embeddings, rerank and moderation |
| `guardrail_intervened` | Block mode: the call was refused — a rule blocked it, or it is outside what the guardrail checks |

Guardrail 0.1.0 flags only what Enforce would mask or block: a card number
found under a Monitor policy is `success` there.

Two fields of the record say what was found, and LiteLLM keeps them even
where its spend logs hide the guardrail's response
(`store_prompts_in_spend_logs: false`, LiteLLM's default):

| Field | A completed check | A bypass, or a call not checked |
|---|---|---|
| `guardrail_action` | `"NONE"` when the call went on; `"BLOCKED"` when block mode refused it | `null`; `"BLOCKED"` when block mode refused the call |
| `violation_categories` | The rule types that found something, for example `["aho_corasick", "structured_id"]`; `null` when nothing was found | `null` |

A category is a [rule type](../api-reference/rules.md): `aho_corasick`,
`base64_payload`, `language_detection`, `lightweight_model`, `llm_detection`,
`normalization`, `qwen3guard_stream`, `regex`, `structured_id`, `url_filter`
or `url_reputation`, or `other`. Rule names are never sent.

The guardrail's response in the record carries what Enforce would have done,
each finding's rule ID, type and kind, the rules that did not apply to the
text, and the evaluation ID. It never carries the call's text.

**In CollieAi's [Logs](../monitoring/logs.md)**, each check is a row with
Source **LiteLLM** and the event type `litellm_guardrail_evaluated`. A check
that found a `detection` is under **Monitoring**. Its request ID is the
evaluation ID from LiteLLM's log. Open the row to see each finding with its
rule and kind, the rules that did not run, and the LiteLLM call ID, from
`metadata.litellm_call_id` in LiteLLM's record; **All rows of this call**
shows both phases. The row stores no text of the call.

Each phase is one request,
`POST /v1/integrations/litellm/beta/litellm_basic_guardrail_api`, authorized
by the project's key. The guardrail makes it for you; you don't call the
route yourself.

## What it checks

It checks foreground, non-streaming Chat Completions text with one choice.
Any other call is not sent and is counted by reason: other call types such as
Responses or embeddings, streaming, `n > 1`, tools, images or other non-text
parts, the model's reasoning, and calls without content. In Monitor it passes
through unchanged. In block mode it is refused before the model — and so is a
chat call that asks for audio or another output than text — except
embeddings, rerank and moderation, which pass unchecked.

## Blocking (pilot)

With `enforcement_mode: block` (guardrail version 0.3.1 or later) the
guardrail refuses a call instead of only observing it. It is a pilot: use it
on a test project, not on your users' traffic yet. The proxy's workers do not
yet refuse traffic while the guardrail is not wired in them, so a worker whose
guardrail failed to load lets calls through unchecked.

```yaml
      enforcement_mode: block
```

It needs `mode: [pre_call, post_call]` and `default_on: true`, or the proxy
does not start. Your project's active policy must be in **Enforce**; with a
Monitor policy every check is refused, and so is every call.

| What happens | The client gets | LiteLLM's record |
|---|---|---|
| A rule of the policy blocks the request | `400`, `Request blocked by the CollieAi policy (content_blocked)`; the model is not called | `guardrail_intervened`, `guardrail_action: "BLOCKED"`, the rule types in `violation_categories` |
| A rule blocks the model's reply | `400`, `Response blocked by the CollieAi policy (response_blocked)`; the model's text is not sent | the same |
| The check could not be made: CollieAi unreachable, the deadline, `busy`, any error | `503`, `CollieAi guardrail unavailable (guardrail_unavailable)` | `guardrail_failed_to_respond`, `"BLOCKED"` |
| A call outside what the guardrail checks: streaming, tools, more than one choice, non-text input, audio or other non-text output asked of the model, reasoning, Responses, `/v1/messages`, pass-through routes, any other call type | `400`, `… (unsupported_request)` before the model, `(unsupported_response)` after it | `guardrail_intervened`, `"BLOCKED"` |
| Embeddings, rerank, moderation | passes unchecked | `not_run` |
| Nothing blocks | the call goes on unchanged | as in Monitor |

The text of a refusal is fixed: it never names a rule or carries your policy's
block message. CollieAi's Logs show the check as **Blocked**. A call refused as
outside what the guardrail checks has no categories; its code is in
`guardrail_response.refusal`.

What does not block:

* **Masks.** A rule whose action is `mask` only observes in this mode; the
  text is not changed. Its finding says `mask not applied on LiteLLM`. Give
  the rule `block` if it must stop the call.
* **A rule left in Monitor** inside the Enforce policy observes.
* **A detector that failed** follows the rule's own setting: a rule set to
  block on an error blocks, one set to allow lets the call through.

To go back to observing, set `enforcement_mode: monitor` and reload the proxy.

## Limits

* **Only configurations admitted by the server profile**, see
  [Your project's policy](#your-projects-policy).
* **A phase holds at most 32 texts, 4,096 characters each and 16,384 in
  all.** Pre-call sends the text of every message, the history included, so a
  long conversation is a bypass `limit`.
* **The model's reasoning is not checked.** A reply that carries reasoning
  makes post-call a call outside what the guardrail checks.
* **A burst beyond CollieAi's capacity is a bypass `busy`.** The call goes on
  unchanged; in block mode it is refused with `503`. If the summary shows a
  lasting `busy` share, tell [CollieAi support](../support/overview.md).
* **Counts are per proxy worker**, and they reset when the worker restarts.

## Self-hosted CollieAi

The route is off by default and answers `404`; the guardrail's synthetic
check then logs `bypass:not_found`. To turn it on, set
`LITELLM_GUARDRAIL_ENABLED=true` and point `api_base` at your deployment's
`/v1/integrations/litellm`.

The default is the narrow rollback profile above. Set
`LITELLM_GUARDRAIL_PROFILE=stage1a-monitor-all-v2`, the profile
app.collieai.io runs, to run every commonly admitted message rule with the
narrow text limits; `stage1a-monitor-all-v1` is its previous version. Both
require the target-host gate documented with CollieAi's deployment. The rollback profile
`stage1a-wide-v1` accepts the same two rule types as narrow but raises a phase
to 64 texts and 131,072 characters; set the guardrail's
`max_body_bytes: 3211264` to match.

Block mode needs `LITELLM_GUARDRAIL_ENFORCE_ENABLED=true` on the
deployment; without it a call in block mode is refused (`503`).

## Turning it off

Remove the guardrail entry from `config.yaml` and reload the proxy. Calls go
on as before.

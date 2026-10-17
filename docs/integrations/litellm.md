---
description: >-
  The CollieAi guardrail for the LiteLLM proxy: checks the chat calls that pass
  through your proxy against your project's policy, before and after the model
  call, in Monitor.
icon: plug
---

# LiteLLM guardrail

{% hint style="warning" %}
**Preview, Monitor only.** The guardrail observes: it never blocks or changes
a call. Its behaviour and settings may still change. It runs only the
project's dictionary rules, see [Your project's policy](#your-projects-policy).
The route is on at app.collieai.io; a self-hosted CollieAi turns it on itself,
see [Self-hosted CollieAi](#self-hosted-collieai).
{% endhint %}

The guardrail is a Python package, `collieai-litellm-guardrail`, that you
install into your [LiteLLM proxy](https://docs.litellm.ai/docs/simple_proxy).
LiteLLM calls it before the model call (pre-call) and after it (post-call).
For each phase of an eligible call it sends the call's text to CollieAi, which
runs your project's policy in Monitor and answers what Enforce would have
done. The answer goes into LiteLLM's guardrail log and CollieAi's Logs.

The call itself goes on unchanged, whatever the answer and whatever fails.
Each phase waits at most its own deadline, 2.5 s by default, so a call waits
at most 5 s more.

## Before you start

* A LiteLLM proxy. The guardrail is tested with **LiteLLM 1.102.4**. Use
  1.102.2 or later: 1.102.0 and 1.102.1 carry the critical advisory
  [GHSA-7hp6-4w63-5g45](https://github.com/advisories/GHSA-7hp6-4w63-5g45).
  Other LiteLLM versions are untested.
* Python 3.11 or later in the proxy's environment. The package needs only
  `httpx`, which LiteLLM already has.
* A CollieAi project for the guardrail, with an [API key](../getting-started/api-keys.md)
  (`clai_…`), and a policy for it that holds only dictionary rules. A new
  project starts with Starter Monitor, which doesn't qualify, see below.

## Your project's policy

The guardrail runs two of CollieAi's rule types:
[dictionary matching](../security-rules/detecting-pii/dictionary-matching.md)
(`aho_corasick`) and [normalization](../security-rules/text-processing/normalization.md).
Each phase runs the policy's rules for its direction: Input rules for
pre-call, Output rules for post-call. If one of them is outside what the
guardrail runs, the phase is refused as a whole. The call goes on unchanged,
and the phase counts as a bypass with the reason `capability`. That happens
with:

* a rule of any other type: regex, structured IDs, URL rules, LLM detection
  and so on;
* more than 16 rules for one direction, or more than 8 dictionary rules;
* a dictionary rule on a dictionary group, a dictionary over 256 KiB, or a
  match mode other than `substring` with `whole_word` on;
* a normalization rule with `trim_punctuation`.

CollieAi's Logs show such a check with the error `capability:<what>`, for
example `capability:rule_type`.

**Set the policy up before you connect the proxy.** A new project starts with
the [Starter Monitor](../getting-started/quick-start.md) policy, which has
rules of other types, so a new project alone still gives `bypass:capability`:

1. Give the guardrail's project a [policy](../projects-and-policies/policies.md)
   that holds only `aho_corasick` rules and normalization rules without
   `trim_punctuation`, within the limits above. Create one, or delete or
   disable every other Input and Output rule in a policy no other project
   uses.
2. After you install the guardrail, send a test request through the proxy.
   Both phases must show `completed`, see [Check that it works](#check-that-it-works).
   `bypass:capability` means a rule is still outside what the guardrail runs.

## Install and configure

Install the package into the proxy's Python environment, or its image:

```bash
pip install collieai-litellm-guardrail
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
   `bypass:auth` for a wrong key, `bypass:capability` for a policy rule the
   guardrail doesn't run, `bypass:not_found` when the route is off,
   `bypass:transport` when CollieAi can't be reached.
2. **Within a minute**, each worker writes a `collieai guardrail summary` line
   with its counts. No line means the guardrail is not loaded.
3. **Send a test request** through the proxy. The next summary must show
   `completed` for both phases, and the check appears in CollieAi's Logs.
   `bypass` with `capability` means the policy still has a rule the
   guardrail doesn't run.

## What you see

**In LiteLLM's guardrail log**, each phase adds a record with
`guardrail_provider: collieai`:

| `guardrail_status` | When |
|---|---|
| `success` | The check found nothing |
| `guardrail_flagged` | The check found something Enforce would mask or block. The call still went through unchanged |
| `guardrail_failed_to_respond` | Bypass: no check, with its reason |
| `not_run` | The call is outside what the guardrail checks |

A completed check carries what Enforce would have done, the rule IDs and
types, and the evaluation ID. The record never carries the call's text.

**In CollieAi's [Logs](../monitoring/logs.md)**, each check is a row with the
event type `litellm_guardrail_evaluated`. Its request ID is the evaluation ID
from LiteLLM's log. The row stores no text of the call.

Each phase is one request,
`POST /v1/integrations/litellm/beta/litellm_basic_guardrail_api`, authorized
by the project's key. The guardrail makes it for you; you don't call the
route yourself.

## What it checks

It checks foreground, non-streaming Chat Completions text with one choice.
Any other call passes through unchanged, is not sent, and is counted by
reason: other call types such as Responses or embeddings, streaming, `n > 1`,
tools, images or other non-text parts, the model's reasoning, and calls
without content.

## Limits

* **Dictionary rules only**, see [Your project's policy](#your-projects-policy).
* **A phase holds at most 32 texts, 4,096 characters each and 16,384 in
  all.** Pre-call sends the text of every message, the history included, so a
  long conversation is a bypass `limit`.
* **The model's reasoning is not checked.** A reply that carries reasoning
  makes post-call a call outside what the guardrail checks.
* **A burst beyond CollieAi's capacity is a bypass `busy`.** The call goes on
  unchanged. If the summary shows a lasting `busy` share, tell
  [CollieAi support](../support/overview.md).
* **Counts are per proxy worker**, and they reset when the worker restarts.

## Self-hosted CollieAi

The route is off by default and answers `404`; the guardrail's synthetic
check then logs `bypass:not_found`. To turn it on, set
`LITELLM_GUARDRAIL_ENABLED=true` and point `api_base` at your deployment's
`/v1/integrations/litellm`.

The deployment runs the narrow profile above. With
`LITELLM_GUARDRAIL_PROFILE=stage1a-wide-v1` a phase takes 64 texts and 131,072
characters; set the guardrail's `max_body_bytes: 3211264` to match.

## Turning it off

Remove the guardrail entry from `config.yaml` and reload the proxy. Calls go
on as before.

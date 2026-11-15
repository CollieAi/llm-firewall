---
description: >-
  Check n8n workflows against your CollieAi project's policy: the CollieAi node
  checks a user's message and the model's reply in any workflow, or n8n's
  OpenAI credential pointed at CollieAi checks every model call of an AI Agent
  or LLM chain.
icon: plug
---

# n8n

{% hint style="info" %}
**The CollieAi node** is on npm, `@collieai/n8n-nodes-collieai`, for
self-hosted n8n: n8n has not verified it yet, and n8n Cloud installs only
verified community nodes. **The proxy** is available on app.collieai.io. Both
are tested with n8n **2.47.3 and 2.48.0**; the proxy with the OpenAI Chat
Model node, `gpt-4o-mini` and `gpt-5-mini`.
{% endhint %}

There are two ways to check an n8n workflow against your project's policy:

| | [The CollieAi node](#the-collieai-node) | [The proxy](#the-proxy) |
|---|---|---|
| What you add | A node before the model and one after it | No node: n8n's OpenAI credential, pointed at CollieAi |
| What is checked | The text you give the node: a user's message, the model's reply | Every model call of an AI Agent or a Basic LLM Chain: the system message, the user's message, tool results, the reply |
| The model | Any | OpenAI chat models; Claude models without tools or streaming |
| A blocked text | An item with `allowed: false`: branch on it and reply with the policy's message | The AI node fails with an error |
| Agents with tools | Any agent | Depends on the project's Output rules, see [Agents with tools](#agents-with-tools) |

Use one of the two in a workflow. With both, the same policy checks each turn
twice, and a block by the proxy is an error of the AI Agent node, which stops
the workflow unless the agent's **On Error** handles it.

## Before you start

* A CollieAi project and its [API key](../getting-started/api-keys.md)
  (`clai_…`). Sign up at [app.collieai.io](https://app.collieai.io): the
  first visit to **Get Started** sets up a project with the Starter policy
  and a key, see [Quick start](../getting-started/quick-start.md). The
  Starter policy starts in Monitor, where rules only log: nothing is blocked
  or masked until you switch the policy to Enforce on the **Policies** page.
* If your account has an [IP allowlist](../getting-started/ip-allowlist.md),
  add n8n's outgoing addresses to it.

[Get Started](https://app.collieai.io/app/get-started?option=n8n) has an n8n
panel. It asks where your n8n runs and shows the steps with your project's
key and base URL: for self-hosted n8n the node and a workflow to paste, for
n8n Cloud the proxy.

## The CollieAi node

### Install

In n8n: **Settings → Community Nodes → Install**, package
`@collieai/n8n-nodes-collieai`. See n8n's
[guide](https://docs.n8n.io/integrations/community-nodes/installation/).

### Credential

Create a **CollieAi API** credential:

| Field | Value |
|---|---|
| API Key | Your project's key, `clai_…` |
| Base URL | `https://app.collieai.io`. Change it only for a dedicated CollieAi host |

The key is sent over `https://` only, `http://` only on `localhost`, and only
to the Base URL's host: saving the credential with any other Base URL fails
before the key leaves n8n. Saving it checks the key against your project.

### Check Input and Check Output

| Operation | Checks | Against |
|---|---|---|
| **Check Input** | A user's message, before the model | The project's Input rules |
| **Check Output** | The model's reply, before the user | The project's Output rules |

| Parameter | |
|---|---|
| Text | The text to check. An empty text is an error |
| Conversation ID | Optional. Groups the turns of one conversation in CollieAi [Logs](../monitoring/logs.md), for example the Chat Trigger's `sessionId` |
| Options → Timeout | Seconds to wait for the verdict once the check is created. Default 30 |
| Options → Include Match Details | Adds each rule's match details. Off by default: for pattern rules they hold the matched text, which n8n keeps in its execution history |

Each check is one call against your plan's monthly quota, see
[Plans and billing](../getting-started/plans-and-billing.md): checking a turn
with both operations costs two.

### Output

Every input item comes out once, with its own fields and a `collieai`
object:

```json
{
  "collieai": {
    "allowed": true,
    "blocked": false,
    "text": "Call me at [PHONE]",
    "blockMessage": null,
    "triggeredRules": [
      { "ruleId": "…", "ruleName": "PII", "ruleType": "pii", "decision": "mask", "monitoring": false }
    ],
    "jobId": "…",
    "requestId": null
  }
}
```

| Field | |
|---|---|
| `allowed` | `true` only when the policy lets the text through |
| `blocked` | `true` when it does not, or when the answer was ambiguous |
| `text` | The text to pass on: masked when a rule masked it, else the original. `null` when blocked |
| `blockMessage` | The rule's message for the user, when one blocked |
| `triggeredRules` | The rules that matched. A rule in Monitor has `monitoring: true` and does not block |
| `jobId` | The check's ID in CollieAi Logs; give it to CollieAi support |
| `requestId` | `null`: CollieAi does not return a request ID for checks yet |

Pass `collieai.text` on, not the original text: it is the one the policy
masked.

### Branching

Add an **IF** node after the CollieAi node and branch on
`{{ $json.collieai.allowed }}` being `true` (boolean). Do not branch on
`collieai.blocked`: an item without the `collieai` object must never count as
allowed.

A typical chat workflow:

```
Chat Trigger → CollieAi (Check Input) → IF allowed → AI Agent → CollieAi (Check Output) → IF allowed → reply
                                         └ else → reply with collieai.blockMessage       └ else → reply with collieai.blockMessage
```

### Errors

A check that cannot be made never comes out as allowed. What happens is the
node's **On Error** setting:

| On Error | What you get |
|---|---|
| Stop Workflow (default) | The workflow stops with the error |
| Continue | The item comes out blocked: `allowed: false`, `blocked: true`, and `collieai.error` with a `code` and a `message` |
| Continue (using error output) | The item goes to the error output; n8n replaces its fields with the error message |

The error's description says what to do next and ends with its identifiers:
the node's code, CollieAi's code and the check's job ID when there are any.
It never carries your API key or the checked text.

**Turn Retry On Fail off for this node.** n8n's Retry On Fail re-runs every
item of the node, so each retry would create new, billed checks. The node
refuses to run with it on. It does not repeat a check itself either: a check
that got no answer may still have been made.

A `429` when the node creates a check is an error: your project's rate limit
(off by default) or its monthly quota. While the node waits for the verdict,
a `429` is waited out.

### Limits of the node

* The node sees only the text you give it. The system prompt, memory and
  tool results inside an AI Agent are not checked by it.
* The reply is checked once the model has finished it; there is no streaming
  check.
* Items are checked one after another within an execution. Parallel
  executions run their checks at the same time; your project's rate limit,
  if set, applies to them together.

## The proxy

n8n's AI nodes, such as the AI Agent and the Basic LLM Chain, call their model
through a chat model node. Give that node an OpenAI credential whose Base URL
is CollieAi, and every model call goes through the
[CollieAi proxy](../proxy-integration/overview.md): your project's Input rules
check the prompt before the model sees it, and its Output rules check the
reply before n8n gets it. A blocked call fails in n8n with CollieAi's message;
a masked value never reaches the model.

### What the proxy needs

* An OpenAI [provider token](../projects-and-policies/provider-tokens.md) in
  your account, marked as default: CollieAi calls OpenAI with it. With no
  provider token at all, n8n's credential test fails.
* For an AI Agent with tools, a policy that allows tools: see
  [Agents with tools](#agents-with-tools). The Starter policy does not.

### Set up

1. In n8n, create an **OpenAI** credential:
   * **API Key**: your CollieAi key, `clai_…`;
   * **Organization ID**: leave it empty;
   * **Base URL**: `https://app.collieai.io/v1`.

   When you save it, n8n tests it with `GET /v1/models`.
2. Add an **OpenAI Chat Model** node to your AI Agent or Basic LLM Chain and
   select this credential.
3. Turn off **Use Responses API** in the chat model node. It is on by default,
   and CollieAi serves Chat Completions, not the Responses API: with it on,
   every call fails with `404`.
4. Pick the model, see [Models](#models).

### Models

* OpenAI chat models pass through as they are. We test with `gpt-4o-mini`
  and `gpt-5-mini`, n8n's default. For `gpt-5` and `o`-series models, n8n
  sends the system message with the `developer` role; CollieAi checks it as a
  system message. `gpt-5-mini` accepts only the default temperature, so
  leave **Sampling Temperature** unset for it.
* **Claude models** (with an Anthropic provider token) work through the same
  credential for calls without tools and without streaming. Tool calls and
  streamed answers are refused. If a model is not in n8n's list, enter it by
  ID. The newest Claude models refuse a temperature, so leave
  **Sampling Temperature** unset.

### What CollieAi checks

| Content | Checked by | Notes |
|---|---|---|
| The system message | Input rules | Always. |
| The user's message | Input rules | The latest one. |
| Earlier messages of the conversation | Input rules | Only when the project's **Filter all messages** is on (`filter_all_messages`). An agent with memory sends the whole conversation on every call: turn it on for agents. |
| Tool results | Input rules | A tool result that a block rule matches stops the agent on its next model call. |
| The model's reply | Output rules | |
| The tool-call arguments the model writes | Output rules | When the agent does not stream. |

A mask rule replaces the value before the model sees it. A card number in a
prompt reaches the model as `************1111`.

### Agents with tools

When the model may call tools, CollieAi cannot rewrite the arguments of a
tool call. So whether an agent with tools runs depends on your project's
Output rules and on whether the agent streams:

| The project's Output rules | The agent does not stream | The agent streams |
|---|---|---|
| None | Runs | Runs |
| Only rules that block | Runs, the tool-call arguments checked | Refused, `422` |
| A rule that masks | Refused, `422` | Refused, `422` |

The refusal is `422 tool_calls_unsupported_with_outbound_filtering`, see
[Chat Completions](../api-reference/chat-completions.md#tool-calls-and-filtering).
It counts a rule that masks whether the policy is in Monitor or Enforce.

**The Starter policy refuses every agent with tools**, Starter Monitor
included: its **PII (Structured IDs)** rule masks card numbers, IBANs and BICs
in both directions. To run an agent with tools, open that rule in the policy
and set its direction to **Input**. They are then masked in prompts, not in
replies.

**Streaming.** The agent streams when its trigger answers by streaming: the
Chat Trigger or Webhook with **Response Mode** set to **Streaming**. The Chat
Trigger streams by default when **Make Available in n8n Chat Hub** is on. With
**When Last Node Finishes**, the agent does not stream, whatever its own
**Enable Streaming** option says. So for an agent with tools on a project with
Output rules, set the trigger's Response Mode to **When Last Node Finishes**.

### Blocks and errors

A call your policy blocks fails the AI Agent or chain with n8n's "Bad request -
please check your parameters" and CollieAi's message "Message blocked by
security policy" (`400 policy_violation`).

To let the workflow go on, set the agent's or chain's **On Error** to
**Continue (using error output)**: the blocked call's item goes to the error
output. The item holds only n8n's message, `{"error": "Bad request - please
check your parameters"}`, not CollieAi's, so it does not tell a block from
another `400`. CollieAi's **Logs** show which rule blocked the call.

In a streamed answer, n8n shows only the error's class, for example
"UnprocessableEntityError" for a `422`. For the tool-call refusal, CollieAi's
Logs show the request and its reason. The proxy's errors are listed in
[Error handling](../proxy-integration/error-handling.md).

### Limits of the proxy

* CollieAi sees what the agent sends to the model and what the model answers.
  It does not see the tools run in n8n or their effects, only the tool results
  the agent sends back to the model.

## Execution data

n8n can keep a workflow's data in its execution history, depending on your
n8n's execution settings, the original text included. A mask, by the node or
by the proxy, does not remove the original text from there.

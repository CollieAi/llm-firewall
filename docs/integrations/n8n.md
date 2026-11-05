---
description: >-
  Route n8n's AI Agent and LLM chains through CollieAi: point n8n's OpenAI
  credential at CollieAi, and every model call is checked against your
  project's policy, with no extra node.
icon: plug
---

# n8n

{% hint style="info" %}
Available on app.collieai.io. Tested with n8n **2.46.6 and 3.1.0**, the
OpenAI Chat Model node, `gpt-4o-mini` and `gpt-5-mini`.
{% endhint %}

n8n's AI nodes, such as the AI Agent and the Basic LLM Chain, call their model
through a chat model node. Give that node an OpenAI credential whose Base URL
is CollieAi, and every model call goes through the
[CollieAi proxy](../proxy-integration/overview.md): your project's Input rules
check the prompt before the model sees it, and its Output rules check the
reply before n8n gets it. A blocked call fails in n8n with CollieAi's message;
a masked value never reaches the model.

## Before you start

* A CollieAi project and its [API key](../getting-started/api-keys.md)
  (`clai_…`).
* An OpenAI [provider token](../projects-and-policies/provider-tokens.md) in
  your account, marked as default: CollieAi calls OpenAI with it. With no
  provider token at all, n8n's credential test fails.
* For an AI Agent with tools, a policy that allows tools: see
  [Agents with tools](#agents-with-tools). The Starter policy does not.

## Set up

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

## Models

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

## What CollieAi checks

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

## Agents with tools

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

## Blocks and errors

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

## Limits

* n8n can keep the original prompt in its execution data, depending on your
  n8n's execution settings; a mask changes what the model sees, not what n8n
  stores.
* CollieAi sees what the agent sends to the model and what the model answers.
  It does not see the tools run in n8n or their effects, only the tool results
  the agent sends back to the model.

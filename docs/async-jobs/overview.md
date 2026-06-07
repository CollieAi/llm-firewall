---
description: >-
  How CollieAi Async Jobs work — asynchronous LLM message filtering with webhook
  delivery that lets you bring your own model for batch, multi-model, and
  agentic pipelines.
icon: arrows-repeat
---

# Async Jobs overview

CollieAi Async Jobs provide fully asynchronous message filtering with webhook delivery. Unlike the [drop-in proxy](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/proxy-integration), which sits between your application and your LLM provider, the Jobs API lets you **bring your own model** and just filter messages through CollieAi.

CollieAi does **not** call LLMs on your behalf in this mode. You send content to be filtered, receive the filtered result via webhook, call your own LLM, and optionally send the LLM response back for output filtering.

{% hint style="info" %}
**Key points**

* Async Jobs filter LLM messages asynchronously and deliver results to your webhook.
* You bring your own model — CollieAi filters content but does not call the LLM for you.
* Three filtering modes: Legacy (`message`), Separate (`message_input`/`message_output`), and Combined.
* Best for custom LLM pipelines, multi-model and agentic setups, and batch processing.
{% endhint %}

## What filtering modes do Async Jobs support?

Async Jobs support three modes depending on which fields you include in the request body.

| Mode         | Fields                                  | Use Case                                   |
| ------------ | --------------------------------------- | ------------------------------------------ |
| **Legacy**   | `message`                               | Input filtering only (backward compatible) |
| **Separate** | `message_input` and/or `message_output` | Filter input or output independently       |
| **Combined** | `message_input` + `message_output`      | Filter both directions in a single request |

**Legacy mode** exists for backward compatibility. For new integrations, use `message_input` and `message_output` for better ML accuracy -- CollieAi applies different rule sets to input (user) and output (AI) content.

***

## How do Async Jobs work?

### Two-Hook Pattern (Separate Input + Output)

This is the most common pattern when you need to filter both user input and LLM output.

```
Your App                        CollieAi                        Your LLM
   |                               |                               |
   |  1. POST /v1/jobs             |                               |
   |     message_input + webhook   |                               |
   |  ---------------------------> |                               |
   |                               |                               |
   |  <-- 202 Accepted             |                               |
   |     job_id + webhook_secret   |                               |
   |                               |                               |
   |  2. Webhook: inbound_complete |                               |
   |  <--------------------------- |                               |
   |     (filtered user content)   |                               |
   |                               |                               |
   |  3. Call LLM with filtered content                            |
   |  ----------------------------------------------------------> |
   |                                                               |
   |  <-- LLM response                                            |
   |  <---------------------------------------------------------- |
   |                               |                               |
   |  4. POST /v1/jobs/{id}/response                               |
   |     llm_response              |                               |
   |  ---------------------------> |                               |
   |                               |                               |
   |  5. Webhook: outbound_complete|                               |
   |  <--------------------------- |                               |
   |     (filtered LLM response)   |                               |
   |                               |                               |
```

### Combined Mode (Single Request)

When you already have both the user message and the AI response (for example, logging or post-processing), you can filter both in a single request.

```
Your App                        CollieAi
   |                               |
   |  POST /v1/jobs                |
   |  message_input + message_output + webhook
   |  ---------------------------> |
   |                               |
   |  <-- 202 Accepted             |
   |                               |
   |  Webhook: inbound_complete    |
   |  <--------------------------- |
   |                               |
   |  Webhook: outbound_complete   |
   |  <--------------------------- |
   |                               |
```

Webhooks are always delivered in order: input first, then output.

***

## When should you use Async Jobs vs the drop-in proxy?

|                        | Async Jobs                                                 | Drop-in Proxy                               |
| ---------------------- | ---------------------------------------------------------- | ------------------------------------------- |
| **LLM provider**       | Any (you call it)                                          | OpenAI-compatible and Anthropic-native APIs |
| **Integration effort** | Webhook handler required                                   | Change one base URL                         |
| **Flexibility**        | Full control over LLM calls                                | Transparent proxying                        |
| **Latency**            | Async (webhook-based)                                      | Synchronous                                 |
| **Best for**           | Custom LLM pipelines, multi-model setups, batch processing | Quick OpenAI or Anthropic integration       |

Choose **Async Jobs** when you need full control over your LLM calls, use non-OpenAI models, or want to decouple filtering from your request flow.

Choose the **Drop-in Proxy** when you use OpenAI or Anthropic and want the simplest possible integration.

***

## Next Steps

* [Creating Jobs](creating-jobs.md) -- submit content for filtering
* [Webhooks](webhooks.md) -- receive and verify filtered results
* [Job Lifecycle](job-lifecycle.md) -- understand job statuses and best practices

### Frequently asked questions

**What are CollieAi Async Jobs?** CollieAi Async Jobs are an asynchronous API that filters LLM messages and delivers the filtered result to your webhook, so you can secure content while calling any model yourself.

**Can I use CollieAi with my own or a custom LLM?** Yes. With Async Jobs you bring your own model — CollieAi filters the input and output content through your security rules, and you call the LLM (OpenAI, Anthropic, open-source, self-hosted, or multi-model) yourself.

**When should I use Async Jobs instead of the drop-in proxy?** Use Async Jobs when you need full control over your LLM calls, run multi-model or agentic pipelines, or process content in bulk. Use the drop-in proxy for the simplest real-time integration when CollieAi calls the provider for you.

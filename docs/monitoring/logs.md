---
description: >-
  How CollieAi logs work — a searchable, per-project history of every API call
  with event type, latency breakdown, tokens, triggered rules, and block status,
  stored in ClickHouse.
icon: laptop-binary
---

# Logs

Every request that passes through CollieAi is recorded as a log entry with detailed metadata. Logs give you a complete, searchable history of all API activity for a project.

{% hint style="info" %}
**Key points**

* CollieAi records every request through the proxy as a searchable log entry with detailed metadata.
* Each entry includes event type, direction, latency breakdown, model, tokens, triggered rules, and block status.
* Logs are classified by event type for chat and job flows (e.g. `chat.inbound_blocked`, `job.outbound_filtered`).
* You can browse logs in the dashboard or query them via the Logs API, and they're stored in ClickHouse for fast search.
{% endhint %}

## Event types

Each log entry is classified by event type, which tells you exactly what happened:

### Chat events

| Event type              | Description                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `chat.completion`       | A chat completion request was processed successfully.                                 |
| `chat.inbound_blocked`  | The incoming request was blocked by an input rule before reaching the upstream model. |
| `chat.outbound_blocked` | The model response was blocked by an output rule before being returned to the caller. |
| `chat.error`            | The request resulted in an error (upstream failure, timeout, etc.).                   |

### Job events

| Event type               | Description                                       |
| ------------------------ | ------------------------------------------------- |
| `job.created`            | A new asynchronous job was created.               |
| `job.response_submitted` | The job completed and its response was submitted. |
| `job.inbound_filtered`   | The job's input was filtered by an input rule.    |
| `job.outbound_filtered`  | The job's output was filtered by an output rule.  |
| `job.error`              | The job encountered an error during processing.   |

## What does each log entry contain?

Every log entry includes the following fields:

* **Event type** - One of the event types listed above.
* **Direction** - **Input** or **Output**, indicating which stage of the request the event occurred at.
* **Timestamp** - When the event was recorded.
* **Duration** - Total request or event duration in milliseconds.
* **Input filter latency** - When input filtering ran, the time spent evaluating input rules before the prompt reached the model.
* **LLM latency** - For drop-in proxy requests that reached an upstream model, the time spent waiting for the provider response. Input-blocked requests and async filtering events do not have this value.
* **Output filter latency** - When output filtering ran, the time spent evaluating output rules.
* **Queue wait** - For async-job filtering events, the time spent waiting in the worker queue before filtering started.
* **Model** - The model that was called (e.g. `gpt-4o`, `claude-3-opus`).
* **Tokens used** - Input and output token counts.
* **Triggered rules** - Which rules fired during processing.
* **Blocked status** - Whether the request or response was blocked.

## Using the Logs page

The Logs page in the CollieAi dashboard provides an interactive view of your project's event history.

{% stepper %}
{% step %}
### Select a project

Select a project using the project selector at the top of the page.
{% endstep %}

{% step %}
### Filter by event type

Filter by event type using the dropdown filter to narrow results to specific event types (e.g. show only `chat.inbound_blocked` events).
{% endstep %}

{% step %}
### Browse entries

Browse entries in the log table. Each row shows the event type as a color-coded badge, direction, timestamp, model, and other key fields.
{% endstep %}

{% step %}
### Open a detail view

Click any entry to open a detail view containing:

* The full request and response payloads.
* Timing details, including total duration and any available LLM, output-filter, or queue-wait latency.
* All rules that were triggered.
* The `request_id` (for chat events) or `job_id` (for job events), useful for correlating with your own systems.
* The **conversation** id (when your client sent one), with a **View conversation** action to see the whole conversation in one thread.
{% endstep %}
{% endstepper %}

## Session grouping (conversations)

If your client sends a `conversation_id` when it creates a job — the SDK's `conversation_id` argument, or the `conversation_id` field on `POST /v1/jobs` — CollieAi stores it on every log entry for that request, so you can view a whole conversation as a single thread:

{% stepper %}
{% step %}
### Open a log entry

Open any entry and find its **Conversation** id in the detail view, then click **View conversation**.
{% endstep %}

{% step %}
### Read the thread

The list narrows to that conversation's turns, ordered **oldest-first** so it reads top-to-bottom like a transcript. The view is reflected in the page URL, so you can bookmark or share a link straight to a conversation.
{% endstep %}

{% step %}
### Return to all logs

Click **Clear** on the conversation banner to go back to the full list.
{% endstep %}
{% endstepper %}

{% hint style="info" %}
`conversation_id` is captured for **async jobs and SDK streaming**. Synchronous drop-in proxy requests (`/v1/chat/completions`, `/v1/messages`) don't carry it today.
{% endhint %}

## Logs API

You can also query logs programmatically:

```http
GET /logs/api?event_type=chat.completion
```

Use the `event_type` query parameter to filter results. Other filters include `conversation_id` — all turns of one conversation, e.g. `GET /logs/api?conversation_id=<id>`. This returns the same data shown in the dashboard, in JSON format.

## Retention and storage

Logs are stored in ClickHouse, which is optimized for fast querying over large volumes of time-series data. This means searches and filters remain responsive even as your log volume grows.

{% hint style="info" %}
**Body retention vs. metadata retention.** Request and response **bodies** are kept only for your project's `body_retention_hours` (default 48h) and then blanked, while log **metadata** (timing, model, which rules fired, blocked/allowed) is retained for `log_retention_days` (default 90). Set body retention to 0 to never persist prompt/response bodies. See [Data retention](../projects-and-policies/data-retention.md).
{% endhint %}

### Frequently asked questions

**What does CollieAi log for each request?** CollieAi logs the event type, direction, timestamp, latency breakdown (input filter, LLM, output filter, queue wait), model, tokens used, which rules fired, and whether the request was blocked.

**Can I query CollieAi logs programmatically?** Yes. The Logs API returns the same data as the dashboard in JSON, and you can filter by event type — for example `GET /logs/api?event_type=chat.completion`.

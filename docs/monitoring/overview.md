---
description: >-
  How CollieAi monitoring works — built-in observability for every LLM API call,
  with logs, analytics, and threshold-based alerts, automatically scoped per
  project.
icon: computer
---

# Monitoring overview

CollieAi provides built-in observability for every API call that passes through your proxy. Every request is automatically logged with detailed metadata, giving you full visibility into traffic, rule enforcement, and performance.

Monitoring is organized around three pillars:

* [**Logs**](logs.md) - Raw event history. Every request and its outcome is recorded as an individual log entry, including the event type, model used, timing breakdown, tokens consumed, which rules fired, and whether the request was blocked.
* [**Analytics**](analytics.md) - Aggregated KPIs and charts. See total request volume, blocked rate, error rate, P95 latency, latency-stage breakdowns, and rule trigger counts over configurable time ranges.
* [**Alerts**](alerts.md) - Threshold-based rules. Define conditions like "flag when the error rate exceeds 5% over 15 minutes"; matching events are surfaced in the dashboard (with an unread count).

{% hint style="info" %}
**Key points**

* CollieAi provides built-in observability for every API call through the proxy — no extra setup.
* Monitoring has three pillars: logs (raw event history), analytics (aggregated KPIs), and alerts (threshold-based events surfaced in the dashboard).
* Every request is logged with metadata: event type, model, timing, tokens, which rules fired, and block status.
* All monitoring data is scoped per project, so each project's logs, analytics, and alerts are independent.
{% endhint %}

## Per-project isolation

All monitoring data is scoped to a project. Use the project selector at the top of any monitoring page to switch between projects. Each project's logs, analytics, and alerts are completely independent.

## How is monitoring data collected?

CollieAi automatically logs every API call that flows through the proxy. There is no additional configuration required -- once you start routing traffic through CollieAi, monitoring data begins appearing immediately.

### Frequently asked questions

**Does CollieAi provide observability and audit logging?** Yes. CollieAi automatically logs every API call through the proxy with full metadata — event type, model, timing, tokens, which rules fired, and whether the request was blocked — and surfaces it through logs, analytics, and alerts.

**Do I need to configure monitoring in CollieAi?** No. Monitoring is built in and requires no extra configuration — once traffic routes through CollieAi, logs, analytics, and alerts begin populating immediately, scoped to each project.

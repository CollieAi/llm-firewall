---
description: >-
  How CollieAi analytics work — aggregated KPIs and charts for request volume,
  blocked rate, error rate, P95 latency, and rule triggers, with a latency
  breakdown by stage, scoped per project.
icon: subtitles
---

# Analytics

The Analytics page provides aggregated metrics and charts that summarize your project's traffic patterns, rule effectiveness, and performance over time.

{% hint style="info" %}
**Key points**

* The Analytics page aggregates per-project KPIs over a configurable time range.
* Headline metrics: total requests, blocked rate, error rate, P95 latency, and rule trigger count.
* A latency breakdown separates input-filter, LLM, output-filter, proxy-roundtrip, and queue-wait stages.
* Use it to track rule effectiveness, spot spikes in blocked requests, and isolate performance issues.
{% endhint %}

## Key metrics

The following KPIs are displayed at the top of the Analytics page:

| Metric                 | Description                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------- |
| **Total requests**     | The total number of API calls processed in the selected time range.                                |
| **Blocked rate**       | The percentage of requests that were blocked by input or output rules.                             |
| **Error rate**         | The percentage of requests that resulted in an error.                                              |
| **P95 latency**        | The 95th percentile total response time, meaning 95% of requests completed faster than this value. |
| **Rule trigger count** | The total number of times any rule was triggered across all requests.                              |

## Using the Analytics page

1. **Select a project** using the project selector at the top of the page (same pattern as the Logs page).
2. **Choose a time range** to control the period of data shown in all metrics and charts.
3. **Choose a traffic scope** when you want to separate drop-in proxy calls from async filtering events.
4. **Review the KPI cards** for a high-level summary.
5. **Examine the charts** to see how each metric trends over time within the selected range.

## Latency breakdown

The Latency chart can be switched between several stages:

| Stage               | Meaning                                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------------------- |
| **Combined**        | Total latency across matching events. Useful as the headline view.                                            |
| **Input filter**    | Time spent evaluating input rules before a prompt reaches the model.                                          |
| **LLM latency**     | Time spent waiting for the upstream LLM provider to return a response. This excludes CollieAi filtering time. |
| **Output filter**   | Time spent evaluating output rules against the model response.                                                |
| **Proxy roundtrip** | Successful drop-in request roundtrip through CollieAi, including provider time and filtering overhead.        |
| **Queue wait**      | Async-job worker queue wait before filtering starts. This appears only for async traffic.                     |

Some stages are hidden when no matching samples exist in the selected scope and time range. For example, async jobs do not have CollieAi-owned LLM latency because your application calls the LLM and submits content for filtering.

## What to look for

Analytics helps you answer common operational questions:

* **Monitor traffic patterns** — See how request volume changes throughout the day or week. Identify peak usage periods.
* **Track rule effectiveness** — Check the blocked rate and rule trigger count to understand how often your rules are firing and whether they are catching the traffic you expect.
* **Identify spikes in blocked requests** — A sudden increase in the blocked rate may indicate a new pattern of misuse, or it may mean a rule is too aggressive and needs tuning.
* **Spot performance issues** — Watch P95 latency for degradation, then use the Latency chart stage selector to distinguish upstream model slowdowns from CollieAi filter time, proxy overhead, or async queue wait.

### Frequently asked questions

**What metrics does CollieAi analytics show?** CollieAi analytics shows total requests, blocked rate, error rate, P95 latency, and rule trigger count over a selected time range, plus a latency breakdown by stage (input filter, LLM, output filter, proxy roundtrip, and async queue wait).

**Can I tell whether latency comes from the model or from CollieAi?** Yes. The latency chart's stage selector separates upstream LLM time from CollieAi's input/output filtering and proxy overhead, so you can pinpoint where slowdowns originate.

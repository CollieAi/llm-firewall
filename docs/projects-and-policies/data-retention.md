---
description: >-
  How CollieAi data retention works — set per-project body and log retention to
  balance confidentiality with the audit trail needed for GDPR, PCI, and
  compliance.
icon: input-numeric
---

# Data retention

Each project controls how long its log data lives in CollieAI. Two settings, two distinct lifecycles:

| Setting                | Default | Purpose                                                                                                          |
| ---------------------- | ------- | ---------------------------------------------------------------------------------------------------------------- |
| `body_retention_hours` | **48**  | How long `request_body` and `response_body` are kept before being nulled.                                        |
| `log_retention_days`   | **90**  | How long the rest of the log row (metadata, rule firings, tokens, status) is kept before being deleted entirely. |

The split is intentional: bodies are **evidence** for active investigation (false positives, prompt-injection attempts, debugging); metadata is the **audit trail**. They have very different sensitivity profiles, so they get different lifecycles.

{% hint style="info" %}
**Key points**

* Each CollieAi project sets its own data retention, with two independent lifecycles.
* `body_retention_hours` (default 48) controls how long request and response bodies are kept; `log_retention_days` (default 90) controls the metadata audit trail.
* Short body retention protects confidentiality while long metadata retention supports compliance — set `body_retention_hours = 0` to never persist bodies.
* The invariant `body_retention_hours ≤ log_retention_days × 24` is enforced, and changes apply to new logs only.
{% endhint %}

## Why does CollieAi split body and log retention?

Storing every body for 90 days is the worst case for confidentiality — bodies can contain the very secrets a security rule was hired to redact. Conversely, deleting metadata after 48 hours destroys the audit trail you need for compliance.

Keeping bodies short and metadata long lets you investigate something within hours of it happening (false-positive triage, support tickets) while keeping a clean audit trail of _what fired and when_ for as long as your compliance regime requires.

## The invariant

```
body_retention_hours ≤ log_retention_days × 24
```

Bodies cannot outlive the log row that holds them. The API returns `422 retention_invariant_violated` if you try to violate this — including for partial updates that would push you over (e.g., reducing `log_retention_days` below the row hours of `body_retention_hours`).

## Special values

* **`body_retention_hours = 0`** — bodies are never persisted. The next ClickHouse merge nulls them within seconds. Useful for high-sensitivity tenants where any pre-redaction storage is unacceptable.
* **`log_retention_days = 365`** — the maximum. Beyond this, customers should be exporting to cold storage rather than relying on the proxy.

## Behavior on change

**Retention changes apply to new logs only.** Existing rows keep the `body_retention_at` and `log_retention_at` they were written with. This avoids a costly mutation across the whole `request_logs` table on every settings change. If you need to _retroactively_ shorten retention on existing rows, contact support — that's a one-shot manual operation, not a setting.

## How it interacts with the dashboard

* **Body search** in the logs UI matches against `request_body` / `response_body`. Once a row's bodies have been nulled, it stops appearing in body searches — but its metadata, rule firings, event ID, job ID, and request ID remain searchable for the full `log_retention_days` window.
* **Body expiry hint**: every log detail shows when the body expires (`Body expires: in 36h` / `expired`). When a body has already been nulled, you'll see "expired" instead of the JSON.
* **Project-scoped**: each project has its own retention. Changing one project's retention doesn't affect any other.

## Choosing values

Some starting points by use case:

| Use case                   | `body_retention_hours` | `log_retention_days` | Notes                                                    |
| -------------------------- | ---------------------- | -------------------- | -------------------------------------------------------- |
| **PCI / strict regulated** | 0 or 24                | 365                  | Bodies briefly retained or never; long audit trail.      |
| **GDPR-conscious SaaS**    | 24                     | 90                   | Tight body window aligns with data-minimization.         |
| **Active rule tuning**     | 168 (7d)               | 90                   | Longer body window for FP investigation while iterating. |
| **Default (general use)**  | 48                     | 90                   | Balanced; enough body window for most FP triage.         |

## Configuring retention

### Via the dashboard

Project settings → **Data retention** section. Inline validation prevents invariant violations.

### Via the API

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"body_retention_hours": 24, "log_retention_days": 30}'
```

Response includes the updated values in the `ProjectResponse` shape.

## Migration note (existing deployments)

If you're upgrading an existing CollieAI deployment, the `04-retention-ttl.sql` migration adds the per-row retention columns to ClickHouse and switches the table TTL from `date + 90 DAY` to `log_retention_at`.

The migration includes a one-time `UPDATE` that pushes `body_retention_at` out by **30 days from now** for any pre-existing row that still has body content. This grace window lets operators decide which projects need longer body retention before the column TTL claims the data. After 30 days, bodies on legacy rows are nulled at the next merge.

To extend the grace window (or shorten it) before applying the migration, edit step 2b in `clickhouse/init/04-retention-ttl.sql`. Once applied, you can re-run a similar `UPDATE` against the project rows you want to preserve.

## Related

* [Projects](projects.md) — project settings overview
* [Logs](../monitoring/logs.md) — how the logs UI uses retention info
* [Projects API](../api-reference/projects.md) — full schema reference

### Frequently asked questions

**Can I control how long CollieAi stores my data?** Yes. Each project sets `body_retention_hours` for request and response bodies and `log_retention_days` for metadata, so you can keep bodies briefly for confidentiality while retaining the audit trail as long as compliance requires.

**Can CollieAi avoid storing request bodies for sensitive workloads?** Yes. Set `body_retention_hours = 0` and bodies are never persisted — the next storage merge nulls them within seconds, which suits high-sensitivity or strictly regulated tenants.

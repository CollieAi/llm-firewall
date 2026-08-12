---
description: >-
  How to export CollieAi logs programmatically — authenticating against the
  Logs API, applying filters (event type, status, direction, date range,
  full-text search), and paginating a stable export to NDJSON or CSV.
icon: file-export
---

# Exporting logs via the API

The dashboard's Logs page is backed by an HTTP API you can call directly to export filtered logs — for archiving, offline analysis, or feeding your SIEM.

{% hint style="info" %}
**Key points**

* Exports use your **dashboard account** (email + password), not a `clai_*` API key — the Logs API is scoped to the projects your account owns.
* Filters compose: values within one dimension are OR'd, different dimensions are AND'd, and any dimension can be flipped to *exclude* mode.
* Pagination freezes a **snapshot** against newer rows, and the included script runs a count-drift diagnostic that catches most page-shift incidents loudly. Exporting a closed time window fully in the past reduces the residual risk further — see the pagination note for what is and isn't guaranteed.
* A ready-to-run export script (Python, no dependencies) is included below.
{% endhint %}

## Authentication

Log in once and reuse the session cookie:

```
POST https://app.collieai.io/auth/email/login
Content-Type: application/json

{"email": "you@example.com", "password": "..."}
```

The response sets an `auth_token` cookie. Send it on every subsequent request: `Cookie: auth_token=<value>`. Login is rate-limited (5 attempts per minute per email), so authenticate once per export run, not once per page.

{% hint style="warning" %}
If your account uses Google Sign-In only, set a password first (account settings) — the programmatic login endpoint authenticates by email and password.
{% endhint %}

## The export endpoint

```
GET https://app.collieai.io/logs/api?project_id=<PROJECT_ID>&...
```

Returns JSON: `{"logs": [...], "total": N, "page": 1, "page_size": 50, "snapshot": "<timestamp>", ...}`. Each log row carries the full metadata you see in the dashboard — event type, direction, latency breakdown, tokens, triggered rules, block status, request/response bodies (subject to your retention settings), and more.

### Filters

| Parameter | Meaning |
| --- | --- |
| `date_from` / `date_to` | ISO timestamp (`2026-08-12T00:00:00Z`) or calendar date (`2026-08-12`). Timestamp bounds are half-open on the right (`[from, to)`); calendar dates are inclusive. |
| `status` | Repeatable: `success`, `blocked`, `error`, `monitoring`. |
| `event_type` | Repeatable — any event type from the [Logs](logs.md) page, e.g. `chat.completion`, `job.outbound_filtered`, `chunk_submit`. |
| `direction` | Repeatable: `inbound`, `outbound`. |
| `model` | Repeatable — model names as recorded in the logs. |
| `source` | Repeatable — traffic source classification (e.g. `playground`). |
| `<dimension>_mode=exclude` | Flips that dimension's values to "everything except". Example: `source=playground&source_mode=exclude` exports everything **but** Playground traffic. |
| `search` | Case-insensitive substring search — matches request/response bodies **and** metadata (model, error messages, rule containers, job/request/event IDs). Minimum 2 characters; shorter terms are ignored by the API. |
| `has_rules` | `yes` (only rows with triggered rules) or `no`. Any other value is ignored. The export script accepts `--has-rules true\|false` and maps it to this wire contract. |
| `duration_min` / `duration_max` | Milliseconds. |
| `tokens_min` / `tokens_max` | Total tokens. |
| `conversation_id` | Restrict to one conversation thread. Thread exports are ordered oldest-first and are not snapshot-frozen. |
| `context_status` | Repeatable — context-analysis outcome facet (same exclude-mode support). |
| `collapse_streams` | `true` (dashboard default: finished chunk streams collapse to their terminal row) or `false` (every chunk row). **For archival/SIEM exports use `false`** — the script defaults to it. |

Repeating a parameter builds an OR set within that dimension (`status=blocked&status=error`); different dimensions combine with AND. For the closed-vocabulary facets (`status`, `direction`, `context_status`, `source`) an unknown value returns `422` with the list of allowed values; `model` and `event_type` are open vocabularies — an unknown value simply matches nothing.

### Stable pagination

Page through results with `page` and `page_size`. The first response includes a `snapshot` timestamp — pass it back as `before` on every subsequent page. This freezes the export window against rows arriving with **newer** timestamps.

{% hint style="warning" %}
The freeze is not absolute: asynchronous writes can land with timestamps at or before the snapshot and shift offset-based pages. When run without `--max-rows`, the export script exits non-zero if the exported count differs from the matched total. Treat that as a **drift diagnostic, not a completeness proof** — a shift can duplicate one row and drop another while keeping the count.

Exporting a closed historical window (`date_from`/`date_to` fully in the past, once ingestion for that period has settled) **reduces** the risk, but does not guarantee completeness either: `date_to` bounds the event timestamp, not when the row was actually inserted, so a backdated insert can still land inside a past window during or after your export. A true guarantee would need a server-side snapshot/ingestion watermark; re-running the same window later and comparing counts is the practical cross-check. A failed run never touches an existing output file.
{% endhint %}

## Export script

A self-contained script (Python 3.8+, standard library only) that logs in, applies your filters, paginates with the snapshot freeze, and writes NDJSON or CSV:

{% file src="../.gitbook/assets/collieai_export_logs.py" %}

Examples:

```bash
export COLLIEAI_PASSWORD='...'

# Blocked + errored requests for a date range, as CSV
python3 collieai_export_logs.py \
  --email you@example.com --project-id <PROJECT_ID> \
  --date-from 2026-08-01T00:00:00Z --date-to 2026-08-12T00:00:00Z \
  --status blocked --status error \
  --format csv --out logs.csv

# Everything except Playground traffic that mentions "invoice", as NDJSON
python3 collieai_export_logs.py \
  --email you@example.com --project-id <PROJECT_ID> \
  --source playground --exclude source \
  --search "invoice" --out logs.ndjson
```

The script prints the matched total and the snapshot timestamp to stderr, then streams rows into a temp file that atomically replaces `--out` only on a clean finish — a failed export never truncates an existing archive. (The atomicity applies to file outputs; with `--out -` rows stream straight to stdout and a failed run may have emitted a partial export.) Defaults chosen for archival use: `--collapse-streams false` (every chunk row), output files end up with `0600` permissions, and CSV cells that begin with `=`, `+`, `-`, or `@` are neutralized with a leading quote so spreadsheets don't execute them as formulas (`--raw-csv` disables this).

## Retention

Each row carries `body_retention_at` — after that moment the request/response **bodies** are cleared while the log entry itself (metadata, rules, status) remains. Export before the retention deadline if you need full bodies.

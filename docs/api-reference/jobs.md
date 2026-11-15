---
description: >-
  CollieAi Jobs API — create async filtering jobs, poll status, submit LLM
  responses, and stream filtered chunks for your own model via POST /v1/jobs and
  related endpoints.
icon: briefcase-arrow-right
---

# Jobs

Asynchronous request processing. Create a job to evaluate content against your policy rules. Async Jobs **only filter content** — you call your LLM yourself; CollieAi never forwards to a provider. Results are delivered by webhook or by polling.

***

## POST /v1/jobs

Create a new async job.

**URL:** `https://app.collieai.io/v1/jobs`

**Auth:** Bearer token (API key `clai_xxx`)

### Request Body

| Field                | Type    | Required | Description                                                                                   |
| -------------------- | ------- | -------- | --------------------------------------------------------------------------------------------- |
| `message`            | string  | No       | Shorthand for a single user message. Mutually exclusive with `message_input`/`message_output` |
| `message_input`      | string  | No       | Input message to evaluate against input rules                                                 |
| `message_output`     | string  | No       | Output message to evaluate against output rules                                               |
| `webhook_url`        | string  | No       | Optional. URL to receive the job result via POST. Omit to poll `GET /v1/jobs/{id}` instead.    |
| `metadata`           | object  | No       | Arbitrary key-value pairs attached to the job                                                 |
| `expires_in_seconds` | integer | No       | Job TTL in seconds (60–604800). Default: 3600 (1h)                                            |
| `inbound_only`       | boolean | No       | Only run input rules; complete without awaiting an LLM response. Default: `false`             |
| `input_job_id`       | string  | No       | Single-use claim: the id of a completed **input-only** job that already evaluated exactly this `message_input`. The server verifies the reference and skips re-filtering the input on this job (one input pass per streaming turn). Requires `message_input`; cannot be combined with `message_output` or `inbound_only`. Used automatically by the SDK streaming wrappers. |
| `attachments`        | array   | No       | Preview — on at app.collieai.io. Up to 3 files uploaded via [`POST /v1/files`](files.md), as `[{"file_id": "file_..."}]`, checked in the Input phase. A job may carry attachments and no text. See [Attachments](#attachments-preview). |
| `client_deadline_at` | string  | No       | With `attachments`: the moment (ISO 8601, your clock) after which you will not apply the verdict. |
| `client_now`         | string  | No       | With `client_deadline_at`: your clock when you send the request, so the server can correct the deadline for clock skew. |
| `attachments_budget_s` | number | No      | With `attachments` and no `client_deadline_at`: the time for the files in seconds, counted from when the server receives the request (above 0, at most 90). Default: 10. |

### Input-gate claims (`input_job_id`)

A create carrying `input_job_id` is verified against the referenced job:
same project, byte-identical input text, the referenced job completed,
not blocked, itself never pre-gated. Outcomes:

| Outcome | Meaning |
| --- | --- |
| `202` | Claim honored — the job starts at `awaiting_response` with no input pass of its own. An identical resend of a create that already succeeded also returns `202` with the **existing** job (lost-ACK recovery). |
| `400` `invalid_input_gate` | The reference is wrong: unknown id, different project or text, a blocked or non-input-only job, or a job that was itself pre-gated. |
| `409` `input_gate_stale` | The policy changed since the referenced job ran, or it expired. Run the input check again and retry with the fresh id. |
| `409` `input_gate_unverifiable` | The reference cannot be verified right now. Retry the create **without** `input_job_id` — re-running the input check will not help. |
| `409` `input_gate_claimed` | The referenced job was already claimed by another create. Each input-only job can gate at most one session, ever. |

### Attachments (preview)

{% hint style="info" %}
**Status: preview — on at app.collieai.io.** Other deployments need to enable file analysis;
while it is off there, a create with `attachments` answers `422 file_analysis_unavailable`.
Your policy turns the check on in its [`file_analysis`](files.md#file-analysis-in-a-policy)
settings. In this step file findings are recorded, not blocked: `decision: "block"` takes
effect with the full coverage profile (OCR) in a later step.
{% endhint %}

What this step reads and checks:

* **Read:** a PDF's text layer (not its rendered page) and its metadata — document
  properties, annotations, outline, form values; a CSV file; an XLSX workbook's cells,
  formulas, comments, hyperlinks, names and text boxes, hidden sheets included. Each file is
  read in an isolated sandbox.
* **Not read yet:** images (JPEG, PNG; they need OCR, a later step) and every other type,
  macro-enabled workbooks included. Such a file reports `admission.status: "rejected"` with
  the reason `unsupported_media_type` in [`file_result`](#file-result-preview) and counts as
  incomplete.
* **The text** of a file is checked by the policy's Input rules (the file analysis
  `rule_scope`) and judged by its `llm_detection` rule with that rule's prompt for files,
  [`file_system_prompt`](../security-rules/blocking-threats/llm-detection.md#attached-files-file_system_prompt).
  The judge reads the job's `message_input` as the user's request for the file.
* **The structure** of a file — hidden text, hidden sheets, active content, a type that is not
  what the file claims — is decided by the policy's
  [`file_policy`](../security-rules/blocking-threats/file-policy.md) rule.

Upload each file with [`POST /v1/files`](files.md) and send its id. The files are checked in
the Input phase, alongside `message_input` if there is one:

```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message_input": "Summarize the attached invoice",
    "attachments": [{"file_id": "file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234"}],
    "inbound_only": true,
    "client_now": "2026-11-10T10:00:00.000Z",
    "client_deadline_at": "2026-11-10T10:00:09.500Z"
  }'
```

* **Without text.** A job may carry only `attachments`. With `inbound_only: true` it completes
  after the Input phase; without it, it waits in `awaiting_response` like a `message_input`
  job.
* **Your deadline.** Tell the server when you stop waiting: `client_deadline_at` with
  `client_now` (the server moves the deadline into its own clock by the difference), or
  `attachments_budget_s`. With neither, the files get 10 seconds. The Input phase of a job
  with attachments ends at that deadline, at most 90 seconds after the request; a file whose
  check has not finished by then counts as incomplete (`failed`, reason `deadline`). The
  SDKs send `client_deadline_at` and `client_now` for you.
* **The decision.** In this step a file never blocks the job, whatever the policy's
  [`file_analysis`](files.md#file-analysis-in-a-policy) `decision`: a finding is recorded as
  `monitor`, and a file that could not be checked fully — not accepted, read or checked
  completely — counts as incomplete and is recorded as `monitor` too (with the reason
  `not_enforced` where `on_incomplete` is `block`). The text of the job still blocks as usual.
  With the full coverage profile in a later step, `block` takes effect on a policy that
  enforces: a file that blocks the job then sets the status `inbound_blocked` and `blocked_by`
  to `file`, and the job does not wait for the rest of its checks.
* **Files stay in use.** While a job checks a file, the file is `leased`; releasing it then
  deletes its bytes once the job is done with it ([Files](files.md)).

| Status | `error.code`                    | When                                                                 |
| ------ | ------------------------------- | -------------------------------------------------------------------- |
| `400`  | `attachments_with_input_job_id` | `attachments` with `input_job_id`: attach the files to the referenced job instead. |
| `400`  | `attachments_need_inbound`      | `attachments` on a job with only `message_output`: files are checked in the Input phase. |
| `400`  | `duplicate_attachment`          | The same file twice in one job.                                      |
| `404`  | `file_not_found`                | No such file in this project.                                        |
| `409`  | `file_unavailable`              | The file was released or has expired.                                |
| `422`  | `file_analysis_unavailable`     | File analysis is not enabled on this deployment.                     |
| `422`  | — (`error.type`: `validation_error`) | More than 3 attachments, or `attachments_budget_s` outside (0, 90]. |

### Field Behavior

CollieAi never calls your LLM — you do. Depending on which fields you send, a job either filters the input and waits for you to submit the LLM response, or filters input and output together in one call.

| Scenario                           | Input Rules | Output Rules                         | Flow                                                      |
| ---------------------------------- | ----------- | ------------------------------------ | -------------------------------------------------------- |
| `message` only                     | Evaluated   | Evaluated on the response you submit | Waits in `awaiting_response`; you `POST .../response`    |
| `message_input` only               | Evaluated   | Evaluated on the response you submit | Waits in `awaiting_response`; you `POST .../response`    |
| `message_output` only              | Skipped     | Evaluated                            | Completes after output filtering                         |
| `message_input` + `message_output` | Evaluated   | Evaluated                            | Both filtered in one call; no response submission needed |
| `inbound_only: true` + `message`   | Evaluated   | Skipped                              | Completes after input filtering                          |

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "message_input": "Summarize the quarterly earnings report",
    "webhook_url": "https://your-app.com/webhooks/collie",
    "metadata": {
      "user_id": "user_123",
      "session_id": "sess_abc"
    }
  }'
```

### Response -- `202 Accepted`

```json
{
  "job_id": "job_abc123def456",
  "status": "processing_inbound",
  "webhook_secret": "whsec_abc123",
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-16T10:30:00Z"
}
```

### Error Responses

| Status | Description                                                        |
| ------ | ------------------------------------------------------------------ |
| `400`  | Invalid request (e.g. both `message` and `message_input` provided) |
| `401`  | Missing or invalid API key                                         |
| `422`  | Validation error                                                   |

***

## GET /v1/jobs/{job\_id}

Retrieve job status and results.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `job_id`  | string | The job identifier |

### Example Request

```bash
curl https://app.collieai.io/v1/jobs/job_abc123def456 \
  -H "Authorization: Bearer clai_your_api_key"
```

### Response -- `200 OK`

```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "inbound_result": {
    "allowed": true,
    "filtered_content": "What is the balance on my account?",
    "blocked": false,
    "block_message": null,
    "triggered_rules": [],
    "threat_intel_observations": [],
    "llm_detection_stages": []
  },
  "outbound_result": {
    "allowed": true,
    "filtered_content": "Your balance is on the Accounts page.",
    "blocked": false,
    "block_message": null,
    "triggered_rules": [],
    "threat_intel_observations": [],
    "llm_detection_stages": null
  },
  "context_result": null,
  "blocked_by": "none",
  "input_job_id": null,
  "webhook_delivery": {
    "status": "success",
    "attempts": 1,
    "last_attempt_at": "2025-01-15T10:30:04Z",
    "last_response_status": 200,
    "last_error": null,
    "next_retry_at": null
  },
  "metadata": {
    "user_id": "user_123",
    "session_id": "sess_abc"
  },
  "created_at": "2025-01-15T10:30:00Z",
  "expires_at": "2025-01-16T10:30:00Z",
  "completed_at": "2025-01-15T10:30:05Z"
}
```

### File result (preview)

A job with `attachments` has `file_result` once its Input phase is finalized; the key is
absent on every other job. For a job with attachments and no text, `inbound_result` holds the
verdict of the Input phase like on any other job. A one-page PDF with a line of white text on
a white page, which the file judge found to be an injection — recorded, not blocked; in this
step the result is the same under `decision: "block"`:

```json
{
  "status": "complete",
  "decision": "monitor",
  "finalized_early": false,
  "coverage_profile": "text_layer",
  "coverage_profile_version": 1,
  "versions": {
    "file_policy_rule_id": "9a1d7c3e-2b45-4f6a-8c90-1e2d3f4a5b6c",
    "file_policy_defaults_version": 1,
    "file_judge_prompt": "builtin:aadc05b2"
  },
  "effective_deadline_at": "2026-11-10T10:00:09.480000+00:00",
  "verdict_at": "2026-11-10T10:00:00.640000+00:00",
  "verdict_after_client_deadline": false,
  "applied_by_client": "unknown",
  "files": [
    {
      "file_id": "file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234",
      "sha256": "3f9a1c2e…",
      "ordinal": 0,
      "attempt": 1,
      "admission": {"status": "accepted", "reasons": []},
      "declared_class": "pdf",
      "detected_class": "pdf",
      "magika": {"label": "pdf", "score": 0.999},
      "extraction": {
        "status": "complete",
        "reasons": [],
        "coverage": {"pages_total": 1, "pages_text": 1, "pages_ocr": null, "cells_total": null, "chars_union": 97, "truncated": false}
      },
      "detection": {"status": "complete", "reasons": [], "windows_total": 2, "windows_evaluated": 2, "llm_calls": 2, "judge_attempts": 2},
      "required_checks": ["text_layer", "clipped", "glyph_substitution", "hidden_ocg", "occluded", "tr3_over_image", "transparent"],
      "missing_checks": ["clipped", "glyph_substitution", "hidden_ocg", "occluded", "tr3_over_image", "transparent"],
      "signals": [
        {"name": "active_content", "state": "absent", "count": 0},
        {"name": "embedded_or_external", "state": "absent", "count": 0},
        {"name": "type_class_mismatch", "state": "absent", "count": 0},
        {"name": "hidden_text", "state": "present", "count": 1, "locations": [{"page": 0, "bbox": [73.0, 717.7, 267.2, 727.9]}]},
        {"name": "layer_ocr_mismatch", "state": "not_checked", "count": 0},
        {"name": "scanned_ocr_layer", "state": "absent", "count": 0}
      ],
      "findings": [
        {
          "rule_id": "5f0c2a7e-1b34-4c8d-9e21-7a6d3f10b2c4",
          "rule_type": "llm_detection",
          "detector": "hidden_injection",
          "rule_action": "block",
          "effective_action": "monitor",
          "no_enforce_reason": "surface_monitor_only",
          "count": 1,
          "verdict": "injection",
          "where": {"page": 0, "bbox": [73.0, 717.7, 267.2, 727.9], "channel": "text_layer", "hidden": true},
          "evidence": {"window_fp": "hmac:v1:cbd0184f…"}
        },
        {
          "rule_id": "9a1d7c3e-2b45-4f6a-8c90-1e2d3f4a5b6c",
          "rule_type": "file_policy",
          "detector": "hidden_text",
          "rule_action": "monitor",
          "effective_action": "monitor",
          "no_enforce_reason": "decision_monitor",
          "count": 1,
          "signal": "hidden_text"
        }
      ],
      "versions": {"extractor": "fx-3", "pypdfium2": "5.15.2", "pdfium": "159.0.8149.0", "pikepdf": "10.18.0"},
      "retention_status": "none",
      "decision": "monitor",
      "decision_reasons": ["llm_detection:hidden_injection", "file_policy:hidden_text"]
    }
  ]
}
```

| Field | Meaning |
| --- | --- |
| `status` | `complete`, `partial` (some file not checked fully), `failed` (no file could be read) or `rejected` (no file was accepted). |
| `decision` | The strongest decision of the files and the text: `block`, `monitor` or `allow`. |
| `finalized_early` | The phase ended before every check finished — a block decided it. |
| `coverage_profile`, `coverage_profile_version` | What this step checks: `text_layer`, version `1` — the text a file holds, not what its rendered page shows. |
| `versions` | The policy's `file_policy` rule the job used (`file_policy_rule_id`, `file_policy_defaults_version`) and the file judge's prompt (`file_judge_prompt`: `builtin` or `custom`, and a short hash of the text). |
| `effective_deadline_at` | Your deadline in the server's clock (from `client_deadline_at`, `attachments_budget_s` or the default). |
| `verdict_after_client_deadline` | The verdict came after that deadline: you may no longer have applied it. |
| `applied_by_client` | Always `unknown`: the server does not know whether you applied the verdict. |
| `files[].admission`, `extraction`, `detection` | Each step's `status` and `reasons`. `not_run` — the step did not run. See the admission reasons below. |
| `files[].declared_class`, `detected_class`, `magika` | The type the upload declared (`pdf`, `csv`, `xlsx`, `jpeg`, `png`, `csv\|xlsx` or `unknown`), the type found in the bytes, and the file type detector's label and score. |
| `files[].extraction.coverage` | What was read: `pages_total` and `pages_text` (PDF), `cells_total` (CSV, XLSX), `chars_union` (characters read) and `truncated` (the file had more text than is read; the extraction is then `partial`). `pages_ocr` is for OCR, a later step. |
| `files[].detection` | Also: `windows_total` and `windows_evaluated` — the parts of the text checked, and how many every check finished on; `llm_calls` — the parts the file judge was asked about; `judge_attempts` — its calls, retries included. `facts` may hold `no_request` (the job has no `message_input`, so misuse was not judged) or `request_too_long`. |
| `files[].required_checks`, `missing_checks` | The checks a full analysis needs, and those this step does not run yet: for a PDF, the tricks only the rendered page shows (`clipped`, `glyph_substitution`, `hidden_ocg`, `occluded`, `transparent`, `tr3_over_image`) — text they hide is checked as visible text; for a workbook with images, `ocr`. Because of them, file findings are recorded and not blocked in this step. |
| `files[].signals` | The file's structural signals: `name`, `state` (`present`, `absent` or `not_checked`), `count`, and where they were found (`locations`). A [`file_policy`](../security-rules/blocking-threats/file-policy.md) rule decides what a present signal does. |
| `files[].findings` | What the checks found. `detector` is `llm_detection`, `hidden_injection` (an injection in text a reader does not see), `misuse`, another rule type, or the signal a `file_policy` finding is about. `rule_action` is what the rule asks for; `effective_action` what it did — `monitor` in this step — and `no_enforce_reason` why it did not block (`surface_monitor_only`: file findings are recorded, not blocked; `decision_monitor`: the rule itself asks for `monitor`). `where` locates the text: `page` (from 0) and `bbox`, or `sheet_fp`, `cell`, `row`, `col`, with its `channel` and whether it is `hidden`. A finding in a PDF's metadata is only ever recorded (`channel_monitor_only`). `evidence` holds keyed fingerprints of the text (`window_fp`, `match_fp`) — never the text. |
| `files[].versions` | The versions of the extractor and its libraries. |
| `files[].retention_status` | Always `none`: no file is kept for review in this step. |
| `files[].decision`, `decision_reasons` | What the file decides — `monitor` or `allow` in this step — and why: each finding as `<rule_type>:<detector or signal>`; `incomplete` and the steps that were not complete; `not_enforced` when a `block` was not applied. |

Admission reasons (`files[].admission.reasons`) when a file is not accepted:

| Status | Reason | When |
| --- | --- | --- |
| `rejected` | `unsupported_media_type` | A type this step does not read: an image, or any type other than PDF, CSV and XLSX. |
| `rejected` | `class_not_allowed` | A type outside the policy's `allowed_classes`. |
| `rejected` | `encrypted` | A password-protected PDF. |
| `rejected` | `too_many_pages` | A PDF of more than 50 pages. |
| `rejected` | `too_many_cells` | A CSV or XLSX file of more than 200,000 cells, or a CSV file of more than 50,000 rows. |
| `rejected` | `zip_limits` | An XLSX file whose archive is beyond the limits (entries, unpacked size, compression ratio). |
| `rejected` | `exceeds_client_budget` | The files would not be checked by your deadline. |
| `failed` | `malformed` | The file cannot be opened. |
| `failed` | `deadline`, `runner_busy`, `runner_unavailable`, … | The file could not be examined: your deadline had passed, or the service that reads files was busy or unavailable. |

### How LLM Detection decided

`inbound_result.llm_detection_stages` shows how the [two-phase LLM Detection check](../security-rules/blocking-threats/llm-detection.md) decided, including when nothing triggered. `triggered_rules` lists only rules that fired, so a safe message leaves it empty. `GET /v1/jobs` returns the same field. Webhook payloads do not have this field; there, only a rule that fired shows its record, in `triggered_rules[].match_info`.

{% hint style="info" %}
This field is a diagnostic. The content of a record may change between releases, so do not build enforcement on it. Decide with `allowed` and `blocked` only once the status says the check finished, and never in `failed` or `expired`. While `status` is `processing_inbound`, `allowed` is `true` because nothing has been checked yet. In `failed` and `expired` it can be `true` too: a job fails when its check hits an error, as well as when its webhook is not delivered, and expires when its TTL runs out before it reaches a terminal status. Treat the message of such a job as unchecked, as the SDKs do, and check it again with a new job. `triggered_rules` says which rules fired.
{% endhint %}

| Value | Meaning |
| --- | --- |
| `null` | No saved trace, which says nothing about the verdict: the Input phase is not saved yet or was saved before this field existed, or the job references another job through `input_job_id`, which holds the trace. Always `null` on `outbound_result`. |
| `[]` | The Input phase is saved and holds no two-phase record. The project has no such rule, an earlier rule ended the check first, or the rule runs the single check. **This does not mean the message was judged safe.** |
| records | One record for each LLM Detection rule that ran the two phases. If a very long rule chain overflows the limit, the last item is `{"truncated": n}`: `n` records were lost. |

A record for a message that phase 2 cleared, shortened:

```json
{
  "v": 2,
  "pipeline": "cascade",
  "rule_id": "5f0c2a7e-1b34-4c8d-9e21-7a6d3f10b2c4",
  "rule_type": "llm_detection",
  "verdict": "safe",
  "matched": false,
  "applied_from": "judge",
  "router": {
    "outcome": "evaluated",
    "label": "thirdparty",
    "p_label": 0.91,
    "p_malicious": 0.93,
    "known_mass": 0.99,
    "routed_by": "mass",
    "latency_ms": 41
  },
  "judge": {
    "ran": true,
    "outcome": "evaluated",
    "verdict": "safe",
    "p": {"safe": 0.97, "injection": 0.02, "misuse": 0.01},
    "history_turns": 0,
    "degraded_reason": null,
    "latency_ms": 150
  },
  "fallback": {"ran": false, "outcome": null, "verdict": null, "latency_ms": null}
}
```

`router` is phase 1 and `judge` is phase 2. To see who decided, read:

| Fields | Who decided |
| --- | --- |
| `verdict: safe`, `applied_from: router`, `router.outcome: evaluated` | Phase 1. Phase 2 did not run. |
| `applied_from: judge` | Phase 2. |
| `applied_from: fallback` | The fallback check, because phase 2 could not answer or the conversation's saved state could not be read. |
| `verdict: none`, `applied_from: decision_on_error` | No model decided. `matched` is `true` only under `decision_on_error: block`: the rule's result on failure, not a detection. `blocked` says whether the message was stopped. |
| `router.outcome: skipped_placeholder` | No model ran: the message was empty or a placeholder. |

`router.routed_by` says why phase 1 sent the message on: `mass` (the malicious categories were likely enough), `unknown` (too little of its answer fell in the known categories), `state` (the conversation is flagged), or `none` (it did not).

### Job Statuses

| Status              | Description                                             |
| ------------------- | ------------------------------------------------------- |
| `processing_inbound`  | Input filtering in progress                              |
| `inbound_blocked`     | Blocked by an input rule, or by an attachment (terminal) |
| `awaiting_response`   | Input passed; waiting for you to submit the LLM response |
| `processing_outbound` | Output filtering in progress                            |
| `outbound_blocked`    | Blocked by an output rule (terminal)                    |
| `delivering`          | Webhook delivery in progress                            |
| `completed`           | Finished successfully (terminal)                        |
| `failed`              | The check hit an error, or webhook delivery failed after retries (terminal) |
| `expired`             | Job exceeded its TTL (terminal)                         |

### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Missing or invalid API key |
| `404`  | Job not found              |

***

## POST /v1/jobs/{job\_id}/response

Submit an LLM response for a job in `awaiting_response` status. CollieAI evaluates the response against output rules.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/response`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description        |
| --------- | ------ | ------------------ |
| `job_id`  | string | The job identifier |

### Request Body

| Field      | Type   | Required | Description                          |
| ---------- | ------ | -------- | ------------------------------------ |
| `response` | string | Yes      | The LLM response content to evaluate |

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs/job_abc123def456/response \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "response": "The quarterly earnings show revenue of $2.5B..."
  }'
```

### Response -- `202 Accepted`

```json
{
  "job_id": "job_abc123def456",
  "status": "processing_outbound"
}
```

### Error Responses

| Status | Description                              |
| ------ | ---------------------------------------- |
| `400`  | Job is not in `awaiting_response` status |
| `401`  | Missing or invalid API key               |
| `404`  | Job not found                            |

***

## POST /v1/jobs/{job\_id}/chunks

Submit one chunk of an upstream-model stream for filtering. Use this when **you own the model** (your own LLM call, a self-hosted model, or a non-OpenAI provider) and you want CollieAi to filter the streaming output as it's produced. Pair it with `GET /v1/jobs/{job_id}/stream` to surface the filtered chunks to your end user.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/chunks`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description                                    |
| --------- | ------ | ---------------------------------------------- |
| `job_id`  | string | The job identifier returned by `POST /v1/jobs` |

### Request Body

| Field      | Type    | Required | Description                                                                                                                                                                     |
| ---------- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sequence` | integer | Yes      | Monotonic per-job chunk index, starting at `0`. Each subsequent chunk MUST be `N+1`. Repeating the last sequence is treated as an idempotent retry.                             |
| `content`  | string  | Yes      | Text chunk from the upstream model. Empty string is valid (e.g. for a `sequence=N` chunk whose only purpose is to mark `is_final=true`).                                        |
| `is_final` | boolean | No       | `true` on the last chunk of the stream. Triggers the engine's final flush and marks the session terminal. Further submits return `409 chunk_session_finished`. Default `false`. |
| `finish_reason` | string | No | Optional provider finish reason (e.g. `stop`, `length`). Only valid on the final chunk (`is_final: true`); max 64 characters. Persisted to the audit log. |

### Idempotency

Submitting the same `sequence` twice with the **same** body returns the same response (cached on the server). Submitting the same `sequence` with a **different** body returns `409 chunk_idempotency_conflict` — sequences are tied to a body for the lifetime of the session. To send different content, use a new sequence number.

### Example Request

```bash
curl -X POST https://app.collieai.io/v1/jobs/job_abc123def456/chunks \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "sequence": 0,
    "content": "The quarterly earnings ",
    "is_final": false
  }'
```

### Response -- `200 OK`

```json
{
  "sequence": 0,
  "accepted": true,
  "emits": [
    {
      "content": "The quarterly ",
      "blocked": false,
      "final": false,
      "triggered_rules": []
    }
  ],
  "finished": false
}
```

| Field      | Type    | Description                                                                                                                                                      |
| ---------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sequence` | integer | Echo of the submitted sequence.                                                                                                                                  |
| `accepted` | boolean | Always `true` on a `200` response. Errors return the standard `{"error": {...}}` envelope instead.                                                               |
| `emits`    | array   | Filtered safe chunks. May be empty if the upstream chunk is fully held back in the engine's stable-window buffer. Forward `content` to your end user in order.   |
| `finished` | boolean | `true` once the session is terminal (final flush completed OR a rule fired a block). After `finished=true`, further submits return `409 chunk_session_finished`. |

Each emit:

| Field             | Type    | Description                                                                                                  |
| ----------------- | ------- | ------------------------------------------------------------------------------------------------------------ |
| `content`         | string  | Safe text to forward to your end user. Masked content already has placeholders applied.                      |
| `blocked`         | boolean | `true` when a rule fired a block. The emit is the terminal emit; the session is finished.                    |
| `block_message`   | string  | Customer-facing block message (the rule's configured message or the backend default). Present only on blocked emits. |
| `final`           | boolean | `true` for the terminal sentinel emit (sent after `is_final=true` drains the buffer, or for a blocked emit). |
| `triggered_rules` | array   | Rule audit entries that fired on this emit (rule id, name, decision, etc.).                                  |

### Error Responses

All errors use the OpenAI-compatible `{"error": {"message", "type", "code"}}` envelope.

| Status | Code                          | Description                                                                                                                                                                      |
| ------ | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `400`  | `chunk_streaming_unsupported` | The project's active policy can't be served by the streaming engine (a full-context **enforcing** rule, `streaming_mode = "buffered"`, a multi-rule policy that can mutate text, or `STREAMING_MODES_ENABLED=false` on the host). Monitor-only rules do **not** cause this — they stream and observe. |
| `401`  | -                             | Missing or invalid API key.                                                                                                                                                      |
| `404`  | -                             | Job not found or not owned by the API key's project.                                                                                                                             |
| `409`  | `chunk_sequence_conflict`     | `sequence` is not the next expected value (gap, or re-submitting an old sequence after later ones were accepted). Response includes `expected_sequence` and `received_sequence`. |
| `409`  | `chunk_idempotency_conflict`  | `sequence` was previously submitted with different content. Use a new sequence number to send different content.                                                                 |
| `409`  | `chunk_session_finished`      | A prior chunk had `is_final=true` or a rule fired a block. Create a new job to start a new stream.                                                                               |
| `409`  | `chunk_concurrent_submit`     | Another submit for the same job is in-flight. Submissions for one job must be serial; wait for the prior response.                                                               |
| `409`  | `chunk_policy_changed`        | The project's policy changed mid-stream. Create a new job to use the updated policy.                                                                                             |
| `409`  | `chunk_session_unrecoverable` | The session entered a state no retry can repair — a stream gap from a prior commit failure, lost or foreign emit history, lost session state, or corrupt/unreadable session state. Create a new job.                               |
| `410`  | -                             | The job is past its `expires_at`. A non-terminal job is flipped to `expired`; a job that already reached a terminal status keeps it. Create a new job.                            |
| `503`  | `chunk_persistence_unavailable` | A storage step ended in a state the server can't fully vouch for. Retrying the same sequence is **always safe**; what the retry does depends on the branch (the error `message` says which): re-process or replay the chunk (storage failed at an unknown point), record — or land on — the session's terminal state (a fatal condition whose marker write is unsettled; the retry may answer `409 chunk_session_unrecoverable`), or repair the job's status record (the chunk itself is already committed). Retry with backoff. |
| `503`  | `chunk_resolution_unavailable` | The server could not **resolve** the project's policy — a dependency was unreachable, not a policy problem. Retry the same sequence with backoff; retries are safe via idempotency. |
| `504`  | `chunk_filter_timeout`        | Filtering exceeded the per-chunk budget. Retry the same sequence with backoff.                                                                                                   |

***

## GET /v1/jobs/{job\_id}/stream

Server-Sent Events (SSE) stream of the filtered chunks produced by `POST /v1/jobs/{job_id}/chunks`. Subscribers see emits the API has accepted; in-flight or failed submits are never published. Useful for delivering filtered output to a browser or another client while your backend handles the chunk submission.

**URL:** `https://app.collieai.io/v1/jobs/{job_id}/stream`

**Auth:** Bearer token (API key `clai_xxx`)

### Path Parameters

| Parameter | Type   | Description                                    |
| --------- | ------ | ---------------------------------------------- |
| `job_id`  | string | The job identifier returned by `POST /v1/jobs` |

### Request Headers

| Header          | Required | Description                                                                                                                                             |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Last-Event-ID` | No       | Standard SSE resume token — the ID of the last event the client saw. Subscribers resume from the next event. Absent → full backlog replay from chunk 0. |

### Example Request

```bash
curl -N https://app.collieai.io/v1/jobs/job_abc123def456/stream \
  -H "Authorization: Bearer clai_your_api_key" \
  -H "Accept: text/event-stream"
```

### Response -- `200 OK` (`Content-Type: text/event-stream`)

Each filtered emit is delivered as a `chunk` event with a stable stream ID for resume support:

```
id: 1-0
event: chunk
data: {"sequence": 0, "content": "The quarterly ", "blocked": false, "final": false, "triggered_rules": []}

id: 2-0
event: chunk
data: {"sequence": 1, "content": "earnings show ", "blocked": false, "final": false, "triggered_rules": []}

id: 3-0
event: chunk
data: {"sequence": 2, "content": "", "blocked": false, "final": true, "triggered_rules": []}

event: end
data: {"reason": "final"}
```

| Field             | Type    | Description                                                                             |
| ----------------- | ------- | --------------------------------------------------------------------------------------- |
| `sequence`        | integer | The chunk-submission sequence this emit came from. Multiple emits can share a sequence. |
| `content`         | string  | Safe text to render to the end user.                                                    |
| `blocked`         | boolean | `true` when a rule fired a block. Terminal for the stream.                              |
| `final`           | boolean | `true` for the terminal sentinel emit on `is_final=true` chunks.                        |
| `triggered_rules` | array   | Rule audit entries that fired on this emit.                                             |

The stream always closes with a single `end` event:

| `reason`                | Meaning                                                                                                                                                   |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `final`                 | Normal end of stream — the last chunk submitted with `is_final=true` was processed.                                                                       |
| `blocked`               | A rule fired a block and terminated the stream.                                                                                                           |
| `session_finished`      | The session was already terminal when the SSE consumer connected (e.g. SSE opened late, after the producer finished).                                     |
| `session_unrecoverable` | The job's chunk stream entered a state that can't be repaired. The customer's backend should create a new job.                                            |
| `idle_timeout`          | No new emits arrived within the idle window and the session is not terminal. The consumer should reconnect with `Last-Event-ID` if the job is still live. |
| `upstream_error`        | The SSE reader hit an internal error reading the chunk stream. Reconnect with `Last-Event-ID`.                                                            |

Keepalive comments (`: keepalive\n\n`) are sent periodically when no new emits arrive, so reverse proxies don't idle-close the TCP connection. Treat them as no-ops.

### Error Responses

| Status | Description                                         |
| ------ | --------------------------------------------------- |
| `401`  | Missing or invalid API key                          |
| `404`  | Job not found or not owned by the API key's project |

***

## GET /v1/jobs

List jobs for the authenticated project.

**URL:** `https://app.collieai.io/v1/jobs`

**Auth:** Bearer token (API key `clai_xxx`)

### Query Parameters

| Parameter       | Type    | Required | Description                                                                                       |
| --------------- | ------- | -------- | ------------------------------------------------------------------------------------------------- |
| `page`          | integer | No       | Page number, starting from 1. Default: 1                                                          |
| `page_size`     | integer | No       | Items per page, 1-100. Default: 20                                                                |
| `status_filter` | string  | No       | Filter by status (`processing_inbound`, `inbound_blocked`, `awaiting_response`, `processing_outbound`, `outbound_blocked`, `delivering`, `completed`, `failed`, `expired`) |

### Example Request

```bash
curl "https://app.collieai.io/v1/jobs?page=1&page_size=10&status_filter=completed" \
  -H "Authorization: Bearer clai_your_api_key"
```

### Response -- `200 OK`

Abridged. Each item also has `inbound_result`, `outbound_result`, `context_result`, `blocked_by`, `input_job_id` and `expires_at`, as in `GET /v1/jobs/{job_id}`, and `file_result` on a job with attachments. In a list, `block_message` and `webhook_delivery` are always `null`.

```json
{
  "jobs": [
    {
      "job_id": "job_abc123def456",
      "status": "completed",
      "created_at": "2025-01-15T10:30:00Z",
      "completed_at": "2025-01-15T10:30:05Z",
      "metadata": {
        "user_id": "user_123"
      }
    }
  ],
  "total": 42,
  "page": 1,
  "page_size": 10
}
```

### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Missing or invalid API key |
| `422`  | Invalid query parameters   |

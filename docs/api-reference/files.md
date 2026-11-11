---
description: >-
  CollieAi Files API — upload a file for analysis, read its metadata and
  release it via POST /v1/files, GET /v1/files/{file_id} and
  DELETE /v1/files/{file_id}, and attach it to a job. Preview: needs enabling.
icon: file-arrow-up
---

# Files

{% hint style="info" %}
**Status: preview — needs enabling.** File analysis is being rolled out step by step and is
off on every deployment for now, including app.collieai.io. While it is off, every route on
this page answers `422 file_analysis_unavailable`. Uploaded files can be attached to jobs
([Attachments](jobs.md#attachments-preview)); in this step a job tracks its files but does not
read them yet — reading and checking their content comes with a later step.
{% endhint %}

Upload a file once, get a `file_id`, and refer to it later. CollieAi stores the bytes only to
analyse them: it never returns the content, and it deletes the bytes when you release the file
or when it expires.

***

## POST /v1/files

Upload one file (`multipart/form-data`).

**URL:** `https://app.collieai.io/v1/files`

**Auth:** Bearer token (API key `clai_xxx`)

### Form fields

| Field     | Type    | Required | Description                                                     |
| --------- | ------- | -------- | --------------------------------------------------------------- |
| `file`    | file    | Yes      | The file. Its declared type and name are kept as metadata.      |
| `purpose` | string  | No       | `analysis` — the only value. Default: `analysis`.               |
| `retain`  | boolean | No       | Keep the file after the jobs it is attached to finish: it returns to `uploaded` and expires an hour later. Without it, the bytes are deleted once its last job is done. Default: `false`. |

```bash
curl -X POST https://app.collieai.io/v1/files \
  -H "Authorization: Bearer clai_xxx" \
  -F "file=@invoice.pdf;type=application/pdf" \
  -F "purpose=analysis"
```

### Response — 201 Created

```json
{
  "id": "file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234",
  "object": "file",
  "bytes": 182334,
  "sha256": "3f9a1c2e…",
  "filename": "invoice.pdf",
  "declared_media_type": "application/pdf",
  "state": "uploaded",
  "retain": false,
  "created_at": "2026-11-10T10:00:00Z",
  "expires_at": "2026-11-10T11:00:00Z"
}
```

A file that is never attached to a job is deleted one hour after the upload (`expires_at`).

File names longer than 255 characters are shortened to 255.

### Errors

| Status | `error.code`                | When                                                                 |
| ------ | --------------------------- | -------------------------------------------------------------------- |
| 411    | `length_required`           | The request has no `Content-Length`.                                 |
| 413    | `file_too_large`            | The file is larger than the limit (20 MB by default).                |
| 422    | `file_analysis_unavailable` | File analysis is not enabled on this deployment.                     |
| 422    | `invalid_purpose`           | `purpose` is not `analysis`.                                         |
| 422    | `empty_file`                | The file has no bytes.                                               |
| 422    | `missing_file`              | The form has no file in the field `file`.                            |
| 422    | `invalid_retain`            | `retain` is not `true` or `false`.                                   |
| 429    | `file_quota_exceeded`       | The project already stores its maximum of files or bytes (by default 100 files, 200 MB). Released files keep counting until their bytes are deleted. |
| 503    | `file_store_full`           | The store has no room right now. Retry later.                        |
| 503    | `file_uploads_busy`         | Too many uploads at once. Retry after the `Retry-After` seconds.     |

***

## GET /v1/files/{file_id}

Metadata of one of your project's files — never its content. The response has the same fields
as the upload response.

```bash
curl https://app.collieai.io/v1/files/file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234 \
  -H "Authorization: Bearer clai_xxx"
```

`state` is one of:

| State             | Meaning                                                              |
| ----------------- | -------------------------------------------------------------------- |
| `uploaded`        | Stored and ready.                                                    |
| `leased`          | Attached to a job that has not finished checking it.                 |
| `delete_requested`| You released it while a job uses it; the bytes are deleted once the job is done. |
| `release_pending` | You released it, or its last job is done; the bytes are about to be deleted. |
| `expired`         | Its time ran out; the bytes are about to be deleted.                 |
| `deleted`         | The bytes are gone; `filename` is cleared.                           |

`404 file_not_found` — no such file in this project.

***

## DELETE /v1/files/{file_id}

Release a file: its bytes are deleted within a few minutes — if a job is still checking it, once
that job is done. Releasing an already released file succeeds again.

```bash
curl -X DELETE https://app.collieai.io/v1/files/file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234 \
  -H "Authorization: Bearer clai_xxx"
```

**Response:** `204 No Content`. `404 file_not_found` — no such file in this project, or its
bytes are already deleted.

***

## File analysis in a policy

Each policy says what attached files decide, in its `file_analysis` object
([`POST /api/v1/policies`, `PATCH /api/v1/policies/{policy_id}`](policies.md)). A policy without it — or with
`enabled: false` — never blocks on files: an incomplete file is recorded as `monitor`.

| Field                 | Type   | Default   | Description |
| --------------------- | ------ | --------- | ----------- |
| `enabled`             | bool   | `false`   | Analyze attached files (the deployment must have file analysis enabled too). |
| `decision`            | string | `monitor` | `block` or `monitor`. Under `monitor` every file finding and every incomplete check is recorded, and none blocks. A file blocks a job only under `block` on a policy whose `enforcement_mode` is `enforce`. |
| `on_incomplete`       | string | `block`   | What a file that could not be checked fully decides: `block` or `monitor`. A file that was not accepted, read or checked completely counts as incomplete. |
| `rule_scope`          | array  | null      | Advanced: the ids of the rules that check file content. null = the policy's enabled Input rules of the types `llm_detection`, `lightweight_model`, `url_reputation` and `url_filter` whose decision is not `allow`; `regex` and dictionary rules run on files only when listed here. |
| `primary_llm_rule_id` | string | null      | The `llm_detection` rule that judges the content of files. null = the policy's only enabled Input `llm_detection` rule; with several, choose one here. Its prompt for files is [`file_system_prompt`](../security-rules/blocking-threats/llm-detection.md#attached-files-file_system_prompt). |

```bash
curl -X PATCH https://app.collieai.io/api/v1/policies/pol_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "file_analysis": {"enabled": true, "decision": "monitor", "on_incomplete": "block"}
  }'
```

The object is stored whole, with the defaults filled in: a `PATCH` replaces it, and
`"file_analysis": null` removes it. An unknown field answers `422`. `rule_scope` and
`primary_llm_rule_id` take effect once files are read (a later step).

The policy's response lists in `file_analysis_warnings` what the settings cannot do with the
policy's current rules — for example, no enabled Input `llm_detection` rule, several of them
and no `primary_llm_rule_id`, or no rule in scope. A warning never blocks saving: the rules
may change later.

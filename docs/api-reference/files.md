---
description: >-
  CollieAi Files API — upload a file for analysis, read its metadata and
  release it via POST /v1/files, GET /v1/files/{file_id} and
  DELETE /v1/files/{file_id}. Preview: needs enabling.
icon: file-arrow-up
---

# Files

{% hint style="info" %}
**Status: preview — needs enabling.** File analysis is being rolled out step by step and is
off on every deployment for now, including app.collieai.io. While it is off, every route on
this page answers `422 file_analysis_unavailable`. This page describes the upload API of the
first step; attaching uploaded files to jobs comes with a later step.
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
| `retain`  | boolean | No       | Keep the file after its jobs finish (later step). Default: `false`. |

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
| 413    | `file_too_large`            | The file is larger than the limit (20 MB by default).                |
| 422    | `file_analysis_unavailable` | File analysis is not enabled on this deployment.                     |
| 422    | `invalid_purpose`           | `purpose` is not `analysis`.                                         |
| 422    | `empty_file`                | The file has no bytes.                                               |
| 422    | `missing_file`              | The form has no file in the field `file`.                            |
| 429    | `file_quota_exceeded`       | The project already stores its maximum of files or bytes (by default 100 files, 200 MB). Released files keep counting until their bytes are deleted. |
| 503    | `file_store_full`           | The store has no room right now. Retry later.                        |

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
| `release_pending` | You released it; the bytes are about to be deleted.                  |
| `expired`         | Its time ran out; the bytes are about to be deleted.                 |
| `deleted`         | The bytes are gone; `filename` is cleared.                           |

`404 file_not_found` — no such file in this project.

***

## DELETE /v1/files/{file_id}

Release a file: its bytes are deleted within a few minutes. Releasing an already released file
succeeds again.

```bash
curl -X DELETE https://app.collieai.io/v1/files/file_5b0f3a8e9c2d4f6a8b1c3d5e7f901234 \
  -H "Authorization: Bearer clai_xxx"
```

**Response:** `204 No Content`. `404 file_not_found` — no such file in this project, or its
bytes are already deleted.

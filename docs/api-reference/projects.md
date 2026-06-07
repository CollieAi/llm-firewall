---
description: >-
  CollieAi Projects API — create, list, update, and delete projects and their
  settings (active policy, rate limit, data retention, streaming mode) via
  /api/v1/projects.
icon: diagram-project
---

# Projects

Projects are the top-level organizational unit in CollieAi. Each project has its own API keys, policies, and request logs.

## GET /api/v1/projects

List all active projects for the authenticated user.

**URL:** `https://app.collieai.io/api/v1/projects`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/api/v1/projects \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
{
  "projects": [
    {
      "id": "proj_abc123",
      "name": "Production App",
      "description": "Main production application",
      "owner_id": "usr_owner1",
      "active_policy_id": "pol_def456",
      "filter_all_messages": true,
      "rate_limit_rpm": null,
      "body_retention_hours": 48,
      "log_retention_days": 90,
      "streaming_mode": "auto",
      "is_active": true,
      "created_at": "2026-01-10T08:00:00Z",
      "updated_at": "2026-01-14T12:30:00Z"
    }
  ],
  "total": 1
}
```

Project fields are top-level (no `settings` envelope). `streaming_mode` is always present and required by clients — see [Streaming](../proxy-integration/streaming.md).

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

## POST /api/v1/projects

Create a new project. Automatically creates an API key and assigns the user's default policy.

**URL:** `https://app.collieai.io/api/v1/projects`

**Auth:** Session cookie or Bearer token

### Request Body

| Field                  | Type    | Required | Description                                                                                                                                                                                                                                                         |
| ---------------------- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | string  | Yes      | Project name                                                                                                                                                                                                                                                        |
| `description`          | string  | No       | Project description                                                                                                                                                                                                                                                 |
| `body_retention_hours` | integer | No       | Hours to keep `request_body`/`response_body`. Default `48`, range `0–720`. `0` = never store bodies.                                                                                                                                                                |
| `log_retention_days`   | integer | No       | Days to keep log rows for audit. Default `90`, range `1–365`.                                                                                                                                                                                                       |
| `streaming_mode`       | string  | No       | One of `"auto"` (default), `"buffered"`, or `"incremental"`. Controls whether responses are delivered to the client incrementally or after the full response has been filtered. See [Streaming](../proxy-integration/streaming.md) for the delivery-path semantics. |

The invariant `body_retention_hours ≤ log_retention_days × 24` is enforced. See [Data Retention](../projects-and-policies/data-retention.md).

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My New Project",
    "description": "Staging environment",
    "streaming_mode": "auto"
  }'
```

### Response — `201 Created`

```json
{
  "id": "proj_new123",
  "name": "My New Project",
  "description": "Staging environment",
  "owner_id": "usr_owner1",
  "active_policy_id": "pol_auto456",
  "filter_all_messages": true,
  "rate_limit_rpm": null,
  "body_retention_hours": 48,
  "log_retention_days": 90,
  "streaming_mode": "auto",
  "is_active": true,
  "api_key": "clai_abc123def456ghi789",
  "created_at": "2026-01-15T10:00:00Z",
  "updated_at": "2026-01-15T10:00:00Z"
}
```

> The `api_key` field is only returned on creation. Store it securely — it cannot be retrieved again.

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `422`  | Validation error  |

## GET /api/v1/projects/{project\_id}

Get details for a specific project.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

### Example Request

```bash
curl https://app.collieai.io/api/v1/projects/proj_abc123 \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
{
  "id": "proj_abc123",
  "name": "Production App",
  "description": "Main production application",
  "owner_id": "usr_owner1",
  "active_policy_id": "pol_def456",
  "filter_all_messages": true,
  "rate_limit_rpm": null,
  "body_retention_hours": 48,
  "log_retention_days": 90,
  "streaming_mode": "auto",
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-14T12:30:00Z"
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

## PATCH /api/v1/projects/{project\_id}

Update a project. All fields are optional; only provided fields are updated.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

### Request Body

| Field                  | Type    | Description                                                                                                                                                                                                 |
| ---------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`                 | string  | New project name                                                                                                                                                                                            |
| `description`          | string  | New project description                                                                                                                                                                                     |
| `active_policy_id`     | string  | ID of the policy to set as active                                                                                                                                                                           |
| `filter_all_messages`  | boolean | Whether to filter all messages in conversation history (top-level field, not nested under `settings`).                                                                                                      |
| `is_active`            | boolean | Soft-delete toggle. Set to `false` to hide the project without losing data.                                                                                                                                 |
| `rate_limit_rpm`       | integer | Max requests per minute for this project. Range `1–10000`, or `null` for unlimited.                                                                                                                         |
| `body_retention_hours` | integer | Hours to keep `request_body`/`response_body`. Range `0–720`. Validated against current `log_retention_days` if only one of the two is supplied.                                                             |
| `log_retention_days`   | integer | Days to keep log rows for audit. Range `1–365`. Validated against current `body_retention_hours` if only one of the two is supplied.                                                                        |
| `streaming_mode`       | string  | One of `"auto"`, `"buffered"`, or `"incremental"`. Takes effect on the next request. Sending `null` is rejected — omit the field to leave it unchanged. See [Streaming](../proxy-integration/streaming.md). |

Retention changes apply to **new logs only**; existing rows keep their original expiry. See [Data Retention](../projects-and-policies/data-retention.md).

### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/projects/proj_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production App v2",
    "active_policy_id": "pol_new789",
    "filter_all_messages": true,
    "streaming_mode": "auto"
  }'
```

### Response — `200 OK`

```json
{
  "id": "proj_abc123",
  "name": "Production App v2",
  "description": "Main production application",
  "owner_id": "usr_owner1",
  "active_policy_id": "pol_new789",
  "filter_all_messages": true,
  "rate_limit_rpm": null,
  "body_retention_hours": 48,
  "log_retention_days": 90,
  "streaming_mode": "auto",
  "is_active": true,
  "created_at": "2026-01-10T08:00:00Z",
  "updated_at": "2026-01-15T11:00:00Z"
}
```

### Error Responses

| Status | Code                           | Description                                                                                                                         |
| ------ | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `401`  | —                              | Not authenticated                                                                                                                   |
| `404`  | —                              | Project or policy not found                                                                                                         |
| `422`  | `retention_invariant_violated` | `body_retention_hours` would exceed `log_retention_days × 24`. Returned as the OpenAI-compatible error envelope under `error.code`. |
| `422`  | —                              | Other validation error (out-of-bounds value, etc.)                                                                                  |

## DELETE /api/v1/projects/{project\_id}

Hard-delete a project. Associated policies are preserved and can be reused. API keys for this project are deactivated.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/projects/proj_abc123 \
  -H "Authorization: Bearer <token>"
```

### Response — `204 No Content`

No response body.

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

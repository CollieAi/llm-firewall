---
description: >-
  CollieAi API Keys API — create, list, and deactivate project-scoped clai_ keys
  that authenticate requests to the proxy via
  /api/v1/projects/{project_id}/api-keys.
icon: rectangle-api
---

# API keys

API keys authenticate requests to the CollieAi proxy (`/v1/*` endpoints). Each key is scoped to a single project and uses the `clai_` prefix.

## GET /api/v1/projects/{project\_id}/api-keys

List all API keys for a project. Key values are masked in the response.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}/api-keys`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

### Example Request

```bash
curl https://app.collieai.io/api/v1/projects/proj_abc123/api-keys \
  -H "Authorization: Bearer <token>"
```

### Response -- `200 OK`

```json
{
  "api_keys": [
  {
    "id": "key_abc123",
    "name": "Production Key",
    "masked_key": "clai_abc1",
    "is_active": true,
    "created_at": "2025-01-10T08:00:00Z",
    "last_used_at": "2025-01-15T09:30:00Z"
  },
  {
    "id": "key_def456",
    "name": "Development Key",
    "masked_key": "clai_def4",
    "is_active": true,
    "created_at": "2025-01-12T10:00:00Z",
    "last_used_at": null
  }
  ],
  "total": 2
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

## POST /api/v1/projects/{project\_id}/api-keys

Create a new API key for a project. The full key value (format: `clai_xxx`) is only returned once in the response.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}/api-keys`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

### Request Body

| Field         | Type   | Required | Description                         |
| ------------- | ------ | -------- | ----------------------------------- |
| `name`        | string | Yes      | Display name for the key (1–255)    |
| `description` | string | No       | Optional description                |
| `expires_at`  | string | No       | Optional ISO 8601 expiry timestamp  |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/projects/proj_abc123/api-keys \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CI/CD Pipeline Key"
  }'
```

### Response -- `201 Created`

```json
{
  "id": "key_new789",
  "name": "CI/CD Pipeline Key",
  "key": "clai_abc123def456ghi789jkl012mno345",
  "masked_key": "clai_abc1",
  "is_active": true,
  "created_at": "2025-01-15T10:00:00Z",
  "last_used_at": null
}
```

> The `key` field contains the full API key and is only returned on creation. Store it securely -- it cannot be retrieved again.

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |
| `422`  | Validation error  |

## DELETE /api/v1/projects/{project\_id}/api-keys/{key\_id}

Deactivate an API key. The key is immediately invalidated. Any subsequent requests using this key will receive a `401` error.

**URL:** `https://app.collieai.io/api/v1/projects/{project_id}/api-keys/{key_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |
| `key_id`     | string | The API key identifier |

### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/projects/proj_abc123/api-keys/key_abc123 \
  -H "Authorization: Bearer <token>"
```

### Response -- `204 No Content`

No response body.

### Error Responses

| Status | Description                  |
| ------ | ---------------------------- |
| `401`  | Not authenticated            |
| `404`  | Project or API key not found |

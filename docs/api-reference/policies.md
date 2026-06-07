---
description: >-
  CollieAi Policies API — create, list, update, delete, and set a default policy
  via   /api/v1/policies, plus project-scoped policy endpoints.
icon: square-sliders-vertical
---

# Policies

Policies are collections of rules that define how CollieAi evaluates requests and responses. Policies are project-independent and can be shared across projects.

## Project-Independent Endpoints (Recommended)

### GET /api/v1/policies

List all policies accessible to the authenticated user.

**URL:** `https://app.collieai.io/api/v1/policies`

**Auth:** Session cookie or Bearer token

#### Response -- `200 OK`

The response includes the user's `default_policy_id`.

```json
{
  "policies": [
    {
      "id": "pol_abc123",
      "name": "Default Policy",
      "description": "Standard content safety rules",
      "enforcement_mode": "enforce",
      "is_default": true,
      "rules_count": 5,
      "created_at": "2025-01-10T08:00:00Z",
      "updated_at": "2025-01-14T12:30:00Z"
    },
    {
      "id": "pol_def456",
      "name": "Strict Policy",
      "description": "Enhanced filtering for production",
      "enforcement_mode": "enforce",
      "is_default": false,
      "rules_count": 12,
      "created_at": "2025-01-12T09:00:00Z",
      "updated_at": "2025-01-13T15:00:00Z"
    }
  ],
  "default_policy_id": "pol_abc123"
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

### POST /api/v1/policies

Create a new shared policy.

**URL:** `https://app.collieai.io/api/v1/policies`

**Auth:** Session cookie or Bearer token

#### Request Body

| Field              | Type   | Required | Description                      |
| ------------------ | ------ | -------- | -------------------------------- |
| `name`             | string | Yes      | Policy name                      |
| `description`      | string | No       | Policy description               |
| `enforcement_mode` | string | No       | `enforce` (default) or `monitor` |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Strict Policy",
    "description": "Enhanced filtering for production",
    "enforcement_mode": "enforce"
  }'
```

#### Response -- `201 Created`

```json
{
  "id": "pol_new789",
  "name": "Strict Policy",
  "description": "Enhanced filtering for production",
  "enforcement_mode": "enforce",
  "is_default": false,
  "rules_count": 0,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `422`  | Validation error  |

### PATCH /api/v1/policies/{policy\_id}

Update a policy.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

#### Request Body

| Field              | Type   | Description            |
| ------------------ | ------ | ---------------------- |
| `name`             | string | New policy name        |
| `description`      | string | New policy description |
| `enforcement_mode` | string | `enforce` or `monitor` |

#### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/policies/pol_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Policy Name",
    "enforcement_mode": "monitor"
  }'
```

#### Response -- `200 OK`

```json
{
  "id": "pol_abc123",
  "name": "Updated Policy Name",
  "description": "Standard content safety rules",
  "enforcement_mode": "monitor",
  "is_default": true,
  "rules_count": 5,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Policy not found  |
| `422`  | Validation error  |

### DELETE /api/v1/policies/{policy\_id}

Delete a policy. Rejected if the policy is currently set as the active policy for any project.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

#### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/policies/pol_abc123 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description                                     |
| ------ | ----------------------------------------------- |
| `401`  | Not authenticated                               |
| `404`  | Policy not found                                |
| `409`  | Policy is in use as active policy for a project |

### POST /api/v1/policies/{policy\_id}/set-default

Toggle a policy as the default for new projects. If the policy is already the default, it is unset.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/set-default`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/policies/pol_abc123/set-default \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "id": "pol_abc123",
  "name": "Default Policy",
  "description": "Standard content safety rules",
  "enforcement_mode": "enforce",
  "is_default": true,
  "rules_count": 5,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Policy not found  |

## Project-Scoped Endpoints

These endpoints manage policies within a specific project context. Behavior is identical to the project-independent endpoints above.

| Method | Path                                                 |
| ------ | ---------------------------------------------------- |
| GET    | `/api/v1/projects/{project_id}/policies`             |
| POST   | `/api/v1/projects/{project_id}/policies`             |
| GET    | `/api/v1/projects/{project_id}/policies/{policy_id}` |
| PATCH  | `/api/v1/projects/{project_id}/policies/{policy_id}` |
| DELETE | `/api/v1/projects/{project_id}/policies/{policy_id}` |

### Example -- Project-Scoped Request

```bash
curl https://app.collieai.io/api/v1/projects/proj_abc123/policies \
  -H "Authorization: Bearer <token>"
```

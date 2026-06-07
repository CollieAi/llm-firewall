---
description: >-
  CollieAi Admin API — system statistics, user management, and management of
  system dictionaries, policies, and rules via /api/v1/admin endpoints (admin
  role required).
icon: user-tie
---

# Admin

Administrative endpoints for system-wide management. All endpoints require the `admin` role and return `403 Forbidden` for non-admin users.

## System Statistics

### GET /api/v1/admin/stats

Get system-wide statistics.

**URL:** `https://app.collieai.io/api/v1/admin/stats`

**Auth:** Session cookie or Bearer token (admin role required)

#### Example Request

```bash
curl https://app.collieai.io/api/v1/admin/stats \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "total_users": 150,
  "active_users": 87,
  "total_projects": 312,
  "total_requests": 45230
}
```

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |

## User Management

### GET /api/v1/admin/users

List all users with optional search and pagination.

**URL:** `https://app.collieai.io/api/v1/admin/users`

**Auth:** Session cookie or Bearer token (admin role required)

#### Query Parameters

| Parameter   | Type    | Required | Description                              |
| ----------- | ------- | -------- | ---------------------------------------- |
| `search`    | string  | No       | Search by email or name                  |
| `page`      | integer | No       | Page number, starting from 1. Default: 1 |
| `page_size` | integer | No       | Items per page. Default: 20              |

#### Example Request

```bash
curl "https://app.collieai.io/api/v1/admin/users?search=john&page=1&page_size=10" \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "users": [
    {
      "id": "usr_abc123",
      "email": "john@example.com",
      "name": "John Doe",
      "role": "user",
      "is_active": true,
      "project_count": 3,
      "logs_count": 1250,
      "created_at": "2025-01-10T08:00:00Z",
      "last_login_at": "2025-01-15T09:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |

### PATCH /api/v1/admin/users/{user\_id}

Update a user's role, active status, or subscription plan. Self-modification is protected (returns `400`).

**URL:** `https://app.collieai.io/api/v1/admin/users/{user_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Path Parameters

| Parameter | Type   | Description         |
| --------- | ------ | ------------------- |
| `user_id` | string | The user identifier |

#### Request Body

| Field       | Type    | Description                                                                                                                                                         |
| ----------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `role`      | string  | New role: `user` or `admin`                                                                                                                                         |
| `is_active` | boolean | Enable or disable the user account                                                                                                                                  |
| `plan`      | string  | Subscription plan: `free` or `growth`. Resets usage on change. Used for manual overrides — e.g. comping a customer to Growth without going through Stripe Checkout. |

#### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/admin/users/usr_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "admin",
    "is_active": true,
    "plan": "growth"
  }'
```

#### Response -- `200 OK`

```json
{
  "id": "usr_abc123",
  "email": "john@example.com",
  "name": "John Doe",
  "role": "admin",
  "is_active": true,
  "plan": "growth",
  "created_at": "2025-01-10T08:00:00Z",
  "last_login_at": "2025-01-15T09:00:00Z"
}
```

#### Error Responses

| Status | Description                    |
| ------ | ------------------------------ |
| `400`  | Cannot modify your own account |
| `401`  | Not authenticated              |
| `403`  | Admin role required            |
| `404`  | User not found                 |
| `422`  | Validation error               |

## System Dictionaries

System dictionaries are globally available, pre-built dictionaries managed by administrators.

### GET /api/v1/admin/dictionaries

List all system dictionaries.

**URL:** `https://app.collieai.io/api/v1/admin/dictionaries`

**Auth:** Session cookie or Bearer token (admin role required)

#### Example Request

```bash
curl https://app.collieai.io/api/v1/admin/dictionaries \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
[
  {
    "id": "dict_sys001",
    "name": "HIPAA Terms",
    "description": "Healthcare-related protected terms",
    "is_system": true,
    "case_sensitive": false,
    "word_count": 1200,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
]
```

### POST /api/v1/admin/dictionaries

Create a new system dictionary.

**URL:** `https://app.collieai.io/api/v1/admin/dictionaries`

**Auth:** Session cookie or Bearer token (admin role required)

#### Request Body

| Field            | Type    | Required | Description                                   |
| ---------------- | ------- | -------- | --------------------------------------------- |
| `name`           | string  | Yes      | Dictionary name                               |
| `description`    | string  | No       | Dictionary description                        |
| `content`        | string  | Yes      | Dictionary content (one word/phrase per line) |
| `case_sensitive` | boolean | No       | Case-sensitive matching. Default: `false`     |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/admin/dictionaries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "PCI DSS Terms",
    "description": "Payment card industry data security terms",
    "content": "credit card\ncard number\ncvv\nexpiration date\ncardholder",
    "case_sensitive": false
  }'
```

#### Response -- `201 Created`

```json
{
  "id": "dict_sys003",
  "name": "PCI DSS Terms",
  "description": "Payment card industry data security terms",
  "is_system": true,
  "case_sensitive": false,
  "word_count": 5,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |
| `422`  | Validation error    |

### PUT /api/v1/admin/dictionaries/{dictionary\_id}

Update a system dictionary.

**URL:** `https://app.collieai.io/api/v1/admin/dictionaries/{dictionary_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Path Parameters

| Parameter       | Type   | Description               |
| --------------- | ------ | ------------------------- |
| `dictionary_id` | string | The dictionary identifier |

#### Request Body

| Field            | Type    | Required | Description                     |
| ---------------- | ------- | -------- | ------------------------------- |
| `name`           | string  | No       | New dictionary name             |
| `description`    | string  | No       | New dictionary description      |
| `content`        | string  | No       | New content (replaces existing) |
| `case_sensitive` | boolean | No       | Updated case sensitivity        |

#### Example Request

```bash
curl -X PUT https://app.collieai.io/api/v1/admin/dictionaries/dict_sys003 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "credit card\ncard number\ncvv\nexpiration date\ncardholder\nPAN\nIBAN"
  }'
```

#### Response -- `200 OK`

```json
{
  "id": "dict_sys003",
  "name": "PCI DSS Terms",
  "description": "Payment card industry data security terms",
  "is_system": true,
  "case_sensitive": false,
  "word_count": 7,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Error Responses

| Status | Description          |
| ------ | -------------------- |
| `401`  | Not authenticated    |
| `403`  | Admin role required  |
| `404`  | Dictionary not found |
| `422`  | Validation error     |

### DELETE /api/v1/admin/dictionaries/{dictionary\_id}

Delete a system dictionary.

**URL:** `https://app.collieai.io/api/v1/admin/dictionaries/{dictionary_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Path Parameters

| Parameter       | Type   | Description               |
| --------------- | ------ | ------------------------- |
| `dictionary_id` | string | The dictionary identifier |

#### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/admin/dictionaries/dict_sys003 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description          |
| ------ | -------------------- |
| `401`  | Not authenticated    |
| `403`  | Admin role required  |
| `404`  | Dictionary not found |

## System Policies

System policies are globally available policy templates managed by administrators. Deleting a system policy auto-cleans `active_policy_id` and `default_policy_id` references.

### GET /api/v1/admin/policies

List all system policies.

**URL:** `https://app.collieai.io/api/v1/admin/policies`

**Auth:** Session cookie or Bearer token (admin role required)

#### Example Request

```bash
curl https://app.collieai.io/api/v1/admin/policies \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
[
  {
    "id": "pol_sys001",
    "name": "Healthcare Compliance",
    "description": "HIPAA-compliant policy template",
    "is_system": true,
    "rules_count": 8,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-10T12:00:00Z"
  }
]
```

### POST /api/v1/admin/policies

Create a new system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies`

**Auth:** Session cookie or Bearer token (admin role required)

#### Request Body

| Field         | Type   | Required | Description        |
| ------------- | ------ | -------- | ------------------ |
| `name`        | string | Yes      | Policy name        |
| `description` | string | No       | Policy description |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/admin/policies \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Education Sector",
    "description": "Policy template for educational institutions"
  }'
```

#### Response -- `201 Created`

```json
{
  "id": "pol_sys003",
  "name": "Education Sector",
  "description": "Policy template for educational institutions",
  "is_system": true,
  "rules_count": 0,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |
| `422`  | Validation error    |

### PATCH /api/v1/admin/policies/{policy\_id}

Update a system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

#### Request Body

| Field         | Type   | Description            |
| ------------- | ------ | ---------------------- |
| `name`        | string | New policy name        |
| `description` | string | New policy description |

#### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/admin/policies/pol_sys003 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Education Sector (K-12)"
  }'
```

#### Response -- `200 OK`

```json
{
  "id": "pol_sys003",
  "name": "Education Sector (K-12)",
  "description": "Policy template for educational institutions",
  "is_system": true,
  "rules_count": 0,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |
| `404`  | Policy not found    |
| `422`  | Validation error    |

### DELETE /api/v1/admin/policies/{policy\_id}

Delete a system policy. Automatically cleans `active_policy_id` on any projects using this policy and `default_policy_id` on any users defaulting to it.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

#### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/admin/policies/pol_sys003 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `401`  | Not authenticated   |
| `403`  | Admin role required |
| `404`  | Policy not found    |

## System Policy Rules

Manage rules within system policies. These follow the same request/response format as the standard [Rules](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/security-rules) endpoints.

### GET /api/v1/admin/policies/{policy\_id}/rules

List all rules in a system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}/rules`

**Auth:** Session cookie or Bearer token (admin role required)

#### Example Request

```bash
curl https://app.collieai.io/api/v1/admin/policies/pol_sys001/rules \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

Same format as `GET /api/v1/policies/{policy_id}/rules`. See [Rules](/broken/pages/00b5637d96dfd265be895ee331044894a7a072c0).

### POST /api/v1/admin/policies/{policy\_id}/rules

Create a rule in a system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}/rules`

**Auth:** Session cookie or Bearer token (admin role required)

Same request/response format as `POST /api/v1/policies/{policy_id}/rules`. See [Rules](/broken/pages/00b5637d96dfd265be895ee331044894a7a072c0).

### PATCH /api/v1/admin/policies/{policy\_id}/rules/{rule\_id}

Update a rule in a system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token (admin role required)

Same request/response format as `PATCH /api/v1/policies/{policy_id}/rules/{rule_id}`. See [Rules](/broken/pages/00b5637d96dfd265be895ee331044894a7a072c0).

### DELETE /api/v1/admin/policies/{policy\_id}/rules/{rule\_id}

Delete a rule from a system policy.

**URL:** `https://app.collieai.io/api/v1/admin/policies/{policy_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token (admin role required)

#### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/admin/policies/pol_sys001/rules/rule_sys001 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `403`  | Admin role required      |
| `404`  | Policy or rule not found |

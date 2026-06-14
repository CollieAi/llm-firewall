---
description: >-
  CollieAi Rules API — create, list, update, delete, and test security rules
  within a policy via /api/v1/policies/{policy_id}/rules, with all 10 rule types.
icon: sliders-simple
---

# Rules

Rules define individual checks within a policy. Each rule evaluates input messages, output messages, or both, and determines whether to allow, block, or modify content.

The project-independent endpoints under `/api/v1/policies/{policy_id}/rules` are the recommended approach.

## Rule Properties

| Field              | Type    | Required | Description                                                                                                                                                       |
| ------------------ | ------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `name`             | string  | Yes      | Rule display name                                                                                                                                                 |
| `description`      | string  | No       | Human-readable description                                                                                                                                        |
| `rule_type`        | string  | Yes      | Rule type (see values below). Cannot be changed after creation                                                                                                    |
| `order`            | integer | No       | Evaluation order (lower runs first). Default: 0                                                                                                                   |
| `direction`        | string  | Yes      | When to evaluate: `inbound` (Input), `outbound` (Output), or `all`. The dashboard labels these "Input" / "Output" / "All"; the API field uses the literal values. |
| `decision`         | string  | Yes      | Action on match: `allow`, `mask`, or `block`                                                                                                                      |
| `config`           | object  | Yes      | Rule-type-specific configuration (validated per `rule_type`)                                                                                                      |
| `block_message`    | string  | No       | Custom message returned when the rule blocks a request                                                                                                            |
| `is_enabled`       | boolean | No       | Whether the rule is active. Default: `true`                                                                                                                       |
| `enforcement_mode` | string  | No       | `enforce` (default) or `monitor` (evaluate but never block)                                                                                                       |

### Rule Types

| `rule_type`          | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `regex`              | Match content against regular expression patterns       |
| `aho_corasick`       | Dictionary Match — multi-pattern string matching        |
| `url_filter`         | Detect and filter URLs                                  |
| `structured_id`      | Detect structured identifiers (SSN, credit cards, etc.) |
| `base64_payload`     | Detect base64-encoded payloads                          |
| `normalization`      | Text normalization before evaluation                    |
| `lightweight_model`  | ML-based classification (prompt injection, toxicity)    |
| `llm_detection`      | LLM-based content evaluation                            |
| `language_detection` | Detect and filter by language                           |

## GET /api/v1/policies/{policy\_id}/rules

List all rules in a policy.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

### Example Request

```bash
curl https://app.collieai.io/api/v1/policies/pol_abc123/rules \
  -H "Authorization: Bearer <token>"
```

### Response -- `200 OK`

```json
{
  "rules": [
  {
    "id": "rule_001",
    "name": "SSN Pattern Detection",
    "description": "Detect Social Security Number patterns",
    "rule_type": "regex",
    "order": 1,
    "direction": "all",
    "decision": "block",
    "config": {
      "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    },
    "block_message": "SSN pattern detected in content",
    "is_enabled": true,
    "enforcement_mode": "enforce",
    "created_at": "2025-01-10T08:00:00Z",
    "updated_at": "2025-01-10T08:00:00Z"
  },
  {
    "id": "rule_002",
    "name": "Banned Terms",
    "description": "Block messages containing prohibited terms",
    "rule_type": "aho_corasick",
    "order": 2,
    "direction": "inbound",
    "decision": "block",
    "config": {
      "dictionary_id": "dict_abc123"
    },
    "block_message": null,
    "is_enabled": true,
    "enforcement_mode": "enforce",
    "created_at": "2025-01-10T08:30:00Z",
    "updated_at": "2025-01-12T14:00:00Z"
  }
  ],
  "total": 2
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Policy not found  |

## POST /api/v1/policies/{policy\_id}/rules

Create a new rule in a policy. The `config` object is validated against the specified `rule_type`.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

### Request Body

See [Rule Properties](rules.md#rule-properties) above.

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/policies/pol_abc123/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Regex Filter",
    "rule_type": "regex",
    "direction": "inbound",
    "decision": "block",
    "config": {
      "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
    },
    "block_message": "SSN pattern detected",
    "order": 3
  }'
```

### Response -- `201 Created`

```json
{
  "id": "rule_003",
  "name": "Regex Filter",
  "description": null,
  "rule_type": "regex",
  "order": 3,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
  },
  "block_message": "SSN pattern detected",
  "is_enabled": true,
  "enforcement_mode": "enforce",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Error Responses

| Status | Description                                                |
| ------ | ---------------------------------------------------------- |
| `401`  | Not authenticated                                          |
| `404`  | Policy not found                                           |
| `422`  | Validation error (invalid `rule_type`, bad `config`, etc.) |

## PATCH /api/v1/policies/{policy\_id}/rules/{rule\_id}

Update an existing rule. The `rule_type` field cannot be changed.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |
| `rule_id`   | string | The rule identifier   |

### Request Body

All fields are optional. Only provided fields are updated.

### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/policies/pol_abc123/rules/rule_003 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "is_enabled": false,
    "enforcement_mode": "monitor"
  }'
```

### Response -- `200 OK`

```json
{
  "id": "rule_003",
  "name": "Regex Filter",
  "description": null,
  "rule_type": "regex",
  "order": 3,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
  },
  "block_message": "SSN pattern detected",
  "is_enabled": false,
  "enforcement_mode": "monitor",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `404`  | Policy or rule not found |
| `422`  | Validation error         |

## DELETE /api/v1/policies/{policy\_id}/rules/{rule\_id}

Delete a rule from a policy.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |
| `rule_id`   | string | The rule identifier   |

### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/policies/pol_abc123/rules/rule_003 \
  -H "Authorization: Bearer <token>"
```

### Response -- `204 No Content`

No response body.

### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `404`  | Policy or rule not found |

## POST /api/v1/policies/{policy\_id}/rules/{rule\_id}/test

Test a rule against sample content without affecting live traffic.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules/{rule_id}/test`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |
| `rule_id`   | string | The rule identifier   |

### Request Body

| Field       | Type   | Required | Description                                                        |
| ----------- | ------ | -------- | ------------------------------------------------------------------ |
| `message`   | string | Yes      | The text content to test against the rule                          |
| `direction` | string | No       | Test direction: `inbound` (Input side) or `outbound` (Output side) |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/policies/pol_abc123/rules/rule_001/test \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "My SSN is 123-45-6789",
    "direction": "inbound"
  }'
```

### Response -- `200 OK`

```json
{
  "matched": true,
  "decision": "block",
  "modified_message": null,
  "match_info": {
    "matches": [
      {
        "value": "123-45-6789",
        "start": 10,
        "end": 21
      }
    ]
  }
}
```

### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `404`  | Policy or rule not found |
| `422`  | Validation error         |

## Project-Scoped Endpoints

All rule endpoints are also available under a project scope. Behavior is identical.

| Project-Independent                            | Project-Scoped                                               |
| ---------------------------------------------- | ------------------------------------------------------------ |
| `GET /api/v1/policies/{pid}/rules`             | `GET /api/v1/projects/{id}/policies/{pid}/rules`             |
| `POST /api/v1/policies/{pid}/rules`            | `POST /api/v1/projects/{id}/policies/{pid}/rules`            |
| `PATCH /api/v1/policies/{pid}/rules/{rid}`     | `PATCH /api/v1/projects/{id}/policies/{pid}/rules/{rid}`     |
| `DELETE /api/v1/policies/{pid}/rules/{rid}`    | `DELETE /api/v1/projects/{id}/policies/{pid}/rules/{rid}`    |
| `POST /api/v1/policies/{pid}/rules/{rid}/test` | `POST /api/v1/projects/{id}/policies/{pid}/rules/{rid}/test` |

## Legacy Endpoints

These operate on the active policy of a project. Maintained for backward compatibility.

| Method | Path                                                 | Description                    |
| ------ | ---------------------------------------------------- | ------------------------------ |
| GET    | `/api/v1/projects/{project_id}/rules`                | List rules in active policy    |
| POST   | `/api/v1/projects/{project_id}/rules`                | Create rule in active policy   |
| PATCH  | `/api/v1/projects/{project_id}/rules/{rule_id}`      | Update rule in active policy   |
| DELETE | `/api/v1/projects/{project_id}/rules/{rule_id}`      | Delete rule from active policy |
| POST   | `/api/v1/projects/{project_id}/rules/{rule_id}/test` | Test rule in active policy     |

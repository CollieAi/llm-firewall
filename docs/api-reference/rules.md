---
description: >-
  CollieAi Rules API — create, list, update, delete, and test security rules
  within a policy via /api/v1/policies/{policy_id}/rules, with all 12 rule types.
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
| `order`            | integer | No       | Evaluation order (lower runs first). Default: `5`                                                                                                                 |
| `direction`        | string  | No       | When to evaluate: `inbound` (Input), `outbound` (Output), or `all`. Default: `all`. The dashboard labels these "Input" / "Output" / "All"; the API field uses the literal values. `qwen3guard_stream` accepts only `outbound`. |
| `decision`         | string  | Yes      | Action on match: `allow`, `mask`, or `block`. `url_reputation` and `tool_access` accept only `block`.                                                             |
| `config`           | object  | Yes      | Rule-type-specific configuration (validated per `rule_type`)                                                                                                      |
| `block_message`    | string  | No       | Custom message returned when the rule blocks a request. Default: `Message blocked by security policy`                                                             |
| `is_enabled`       | boolean | No       | Whether the rule is active. Default: `true`                                                                                                                       |
| `enforcement_mode` | string  | No       | `inherit` (default — follow the policy's mode), `enforce`, or `monitor` (evaluate but never block)                                                                |
| `targeting`        | object  | No       | Where the rule applies. Omitted or `null`: chat and API messages only. See [Targeting](rules.md#targeting)                                                        |

### Rule Types

| `rule_type`          | Description                                             |
| -------------------- | ------------------------------------------------------- |
| `regex`              | Match content against regular expression patterns       |
| `aho_corasick`       | Dictionary Match — multi-pattern string matching        |
| `url_filter`         | Detect and filter URLs                                  |
| `url_reputation`     | Block URLs listed in a threat-intelligence feed         |
| `structured_id`      | Detect structured identifiers (SSN, credit cards, etc.) |
| `base64_payload`     | Detect base64-encoded payloads                          |
| `normalization`      | Text normalization before evaluation                    |
| `lightweight_model`  | ML-based classification (prompt injection, toxicity)    |
| `llm_detection`      | LLM-based content evaluation                            |
| `language_detection` | Detect and filter by language                           |
| `qwen3guard_stream`  | Streaming guard — safety check of model output (Output only) |
| `tool_access`        | Allow or deny MCP tool calls by server and tool name    |

### Targeting

A rule without `targeting` checks chat and API messages — every rule created before targeting existed works this way. Rules never apply to tool calls through the MCP gateway unless their `targeting` says so.

| Field        | Type             | Description                                                                                                           |
| ------------ | ---------------- | --------------------------------------------------------------------------------------------------------------------- |
| `surfaces`   | array of strings | Required. `message` (chat and API messages), `mcp` (tool calls through the MCP gateway), or both                       |
| `stages`     | array of strings | `mcp` only. `pre` (tool arguments), `post` (tool results), `catalog` (a server's tool list). Default: `pre` and `post` |
| `server_ids` | array of strings | `mcp` only. Apply to these MCP servers only                                                                           |
| `tool_names` | array of strings | `mcp` only. Apply to these tools only                                                                                 |
| `registry`   | object           | `mcp` only. Match tools by their registry properties: `mutating`, `destructive`, `open_world`, `confirmation_expected` (each `true` or `false`) |
| `principal`  | object           | `mcp` only. Match the caller: `roles_any`, `user_ids`, `company_ids`                                                  |

All selectors must match; a selector you leave out matches anything. A message-only rule may not carry `stages` or selectors.

* `tool_access` must target exactly the `mcp` surface and the `pre` stage (its default), with `direction` `inbound` or `all` and `decision` `block`. Its `config` is `mode` (`allowlist` or `blocklist`) and `tools`, a list of `{"tool_name": ..., "server_id": ...}`; without `server_id` the entry matches that tool on any server.
* `url_reputation` runs on messages only; `mcp` targeting is refused.
* A rule with the `catalog` stage must have `direction` `inbound` or `all`.
* A detector that fails open — `decision_on_error: "allow"`, set or by default, and always `qwen3guard_stream` — may not target tools that can change data, delete or reach outside systems. Set `decision_on_error: "block"` where the rule type has it, or confine the rule with `registry` `mutating`, `destructive` and `open_world` all `false`.

{% hint style="info" %}
The MCP gateway currently evaluates every MCP rule in Monitor: it reports what a rule would block and does not block the call (`coverage.forced_monitor: true` in its response).
{% endhint %}

## GET /api/v1/policies/{policy\_id}/rules

List all rules in a policy.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |

### Query Parameters

| Parameter      | Type    | Description                                     |
| -------------- | ------- | ----------------------------------------------- |
| `enabled_only` | boolean | Return only enabled rules. Default: `false`      |

Rules come back in evaluation order: by `order`, then by creation time.

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
        "patterns": [
          {
            "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
            "replacement": null,
            "flags": 0
          }
        ],
        "mask_char": "*",
        "streaming_window_chars": null,
        "allowlist": null
      },
      "block_message": "SSN pattern detected in content",
      "is_enabled": true,
      "enforcement_mode": "enforce",
      "targeting": null,
      "project_id": null,
      "policy_id": "pol_abc123",
      "triggered_count": 14,
      "last_triggered_at": "2025-01-14T16:20:00Z",
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
        "dictionary_id": "7d0c6a3e-2b1f-4c8e-9a51-3f2d8e6b4c10",
        "dictionary_group_id": null,
        "languages": null,
        "always_include_english": false,
        "replacement": null,
        "mask_char": "*",
        "whole_word": true,
        "case_sensitive": false,
        "match_mode": "substring",
        "window_size": 10
      },
      "block_message": "Message blocked by security policy",
      "is_enabled": true,
      "enforcement_mode": "inherit",
      "targeting": null,
      "project_id": null,
      "policy_id": "pol_abc123",
      "triggered_count": 0,
      "last_triggered_at": null,
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

## GET /api/v1/policies/{policy\_id}/rules/{rule\_id}

Get one rule. Works for your own policies and for system policies.

**URL:** `https://app.collieai.io/api/v1/policies/{policy_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter   | Type   | Description           |
| ----------- | ------ | --------------------- |
| `policy_id` | string | The policy identifier |
| `rule_id`   | string | The rule identifier   |

### Example Request

```bash
curl https://app.collieai.io/api/v1/policies/pol_abc123/rules/rule_001 \
  -H "Authorization: Bearer <token>"
```

### Response -- `200 OK`

```json
{
  "id": "rule_001",
  "name": "SSN Pattern Detection",
  "description": "Detect Social Security Number patterns",
  "rule_type": "regex",
  "order": 1,
  "direction": "all",
  "decision": "block",
  "config": {
    "patterns": [
      {
        "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "replacement": null,
        "flags": 0
      }
    ],
    "mask_char": "*",
    "streaming_window_chars": null,
    "allowlist": null
  },
  "block_message": "SSN pattern detected in content",
  "is_enabled": true,
  "enforcement_mode": "enforce",
  "targeting": null,
  "project_id": null,
  "policy_id": "pol_abc123",
  "triggered_count": 14,
  "last_triggered_at": "2025-01-14T16:20:00Z",
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-10T08:00:00Z"
}
```

### Error Responses

| Status | Description                                         |
| ------ | --------------------------------------------------- |
| `401`  | Not authenticated                                   |
| `404`  | Policy not found, or the rule is not in this policy |

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
        "patterns": [
          {
            "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b"
          }
        ]
      },
      "block_message": "SSN pattern detected",
      "order": 3
    }'
```

### Response -- `201 Created`

The response is the rule as stored: `config` is normalized, with every field the rule type accepts, and fields you left out carry their defaults (`enforcement_mode` is `inherit`).

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
    "patterns": [
      {
        "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "replacement": null,
        "flags": 0
      }
    ],
    "mask_char": "*",
    "streaming_window_chars": null,
    "allowlist": null
  },
  "block_message": "SSN pattern detected",
  "is_enabled": true,
  "enforcement_mode": "inherit",
  "targeting": null,
  "project_id": null,
  "policy_id": "pol_abc123",
  "triggered_count": 0,
  "last_triggered_at": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Error Responses

| Status | Description                                                |
| ------ | ---------------------------------------------------------- |
| `401`  | Not authenticated                                          |
| `403`  | The policy is a system policy and cannot be changed        |
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

All fields are optional. Only provided fields are updated. Send `"targeting": null` to make the rule message-only again.

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
    "patterns": [
      {
        "pattern": "\\b\\d{3}-\\d{2}-\\d{4}\\b",
        "replacement": null,
        "flags": 0
      }
    ],
    "mask_char": "*",
    "streaming_window_chars": null,
    "allowlist": null
  },
  "block_message": "SSN pattern detected",
  "is_enabled": false,
  "enforcement_mode": "monitor",
  "targeting": null,
  "project_id": null,
  "policy_id": "pol_abc123",
  "triggered_count": 0,
  "last_triggered_at": null,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `403`  | System policy — cannot be changed |
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
| `403`  | System policy — cannot be changed |
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
| `direction` | string | Yes      | Test direction: `inbound` (Input side) or `outbound` (Output side) |

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
  },
  "enforcement_mode": "enforce",
  "no_enforce_reason": null
}
```

`enforcement_mode` says what the rule would actually do under its policy and this deployment: `enforce` or `monitor`. When it would not enforce, `no_enforce_reason` says why — the policy's or the rule's own Monitor mode, a deployment that restricts the rule's source to Monitor (`source_monitor_only`), or a decision the rule type does not support. Both are `null` when nothing matched.

### Error Responses

| Status | Description              |
| ------ | ------------------------ |
| `401`  | Not authenticated        |
| `403`  | System policy — cannot be changed |
| `404`  | Policy or rule not found |
| `422`  | Validation error         |

## Project-Scoped Endpoints

All rule endpoints are also available under a project scope. Behavior is identical.

| Project-Independent                            | Project-Scoped                                               |
| ---------------------------------------------- | ------------------------------------------------------------ |
| `GET /api/v1/policies/{pid}/rules`             | `GET /api/v1/projects/{id}/policies/{pid}/rules`             |
| `GET /api/v1/policies/{pid}/rules/{rid}`       | `GET /api/v1/projects/{id}/policies/{pid}/rules/{rid}`       |
| `POST /api/v1/policies/{pid}/rules`            | `POST /api/v1/projects/{id}/policies/{pid}/rules`            |
| `PATCH /api/v1/policies/{pid}/rules/{rid}`     | `PATCH /api/v1/projects/{id}/policies/{pid}/rules/{rid}`     |
| `DELETE /api/v1/policies/{pid}/rules/{rid}`    | `DELETE /api/v1/projects/{id}/policies/{pid}/rules/{rid}`    |
| `POST /api/v1/policies/{pid}/rules/{rid}/test` | `POST /api/v1/projects/{id}/policies/{pid}/rules/{rid}/test` |

## Legacy Endpoints

These operate on the active policy of a project. Maintained for backward compatibility.

| Method | Path                                                 | Description                    |
| ------ | ---------------------------------------------------- | ------------------------------ |
| GET    | `/api/v1/projects/{project_id}/rules`                | List rules in active policy    |
| GET    | `/api/v1/projects/{project_id}/rules/{rule_id}`      | Get rule in active policy      |
| POST   | `/api/v1/projects/{project_id}/rules`                | Create rule in active policy   |
| PATCH  | `/api/v1/projects/{project_id}/rules/{rule_id}`      | Update rule in active policy   |
| DELETE | `/api/v1/projects/{project_id}/rules/{rule_id}`      | Delete rule from active policy |
| POST   | `/api/v1/projects/{project_id}/rules/{rule_id}/test` | Test rule in active policy     |

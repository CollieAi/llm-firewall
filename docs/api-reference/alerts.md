---
description: >-
  CollieAi Alerts API — create, list, update, and delete alert rules and
  acknowledge alert events for a project via
  /api/v1/alerts/projects/{project_id}.
icon: siren-on
---

# Alerts

Automated monitoring for projects. Define alert rules that trigger events when metrics exceed thresholds, then track and acknowledge events.

## Alert Rules

### POST /api/v1/alerts/projects/{project\_id}/rules

Create an alert rule for a project.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/rules`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

#### Request Body

| Field              | Type    | Required | Description                                                                    |
| ------------------ | ------- | -------- | ------------------------------------------------------------------------------ |
| `name`             | string  | Yes      | Alert rule name                                                                |
| `description`      | string  | No       | Alert rule description                                                         |
| `metric`           | string  | Yes      | Metric to monitor (`block_rate`, `error_rate`, `latency_p99`, `request_count`) |
| `operator`         | string  | Yes      | Comparison operator: `gt`, `gte`, `lt`, `lte`, `eq`                            |
| `threshold`        | number  | Yes      | Threshold value that triggers the alert                                        |
| `time_window`      | integer | Yes      | Evaluation window in minutes                                                   |
| `cooldown_minutes` | integer | No       | Minimum minutes between repeated alerts. Default: 60                           |
| `is_enabled`       | boolean | No       | Whether the rule is active. Default: `true`                                    |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Block Rate",
    "description": "Alert when block rate exceeds 25%",
    "metric": "block_rate",
    "operator": "gt",
    "threshold": 0.25,
    "time_window": 15,
    "cooldown_minutes": 30
  }'
```

#### Response -- `201 Created`

```json
{
  "id": "alert_rule_abc123",
  "name": "High Block Rate",
  "description": "Alert when block rate exceeds 25%",
  "metric": "block_rate",
  "operator": "gt",
  "threshold": 0.25,
  "time_window": 15,
  "cooldown_minutes": 30,
  "is_enabled": true,
  "project_id": "proj_abc123",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |
| `422`  | Validation error  |

### GET /api/v1/alerts/projects/{project\_id}/rules

List all alert rules for a project.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/rules`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

#### Example Request

```bash
curl https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
[
  {
    "id": "alert_rule_abc123",
    "name": "High Block Rate",
    "description": "Alert when block rate exceeds 25%",
    "metric": "block_rate",
    "operator": "gt",
    "threshold": 0.25,
    "time_window": 15,
    "cooldown_minutes": 30,
    "is_enabled": true,
    "project_id": "proj_abc123",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  }
]
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

### PATCH /api/v1/alerts/projects/{project\_id}/rules/{rule\_id}

Update an alert rule. All fields are optional.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description               |
| ------------ | ------ | ------------------------- |
| `project_id` | string | The project identifier    |
| `rule_id`    | string | The alert rule identifier |

#### Request Body

| Field              | Type    | Description                    |
| ------------------ | ------- | ------------------------------ |
| `name`             | string  | New rule name                  |
| `description`      | string  | New rule description           |
| `metric`           | string  | Updated metric                 |
| `operator`         | string  | Updated operator               |
| `threshold`        | number  | Updated threshold              |
| `time_window`      | integer | Updated time window in minutes |
| `cooldown_minutes` | integer | Updated cooldown               |
| `is_enabled`       | boolean | Enable or disable the rule     |

#### Example Request

```bash
curl -X PATCH https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules/alert_rule_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "threshold": 0.30,
    "is_enabled": false
  }'
```

#### Response -- `200 OK`

```json
{
  "id": "alert_rule_abc123",
  "name": "High Block Rate",
  "description": "Alert when block rate exceeds 25%",
  "metric": "block_rate",
  "operator": "gt",
  "threshold": 0.30,
  "time_window": 15,
  "cooldown_minutes": 30,
  "is_enabled": false,
  "project_id": "proj_abc123",
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

#### Error Responses

| Status | Description                     |
| ------ | ------------------------------- |
| `401`  | Not authenticated               |
| `404`  | Project or alert rule not found |
| `422`  | Validation error                |

### DELETE /api/v1/alerts/projects/{project\_id}/rules/{rule\_id}

Delete an alert rule. Previously generated events are preserved.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/rules/{rule_id}`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description               |
| ------------ | ------ | ------------------------- |
| `project_id` | string | The project identifier    |
| `rule_id`    | string | The alert rule identifier |

#### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules/alert_rule_abc123 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description                     |
| ------ | ------------------------------- |
| `401`  | Not authenticated               |
| `404`  | Project or alert rule not found |

## Alert Events

### GET /api/v1/alerts/projects/{project\_id}/events

List alert events for a project, ordered newest first.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/events`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

#### Query Parameters

| Parameter | Type    | Required | Description                             |
| --------- | ------- | -------- | --------------------------------------- |
| `limit`   | integer | No       | Number of events to return. Default: 20 |
| `offset`  | integer | No       | Number of events to skip. Default: 0    |

#### Example Request

```bash
curl "https://app.collieai.io/api/v1/alerts/projects/proj_abc123/events?limit=10&offset=0" \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "events": [
    {
      "id": "evt_abc123",
      "alert_rule_id": "alert_rule_abc123",
      "alert_rule_name": "High Block Rate",
      "metric": "block_rate",
      "metric_value": 0.32,
      "threshold": 0.25,
      "operator": "gt",
      "is_acknowledged": false,
      "triggered_at": "2025-01-15T10:15:00Z",
      "acknowledged_at": null
    }
  ],
  "total": 24,
  "unread_count": 5
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

### POST /api/v1/alerts/projects/{project\_id}/events/{event\_id}/acknowledge

Acknowledge a single alert event.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/events/{event_id}/acknowledge`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description                |
| ------------ | ------ | -------------------------- |
| `project_id` | string | The project identifier     |
| `event_id`   | string | The alert event identifier |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/alerts/projects/proj_abc123/events/evt_abc123/acknowledge \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "id": "evt_abc123",
  "is_acknowledged": true,
  "acknowledged_at": "2025-01-15T10:20:00Z"
}
```

#### Error Responses

| Status | Description                |
| ------ | -------------------------- |
| `401`  | Not authenticated          |
| `404`  | Project or event not found |

### POST /api/v1/alerts/projects/{project\_id}/events/acknowledge-all

Acknowledge all unread alert events for a project.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/events/acknowledge-all`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/alerts/projects/proj_abc123/events/acknowledge-all \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "acknowledged_count": 5
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

### GET /api/v1/alerts/projects/{project\_id}/unread-count

Get the count of unacknowledged alert events.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/unread-count`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter    | Type   | Description            |
| ------------ | ------ | ---------------------- |
| `project_id` | string | The project identifier |

#### Example Request

```bash
curl https://app.collieai.io/api/v1/alerts/projects/proj_abc123/unread-count \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "unread_count": 3
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `404`  | Project not found |

---
description: >-
  CollieAi Alerts API — create, list, update, and delete alert rules and
  acknowledge alert events for a project via
  /api/v1/alerts/projects/{project_id}.
icon: siren-on
---

# Alerts

Automated monitoring for projects. Define alert rules that fire events when a metric crosses a threshold over a time window, then track and acknowledge those events in the dashboard.

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

| Field              | Type    | Required | Description                                                                                       |
| ------------------ | ------- | -------- | ------------------------------------------------------------------------------------------------- |
| `name`             | string  | Yes      | Alert rule name (1–255 chars)                                                                     |
| `description`      | string  | No       | Alert rule description                                                                            |
| `metric`           | string  | Yes      | Metric to monitor: `blocked_rate`, `error_rate`, `latency_p95`, `rule_triggers`, `total_requests` |
| `operator`         | string  | Yes      | Comparison operator: `>`, `<`, `>=`, `<=`                                                         |
| `threshold`        | number  | Yes      | Threshold value that triggers the alert (≥ 0)                                                     |
| `time_window`      | string  | Yes      | Evaluation window: `5m`, `15m`, or `1h`                                                           |
| `cooldown_minutes` | integer | No       | Minimum minutes between repeated alerts (1–1440). Default: 60                                     |
| `is_enabled`       | boolean | No       | Whether the rule is active. Default: `true`                                                       |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High Block Rate",
    "description": "Alert when block rate exceeds 25%",
    "metric": "blocked_rate",
    "operator": ">",
    "threshold": 0.25,
    "time_window": "15m",
    "cooldown_minutes": 30
  }'
```

#### Response -- `201 Created`

```json
{
  "id": "alert_rule_abc123",
  "project_id": "proj_abc123",
  "name": "High Block Rate",
  "description": "Alert when block rate exceeds 25%",
  "metric": "blocked_rate",
  "operator": ">",
  "threshold": 0.25,
  "time_window": "15m",
  "cooldown_minutes": 30,
  "is_enabled": true,
  "last_triggered_at": null,
  "last_value": null,
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

#### Example Request

```bash
curl https://app.collieai.io/api/v1/alerts/projects/proj_abc123/rules \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "alert_rules": [
    {
      "id": "alert_rule_abc123",
      "project_id": "proj_abc123",
      "name": "High Block Rate",
      "description": "Alert when block rate exceeds 25%",
      "metric": "blocked_rate",
      "operator": ">",
      "threshold": 0.25,
      "time_window": "15m",
      "cooldown_minutes": 30,
      "is_enabled": true,
      "last_triggered_at": null,
      "last_value": null,
      "created_at": "2025-01-15T10:00:00Z",
      "updated_at": "2025-01-15T10:00:00Z"
    }
  ],
  "total": 1
}
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

#### Request Body

| Field              | Type    | Description                              |
| ------------------ | ------- | ---------------------------------------- |
| `name`             | string  | New rule name                            |
| `description`      | string  | New rule description                     |
| `metric`           | string  | Updated metric                           |
| `operator`         | string  | Updated operator                         |
| `threshold`        | number  | Updated threshold                        |
| `time_window`      | string  | Updated window (`5m`, `15m`, `1h`)       |
| `cooldown_minutes` | integer | Updated cooldown (1–1440)                |
| `is_enabled`       | boolean | Enable or disable the rule               |

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

Returns the updated alert rule (same shape as the create response).

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

#### Response -- `204 No Content`

No response body.

#### Error Responses

| Status | Description                     |
| ------ | ------------------------------- |
| `401`  | Not authenticated               |
| `404`  | Project or alert rule not found |

## Alert Events

When a rule's condition is met, CollieAi records an **alert event**. Events are surfaced in the dashboard (there is no email/webhook push); poll these endpoints or the unread count to react to them.

### GET /api/v1/alerts/projects/{project\_id}/events

List alert events for a project, newest first.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/events`

**Auth:** Session cookie or Bearer token

#### Query Parameters

| Parameter | Type    | Required | Description                             |
| --------- | ------- | -------- | --------------------------------------- |
| `limit`   | integer | No       | Number of events to return. Default: 50 |
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
      "project_id": "proj_abc123",
      "alert_rule_name": "High Block Rate",
      "metric": "blocked_rate",
      "operator": ">",
      "threshold": 0.25,
      "actual_value": 0.32,
      "time_window": "15m",
      "is_read": false,
      "acknowledged_at": null,
      "created_at": "2025-01-15T10:15:00Z"
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

Acknowledge (mark read) a single alert event.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/events/{event_id}/acknowledge`

**Auth:** Session cookie or Bearer token

#### Response -- `200 OK`

```json
{
  "id": "evt_abc123",
  "is_read": true,
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

#### Response -- `200 OK`

```json
{
  "acknowledged_count": 5
}
```

### GET /api/v1/alerts/projects/{project\_id}/unread-count

Get the count of unread alert events.

**URL:** `https://app.collieai.io/api/v1/alerts/projects/{project_id}/unread-count`

**Auth:** Session cookie or Bearer token

#### Response -- `200 OK`

```json
{
  "unread_count": 3
}
```

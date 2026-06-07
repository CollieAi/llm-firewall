---
description: >-
  CollieAi Support Tickets API — create tickets, list and view them, add
  messages and attachments, and admin endpoints for managing all tickets via
  /api/v1/support and /api/v1/admin/tickets.
icon: message
---

# Support tickets

## User Endpoints

### POST /api/v1/support/tickets

Create a new support ticket.

**Auth:** Bearer token (session cookie or JWT)

**Content-Type:** `multipart/form-data`

| Field     | Type    | Required | Description                                                               |
| --------- | ------- | -------- | ------------------------------------------------------------------------- |
| `subject` | string  | Yes      | Ticket subject (1--255 characters)                                        |
| `message` | string  | Yes      | Initial message body (1--5,000 characters)                                |
| `files`   | file\[] | No       | Screenshot attachments (PNG, JPG, JPEG, WebP; max 5 MB each; max 3 files) |

#### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/support/tickets \
  -H "Authorization: Bearer <token>" \
  -F "subject=Cannot create API key" \
  -F "message=I get a 500 error when clicking Create Key." \
  -F "files=@screenshot.png"
```

#### Response -- `201 Created`

```json
{
  "id": "a1b2c3d4-...",
  "user_id": "user-123",
  "user_name": "Jane Doe",
  "user_email": "jane@example.com",
  "subject": "Cannot create API key",
  "status": "open",
  "priority": "normal",
  "message_count": 1,
  "last_message_at": "2026-04-08T12:00:00Z",
  "created_at": "2026-04-08T12:00:00Z",
  "updated_at": "2026-04-08T12:00:00Z",
  "messages": [
    {
      "id": "msg-1",
      "ticket_id": "a1b2c3d4-...",
      "sender_id": "user-123",
      "sender_type": "user",
      "sender_name": "Jane Doe",
      "sender_email": "jane@example.com",
      "body": "I get a 500 error when clicking Create Key.",
      "attachments": [
        {
          "filename": "ab12cd34_screenshot.png",
          "original_name": "screenshot.png",
          "size": 245760,
          "content_type": "image/png"
        }
      ],
      "created_at": "2026-04-08T12:00:00Z"
    }
  ]
}
```

***

### GET /api/v1/support/tickets

List the authenticated user's tickets.

**Auth:** Bearer token

| Parameter   | Type    | Default | Description                                                    |
| ----------- | ------- | ------- | -------------------------------------------------------------- |
| `page`      | integer | 1       | Page number                                                    |
| `page_size` | integer | 20      | Tickets per page (max 100)                                     |
| `status`    | string  | --      | Filter by status (`open`, `in_progress`, `resolved`, `closed`) |

#### Response -- `200 OK`

```json
{
  "tickets": [
    {
      "id": "a1b2c3d4-...",
      "user_id": "user-123",
      "subject": "Cannot create API key",
      "status": "open",
      "priority": "normal",
      "message_count": 3,
      "last_message_at": "2026-04-08T14:30:00Z",
      "created_at": "2026-04-08T12:00:00Z",
      "updated_at": "2026-04-08T14:30:00Z"
    }
  ],
  "total": 1
}
```

***

### GET /api/v1/support/tickets/{ticket\_id}

Get a ticket with all messages. The user must own the ticket.

**Auth:** Bearer token

#### Response -- `200 OK`

Returns the same shape as the create response, with all messages included.

***

### POST /api/v1/support/tickets/{ticket\_id}/messages

Add a message to an existing ticket. The user must own the ticket. Cannot add messages to closed tickets.

**Auth:** Bearer token

**Content-Type:** `multipart/form-data`

| Field   | Type    | Required | Description                                             |
| ------- | ------- | -------- | ------------------------------------------------------- |
| `body`  | string  | Yes      | Message text (1--5,000 characters)                      |
| `files` | file\[] | No       | Screenshot attachments (same limits as ticket creation) |

#### Response -- `201 Created`

Returns the new message object.

***

### GET /api/v1/support/tickets/{ticket\_id}/attachments/{message\_id}/{filename}

Download a ticket attachment. The user must own the ticket or be an admin.

**Auth:** Bearer token

#### Response -- `200 OK`

Returns the file with the appropriate content type.

***

## Admin Endpoints

All admin endpoints require the `admin` role. Non-admins receive `403 Forbidden`.

### GET /api/v1/admin/tickets

List all tickets across all users. See [Managing Tickets (Admin)](../support/managing-tickets.md) for query parameters.

### GET /api/v1/admin/tickets/{ticket\_id}

Get any ticket with all messages.

### PATCH /api/v1/admin/tickets/{ticket\_id}

Update ticket status and/or priority.

```json
{
  "status": "resolved",
  "priority": "high"
}
```

### POST /api/v1/admin/tickets/{ticket\_id}/messages

Admin reply. Same format as the user message endpoint. Auto-transitions open tickets to in progress.

***

## Error Responses

| Status | Condition                                                                 |
| ------ | ------------------------------------------------------------------------- |
| `400`  | Ticket is closed, invalid file type, file too large, too many attachments |
| `401`  | Missing or invalid authentication                                         |
| `403`  | Non-admin accessing admin endpoints                                       |
| `404`  | Ticket not found or not owned by the user                                 |
| `422`  | Invalid status or priority value                                          |

---
description: >-
  How CollieAi admins manage support tickets — view, filter, reply to, and
  update the status and priority of all user tickets from the admin panel or via
  the admin API.
icon: message-plus
---

# Managing tickets (admin)

Admins can view and respond to all support tickets across all users. Access the ticket management page from **Admin > Support Tickets**.

***

## Ticket List

The admin ticket list shows all tickets with the following columns:

| Column            | Description                                       |
| ----------------- | ------------------------------------------------- |
| **Subject**       | Ticket subject line                               |
| **User**          | Name and email of the user who created the ticket |
| **Status**        | Current status (editable from the detail view)    |
| **Priority**      | Current priority (editable from the detail view)  |
| **Messages**      | Total message count                               |
| **Last Activity** | Time since the last message                       |

### Filtering

Use the toolbar at the top to filter tickets:

* **Search** -- filter by subject, user name, or email
* **Status** -- show only tickets with a specific status
* **Priority** -- show only tickets with a specific priority

Click any row to open the ticket detail view.

## Ticket Detail View

The detail view shows the full message thread and allows admins to reply and manage the ticket.

### Changing Status

Use the **Status** dropdown in the ticket header to update the status. Available transitions:

* **Open** -- ticket has not been addressed yet
* **In Progress** -- the team is actively working on it
* **Resolved** -- the issue has been addressed
* **Closed** -- the conversation is finished (no more messages can be added)

When an admin sends the first reply to an **Open** ticket, the status automatically transitions to **In Progress**.

### Changing Priority

Use the **Priority** dropdown in the ticket header to set the priority:

* **Low**, **Normal**, **High**, or **Urgent**

### Replying

Type a response in the text area at the bottom of the thread and click **Send Reply**. You can attach up to 3 screenshots per message (same limits as user attachments).

When you reply, the user receives an email notification with the response text and a link to the ticket in their dashboard.

Admins cannot reply to **Closed** tickets. Change the status first if the conversation needs to be reopened.

## API Reference

All endpoints require admin authentication. Non-admins receive `403 Forbidden`.

### List all tickets

```
GET /api/v1/admin/tickets?page=1&page_size=20&status=open&priority=high&search=login
```

| Parameter   | Type    | Default | Description                         |
| ----------- | ------- | ------- | ----------------------------------- |
| `page`      | integer | 1       | Page number                         |
| `page_size` | integer | 20      | Tickets per page (max 100)          |
| `status`    | string  | --      | Filter by status                    |
| `priority`  | string  | --      | Filter by priority                  |
| `search`    | string  | --      | Search subject, user name, or email |

### Get ticket detail

```
GET /api/v1/admin/tickets/{ticket_id}
```

Returns the ticket with all messages and sender information.

### Update ticket

```
PATCH /api/v1/admin/tickets/{ticket_id}
```

```json
{
  "status": "in_progress",
  "priority": "high"
}
```

Both fields are optional.

### Reply to ticket

```
POST /api/v1/admin/tickets/{ticket_id}/messages
```

Multipart form data:

| Field   | Type    | Required | Description                                               |
| ------- | ------- | -------- | --------------------------------------------------------- |
| `body`  | string  | Yes      | Reply text (max 5,000 characters)                         |
| `files` | file\[] | No       | Up to 3 image attachments (PNG, JPG, WebP, max 5 MB each) |

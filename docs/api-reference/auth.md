---
description: >-
  CollieAi authentication API reference — endpoints for email/password login
  with the emailed sign-in code, Google OAuth login, password management,
  session info, IP allowlist, and logout.
icon: fingerprint
---

# Auth

Authentication endpoints for login, logout, password management, and OAuth.

***

## GET /auth/login

Render the login page with email/password form and Google OAuth button.

**URL:** `https://app.collieai.io/auth/login`

**Auth:** None

### Response — `200 OK`

Returns HTML login page.

***

## POST /auth/email/login

Authenticate with email and password. On `app.collieai.io` a correct password
opens no session yet: CollieAi emails a 6-digit code and the sign-in finishes
with [POST /auth/email/code](#post-auth-email-code). A deployment with the
sign-in code turned off sets the session cookie here.

**URL:** `https://app.collieai.io/auth/email/login`

**Auth:** None

**Rate Limits** (failed attempts):

* 10 per minute per IP address
* 5 per minute per email address

### Request Body

| Field      | Type   | Required | Description        |
| ---------- | ------ | -------- | ------------------ |
| `email`    | string | Yes      | User email address |
| `password` | string | Yes      | User password      |

### Example Request

```bash
curl -X POST https://app.collieai.io/auth/email/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

### Response — `200 OK`, code required

```json
{
  "code_required": true,
  "challenge": "k3Vq9wX1pZ7tR2mN8bL5cH4dF6gJ0sYe"
}
```

The code goes to the user's email. Pass `challenge` with the code to
`POST /auth/email/code`.

### Response — `200 OK`, signed in

Where the sign-in code is turned off:

```json
{
  "message": "Login successful",
  "redirect": "/app/"
}
```

Sets the `auth_token` session cookie (7 days).

### Error Responses

| Status | Description                                                         |
| ------ | ------------------------------------------------------------------- |
| `401`  | Invalid email or password                                           |
| `422`  | Validation error                                                    |
| `429`  | Rate limit exceeded, or 10 sign-in codes this hour for this account |

***

## POST /auth/email/code

Finish a password sign-in with the code from the email. Sets the session
cookie.

**URL:** `https://app.collieai.io/auth/email/code`

**Auth:** None

A code works for 10 minutes, once. Five wrong codes end the sign-in: start
again with `POST /auth/email/login`.

### Request Body

| Field       | Type   | Required | Description                                   |
| ----------- | ------ | -------- | --------------------------------------------- |
| `challenge` | string | Yes      | `challenge` from `POST /auth/email/login`     |
| `code`      | string | Yes      | The 6-digit code from the email               |

### Example Request

```bash
curl -X POST https://app.collieai.io/auth/email/code \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "challenge": "k3Vq9wX1pZ7tR2mN8bL5cH4dF6gJ0sYe",
    "code": "123456"
  }'
```

### Response — `200 OK`

```json
{
  "message": "Login successful",
  "redirect": "/app/"
}
```

Sets the `auth_token` session cookie (7 days).

### Error Responses

| Status | `error.code`         | Description                                                    |
| ------ | -------------------- | -------------------------------------------------------------- |
| `400`  | `wrong_code`         | Wrong code; the message says how many attempts are left        |
| `400`  | `too_many_attempts`  | Fifth wrong code; the sign-in is over, log in again            |
| `400`  | `code_expired`       | The code expired or was already used; log in again             |
| `404`  | —                    | The sign-in code is turned off on this deployment              |
| `429`  | —                    | More than 20 requests per minute from one IP address           |

***

## POST /auth/email/code/resend

Email a new code for the same sign-in. The previous code stops working.

**URL:** `https://app.collieai.io/auth/email/code/resend`

**Auth:** None

Once a minute, up to five codes per sign-in, and at most 10 codes per hour
for one account (first codes and new ones together). A new code works for
10 minutes.

### Request Body

| Field       | Type   | Required | Description                               |
| ----------- | ------ | -------- | ----------------------------------------- |
| `challenge` | string | Yes      | `challenge` from `POST /auth/email/login` |

### Response — `200 OK`

```json
{
  "message": "We sent a new code."
}
```

### Error Responses

| Status | Description                                                            |
| ------ | ---------------------------------------------------------------------- |
| `400`  | The sign-in expired (`error.code` = `code_expired`); log in again      |
| `404`  | The sign-in code is turned off on this deployment                      |
| `429`  | Less than a minute since the last code, five codes already sent for this sign-in, or 10 codes this hour for the account |

***

## POST /auth/set-password

Set or change the password for the authenticated user. Use this to set an initial password for OAuth-only users or to change an existing password.

**URL:** `https://app.collieai.io/auth/set-password`

**Auth:** Session cookie or Bearer token

### Request Body

| Field      | Type   | Required | Description                                                                  |
| ---------- | ------ | -------- | ---------------------------------------------------------------------------- |
| `password` | string | Yes      | New password (8-72 characters, must contain uppercase, lowercase, and digit) |

### Example Request

```bash
curl -X POST https://app.collieai.io/auth/set-password \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "password": "NewSecure1Password"
  }'
```

### Response — `200 OK`

```json
{
  "message": "Password updated successfully"
}
```

### Error Responses

| Status | Description                                                               |
| ------ | ------------------------------------------------------------------------- |
| `401`  | Not authenticated                                                         |
| `422`  | Validation error (password too short, missing required character classes) |

***

## GET /auth/google/authorize

Initiate Google OAuth login flow. Redirects to Google's consent screen.

**URL:** `https://app.collieai.io/auth/google/authorize`

**Auth:** None

### Response — `302 Found`

Redirects to Google OAuth consent screen.

***

## GET /auth/google/callback

Google OAuth callback. Handles auto-registration for new users. Sets session cookie and redirects to the application.

**URL:** `https://app.collieai.io/auth/google/callback`

**Auth:** None (receives OAuth code from Google)

### Query Parameters

| Parameter | Type   | Description                     |
| --------- | ------ | ------------------------------- |
| `code`    | string | Authorization code from Google  |
| `state`   | string | CSRF protection state parameter |

### Response — `302 Found`

Redirects to the application with `auth_token` session cookie set.

### Error Responses

| Status | Description                           |
| ------ | ------------------------------------- |
| `400`  | Invalid or expired authorization code |
| `403`  | OAuth account not authorized          |

***

## GET /auth/me

Get the currently authenticated user's profile.

**URL:** `https://app.collieai.io/auth/me`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/auth/me \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/...",
  "role": "user",
  "has_password": true,
  "default_policy_id": "pol_abc123"
}
```

| Field               | Type           | Description                                                    |
| ------------------- | -------------- | -------------------------------------------------------------- |
| `id`                | string         | Unique user identifier                                         |
| `email`             | string         | User email address                                             |
| `name`              | string         | User display name                                              |
| `picture`           | string or null | Profile picture URL (from OAuth provider)                      |
| `role`              | string         | User role (`user` or `admin`)                                  |
| `has_password`      | boolean        | Whether the user has set a password                            |
| `ip_allowlist`      | string\[]      | List of allowed IP addresses/CIDR ranges (empty = all allowed) |
| `default_policy_id` | string or null | User's default policy for new projects                         |

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

***

## GET /auth/ip-allowlist

Get the current IP allowlist for the authenticated user.

**URL:** `https://app.collieai.io/auth/ip-allowlist`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/auth/ip-allowlist \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
{
  "ips": ["192.168.1.0/24", "10.0.0.1"],
  "enabled": true
}
```

| Field     | Type      | Description                                  |
| --------- | --------- | -------------------------------------------- |
| `ips`     | string\[] | List of allowed IP addresses and CIDR ranges |
| `enabled` | boolean   | `true` if the list is non-empty              |

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

***

## PUT /auth/ip-allowlist

Replace the IP allowlist for the authenticated user. Send an empty list to disable IP restrictions.

**URL:** `https://app.collieai.io/auth/ip-allowlist`

**Auth:** Session cookie or Bearer token

### Request Body

| Field | Type      | Required | Description                                         |
| ----- | --------- | -------- | --------------------------------------------------- |
| `ips` | string\[] | Yes      | List of IPv4/IPv6 addresses or CIDR ranges (max 50) |

### Example Request

```bash
curl -X PUT https://app.collieai.io/auth/ip-allowlist \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "ips": ["203.0.113.0/24", "198.51.100.42"]
  }'
```

### Response — `200 OK`

```json
{
  "ips": ["203.0.113.0/24", "198.51.100.42"],
  "enabled": true
}
```

### Error Responses

| Status | Description                                                |
| ------ | ---------------------------------------------------------- |
| `401`  | Not authenticated                                          |
| `422`  | Validation error (invalid IP/CIDR or more than 50 entries) |

***

## POST /auth/logout

Log out the current user. Clears the session cookie.

**URL:** `https://app.collieai.io/auth/logout`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl -X POST https://app.collieai.io/auth/logout \
  -H "Authorization: Bearer <token>"
```

### Response — `200 OK`

```json
{
  "message": "Logged out successfully"
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

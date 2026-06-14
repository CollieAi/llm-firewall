---
description: >-
  CollieAi Dictionaries API — list, create, upload, extract, update, and delete
  word-list dictionaries and dictionary groups for Dictionary Match rules via
  /api/v1/dictionaries.
icon: spell-check
---

# Dictionaries

Dictionaries are reusable word/phrase lists used by Dictionary Match rules (`aho_corasick`) to match content. Two kinds: **user dictionaries** (created by you) and **system dictionaries** (pre-built, read-only).

Dictionaries can be organized into **groups** -- each group represents a concept (e.g. "profanity") with one dictionary per supported language.

***

## Dictionary Groups

### GET /api/v1/dictionary-groups

List all dictionary groups accessible to the authenticated user.

**URL:** `https://app.collieai.io/api/v1/dictionary-groups`

**Auth:** Session cookie or Bearer token

#### Example Request

```bash
curl https://app.collieai.io/api/v1/dictionary-groups \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "groups": [
    {
      "id": "grp_abc123",
      "slug": "profanity",
      "name": "Profanity",
      "description": null,
      "group_type": "system",
      "owner_id": null,
      "is_active": true,
      "languages": ["ar", "cs", "de", "en", "es", "fr", "ja", "ko", "ru", "zh"],
      "dictionary_count": 23,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ],
  "total": 21
}
```

#### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

### GET /api/v1/dictionary-groups/{group\_id}

Get a dictionary group with its child dictionaries.

**URL:** `https://app.collieai.io/api/v1/dictionary-groups/{group_id}`

**Auth:** Session cookie or Bearer token

#### Path Parameters

| Parameter  | Type   | Description                     |
| ---------- | ------ | ------------------------------- |
| `group_id` | string | The dictionary group identifier |

#### Example Request

```bash
curl https://app.collieai.io/api/v1/dictionary-groups/grp_abc123 \
  -H "Authorization: Bearer <token>"
```

#### Response -- `200 OK`

```json
{
  "id": "grp_abc123",
  "slug": "profanity",
  "name": "Profanity",
  "group_type": "system",
  "is_active": true,
  "languages": ["en", "de", "fr", "ru"],
  "dictionary_count": 23,
  "dictionaries": [
    {"id": "dict_en1", "name": "Profanity (EN)", "language": "en", "word_count": 450, "is_active": true},
    {"id": "dict_de1", "name": "Profanity (DE)", "language": "de", "word_count": 380, "is_active": true}
  ],
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### Error Responses

| Status | Description                                      |
| ------ | ------------------------------------------------ |
| `401`  | Not authenticated                                |
| `403`  | Access denied (user group owned by another user) |
| `404`  | Group not found                                  |

***

## Dictionaries

### GET /api/v1/dictionaries

List all dictionaries accessible to the authenticated user (both user and system).

**URL:** `https://app.collieai.io/api/v1/dictionaries`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer <token>"
```

### Response -- `200 OK`

```json
{
  "dictionaries": [
  {
    "id": "dict_abc123",
    "name": "Profanity List",
    "description": "Common profane words and phrases",
    "dictionary_type": "user",
    "case_sensitive": false,
    "word_count": 245,
    "created_at": "2025-01-10T08:00:00Z",
    "updated_at": "2025-01-14T12:30:00Z"
  },
  {
    "id": "dict_sys001",
    "name": "HIPAA Terms",
    "description": "Healthcare-related protected terms",
    "dictionary_type": "system",
    "case_sensitive": false,
    "word_count": 1200,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
  ],
  "total": 2
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

### GET /api/v1/dictionaries/system

List system (pre-built) dictionaries only.

**URL:** `https://app.collieai.io/api/v1/dictionaries/system`

**Auth:** Session cookie or Bearer token

### Example Request

```bash
curl https://app.collieai.io/api/v1/dictionaries/system \
  -H "Authorization: Bearer <token>"
```

### Response -- `200 OK`

```json
{
  "dictionaries": [
  {
    "id": "dict_sys001",
    "name": "HIPAA Terms",
    "description": "Healthcare-related protected terms",
    "dictionary_type": "system",
    "case_sensitive": false,
    "word_count": 1200,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
  ],
  "total": 1
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |

### POST /api/v1/dictionaries

Create a new user dictionary with content provided as JSON.

**URL:** `https://app.collieai.io/api/v1/dictionaries`

**Auth:** Session cookie or Bearer token

### Request Body

| Field            | Type    | Required | Description                                   |
| ---------------- | ------- | -------- | --------------------------------------------- |
| `name`           | string  | Yes      | Dictionary name                               |
| `description`    | string  | No       | Dictionary description                        |
| `content`        | string  | Yes      | Dictionary content (one word/phrase per line) |
| `case_sensitive` | boolean | No       | Case-sensitive matching. Default: `false`     |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Internal Project Names",
    "description": "Codenames that should not appear in outputs",
    "content": "project-atlas\nproject-horizon\noperation-sunrise",
    "case_sensitive": false
  }'
```

### Response -- `201 Created`

```json
{
  "id": "dict_new789",
  "name": "Internal Project Names",
  "description": "Codenames that should not appear in outputs",
  "dictionary_type": "user",
  "case_sensitive": false,
  "word_count": 3,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `422`  | Validation error  |

### POST /api/v1/dictionaries/upload

Create a new dictionary by uploading a file (multipart/form-data). Supports plain text files with one word/phrase per line.

**URL:** `https://app.collieai.io/api/v1/dictionaries/upload`

**Auth:** Session cookie or Bearer token

### Request Body (multipart/form-data)

| Field            | Type    | Required | Description                               |
| ---------------- | ------- | -------- | ----------------------------------------- |
| `file`           | file    | Yes      | Text file with one word/phrase per line   |
| `name`           | string  | Yes      | Dictionary name                           |
| `description`    | string  | No       | Dictionary description                    |
| `case_sensitive` | boolean | No       | Case-sensitive matching. Default: `false` |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@wordlist.txt" \
  -F "name=Uploaded Dictionary" \
  -F "description=Imported from external source" \
  -F "case_sensitive=false"
```

### Response -- `201 Created`

```json
{
  "id": "dict_upl456",
  "name": "Uploaded Dictionary",
  "description": "Imported from external source",
  "dictionary_type": "user",
  "case_sensitive": false,
  "word_count": 150,
  "created_at": "2025-01-15T10:00:00Z",
  "updated_at": "2025-01-15T10:00:00Z"
}
```

### Error Responses

| Status | Description         |
| ------ | ------------------- |
| `400`  | Invalid file format |
| `401`  | Not authenticated   |
| `422`  | Validation error    |

### POST /api/v1/dictionaries/extract

Extract words from text with relevance scoring. Useful for building dictionaries from sample content.

**URL:** `https://app.collieai.io/api/v1/dictionaries/extract`

**Auth:** Session cookie or Bearer token

### Request Body

| Field  | Type   | Required | Description                    |
| ------ | ------ | -------- | ------------------------------ |
| `content` | string | Yes    | The text to extract words from |

### Example Request

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/extract \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "The patient was diagnosed with diabetes mellitus type 2 and prescribed metformin."
  }'
```

### Response -- `200 OK`

```json
{
  "words": [
    {"word": "diabetes mellitus", "score": 0.95},
    {"word": "metformin", "score": 0.92},
    {"word": "diagnosed", "score": 0.78},
    {"word": "patient", "score": 0.75}
  ]
}
```

### Error Responses

| Status | Description       |
| ------ | ----------------- |
| `401`  | Not authenticated |
| `422`  | Validation error  |

### PUT /api/v1/dictionaries/{dictionary\_id}

Update an existing user dictionary. System dictionaries cannot be updated.

**URL:** `https://app.collieai.io/api/v1/dictionaries/{dictionary_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter       | Type   | Description               |
| --------------- | ------ | ------------------------- |
| `dictionary_id` | string | The dictionary identifier |

### Request Body

| Field            | Type    | Required | Description                                            |
| ---------------- | ------- | -------- | ------------------------------------------------------ |
| `name`           | string  | No       | New dictionary name                                    |
| `description`    | string  | No       | New dictionary description                             |
| `content`        | string  | No       | New dictionary content (replaces all existing content) |
| `case_sensitive` | boolean | No       | Updated case sensitivity setting                       |

### Example Request

```bash
curl -X PUT https://app.collieai.io/api/v1/dictionaries/dict_abc123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Profanity List (Updated)",
    "content": "word1\nword2\nword3\nnew-word"
  }'
```

### Response -- `200 OK`

```json
{
  "id": "dict_abc123",
  "name": "Profanity List (Updated)",
  "description": "Common profane words and phrases",
  "dictionary_type": "user",
  "case_sensitive": false,
  "word_count": 4,
  "created_at": "2025-01-10T08:00:00Z",
  "updated_at": "2025-01-15T11:00:00Z"
}
```

### Error Responses

| Status | Description                       |
| ------ | --------------------------------- |
| `401`  | Not authenticated                 |
| `403`  | Cannot modify a system dictionary |
| `404`  | Dictionary not found              |
| `422`  | Validation error                  |

### DELETE /api/v1/dictionaries/{dictionary\_id}

Delete a user dictionary. System dictionaries cannot be deleted. Rules referencing this dictionary will no longer match.

**URL:** `https://app.collieai.io/api/v1/dictionaries/{dictionary_id}`

**Auth:** Session cookie or Bearer token

### Path Parameters

| Parameter       | Type   | Description               |
| --------------- | ------ | ------------------------- |
| `dictionary_id` | string | The dictionary identifier |

### Example Request

```bash
curl -X DELETE https://app.collieai.io/api/v1/dictionaries/dict_abc123 \
  -H "Authorization: Bearer <token>"
```

### Response -- `204 No Content`

No response body.

### Error Responses

| Status | Description                       |
| ------ | --------------------------------- |
| `401`  | Not authenticated                 |
| `403`  | Cannot delete a system dictionary |
| `404`  | Dictionary not found              |

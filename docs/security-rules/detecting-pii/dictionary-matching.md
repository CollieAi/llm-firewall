---
description: >-
  How CollieAi dictionary matching filters content — fast Aho-Corasick word-list
  matching for profanity, PII keywords, prompt injection, and custom terms
  across 23 languages.
icon: spell-check
---

# Dictionary matching

## What is the dictionary match rule type?

The Dictionary Match rule type (`aho_corasick`) enables efficient multi-pattern string matching using dictionary-based word lists. It uses the Aho-Corasick algorithm internally, which provides O(n + m + z) time complexity where n is text length, m is total pattern length, and z is number of matches.

**Ideal for:**

* Profanity filtering
* PII detection (keywords)
* Custom sensitive term blocking
* Brand/competitor name filtering
* Compliance keyword detection

{% hint style="info" %}
**Key points**

* Dictionary matching scans messages against word lists using the Aho-Corasick algorithm — O(n) regardless of dictionary size.
* CollieAi ships 21 system dictionary groups across 23 languages (profanity, prompt injection, code secrets, brand safety, and more).
* You can use system dictionaries or upload your own, and match in `substring` (exact) or `unordered` (any-order) mode.
* It is faster than running many regex patterns and is ideal for keyword lists and custom blocklists.
{% endhint %}

## How does dictionary matching work?

1. Dictionary words are compiled into an automaton (finite state machine)
2. The automaton is cached in memory for fast repeated lookups
3. When a message is evaluated, it's scanned once to find all dictionary matches
4. Matches can be masked or used to block/allow the message

## Rule Configuration

### Properties

You must provide exactly one of `dictionary_id` or `dictionary_group_id`.

| Property                 | Type            | Required | Default     | Description                                                                                                                                                                                                                     |
| ------------------------ | --------------- | -------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `dictionary_id`          | string (UUID)   | One of   | -           | ID of a single dictionary to use                                                                                                                                                                                                |
| `dictionary_group_id`    | string (UUID)   | One of   | -           | ID of a dictionary group                                                                                                                                                                                                        |
| `languages`              | string\[]       | No       | -           | Language codes for group mode (e.g. `["en", "de"]`). Omit for auto-detection.                                                                                                                                                   |
| `always_include_english` | boolean         | No       | `false`     | Always check the English dictionary alongside the detected/selected language. Recommended for Prompt Security groups where attack patterns and code artifacts are typically in English regardless of surrounding text language. |
| `replacement`            | string          | No       | -           | Text to replace matches                                                                                                                                                                                                         |
| `mask_char`              | string (1 char) | No       | `*`         | Character for masking                                                                                                                                                                                                           |
| `whole_word`             | boolean         | No       | `true`      | Match whole words only                                                                                                                                                                                                          |
| `case_sensitive`         | boolean         | No       | `false`     | Override dictionary setting                                                                                                                                                                                                     |
| `match_mode`             | string          | No       | `substring` | `substring` (exact sequence) or `unordered` (words in any order)                                                                                                                                                                |
| `window_size`            | integer (1-100) | No       | `10`        | Max word distance for unordered mode                                                                                                                                                                                            |

### Example Configuration

**Single dictionary (substring mode):**

```json
{
  "dictionary_id": "550e8400-e29b-41d4-a716-446655440000",
  "replacement": "[REDACTED]",
  "whole_word": true,
  "case_sensitive": false
}
```

**Dictionary group with explicit languages:**

```json
{
  "dictionary_group_id": "660e8400-e29b-41d4-a716-446655440000",
  "languages": ["en", "de", "fr"],
  "replacement": "[REDACTED]",
  "whole_word": true
}
```

**Dictionary group with auto-detection:**

```json
{
  "dictionary_group_id": "660e8400-e29b-41d4-a716-446655440000",
  "whole_word": true,
  "mask_char": "*"
}
```

When `languages` is omitted, the rule reads the detected language from an upstream [Language Detection](../text-processing/language-detection.md) rule. If detection confidence is below the threshold configured on the language detection rule (default 50%), English is used as fallback.

**Prompt Security with always\_include\_english:**

```json
{
  "dictionary_group_id": "770e8400-e29b-41d4-a716-446655440000",
  "always_include_english": true,
  "whole_word": true
}
```

When `always_include_english` is enabled, the English dictionary is always checked alongside the detected or selected language. This is important for prompt injection and code secret detection, where attack patterns like `BEGIN ENCRYPTED PRIVATE KEY` or `api_key` appear in English regardless of the surrounding text language.

**Single dictionary (unordered mode):**

```json
{
  "dictionary_id": "550e8400-e29b-41d4-a716-446655440000",
  "match_mode": "unordered",
  "window_size": 10,
  "replacement": "[BLOCKED]",
  "whole_word": true
}
```

## Dictionaries

Dictionaries store word lists used for matching.

### Dictionary Groups

Dictionaries are organized into **groups** -- each group represents a concept (e.g. "profanity", "brand-safety") with one dictionary per supported language. CollieAi ships with 21 system groups across 23 languages.

When creating a rule, you can reference a group plus a language selection instead of a single dictionary. See the configuration table above.

```http
GET /api/v1/dictionary-groups
Authorization: Bearer {auth_token}
```

### System Dictionaries

Pre-configured dictionaries available to all users. System groups include: Profanity, Hate Speech, CSAM, Prompt Injection, Brand Safety, Violence, Weapons, Drugs, Extremism, Self-Harm, Code Secrets, and unordered/soft variants -- each with dictionaries in 23 languages.

Legacy standalone system dictionaries (Profanity Filter, PII Keywords) are also available for backward compatibility.

System dictionaries are **read-only** and cannot be modified or deleted.

### User Dictionaries

Custom dictionaries uploaded by users:

* Isolated per user (only accessible to the creator)
* Can be created, updated, and deleted
* Plain text format (one word/phrase per line)
* Maximum file size: 5MB

## Dictionary API

### List All Dictionaries

Get all dictionaries accessible to the user (system + user's own).

```http
GET /api/v1/dictionaries
Authorization: Bearer {auth_token}
```

**Response:**

```json
{
  "dictionaries": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Profanity Filter",
      "description": "Common profanity and offensive words",
      "dictionary_type": "system",
      "owner_id": null,
      "word_count": 15,
      "case_sensitive": false,
      "is_active": true,
      "version": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 3
}
```

### Create Dictionary (JSON)

Create a new user dictionary via JSON body.

```http
POST /api/v1/dictionaries
Content-Type: application/json
Authorization: Bearer {auth_token}

{
  "name": "Custom Blocklist",
  "description": "Company-specific blocked terms",
  "content": "term1\nterm2\nterm3",
  "case_sensitive": false
}
```

### Upload Dictionary (File)

Upload a dictionary as a plain text file.

```http
POST /api/v1/dictionaries/upload
Content-Type: multipart/form-data
Authorization: Bearer {auth_token}

name=Custom Blocklist
description=Company-specific blocked terms
case_sensitive=false
file=@blocklist.txt
```

**File Format:**

```
badword1
badword2
sensitive phrase
another term
```

### Extract Words from Text

Automatically extract domain-specific words from SQL schemas, code, configs, or any text content. This feature helps build custom dictionaries by identifying "specific" words and filtering out common/generic terms.

```http
POST /api/v1/dictionaries/extract
Content-Type: application/json
Authorization: Bearer {auth_token}

{
  "content": "CREATE TABLE threads (userid uuid, companyid uuid, reminderdisabled boolean)",
  "min_length": 6,
  "extract_snake_case": true,
  "extract_camel_case": true,
  "extract_prefixed": true,
  "extract_suffixed": true,
  "filter_common_words": true,
  "filter_sql_keywords": true,
  "filter_programming_keywords": true,
  "filter_english_words": true,
  "custom_stopwords": []
}
```

**Response:**

```json
{
  "words": [
    {"word": "reminderdisabled", "score": 0.25, "reasons": ["very_long", "rare"], "frequency": 1},
    {"word": "unreadmessagescount", "score": 0.25, "reasons": ["very_long", "rare"], "frequency": 1},
    {"word": "companyid", "score": 0.10, "reasons": ["rare"], "frequency": 1},
    {"word": "userid", "score": 0.10, "reasons": ["rare"], "frequency": 1}
  ],
  "total_candidates": 21,
  "filtered_count": 16,
  "summary": {"by_reason": {"very": 2, "rare": 4}}
}
```

#### Word Scoring Algorithm

Words are scored (0-1) based on factors that indicate domain specificity:

| Factor                                 | Score Bonus | Example                  |
| -------------------------------------- | ----------- | ------------------------ |
| snake\_case (underscore in middle)     | +0.30       | `user_id`, `pg_catalog`  |
| camelCase/PascalCase                   | +0.25       | `userId`, `CompanyId`    |
| Technical prefix (is\_, has\_, get\_)  | +0.20       | `isEnabled`, `hasAccess` |
| Technical suffix (\_id, \_at, \_count) | +0.20       | `created_at`, `user_id`  |
| Length 15+ chars                       | +0.15       | `unreadmessagescount`    |
| Length 10+ chars                       | +0.10       | `companyid`              |
| Contains numbers                       | +0.10       | `thread2`, `v2_schema`   |
| Rare in input (appears once)           | +0.10       | unique terms             |

#### Filtering

The extractor filters out:

* **Common words**: Generic terms like `status`, `type`, `name`, `value`, `data` (\~260 words)
* **SQL keywords**: `SELECT`, `FROM`, `CREATE`, `TABLE`, `VARCHAR`, `INTEGER` (\~160 keywords)
* **Programming keywords**: `function`, `class`, `return`, `if`, `const`, `public` (\~130 keywords)
* **Generic identifiers**: `id`, `pk`, `uuid`, `key`, `tmp`, `obj` (\~50 identifiers)
* **English dictionary words**: Plain English words like `verified`, `wallet`, `without` (\~427K words, smart filter)

#### Smart English Dictionary Filter

The `filter_english_words` option uses a **smart filtering** approach that preserves domain-specific identifiers while filtering plain English words:

| Word            | Has Domain Indicator? | Filtered? | Reason                 |
| --------------- | --------------------- | --------- | ---------------------- |
| `verified`      | No                    | Yes       | Plain English word     |
| `wallet`        | No                    | Yes       | Plain English word     |
| `user_verified` | Yes (snake\_case)     | No        | Has underscore         |
| `userVerified`  | Yes (camelCase)       | No        | Has mixed case         |
| `isVerified`    | Yes (prefix)          | No        | Technical prefix `is`  |
| `verified_at`   | Yes (suffix)          | No        | Technical suffix `_at` |
| `wallet2`       | Yes (number)          | No        | Contains digit         |

This prevents false positives where common English words appear in SQL schemas or code, while preserving domain-specific compound identifiers.

#### Request Parameters

| Parameter                     | Type   | Default  | Description                                          |
| ----------------------------- | ------ | -------- | ---------------------------------------------------- |
| `content`                     | string | required | Text to extract words from                           |
| `min_length`                  | int    | 6        | Minimum word length (2-50)                           |
| `extract_snake_case`          | bool   | true     | Boost snake\_case words                              |
| `extract_camel_case`          | bool   | true     | Boost camelCase words                                |
| `extract_prefixed`            | bool   | true     | Boost words with technical prefixes                  |
| `extract_suffixed`            | bool   | true     | Boost words with technical suffixes                  |
| `filter_common_words`         | bool   | true     | Filter common English words                          |
| `filter_sql_keywords`         | bool   | true     | Filter SQL keywords                                  |
| `filter_programming_keywords` | bool   | true     | Filter programming keywords                          |
| `filter_english_words`        | bool   | true     | Filter plain English dictionary words (smart filter) |
| `custom_stopwords`            | array  | null     | Additional words to filter                           |

### Update Dictionary

```http
PUT /api/v1/dictionaries/{dictionary_id}
Content-Type: application/json
Authorization: Bearer {auth_token}

{
  "name": "Updated Name",
  "content": "newterm1\nnewterm2"
}
```

### Delete Dictionary

```http
DELETE /api/v1/dictionaries/{dictionary_id}
Authorization: Bearer {auth_token}
```

## Example Rules

{% stepper %}
{% step %}
### Profanity Filter (Mask)

```json
{
  "name": "Profanity Filter",
  "rule_type": "aho_corasick",
  "order": 10,
  "direction": "all",
  "decision": "mask",
  "config": {
    "dictionary_id": "{profanity-dictionary-id}",
    "replacement": "[FILTERED]",
    "whole_word": true
  }
}
```
{% endstep %}

{% step %}
### PII Keyword Detection (Block)

```json
{
  "name": "Block PII Keywords",
  "rule_type": "aho_corasick",
  "order": 5,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "dictionary_id": "{pii-keywords-dictionary-id}",
    "whole_word": true
  },
  "block_message": "Message contains sensitive information keywords"
}
```
{% endstep %}

{% step %}
### Prompt Injection Dictionary (Unordered)

```json
{
  "name": "Prompt Injection Phrases",
  "rule_type": "aho_corasick",
  "order": 40,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "dictionary_id": "{prompt-injection-dictionary-id}",
    "match_mode": "unordered",
    "window_size": 10,
    "whole_word": true
  },
  "block_message": "Message contains prompt injection patterns"
}
```
{% endstep %}

{% step %}
### Content Safety Filter — Multi-Language (Group)

```json
{
  "name": "Content Safety (EN/DE/FR)",
  "rule_type": "aho_corasick",
  "order": 15,
  "direction": "all",
  "decision": "mask",
  "config": {
    "dictionary_group_id": "{content-safety-group-id}",
    "languages": ["en", "de", "fr"],
    "replacement": "[FILTERED]",
    "whole_word": true
  }
}
```
{% endstep %}

{% step %}
### Content Safety Filter — Auto-Detect Language (Group)

```json
{
  "name": "Content Safety (auto-detect)",
  "rule_type": "aho_corasick",
  "order": 15,
  "direction": "all",
  "decision": "mask",
  "config": {
    "dictionary_group_id": "{content-safety-group-id}",
    "replacement": "[FILTERED]",
    "whole_word": true
  }
}
```

> Place a Language Detection rule earlier in the pipeline so the detected language is available for auto-selection.
{% endstep %}

{% step %}
### Prompt Security — Always Include English (Group)

```json
{
  "name": "Prompt Security (auto-detect + EN)",
  "rule_type": "aho_corasick",
  "order": 5,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "dictionary_group_id": "{prompt-security-group-id}",
    "always_include_english": true,
    "whole_word": true
  },
  "block_message": "Message contains prompt injection or code secret patterns"
}
```

> English attack patterns like `BEGIN ENCRYPTED PRIVATE KEY` and `api_key` are checked regardless of the detected message language.
{% endstep %}

{% step %}
### Custom Sensitive Terms (Mask)

```json
{
  "name": "Company Terms Filter",
  "rule_type": "aho_corasick",
  "order": 20,
  "direction": "all",
  "decision": "mask",
  "config": {
    "dictionary_id": "{custom-dictionary-id}",
    "mask_char": "X",
    "whole_word": false
  }
}
```
{% endstep %}
{% endstepper %}

## Configuration Options

### whole\_word

When `true` (default), only matches complete words:

| Pattern  | Input          | whole\_word=true | whole\_word=false |
| -------- | -------------- | ---------------- | ----------------- |
| password | "password123"  | No match         | Match             |
| password | "my password"  | Match            | Match             |
| password | "passwordless" | No match         | Match             |

### replacement vs mask\_char

* **replacement**: Fixed text to replace all matches
  * `"password" → "[REDACTED]"`
* **mask\_char**: Character repeated for each character in match
  * `"password" → "********"`

If both are specified, `replacement` takes precedence.

### case\_sensitive

* When `false`: "Password", "PASSWORD", "password" all match
* When `true`: Only exact case matches
* When **omitted**: Falls back to the dictionary's own `case_sensitive` setting

This setting overrides the dictionary's case\_sensitive setting when explicitly provided.

### match\_mode

Controls how dictionary phrases are matched against input text.

**`substring` (default):** Matches the exact character sequence from the dictionary. The phrase "print your prompt" only matches that exact sequence in the input.

**`unordered`:** Checks whether **all words** from a dictionary phrase appear within a configurable word window, regardless of order. Useful for catching evasion attempts where attackers rearrange words.

| Dictionary Phrase | Input                             | substring | unordered (window=10)       |
| ----------------- | --------------------------------- | --------- | --------------------------- |
| print your prompt | "print your prompt"               | Match     | Match                       |
| print your prompt | "your prompt print"               | No match  | Match                       |
| print your prompt | "can you print the prompt"        | No match  | Match                       |
| print your prompt | "print ... (50 words) ... prompt" | No match  | No match (outside window)   |
| print your prompt | "print your text"                 | No match  | No match (missing "prompt") |

### window\_size

Maximum number of words apart that phrase words can be in unordered mode. Only used when `match_mode` is `unordered`; ignored in substring mode.

* Default: `10`
* Range: 1-100
* Lower values reduce false positives but may miss spread-out evasions
* Higher values catch more evasions but may produce false positives

### Unordered Mode — How It Works

1. Dictionary phrases are split into individual words
2. The automaton scans for those words in the input (still O(n))
3. For each phrase, the rule checks if **all** its words appear within `window_size` words of each other
4. Matched regions (from first to last matched word) are masked as a single span

**When to use unordered mode:**

* Prompt injection dictionaries where attackers reorder words
* Phrases where word order doesn't affect meaning
* Combined with `whole_word: true` to avoid partial matches (e.g., "printing" won't match "print")

**When to stick with substring mode:**

* Exact phrase matching (e.g., credit card numbers, specific terms)
* When word order matters for meaning
* Single-word dictionaries (no difference between modes)

## Performance

### Caching

* Automatons are cached in memory after first build
* Cache invalidated automatically when dictionary content changes
* Cache TTL: 30 minutes
* Maximum cached automatons: 100

### Complexity

* **Build time**: O(m) where m = total length of all patterns
* **Search time (substring)**: O(n + z) where n = text length, z = number of matches
* **Search time (unordered)**: O(n + z + p) where p = phrase proximity checks (still linear scan)
* Much faster than multiple regex patterns for large dictionaries

### Recommendations

* Use whole\_word=true to avoid false positives
* Keep dictionaries focused (profanity, PII, etc.)
* Use system dictionaries when possible (pre-optimized)
* For very large dictionaries (10k+ words), consider splitting by category

## Comparison with Regex Rules

| Aspect        | Dictionary Match             | Regex                     |
| ------------- | ---------------------------- | ------------------------- |
| Best for      | Fixed word lists             | Complex patterns          |
| Performance   | O(n) for any dictionary size | Slower with many patterns |
| Pattern types | Exact strings                | Any regex                 |
| Maintenance   | Edit dictionary              | Edit regex pattern        |
| Use case      | Profanity, keywords          | Credit cards, emails      |

## Troubleshooting

### Why is my dictionary not found?

Ensure the dictionary\_id is correct and the dictionary is active:

```http
GET /api/v1/dictionaries/{dictionary_id}
```

### Why aren't matches detected?

1. Check `whole_word` setting - substring matches may be filtered out
2. Verify `case_sensitive` setting matches your expectation
3. Ensure the dictionary contains the expected words
4. Test the rule with the `/test` endpoint
5. For unordered mode: check `window_size` — words may be too far apart to match
6. For unordered mode: ensure **all** words from the phrase are present in the input

### Why is dictionary matching slow?

1. Check dictionary word count (very large dictionaries may be slow to build)
2. Verify automaton is being cached (check logs for cache hits)
3. Consider splitting large dictionaries into smaller, focused ones

## Building Dictionaries from Code/Schema

The word extraction feature helps you build domain-specific dictionaries from your existing codebase, database schemas, or configuration files.

### UI Workflow

{% stepper %}
{% step %}
Navigate to **Dictionaries** page
{% endstep %}

{% step %}
Click **Add Dictionary**
{% endstep %}

{% step %}
Select the **Extract from Text** tab
{% endstep %}

{% step %}
Paste your content (SQL DDL, code, config files)
{% endstep %}

{% step %}
Adjust extraction settings:

* **Minimum word length**: Filter short words (default: 6)
* **Boost snake\_case**: Score `user_id`, `created_at` higher
* **Boost camelCase**: Score `userId`, `CreatedAt` higher
* **Filter common words**: Remove generic terms
* **Filter SQL keywords**: Remove SQL syntax
* **Filter programming keywords**: Remove language keywords
* **Filter English dictionary words**: Remove plain English words (smart filter preserves domain identifiers)
{% endstep %}

{% step %}
Click **Preview Extracted Words**
{% endstep %}

{% step %}
Review the word list sorted by specificity score
{% endstep %}

{% step %}
Deselect any unwanted words using checkboxes
{% endstep %}

{% step %}
Click **Use Selected Words** to populate the dictionary content
{% endstep %}

{% step %}
Fill in dictionary name and description
{% endstep %}

{% step %}
Save the dictionary
{% endstep %}
{% endstepper %}

### Example: SQL Schema

**Input:**

```sql
CREATE TABLE public.threads (
    id uuid NOT NULL,
    userid uuid NOT NULL,
    companyid uuid NOT NULL,
    title text COLLATE pg_catalog."default" NOT NULL,
    reminderdisabled boolean DEFAULT false,
    unreadmessagescount integer NOT NULL DEFAULT 0
)
```

**Good extractions:**

* `reminderdisabled` (very\_long, rare)
* `unreadmessagescount` (very\_long, rare)
* `companyid` (rare)
* `userid` (rare)
* `threads` (rare)

**Filtered out:**

* `id` (generic identifier)
* `title`, `text` (common words)
* `uuid`, `boolean`, `integer` (SQL types)
* `NOT`, `NULL`, `DEFAULT` (SQL keywords)
* `CREATE`, `TABLE`, `COLLATE` (SQL syntax)

### Example: TypeScript Code

**Input:**

```typescript
interface UserPreferences {
  notificationEnabled: boolean;
  darkModeActivated: boolean;
  languageCode: string;
  lastLoginTimestamp: number;
}
```

**Good extractions:**

* `notificationEnabled` (camel\_case, suffix\_Enabled)
* `darkModeActivated` (camel\_case, suffix\_Activated)
* `lastLoginTimestamp` (camel\_case, suffix\_Timestamp, very\_long)
* `UserPreferences` (camel\_case)
* `languageCode` (camel\_case)

**Filtered out:**

* `interface` (programming keyword)
* `boolean`, `string`, `number` (type keywords)

### Use Cases

1. **Prompt Injection Protection**: Extract your database column names, API endpoints, and internal identifiers to detect when users try to reference internal system details
2. **Data Leakage Prevention**: Build dictionaries of internal project names, codenames, or proprietary terms that shouldn't appear in LLM outputs
3. **Compliance Filtering**: Extract industry-specific terminology from compliance documents to ensure proper handling
4. **Custom Entity Detection**: Extract product names, feature flags, or business terms unique to your application

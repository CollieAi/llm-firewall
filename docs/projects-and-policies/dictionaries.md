---
description: >-
  How CollieAi dictionaries work — reusable word lists for Dictionary Match
  rules, with system groups across 23 languages, custom uploads, and automatic
  word extraction from code and schemas.
icon: spell-check
---

# Dictionaries

Dictionaries are word lists used by [Dictionary Match](../security-rules/detecting-pii/dictionary-matching.md) rules. They power CollieAi's multi-pattern matching — load a list of terms once, and every message is scanned for all of them in a single pass.

{% hint style="info" %}
**Key points**

* Dictionaries are reusable word lists that power CollieAi's Dictionary Match (Aho-Corasick) rules.
* CollieAi ships 4 system groups across 23 languages (Content Safety and Prompt Security, each ordered and unordered).
* You can upload custom dictionaries (up to 5 MB) or auto-extract domain terms from SQL schemas and code.
* Reference a single dictionary by ID or a group with language selection when configuring a rule.
{% endhint %}

***

## Dictionary groups

Dictionaries are organized into **groups**. A group represents a broad protection category with one dictionary per supported language.

CollieAi ships with **4 system groups** covering 23 languages:

| Group                           | Match Mode | Description                                                                                                                                        |
| ------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Content Safety**              | substring  | Profanity, hate speech, CSAM, drugs, extremism, brand safety, self-harm, violence, weapons — merged into one comprehensive dictionary per language |
| **Content Safety (Unordered)**  | unordered  | Same categories optimized for unordered phrase matching                                                                                            |
| **Prompt Security**             | substring  | Prompt injection patterns (including soft indicators) and code/API secret detection                                                                |
| **Prompt Security (Unordered)** | unordered  | Prompt injection phrases optimized for unordered matching                                                                                          |

When configuring an Aho-Corasick rule, you can reference a group and select which languages to apply — instead of picking individual dictionaries one by one.

```bash
# List all dictionary groups
curl https://app.collieai.io/api/v1/dictionary-groups \
  -H "Authorization: Bearer clai_..."
```

***

## System dictionaries

CollieAi also includes **legacy standalone system dictionaries** for backward compatibility:

| Dictionary           | Description                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------- |
| **Profanity Filter** | Common profanity and offensive terms.                                                                            |
| **PII Keywords**     | Terms that indicate the presence of personal data (e.g., "social security", "date of birth", "passport number"). |

System dictionaries are **read-only** -- you cannot edit or delete them.

```bash
# List all dictionaries (includes both system and custom)
curl https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer clai_..."
```

***

## User dictionaries

You can create **custom dictionaries** with your own terms. Custom dictionaries are user-scoped -- only you can see and use them.

### Size limit

Each custom dictionary can be up to **5 MB** in size. This is enough for tens of thousands of terms.

### Creating via JSON body

Pass the dictionary name and a list of words directly in the request body:

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "employee-names",
    "words": [
      "Alice Johnson",
      "Bob Smith",
      "Carol Williams"
    ]
  }'
```

### Creating via file upload

Upload a text file where each line is one term:

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/upload \
  -H "Authorization: Bearer clai_..." \
  -F "name=medical-terms" \
  -F "file=@medical-terms.txt"
```

The file should contain one word or phrase per line:

```
acetaminophen
amoxicillin
blood pressure
cholesterol
diabetes mellitus
```

***

## Word extraction

CollieAI can automatically **extract domain-specific words** from structured sources like SQL schemas, code files, and configuration files. This is useful when you want to detect references to your internal database columns, table names, or application-specific terminology.

The extraction process uses smart scoring to remove common words, SQL keywords, and programming language reserved words, leaving only the domain-relevant terms.

```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/extract \
  -H "Authorization: Bearer clai_..." \
  -F "name=database-terms" \
  -F "file=@schema.sql"
```

For example, given a SQL schema like:

```sql
CREATE TABLE customer_orders (
    order_id INTEGER PRIMARY KEY,
    customer_name VARCHAR(100),
    shipping_address TEXT
);
```

The extraction would produce terms like `customer_orders`, `order_id`, `customer_name`, and `shipping_address`, while filtering out SQL keywords like `CREATE`, `TABLE`, `INTEGER`, and `VARCHAR`.

***

## Updating a dictionary

Replace the words in an existing dictionary:

```bash
curl -X PUT https://app.collieai.io/api/v1/dictionaries/{dictionary_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "employee-names-v2",
    "words": [
      "Alice Johnson",
      "Bob Smith",
      "Carol Williams",
      "David Lee"
    ]
  }'
```

{% hint style="info" %}
Updating a dictionary affects all rules that reference it. The updated word list takes effect on the next request.
{% endhint %}

***

## Deleting a dictionary

```bash
curl -X DELETE https://app.collieai.io/api/v1/dictionaries/{dictionary_id} \
  -H "Authorization: Bearer clai_..."
```

You cannot delete system dictionaries. If a custom dictionary is referenced by an active rule, you should remove or update the rule first to avoid matching errors.

***

## API reference

### List all dictionaries

```bash
curl https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer clai_..."
```

### Create a dictionary

{% tabs %}
{% tab title="JSON" %}
```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-dictionary",
    "words": ["term1", "term2", "term3"]
  }'
```
{% endtab %}

{% tab title="File upload" %}
```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/upload \
  -H "Authorization: Bearer clai_..." \
  -F "name=my-dictionary" \
  -F "file=@words.txt"
```
{% endtab %}

{% tab title="Word extraction" %}
```bash
curl -X POST https://app.collieai.io/api/v1/dictionaries/extract \
  -H "Authorization: Bearer clai_..." \
  -F "name=schema-terms" \
  -F "file=@schema.sql"
```
{% endtab %}
{% endtabs %}

### Update a dictionary

```bash
curl -X PUT https://app.collieai.io/api/v1/dictionaries/{dictionary_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "updated-name",
    "words": ["term1", "term2"]
  }'
```

### Delete a dictionary

```bash
curl -X DELETE https://app.collieai.io/api/v1/dictionaries/{dictionary_id} \
  -H "Authorization: Bearer clai_..."
```

***

## Using dictionaries in rules

Once a dictionary exists, reference it by ID when creating a [dictionary matching](../security-rules/detecting-pii/dictionary-matching.md) rule:

```bash
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/rules \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "mask-employee-names",
    "rule_type": "aho_corasick",
    "direction": "all",
    "decision": "mask",
    "config": {
      "dictionary_id": "{dictionary_id}",
      "case_sensitive": false,
      "whole_word": true
    }
  }'
```

### Using dictionary groups

Instead of a single dictionary, you can reference a **dictionary group** and specify which languages to use:

```bash
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/rules \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "profanity-filter-multilang",
    "rule_type": "aho_corasick",
    "direction": "all",
    "decision": "mask",
    "config": {
      "dictionary_group_id": "{group_id}",
      "languages": ["en", "de", "fr"],
      "whole_word": true
    }
  }'
```

If you omit `languages`, the rule will auto-detect the message language from an upstream [Language Detection](../security-rules/text-processing/language-detection.md) rule and select the matching dictionary automatically. If detection confidence is below the threshold configured on the language detection rule, English is used as fallback.

### Always include English

For **Prompt Security** groups, enable `always_include_english` to also check the English dictionary regardless of the detected language. English technical patterns like `BEGIN ENCRYPTED PRIVATE KEY`, `api_key`, and prompt injection phrases appear in text of any language:

```bash
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/rules \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "prompt-security-multilang",
    "rule_type": "aho_corasick",
    "direction": "inbound",
    "decision": "block",
    "config": {
      "dictionary_group_id": "{prompt-security-group-id}",
      "always_include_english": true,
      "whole_word": true
    }
  }'
```

See [Dictionary Matching](../security-rules/detecting-pii/dictionary-matching.md) for full configuration options.

***

## Next steps

* [Dictionary Matching](../security-rules/detecting-pii/dictionary-matching.md) -- configure rules that use dictionaries.
* [Policies](policies.md) -- organize rules into policies.
* [Projects](projects.md) -- assign policies to projects.

### Frequently asked questions

**What are dictionaries in CollieAi?** Dictionaries in CollieAi are reusable word lists used by Dictionary Match rules to scan every message for many terms in a single pass — for profanity, PII keywords, prompt injection phrases, or your own custom terms.

**Can I build a dictionary from my own data?** Yes. You can upload a custom dictionary (up to 5 MB) or have CollieAi automatically extract domain-specific terms from SQL schemas, code, and config files, filtering out common words and keywords.

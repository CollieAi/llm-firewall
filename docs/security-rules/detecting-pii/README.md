---
description: >-
  How CollieAi detects and redacts PII in LLM applications — regex patterns,
  checksum-validated structured IDs, and dictionary matching for automated PII
  redaction and data masking.
icon: id-card
---

# PII detection and redaction

CollieAi provides three rule types for automated PII detection and redaction in LLM messages: regex patterns, checksum-validated structured IDs, and dictionary matching. Each approach is optimized for different kinds of sensitive data.

{% hint style="info" %}
**Key points**

* CollieAi detects and redacts personally identifiable information (PII) on both input and output.
* It offers three methods: regex patterns, checksum-validated structured IDs, and dictionary matching.
* Structured-ID validation (Luhn, MOD-97, ISO 9362) produces fewer false positives than regex alone.
* You can combine all three rule types in one policy to cover formatted data, validated IDs, and custom terms.
{% endhint %}

## Rule Types

### [Regex Patterns](regex-patterns.md)

Pattern-based detection using regular expressions. Best for data that follows predictable text formats.

**Use when detecting:**

* Email addresses
* Phone numbers
* Social Security Numbers
* API keys and secrets
* Any data matching a known text pattern

### [Structured IDs](structured-ids.md)

Checksum-validated detection for identifiers with built-in validation algorithms. Produces fewer false positives than regex alone.

**Use when detecting:**

* Credit card numbers (Luhn algorithm)
* IBAN numbers (MOD-97-10)
* SWIFT/BIC codes (ISO 9362)
* National identity numbers with checksum validation

### [Dictionary Matching](dictionary-matching.md)

Fast multi-pattern matching against word lists. Ideal for organization-specific terms and custom blocklists.

**Use when detecting:**

* Company-specific terms and internal project names
* Custom PII keyword lists
* Known entity names (people, organizations)
* Profanity and prohibited terms

## Which PII rule type should you use?

| Scenario                          | Recommended Rule Type             |
| --------------------------------- | --------------------------------- |
| Emails, phone numbers, SSNs       | Regex Patterns                    |
| Credit card numbers, IBANs        | Structured IDs                    |
| Custom word lists, internal terms | Dictionary Matching               |
| API keys, tokens, secrets         | Regex Patterns (built-in presets) |
| National IDs with checksums       | Structured IDs                    |
| Profanity filtering               | Dictionary Matching               |

You can combine multiple rule types in a single policy. For example, use Regex Patterns for emails and phone numbers, Structured IDs for credit cards, and Dictionary Matching for company-specific terms -- all evaluated in the order you define.

### Frequently asked questions

**How does CollieAi detect and redact PII?** CollieAi detects and redacts PII using three rule types — regex patterns for formatted data, checksum-validated structured IDs for identifiers like credit cards and IBANs, and dictionary matching for custom term lists — and masks matches with placeholders on both input and output.

**What types of PII can CollieAi detect?** CollieAi can detect emails, phone numbers, Social Security Numbers, and API keys or secrets (regex); credit card numbers, IBANs, SWIFT/BIC codes, and national IDs with checksum validation (structured IDs); and custom terms like internal project or entity names (dictionary matching).

**Can I use more than one PII rule type at once?** Yes. You can combine regex patterns, structured IDs, and dictionary matching in a single policy, and CollieAi evaluates them in the order you define.

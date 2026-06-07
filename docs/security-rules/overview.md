---
description: >-
  How CollieAi security rules work — the input/output guardrails pipeline with 9
  rule types for PII redaction, prompt injection blocking, and text processing.
icon: toggle-large-on
---

# Overview

Security rules are the core of CollieAi's guardrails. A security rule defines what to look for in a message and what to do when a match is found — mask it, block it, or allow it. Rules are organized inside [policies](../projects-and-policies/policies.md), and each [project](../projects-and-policies/projects.md) has one active policy at a time.

{% hint style="info" %}
**Key points**

* Security rules are CollieAi's guardrails — they inspect, mask, or block content on both input and output.
* CollieAi provides 9 rule types in 3 categories: PII detection, threat blocking, and text processing.
* Each rule has a decision (`allow`, `mask`, or `block`) and a direction (input, output, or all).
* Rules run in order inside a policy, and each project has one active policy at a time.
* Monitor mode lets you test rules without masking or blocking real traffic.
{% endhint %}

## How does the security rules pipeline work?

Every request passes through a multi-stage pipeline:

```
1. Authenticate    -->  Validate the API key and load the project's policy
2. Input filter    -->  Apply input rules to the user's message
3. Proxy / Process -->  Forward the (filtered) request to the LLM provider
4. Output filter   -->  Apply output rules to the model's response
5. Return          -->  Send the filtered response back to your application
```

If any rule with a **block** decision triggers during the input stage, the request is rejected immediately and never reaches the provider.

## Rule Properties

Every rule has the following properties:

| Property      | Description                                                                           |
| ------------- | ------------------------------------------------------------------------------------- |
| **Name**      | A human-readable label for the rule.                                                  |
| **Type**      | Determines what the rule does (e.g., `regex`, `structured_id`, `llm_detection`).      |
| **Order**     | Numeric value that controls when this rule runs relative to others. Lower runs first. |
| **Direction** | Which stage of the pipeline the rule applies to: **Input**, **Output**, or **All**.   |
| **Decision**  | What happens when the rule matches: `allow`, `mask`, or `block`.                      |

## Processing Order

Rules execute in ascending order by the **order** field. If two rules share the same order value, the one created first runs first.

Choose order values intentionally -- the sequence matters because earlier rules can change the content that later rules see.

## Decisions

When a rule matches content, its **decision** determines what happens next:

| Decision  | Behavior                                                                                                              |
| --------- | --------------------------------------------------------------------------------------------------------------------- |
| **Allow** | The content is explicitly permitted. **Processing stops** -- no further rules are evaluated.                          |
| **Mask**  | The matched content is replaced with a placeholder (e.g., `****`). Processing **continues** with the remaining rules. |
| **Block** | The entire request is rejected with a `policy_violation` error. **Processing stops** immediately.                     |

Because `allow` and `block` both stop the pipeline, put your most important rules first.

## Directions

| Direction  | When it runs                                                                                        |
| ---------- | --------------------------------------------------------------------------------------------------- |
| **Input**  | Before the request is sent to the LLM provider. Use this to filter what the model sees.             |
| **Output** | After the response comes back from the provider. Use this to filter what your application receives. |
| **All**    | Runs on both input and output stages.                                                               |

## What are the 9 security rule types?

CollieAi provides 9 rule types organized into three categories:

### PII Detection

Identify and mask personally identifiable information.

| Type                                                         | Description                                                                                                                                                 |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Regex Patterns**](detecting-pii/regex-patterns.md)        | Match custom patterns (emails, phone numbers, account IDs) using regular expressions.                                                                       |
| [**Structured IDs**](detecting-pii/structured-ids.md)        | Detect credit card numbers, IBANs, BIC/SWIFT codes, and national IDs with checksum validation.                                                              |
| [**Dictionary Match**](detecting-pii/dictionary-matching.md) | Fast multi-pattern matching against word lists. Link a dictionary of terms (names, company names, medical terms) and find all occurrences in a single pass. |

### Threat Blocking

Prevent malicious or unwanted content from reaching the model or your users.

| Type                                                         | Description                                                                                                                |
| ------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| [**Prompt Injection**](blocking-threats/prompt-injection.md) | A lightweight ML classifier that detects prompt injection and jailbreak attempts with a configurable confidence threshold. |
| [**LLM Detection**](blocking-threats/llm-detection.md)       | Uses a secondary LLM call to analyze messages for sophisticated injection attacks that evade simpler classifiers.          |
| [**URL Filtering**](blocking-threats/url-filtering.md)       | Inspect URLs in messages. Allow or deny specific schemes, domains, and ports. Block IP literals and encoded patterns.      |
| [**Base64 Payloads**](blocking-threats/base64-payloads.md)   | Detect base64-encoded content that might hide malicious payloads. Configure minimum length and file signature detection.   |

### Text Processing

Normalize or classify content before other rules run.

| Type                                                            | Description                                                                                                                   |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| [**Normalization**](text-processing/normalization.md)           | Standardize Unicode, whitespace, and encoding to prevent rule-evasion tricks (homoglyphs, zero-width characters, diacritics). |
| [**Language Detection**](text-processing/language-detection.md) | Identify the language of the content and optionally block unsupported languages.                                              |

## How should you order security rules?

A well-ordered pipeline processes text in layers. Here is a recommended pattern:

| Order Range   | Purpose            | Example Rules                                                  |
| ------------- | ------------------ | -------------------------------------------------------------- |
| **1 -- 5**    | Text normalization | Normalization (clean up Unicode tricks before other rules run) |
| **5 -- 10**   | Whitelisting       | Allow rules for trusted patterns or known-safe content         |
| **10 -- 50**  | PII masking        | Regex, Structured ID, and Dictionary rules                     |
| **50 -- 100** | Threat blocking    | Prompt injection, LLM detection, URL filtering, Base64         |

This ordering ensures that normalization happens first (so attackers cannot bypass rules with encoding tricks), then trusted content is allowed through, then sensitive data is masked, and finally threats are blocked.

## Enforcement Mode

Policies can run in **enforce** or **monitor** mode. In monitor mode, rules still evaluate and their results are recorded, but content is never actually masked or blocked. This is useful for testing new rules before enabling them in production.

See [Enforcement Mode](enforcement-mode.md) for details.

## Next Steps

* [Enforcement Mode](enforcement-mode.md) -- Understand enforce vs. monitor mode.
* [Detecting PII](detecting-pii/) -- Regex, structured IDs, and dictionary matching.
* [Blocking Threats](blocking-threats/) -- Prompt injection, LLM detection, URL filtering, base64.
* [Text Processing](text-processing/) -- Normalization and language detection.
* [Policies](../projects-and-policies/policies.md) -- How rules are organized into policies.

### Frequently asked questions

**What is a security rule in CollieAi?** A security rule in CollieAi is a guardrail that defines what to look for in a message and what to do on a match — allow, mask, or block — applied to input, output, or both.

**What types of security rules does CollieAi support?** CollieAi supports 9 rule types in three categories: PII detection (regex patterns, structured IDs, dictionary matching), threat blocking (prompt injection, LLM detection, URL filtering, base64 payloads), and text processing (normalization, language detection).

**What is the difference between mask and block?** A mask decision replaces the matched content with a placeholder and lets processing continue, while a block decision rejects the entire request with a policy\_violation error and stops the pipeline.

**Can I test security rules before enforcing them?** Yes. CollieAi policies can run in monitor mode, where rules evaluate and results are recorded but content is never actually masked or blocked — useful for testing new rules before production.

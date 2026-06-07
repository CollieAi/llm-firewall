---
description: >-
  How CollieAi text-processing rules prepare LLM messages — Unicode
  normalization to defeat obfuscation and language detection to enforce language
  policies before other rules run.
icon: input-text
---

# Text Processing

{% hint style="info" %}
**Key points**

* Text-processing rules transform and analyze message content before PII and threat rules evaluate it.
* CollieAi offers two: normalization (defeats Unicode, homoglyph, and zero-width obfuscation) and language detection.
* Run them early — but place ML rules (prompt injection, LLM detection) before normalization, since those models expect natural text.
* Language detection shares the detected language with downstream rules for language-based model routing.
{% endhint %}

Text processing rules transform and analyze message content before other rules evaluate it. Place these rules early in your rule order so that downstream rules (PII detection, threat blocking) work with clean, standardized text.

### Rule Types <a href="#rule-types" id="rule-types"></a>

#### [Normalization](normalization.md)

Standardizes text to defeat obfuscation techniques. Handles Unicode normalization, homoglyph mapping, zero-width character removal, and more.

**Use for:** Preventing evasion via Cyrillic lookalikes, zero-width characters, Unicode tricks, and whitespace manipulation.

#### [Language Detection](language-detection.md)

Identifies the language of a message and optionally restricts which languages are allowed through the pipeline. Shares detected language context with downstream rules.

**Use for:** Enforcing language policies, routing messages to language-specific models, blocking unsupported languages.

### Where should text-processing rules run? <a href="#recommended-placement" id="recommended-placement"></a>

Text processing rules should run early in the pipeline. However, ML-based rules (prompt injection, LLM detection) should run **before** normalization because they are trained on natural text.

A typical ordering:

| Order | Rule Type                        |
| ----- | -------------------------------- |
| 1     | Language Detection               |
| 2-3   | Prompt Injection / LLM Detection |
| 4-5   | Normalization                    |
| 6+    | URL Filtering, Base64, PII rules |

This ensures language context is available for ML model routing, ML models see the original text, and all subsequent rules benefit from normalized input.

### Frequently asked questions

**How does CollieAi prevent obfuscation and evasion?** CollieAi's normalization rule standardizes Unicode, maps homoglyphs such as Cyrillic lookalikes, and strips zero-width characters and whitespace tricks, so attackers can't bypass downstream rules with encoding tricks.

**Can CollieAi restrict which languages are allowed?** Yes. The language detection rule identifies a message's language and can block unsupported languages or route messages to language-specific models, sharing the detected language with downstream rules.

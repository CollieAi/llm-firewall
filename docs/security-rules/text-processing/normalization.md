---
description: >-
  How CollieAi normalization defeats text obfuscation — Unicode (NFKC),
  homoglyph mapping, zero-width removal, and whitespace cleanup so downstream
  rules see clean, standardized text.
icon: horizontal-rule
---

# Normalization

## What is the normalization rule type?

The Normalization rule type applies configurable text transformations to normalize messages before they are processed by subsequent rules in the filtering pipeline. Unlike other rules that detect and block/mask content, normalization rules transform the message text itself, making downstream pattern matching more effective.

**Ideal for:**

* Defeating text obfuscation techniques (homoglyphs, zero-width characters)
* Standardizing Unicode representations for consistent matching
* Preparing text for case-insensitive pattern detection
* Removing invisible characters used for watermarking or evasion
* Normalizing whitespace for cleaner text processing

{% hint style="info" %}
**Key points**

* Normalization transforms message text before other rules run, so downstream detection sees clean, standardized input.
* It defeats obfuscation: Unicode normalization (NFKC), homoglyph mapping (e.g. Cyrillic lookalikes), zero-width removal, and whitespace cleanup.
* It always transforms but never blocks, and preserves the original text hash and sample for auditing.
* Place it early — but after ML rules (prompt injection, LLM detection), which expect natural, un-normalized text.
{% endhint %}

## How does normalization work?

1. **Pipeline Position:** Place normalization rules early in the rule chain so subsequent rules see normalized text
2. **Transformation Order:** Transformations are applied in a stable, predictable order
3. **Pass-Through Behavior:** Normalization rules always "match" (if changes occur) but never block
4. **Audit Trail:** Original text is preserved in metadata (hash + sample) for auditing
5. **Cumulative Effect:** Rules after normalization see the transformed text

## Transformation Order

When multiple transformations are enabled, they are applied in this fixed order:

1. **Unicode Normalization** - Canonical form normalization (NFC, NFD, NFKC, NFKD)
2. **Lowercase** - Convert to lowercase
3. **Diacritics Removal** - Strip accent marks
4. **Homoglyph Mapping** - Map lookalike characters to ASCII
5. **Zero-Width Removal** - Remove invisible characters
6. **Whitespace Collapse** - Normalize and collapse whitespace
7. **Punctuation Trimming** - Remove leading/trailing punctuation

## Available Transformations

### Unicode Normalization

Applies Unicode normalization forms to standardize character representations.

| Form   | Description                         | Use Case                               |
| ------ | ----------------------------------- | -------------------------------------- |
| `NFC`  | Canonical composition               | Compose characters (e + accent -> e)   |
| `NFD`  | Canonical decomposition             | Decompose characters (e -> e + accent) |
| `NFKC` | Compatibility composition (default) | Strongest normalization                |
| `NFKD` | Compatibility decomposition         | Decompose compatibility chars          |

**NFKC** (the default) is recommended because it:

* Converts fullwidth characters to ASCII: `Ｈｅｌｌｏ` -> `Hello`
* Normalizes ligatures: `ﬁle` -> `file`
* Composes combining marks

### Lowercase Conversion

Converts all text to lowercase for case-insensitive downstream matching.

```
INPUT:  "Hello WORLD Mixed Case"
OUTPUT: "hello world mixed case"
```

### Diacritics Removal

Removes accents and diacritical marks from characters.

```
INPUT:  "cafe resume naive senor"
OUTPUT: "cafe resume naive senor"
```

{% hint style="warning" %}
This may affect languages where diacritics carry semantic meaning (e.g., Vietnamese, Arabic).
{% endhint %}

### Homoglyph Mapping

Converts visually similar Unicode characters to their ASCII equivalents. This defeats obfuscation attempts using lookalike characters from other scripts.

**Covered character sets:**

* Cyrillic lookalikes: `а` (U+0430) -> `a`, `е` (U+0435) -> `e`, etc.
* Greek lookalikes: `Α` (U+0391) -> `A`, `Ο` (U+039F) -> `O`, etc.
* Fullwidth characters: `Ａ` (U+FF21) -> `A`, etc.
* Mathematical symbols: `²` -> `2`, etc.
* Typography variants: -> `-`, \`\` -> `'`, etc.

```
INPUT:  "pаsswоrd" (Cyrillic а and о)
OUTPUT: "password"
```

### Zero-Width Character Removal

Removes invisible zero-width characters often used for:

* Text obfuscation (breaking up keywords)
* Watermarking/fingerprinting
* Bypass attempts

**Removed characters:**

| Character | Name                  |
| --------- | --------------------- |
| `U+200B`  | Zero-width space      |
| `U+200C`  | Zero-width non-joiner |
| `U+200D`  | Zero-width joiner     |
| `U+200E`  | Left-to-right mark    |
| `U+200F`  | Right-to-left mark    |
| `U+2060`  | Word joiner           |
| `U+FEFF`  | Byte order mark (BOM) |

```
INPUT:  "pass\u200Bword" (zero-width space in middle)
OUTPUT: "password"
```

### Whitespace Collapse

Normalizes various whitespace characters and collapses multiple consecutive whitespace into single spaces.

**Normalizes:**

* Multiple spaces -> single space
* Tab characters -> space
* Unicode spaces (em space, hair space, etc.) -> ASCII space
* Multiple newlines (3+) -> double newline

```
INPUT:  "hello    world\t\ttabs"
OUTPUT: "hello world tabs"
```

### Punctuation Trimming

Removes leading and trailing punctuation and whitespace from the message.

```
INPUT:  "...Hello World!!!"
OUTPUT: "Hello World"
```

{% hint style="info" %}
Punctuation in the middle of the message is preserved.
{% endhint %}

## Rule Configuration

### Properties

| Property                | Type    | Required | Default | Description                        |
| ----------------------- | ------- | -------- | ------- | ---------------------------------- |
| `unicode_normalization` | boolean | No       | `false` | Apply Unicode normalization        |
| `unicode_form`          | string  | No       | `NFKC`  | Form: `NFC`, `NFD`, `NFKC`, `NFKD` |
| `lowercase`             | boolean | No       | `false` | Convert to lowercase               |
| `remove_diacritics`     | boolean | No       | `false` | Remove accents/diacritics          |
| `homoglyph_mapping`     | boolean | No       | `false` | Map homoglyphs to ASCII            |
| `remove_zero_width`     | boolean | No       | `false` | Remove zero-width characters       |
| `collapse_whitespace`   | boolean | No       | `false` | Collapse multiple whitespace       |
| `trim_punctuation`      | boolean | No       | `false` | Trim leading/trailing punctuation  |

{% hint style="info" %}
At least one transformation must be enabled for the rule to be valid.
{% endhint %}

### Example Configuration

```json
{
  "unicode_normalization": true,
  "unicode_form": "NFKC",
  "lowercase": true,
  "homoglyph_mapping": true,
  "remove_zero_width": true,
  "collapse_whitespace": true
}
```

## Example Rules

### 1. Anti-Obfuscation Normalization

Defeats common text obfuscation techniques:

```json
{
  "name": "Anti-Obfuscation",
  "rule_type": "normalization",
  "order": 1,
  "direction": "inbound",
  "decision": "mask",
  "config": {
    "unicode_normalization": true,
    "homoglyph_mapping": true,
    "remove_zero_width": true
  }
}
```

### 2. Case-Insensitive Preparation

Prepare text for case-insensitive keyword detection:

```json
{
  "name": "Lowercase Normalization",
  "rule_type": "normalization",
  "order": 2,
  "direction": "all",
  "decision": "mask",
  "config": {
    "lowercase": true
  }
}
```

### 3. Full Text Cleanup

Comprehensive normalization for clean text:

```json
{
  "name": "Full Text Cleanup",
  "rule_type": "normalization",
  "order": 1,
  "direction": "inbound",
  "decision": "mask",
  "config": {
    "unicode_normalization": true,
    "lowercase": true,
    "remove_diacritics": true,
    "homoglyph_mapping": true,
    "remove_zero_width": true,
    "collapse_whitespace": true,
    "trim_punctuation": true
  }
}
```

### 4. Whitespace-Only Normalization

Clean up whitespace without changing characters:

```json
{
  "name": "Whitespace Cleanup",
  "rule_type": "normalization",
  "order": 3,
  "direction": "all",
  "decision": "mask",
  "config": {
    "collapse_whitespace": true,
    "trim_punctuation": true
  }
}
```

### 5. Unicode Standardization for Output

Ensure LLM responses use standard characters:

```json
{
  "name": "Output Unicode Standardization",
  "rule_type": "normalization",
  "order": 1,
  "direction": "outbound",
  "decision": "mask",
  "config": {
    "unicode_normalization": true,
    "unicode_form": "NFC"
  }
}
```

## Metadata Output

When a normalization rule matches (applies changes), the metadata includes:

```json
{
  "normalization_applied": true,
  "transformations_applied": ["unicode_normalization", "lowercase", "homoglyph_mapping"],
  "transformation_count": 3,
  "transformation_details": {
    "unicode_normalization": {
      "form": "NFKC",
      "chars_changed": 5
    },
    "lowercase": {
      "chars_changed": 12
    },
    "homoglyph_mapping": {
      "homoglyphs_found": 3,
      "unique_homoglyphs": 2,
      "sample_mappings": ["а -> a", "о -> o"]
    }
  },
  "original_text_hash": "sha256...",
  "original_text_sample": "First 100 chars of original...",
  "original_length": 150,
  "normalized_length": 145,
  "length_change": -5
}
```

## Rule Chain Placement

### Recommended Position

Place normalization rules **early** in the rule chain (low `order` value):

```
1. Normalization Rule (order: 1)    <- Text normalized here
2. Keyword Detection (order: 10)    <- Sees normalized text
3. Regex Pattern (order: 20)        <- Sees normalized text
4. PII Masking (order: 30)          <- Sees normalized text
```

### Before vs. After

| Placement                  | Effect                                                    |
| -------------------------- | --------------------------------------------------------- |
| **Before detection rules** | Detection rules match normalized text (recommended)       |
| **After detection rules**  | Detection rules see raw text, may miss obfuscated content |

### Multiple Normalization Rules

You can use multiple normalization rules if needed:

```
1. Zero-width removal (order: 1)    <- Security-critical
2. Homoglyph mapping (order: 2)     <- Security-critical
3. Keyword detection (order: 10)
4. Lowercase for logging (order: 90) <- Non-security
```

## Use Cases

### Security

**Homoglyph Attack Prevention**

Attackers may use Cyrillic characters to bypass keyword filters:

```
"ignore previous instructions" -> "іgnore prevіous іnstructіons" (Cyrillic і)
```

Homoglyph mapping normalizes these to detectable ASCII.

**Zero-Width Evasion Prevention**

Attackers may insert zero-width characters to break keyword matching:

```
"password" -> "pass\u200Bword" (invisible character in middle)
```

Zero-width removal makes the keyword detectable.

**Unicode Normalization Attacks**

Different Unicode representations of the same visual text:

```
"file" (ASCII) vs "ﬁle" (ligature) vs "file" (fullwidth)
```

NFKC normalization ensures consistent representation.

### Compliance

* Standardize text encoding for consistent audit logs
* Ensure reproducible pattern matching across systems
* Create canonical form of all messages for archival

### Cost Optimization

* Remove invisible characters that consume tokens
* Collapse whitespace to reduce message size
* Trim unnecessary punctuation

## Limitations

1. **Language Impact:** Diacritics removal affects meaning in some languages
2. **Lossy Transformation:** Original characters cannot be recovered (but hash is preserved)
3. **Not Reversible:** Original text is only available in metadata, not the message
4. **Order Dependency:** Transformation order is fixed; cannot be customized
5. **Coverage:** Homoglyph mapping covers common cases but not all possible confusables

## Troubleshooting

### Transformations Not Applied

1. Verify at least one transformation is enabled in config
2. Check if the message already matches the normalized form
3. Enable the specific transformation for the obfuscation type

### Text Changed Unexpectedly

1. Review which transformations are enabled
2. Check `transformation_details` in metadata to see what changed
3. Disable transformations that are too aggressive for your use case

### Pattern Still Not Matching

1. Verify normalization rule runs before detection rule (lower `order` value)
2. Check if the obfuscation technique is covered by enabled transformations
3. Test with the `/test` endpoint to see normalized output

### Performance Issues

1. Place normalization rules early to avoid re-processing
2. Enable only necessary transformations
3. Consider using direction filtering to skip unnecessary normalization

## Performance Considerations

1. **Transformation Count:** Each enabled transformation adds processing time
2. **Message Length:** Processing time scales with message length
3. **Homoglyph Mapping:** O(n) character-by-character lookup
4. **Unicode Normalization:** Uses Python's `unicodedata` (optimized C implementation)
5. **Regex Operations:** Whitespace collapse and punctuation trim use regex

Typical processing time: <1ms for messages under 10KB with all transformations enabled.

### Frequently asked questions

**How does CollieAi stop homoglyph and zero-width evasion?** CollieAi's normalization rule maps homoglyphs such as Cyrillic lookalikes to ASCII and strips zero-width characters, so an obfuscated phrase like "іgnore prevіous іnstructіons" becomes detectable plain text for downstream rules.

**Does normalization block content?** No. Normalization only transforms the message text so later rules match more reliably; it never blocks on its own and preserves the original text hash and sample for auditing.

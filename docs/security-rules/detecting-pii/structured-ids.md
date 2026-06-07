---
description: >-
  How CollieAi structured-ID detection redacts PII — checksum-validated credit
  cards (Luhn), IBANs (MOD-97), SWIFT/BIC, and national IDs, with far fewer
  false positives than regex.
icon: id-card
---

# Structured IDs

## What is the structured ID rule type?

The Structured ID Detection rule type enables detection and handling of structured identifiers such as credit cards, IBAN, SWIFT/BIC codes, and national IDs. Unlike simple regex patterns, this rule uses **checksum/format validation** to reduce false positives.

**Ideal for:**

* Credit card number detection (PCI DSS compliance)
* International Bank Account Number (IBAN) detection
* SWIFT/BIC code detection
* National ID number detection (tax IDs, social security numbers)

{% hint style="info" %}
**Key points**

* Structured-ID detection redacts identifiers like credit cards, IBANs, SWIFT/BIC codes, and national IDs.
* It validates checksums (Luhn, MOD-97-10, ISO 7064), so it produces far fewer false positives than regex.
* `require_valid_checksum` (default `true`) rejects random or invalid numbers that merely look like IDs.
* Three mask styles are available: `partial` (default), `full`, and `type_only`.
{% endhint %}

## How does structured ID detection work?

1. Candidate tokens are extracted using pattern matching
2. Tokens are normalized (remove spaces/dashes, uppercase)
3. Checksum/format validation is applied per ID type
4. Valid IDs are masked or used to block/allow the message
5. Metadata includes type detected, normalized value, and checksum status

## Supported ID Types

### Financial Identifiers

#### Credit Cards (Luhn Algorithm)

* **Visa**: 13-16 digits starting with 4
* **Mastercard**: 16 digits starting with 51-55 or 2221-2720
* **American Express**: 15 digits starting with 34 or 37
* **Discover**: 16 digits starting with 6011 or 65
* **Diners Club**: 14 digits starting with 300-305, 36, or 38
* **JCB**: 15-16 digits starting with 2131, 1800, or 35

Validation: ISO/IEC 7812-1 Luhn algorithm

#### IBAN (ISO 13616)

Supported countries include: Germany (DE), UK (GB), France (FR), Spain (ES), Italy (IT), Netherlands (NL), Belgium (BE), Switzerland (CH), Austria (AT), and 60+ more.

Validation: MOD-97-10 check digit calculation

#### SWIFT/BIC (ISO 9362)

Format: `BBBBCCLLXXX`

* BBBB: 4-letter bank code
* CC: 2-letter country code
* LL: 2-character location code
* XXX: Optional 3-character branch code

Validation: Length (8 or 11) and character type validation

### National IDs with Checksum Validation

| ID Type     | Country | Format                       | Checksum           |
| ----------- | ------- | ---------------------------- | ------------------ |
| `de_tax_id` | Germany | 11 digits                    | ISO 7064 MOD 11,10 |
| `pl_pesel`  | Poland  | 11 digits (YYMMDDZZZXQ)      | Weighted sum       |
| `es_dni`    | Spain   | 8 digits + letter            | MOD 23             |
| `es_nie`    | Spain   | X/Y/Z + 7 digits + letter    | MOD 23             |
| `uk_nino`   | UK      | AA999999A                    | Format validation  |
| `fr_nir`    | France  | 15 digits (SYYMMDDDOOONNNCC) | MOD 97             |
| `br_cpf`    | Brazil  | 11 digits (NNN.NNN.NNN-DD)   | Double check digit |
| `ca_sin`    | Canada  | 9 digits (NNN-NNN-NNN)       | Luhn               |

## Rule Configuration

### Properties

| Property                 | Type    | Required | Default   | Description                                                                                                                                                 |
| ------------------------ | ------- | -------- | --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `detect_credit_cards`    | boolean | No       | `true`    | Detect credit card numbers                                                                                                                                  |
| `detect_iban`            | boolean | No       | `true`    | Detect IBAN numbers                                                                                                                                         |
| `detect_bic`             | boolean | No       | `true`    | Detect BIC/SWIFT codes                                                                                                                                      |
| `bic_require_digit`      | boolean | No       | `true`    | Only detect BICs with digits (e.g., BOFAUS3N). Prevents false positives from English words. Set to `false` to also detect all-letter BICs (e.g., DEUTDEFF). |
| `detect_national_ids`    | boolean | No       | `false`   | Detect national ID numbers                                                                                                                                  |
| `national_id_types`      | list    | No       | all       | Which national ID types to detect                                                                                                                           |
| `require_valid_checksum` | boolean | No       | `true`    | Only match IDs with valid checksums                                                                                                                         |
| `replacement`            | string  | No       | -         | Custom replacement text                                                                                                                                     |
| `mask_style`             | string  | No       | `partial` | How to mask: `full`, `partial`, `type_only`                                                                                                                 |

### Example Configuration

```json
{
  "detect_credit_cards": true,
  "detect_iban": true,
  "detect_bic": true,
  "bic_require_digit": true,
  "detect_national_ids": true,
  "national_id_types": ["de_tax_id", "uk_nino", "br_cpf"],
  "require_valid_checksum": true,
  "mask_style": "partial"
}
```

## Masking Styles

### partial (default)

Shows partial information for audit purposes:

* Credit cards: `************0366` (last 4 digits)
* IBAN: `DE89********3000` (country + check digits + last 4)
* BIC: `DEUT****` (bank + country code)
* National IDs: `12****78` (first 2 + last 2)

### full

Complete masking:

* `4532015112830366` → `****************`

### type\_only

Type-labeled replacement:

* `4532015112830366` → `[CREDIT_CARD_VISA_REDACTED]`
* `DE89370400440532013000` → `[IBAN_REDACTED]`

## Example Rules

{% stepper %}
{% step %}
### Block Credit Cards (PCI Compliance)

```json
{
  "name": "Block Credit Cards",
  "rule_type": "structured_id",
  "order": 1,
  "direction": "all",
  "decision": "block",
  "config": {
    "detect_credit_cards": true,
    "detect_iban": false,
    "detect_bic": false,
    "require_valid_checksum": true
  },
  "block_message": "Credit card numbers are not allowed"
}
```
{% endstep %}

{% step %}
### Mask Financial Data (Input)

```json
{
  "name": "Mask Financial Data",
  "rule_type": "structured_id",
  "order": 5,
  "direction": "inbound",
  "decision": "mask",
  "config": {
    "detect_credit_cards": true,
    "detect_iban": true,
    "detect_bic": true,
    "mask_style": "partial"
  }
}
```
{% endstep %}

{% step %}
### Detect European National IDs (Output)

```json
{
  "name": "Mask EU National IDs",
  "rule_type": "structured_id",
  "order": 10,
  "direction": "outbound",
  "decision": "mask",
  "config": {
    "detect_credit_cards": false,
    "detect_iban": false,
    "detect_bic": false,
    "detect_national_ids": true,
    "national_id_types": ["de_tax_id", "fr_nir", "es_dni", "pl_pesel"],
    "replacement": "[NATIONAL_ID_REDACTED]"
  }
}
```
{% endstep %}

{% step %}
### Comprehensive PII Protection

```json
{
  "name": "Comprehensive PII Protection",
  "rule_type": "structured_id",
  "order": 3,
  "direction": "all",
  "decision": "mask",
  "config": {
    "detect_credit_cards": true,
    "detect_iban": true,
    "detect_bic": true,
    "detect_national_ids": true,
    "require_valid_checksum": true,
    "mask_style": "type_only"
  }
}
```
{% endstep %}
{% endstepper %}

## Metadata Output

When a structured ID rule matches, the metadata includes:

```json
{
  "matched_ids": [
    {
      "id_type": "credit_card_visa",
      "original": "4532-0151-1283-0366",
      "normalized": "4532015112830366",
      "masked": "************0366",
      "checksum_valid": true,
      "position": {"start": 10, "end": 29},
      "extra_info": {"issuer": "visa", "length": 16}
    }
  ],
  "id_count": 1,
  "id_types_found": ["credit_card_visa"]
}
```

## False Positive Reduction

The `require_valid_checksum` option (default: `true`) significantly reduces false positives:

| Scenario                            | Without Checksum | With Checksum |
| ----------------------------------- | ---------------- | ------------- |
| Random 16 digits "1234567890123456" | ✓ Matched        | ✗ Not matched |
| Order number "ORD-1234-5678-9012"   | ✓ Matched        | ✗ Not matched |
| Phone number "555-123-4567"         | ✗ Not matched    | ✗ Not matched |
| Valid Visa "4532015112830366"       | ✓ Matched        | ✓ Matched     |

## Checksum Algorithms Reference

### Luhn Algorithm (Credit Cards, Canadian SIN)

1. From rightmost digit, double every second digit
2. If result > 9, subtract 9
3. Sum all digits
4. Valid if sum mod 10 == 0

### IBAN MOD-97-10

1. Move first 4 characters to end
2. Convert letters to numbers (A=10, B=11, ..., Z=35)
3. Calculate mod 97
4. Valid if result == 1

### Spanish DNI/NIE

1. For NIE: X=0, Y=1, Z=2
2. Calculate: number mod 23
3. Map to control letter: TRWAGMYFPDXBNJZSQVHLCKE

## Limitations

1. **National IDs**: Only IDs with public checksum algorithms are supported
2. **False Negatives**: Malformed or truncated IDs may not be detected
3. **Context**: The rule doesn't understand context (e.g., "test card 4111111111111111")
4. **Overlapping Detection**: When multiple ID types could match, the first valid match wins

## Performance Considerations

1. Checksum validation adds minimal overhead (\~microseconds per ID)
2. Multiple ID types are checked sequentially
3. Enable only the ID types you need for best performance
4. Consider using `require_valid_checksum: true` to reduce processing

## Troubleshooting

### How does structured ID detection work?

1. Verify the ID format is supported
2. Check if `require_valid_checksum` is filtering it out
3. Ensure the correct ID type is enabled in config
4. Test with the `/test` endpoint

### Why are there too many false positives?

1. Enable `require_valid_checksum: true`
2. Disable ID types you don't need
3. Use more specific `national_id_types` list

### Why is checksum validation failing?

1. Verify the ID has correct check digits
2. Some test/example IDs may have invalid checksums
3. Check if separators (spaces/dashes) are being handled

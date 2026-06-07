---
description: >-
  How CollieAi detects base64 payloads — identify data URIs and raw base64 in
  prompts, tool calls, and responses, then block executables, enforce MIME and
  size limits, and stop exfiltration.
icon: square-binary
---

# Base64 Payloads

## What is base64 payload detection?

The Base64 Payload Detection rule type identifies and handles base64-encoded payloads embedded in prompts, tool-call arguments, or LLM responses. It supports both data URIs (`data:mime/type;base64,...`) and raw base64 strings.

**Ideal for:**

* Preventing binary data injection attacks
* Blocking embedded executables or scripts
* Enforcing content type policies on data URIs
* Data exfiltration prevention
* Compliance with payload size limits

{% hint style="info" %}
**Key points**

* Base64 payload detection finds data URIs and raw base64 strings in prompts, tool-call arguments, and LLM responses.
* It can identify file types from magic bytes and enforce MIME allowlists/blocklists, size limits, and payload counts.
* Use it to block embedded executables, prevent data exfiltration, and control token costs from large encoded data.
* A `min_length` threshold (default 50) and validation heuristics keep false positives low.
{% endhint %}

## How It Works

{% stepper %}
{% step %}
### Pattern Matching

Identifies data URIs and raw base64 sequences using regex patterns
{% endstep %}

{% step %}
### Validation

Confirms candidates are valid base64 (character set, padding, decode test)
{% endstep %}

{% step %}
### Optional File Detection

Decodes a prefix to identify file type from magic bytes
{% endstep %}

{% step %}
### Policy Filtering

Applies MIME allowlist/blocklist and size limits
{% endstep %}

{% step %}
### Masking/Blocking

Applies the configured decision (allow, mask, block)
{% endstep %}
{% endstepper %}

## Detection Modes

### Data URI Detection

Detects `data:*;base64,` patterns following RFC 2397.

```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUg...
data:;base64,SGVsbG8gV29ybGQ=
data:application/octet-stream;base64,AAAA...
```

### Raw Base64 Detection

Detects standalone base64 strings meeting configurable length thresholds.

Supports:

* Standard base64 alphabet: `A-Z`, `a-z`, `0-9`, `+`, `/`
* URL-safe base64 alphabet: `A-Z`, `a-z`, `0-9`, `-`, `_`
* Optional `=` padding

## Rule Configuration

### Properties

| Property                | Type    | Required | Default   | Description                                     |
| ----------------------- | ------- | -------- | --------- | ----------------------------------------------- |
| `min_length`            | integer | No       | `50`      | Minimum base64 string length to detect          |
| `max_length`            | integer | No       | -         | Maximum length to process                       |
| `max_decoded_bytes`     | integer | No       | -         | Flag payloads exceeding this decoded size       |
| `max_occurrences`       | integer | No       | -         | Flag messages with more than N payloads         |
| `allow_data_uris`       | boolean | No       | `true`    | Enable data URI detection                       |
| `detect_raw_base64`     | boolean | No       | `true`    | Enable raw base64 detection                     |
| `mime_allowlist`        | list    | No       | -         | Only flag payloads NOT in this list             |
| `mime_blocklist`        | list    | No       | -         | Flag these MIME types (priority over allowlist) |
| `detect_file_signature` | boolean | No       | `false`   | Detect file type from magic bytes               |
| `replacement`           | string  | No       | -         | Custom replacement text                         |
| `mask_style`            | string  | No       | `summary` | How to mask: `full`, `summary`, `type_only`     |

### Example Configuration

```json
{
  "min_length": 50,
  "max_decoded_bytes": 1048576,
  "allow_data_uris": true,
  "detect_raw_base64": true,
  "mime_blocklist": ["application/x-executable", "application/x-msdownload"],
  "detect_file_signature": true,
  "mask_style": "summary"
}
```

## Masking Styles

### summary (default)

Shows payload type and size:

* `data:image/png;base64,iVBORw0KGgo...` -> `[BASE64_PAYLOAD: image/png, 15.2KB]`

### full

Complete masking with asterisks:

* `data:image/png;base64,iVBORw0KGgo...` -> `**************************************************...`

### type\_only

Type-labeled replacement:

* `data:image/png;base64,iVBORw0KGgo...` -> `[BASE64_PAYLOAD_REDACTED]`

## File Signature Detection

When `detect_file_signature` is enabled, the rule decodes the first few bytes to identify file types from magic bytes:

| Signature          | MIME Type                  |
| ------------------ | -------------------------- |
| `\x89PNG`          | `image/png`                |
| `\xff\xd8\xff`     | `image/jpeg`               |
| `GIF87a`, `GIF89a` | `image/gif`                |
| `%PDF`             | `application/pdf`          |
| `PK\x03\x04`       | `application/zip`          |
| `\x1f\x8b`         | `application/gzip`         |
| `MZ`               | `application/x-msdownload` |
| `\x7fELF`          | `application/x-executable` |

This helps detect actual content when the data URI doesn't specify a MIME type.

## Example Rules

### 1. Block Large Payloads

```json
{
  "name": "Block Large Base64",
  "rule_type": "base64_payload",
  "order": 1,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "min_length": 50,
    "max_decoded_bytes": 1048576
  },
  "block_message": "Large binary payloads (>1MB) are not allowed"
}
```

### 2. Mask Embedded Images

```json
{
  "name": "Mask Embedded Images",
  "rule_type": "base64_payload",
  "order": 5,
  "direction": "all",
  "decision": "mask",
  "config": {
    "allow_data_uris": true,
    "detect_raw_base64": false,
    "mask_style": "summary"
  }
}
```

### 3. Block Executable Content

```json
{
  "name": "Block Executables",
  "rule_type": "base64_payload",
  "order": 1,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "allow_data_uris": true,
    "detect_file_signature": true,
    "mime_blocklist": [
      "application/x-executable",
      "application/x-msdownload",
      "application/x-mach-binary"
    ]
  },
  "block_message": "Executable content is not allowed"
}
```

### 4. Allow Only Image Types

```json
{
  "name": "Images Only",
  "rule_type": "base64_payload",
  "order": 3,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "allow_data_uris": true,
    "mime_allowlist": ["image/png", "image/jpeg", "image/gif", "image/webp"]
  },
  "block_message": "Only image data URIs are allowed"
}
```

### 5. Detect Multiple Payloads

```json
{
  "name": "Limit Payloads Per Message",
  "rule_type": "base64_payload",
  "order": 2,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "allow_data_uris": true,
    "detect_raw_base64": true,
    "max_occurrences": 3
  },
  "block_message": "Too many base64 payloads in a single message"
}
```

## Metadata Output

When a base64 payload rule matches, the metadata includes:

```json
{
  "matched_payloads": [
    {
      "payload_type": "data_uri",
      "original_length": 1234,
      "encoded_length": 1200,
      "decoded_size": 900,
      "mime_type": "image/png",
      "file_signature": "image/png",
      "position": {"start": 10, "end": 1244}
    }
  ],
  "payload_count": 1,
  "total_decoded_bytes": 900,
  "occurrence_violation": false,
  "mime_types_found": ["image/png"]
}
```

## False Positive Reduction

### Minimum Length Threshold

The `min_length` setting (default: 50) prevents matching short strings that look like base64 but aren't actual payloads:

| Setting           | Effect                                           |
| ----------------- | ------------------------------------------------ |
| `min_length: 50`  | Ignores short tokens, UUIDs, short API keys      |
| `min_length: 100` | More aggressive filtering, may miss small images |
| `min_length: 20`  | Catches smaller payloads, more false positives   |

### Validation Heuristics

The rule validates candidates to reduce false positives:

* Character set validation (base64 alphabet only)
* Padding validation (proper `=` or `==` suffix)
* Decode test on prefix to confirm validity
* Entropy check (rejects strings with all same character)

## Performance Considerations

1. **Minimum length:** Higher values reduce regex work
2. **File signature detection:** Adds decode overhead per payload
3. **Multiple payloads:** Processed sequentially, deduplicated
4. **Overlapping detection:** Automatically handled to prevent double-counting

## Limitations

1. **URL-encoded base64:** Doesn't detect base64 inside URL parameters
2. **Fragmented payloads:** Can't detect base64 split across messages
3. **Custom encodings:** Only standard and URL-safe base64 alphabets
4. **Nested data URIs:** Only detects outermost data URI

## Troubleshooting

### Why isn't my base64 payload detected?

{% stepper %}
{% step %}
### Check the length threshold

Check if length meets `min_length` threshold
{% endstep %}

{% step %}
### Verify detection settings

Verify `allow_data_uris` or `detect_raw_base64` is enabled
{% endstep %}

{% step %}
### Check MIME filtering

Check if MIME type is filtered by allowlist/blocklist
{% endstep %}

{% step %}
### Test the endpoint

Test with the `/test` endpoint
{% endstep %}
{% endstepper %}

### Why are there too many false positives?

{% stepper %}
{% step %}
### Increase the minimum length

Increase `min_length` (e.g., 100 or higher)
{% endstep %}

{% step %}
### Disable raw base64 detection if needed

Disable `detect_raw_base64` if only data URIs matter
{% endstep %}

{% step %}
### Use the MIME blocklist

Use `mime_blocklist` to target specific types
{% endstep %}
{% endstepper %}

### Why isn't the file type detected?

{% stepper %}
{% step %}
### Enable file signature detection

Enable `detect_file_signature: true`
{% endstep %}

{% step %}
### Check for known magic bytes

Check if file type has known magic bytes
{% endstep %}

{% step %}
### Account for unsupported signatures

Some files may not have recognizable signatures
{% endstep %}
{% endstepper %}

## Use Cases

### Security

* Block injection of malicious scripts via data URIs
* Prevent embedding of executable binaries
* Detect data exfiltration attempts via base64

### Compliance

* Enforce maximum payload sizes
* Restrict allowed content types
* Audit all embedded binary data

### Cost Control

* Prevent large image injection that increases token costs
* Limit number of payloads per request

### Frequently asked questions

**Why block base64 payloads in LLM messages?** Base64-encoded payloads can hide executables, scripts, or exfiltrated data inside prompts and responses. CollieAi detects data URIs and raw base64, identifies file types from magic bytes, and can block, mask, or size-limit them.

**Can CollieAi block embedded executables or large files?** Yes. With file-signature detection and a MIME blocklist you can block executables, and `max_decoded_bytes` and `max_occurrences` enforce size and payload-count limits per message.

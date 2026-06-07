---
description: >-
  How CollieAi language detection filters and routes LLM messages by language —
  FastText lid.176 across 176 languages, with allowlist/blocklist modes and
  language context for model routing.
icon: spell-check
---

# Language detection

## What is the language detection rule type?

The Language Detection rule type enables filtering messages based on detected language using FastText's lid.176 model. It supports 176 languages and provides both allowlist and blocklist modes.

**Ideal for:**

* Enforcing language policies (e.g., support only English)
* Blocking specific languages (e.g., compliance requirements)
* Routing messages based on language
* Detecting unexpected language usage

{% hint style="info" %}
**Key points**

* Language detection identifies a message's language with FastText lid.176 across 176 languages.
* Allowlist mode permits only chosen languages; blocklist mode blocks chosen ones — with a configurable confidence threshold.
* It writes the detected language to a shared context, enabling language-based routing to different ML models.
* It is fast (\~1–5 ms) and fails open by default, so detection failures don't block traffic unless you choose fail-closed.
{% endhint %}

## How does language detection work?

{% stepper %}
{% step %}
### Message is checked against minimum length requirement
{% endstep %}

{% step %}
### FastText lid.176 model detects the primary language
{% endstep %}

{% step %}
### Detection results are written to shared context for downstream rules

This enables downstream rules to access the language detection results.
{% endstep %}

{% step %}
### Detection confidence is compared against threshold
{% endstep %}

{% step %}
### Based on mode (allowlist/blocklist), message is allowed or blocked
{% endstep %}
{% endstepper %}

### Context Sharing

The language detection rule automatically writes detection results to a **shared filtering context** that downstream rules can access. This enables powerful use cases like **language-based model routing**.

**Data written to context:**

| Key                        | Type   | Description                                     |
| -------------------------- | ------ | ----------------------------------------------- |
| `detected_language`        | string | ISO 639-1 language code (lowercase)             |
| `language_confidence`      | float  | Detection confidence (0.0-1.0)                  |
| `language_all_predictions` | list   | All language predictions with confidence scores |

**Example:** A `lightweight_model` rule can read `detected_language` from context to apply different ML models based on message language. See [Lightweight Model - Language-Based Routing](language-detection.md) for details.

## Modes

### Allowlist Mode

Only messages in specified languages pass; all others are blocked/masked.

**Example:** Accept only English and Spanish:

```json
{
  "mode": "allowlist",
  "languages": ["en", "es"],
  "threshold": 0.5
}
```

### Blocklist Mode

Messages in specified languages are blocked; all others pass.

**Example:** Block Russian and Chinese:

```json
{
  "mode": "blocklist",
  "languages": ["ru", "zh"],
  "threshold": 0.5
}
```

## Rule Configuration

| Property            | Type   | Required | Default              | Description                            |
| ------------------- | ------ | -------- | -------------------- | -------------------------------------- |
| `mode`              | string | No       | `blocklist`          | `allowlist` or `blocklist`             |
| `languages`         | list   | **Yes**  | -                    | ISO 639-1 codes (e.g., `["en", "es"]`) |
| `threshold`         | float  | No       | `0.5`                | Confidence threshold (0.0-1.0)         |
| `min_length`        | int    | No       | `20`                 | Skip messages shorter than this        |
| `mask_placeholder`  | string | No       | `[LANGUAGE_BLOCKED]` | Replacement text                       |
| `decision_on_error` | string | No       | `allow`              | `allow` or `block` on failure          |
| `inference_timeout` | float  | No       | `5.0`                | Max detection time (seconds)           |

## Common Language Codes

| Code | Language   |
| ---- | ---------- |
| `en` | English    |
| `es` | Spanish    |
| `fr` | French     |
| `de` | German     |
| `it` | Italian    |
| `pt` | Portuguese |
| `ru` | Russian    |
| `zh` | Chinese    |
| `ja` | Japanese   |
| `ko` | Korean     |
| `ar` | Arabic     |
| `hi` | Hindi      |
| `nl` | Dutch      |
| `pl` | Polish     |
| `tr` | Turkish    |
| `vi` | Vietnamese |
| `th` | Thai       |
| `uk` | Ukrainian  |
| `cs` | Czech      |
| `sv` | Swedish    |

The model supports 176 languages. See [FastText documentation](https://fasttext.cc/docs/en/language-identification.html) for the full list.

## Example Configurations

### Accept English Only

```json
{
  "name": "English Only",
  "rule_type": "language_detection",
  "order": 5,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "mode": "allowlist",
    "languages": ["en"],
    "threshold": 0.7
  },
  "block_message": "Only English messages are accepted."
}
```

### Block Specific Languages

```json
{
  "name": "Block Restricted Languages",
  "rule_type": "language_detection",
  "order": 5,
  "direction": "all",
  "decision": "block",
  "config": {
    "mode": "blocklist",
    "languages": ["ru", "zh", "ar"],
    "threshold": 0.6
  },
  "block_message": "This language is not permitted."
}
```

### Multi-Language Support (EU Languages)

```json
{
  "name": "EU Languages Only",
  "rule_type": "language_detection",
  "order": 5,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "mode": "allowlist",
    "languages": ["en", "de", "fr", "es", "it", "pt", "nl", "pl", "cs", "sv", "da", "fi", "el", "hu", "ro", "bg", "sk", "sl", "hr", "lt", "lv", "et"],
    "threshold": 0.5
  },
  "block_message": "Only EU languages are supported."
}
```

### Strict English with High Confidence

```json
{
  "name": "Strict English Only",
  "rule_type": "language_detection",
  "order": 5,
  "direction": "inbound",
  "decision": "block",
  "config": {
    "mode": "allowlist",
    "languages": ["en"],
    "threshold": 0.9,
    "min_length": 50,
    "decision_on_error": "block"
  },
  "block_message": "High-confidence English content required."
}
```

## Threshold Guidelines

| Threshold | Trade-off                                    |
| --------- | -------------------------------------------- |
| `0.3`     | Very permissive, may have false positives    |
| `0.5`     | Balanced (recommended default)               |
| `0.7`     | More strict, fewer false positives           |
| `0.9`     | Very strict, may miss mixed-language content |

**Recommendations:**

* Use `0.5` for general language filtering
* Use `0.7-0.8` when accuracy is important
* Use `0.9` only for high-security scenarios

## Minimum Length

Short messages may produce unreliable language detection. The `min_length` parameter skips analysis for very short texts:

| min\_length | Effect                                 |
| ----------- | -------------------------------------- |
| `0`         | Analyze all messages (not recommended) |
| `20`        | Default - skip very short messages     |
| `50`        | Skip messages under 50 chars           |
| `100`       | More conservative, only longer texts   |

**Note:** Messages below `min_length` pass through without detection (they are not blocked).

## Error Handling

| `decision_on_error` | Behavior                                               |
| ------------------- | ------------------------------------------------------ |
| `allow`             | Fail-open: message passes if detection fails (default) |
| `block`             | Fail-closed: message blocked if detection fails        |

**Recommendations:**

* Use `allow` (fail-open) for most use cases
* Use `block` (fail-closed) for high-security scenarios where undetected content is risky

## Model Information

| Property           | Value                                             |
| ------------------ | ------------------------------------------------- |
| **Model**          | FastText lid.176.ftz                              |
| **Size**           | \~917KB (compressed)                              |
| **Languages**      | 176                                               |
| **Auto-download**  | Yes                                               |
| **Cache Location** | `~/.cache/fasttext/` or `$FASTTEXT_MODEL_DIR`     |
| **Preloading**     | Automatic at startup (when `PRELOAD_MODELS=true`) |

The model is automatically downloaded from Meta's CDN and preloaded at application startup for optimal performance.

## API Usage

### Create Rule

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/rules" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "English Only",
    "rule_type": "language_detection",
    "order": 10,
    "direction": "inbound",
    "decision": "block",
    "config": {
      "mode": "allowlist",
      "languages": ["en"],
      "threshold": 0.6
    },
    "block_message": "Only English messages are accepted."
  }'
```

### Test Rule

```bash
curl -X POST "http://localhost:8000/api/v1/projects/{project_id}/rules/{rule_id}/test" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Dies ist eine deutsche Nachricht.",
    "direction": "inbound"
  }'
```

**Example Response (blocked):**

```json
{
  "matched": true,
  "decision": "block",
  "modified_message": "[LANGUAGE_BLOCKED]",
  "match_info": {
    "mode": "allowlist",
    "detected_language": "de",
    "confidence": 0.9234,
    "threshold": 0.6,
    "configured_languages": ["en"],
    "all_predictions": [
      {"language": "de", "confidence": 0.9234},
      {"language": "nl", "confidence": 0.0421},
      {"language": "en", "confidence": 0.0123}
    ],
    "text_length": 34
  }
}
```

## Comparison with Other Rules

| Feature         | Language Detection | Regex     | Dictionary Match |
| --------------- | ------------------ | --------- | ---------------- |
| Detection Type  | ML-based           | Pattern   | Dictionary       |
| Languages       | 176                | N/A       | N/A              |
| Speed           | Fast (\~5ms)       | Very Fast | Very Fast        |
| False Positives | Low                | Depends   | Depends          |
| Mixed Content   | Detects primary    | Per-match | Per-match        |

## Performance

| Metric              | Value                   |
| ------------------- | ----------------------- |
| Model Load Time     | \~100ms (first request) |
| Inference Time      | \~1-5ms per message     |
| Memory Usage        | \~10MB                  |
| Concurrent Requests | Supported (thread pool) |

**Caching:**

* Model is loaded once and cached in memory
* Subsequent requests reuse the loaded model
* No per-request overhead after initial load

## Troubleshooting

### Why isn't language detection working?

1. Check that the message is longer than `min_length`
2. Verify FastText is installed: `pip install fasttext-wheel`
3. Check logs for model loading errors
4.  **Check model status via health endpoint:**

    ```bash
    curl http://localhost:8000/api/v1/health/models
    ```

    Expected response shows `"language_detection": {"loaded": true, ...}`

### Why are there too many false positives?

1. Increase `threshold` (e.g., 0.5 → 0.7)
2. Increase `min_length` for short messages
3. Check if content is mixed-language

### Why is the model not loading (rule fails open)?

**Symptom:** Messages in blocked languages pass through without being blocked.

**Cause:** The FastText model failed to load, and the rule fails open (default `decision_on_error: allow`).

**Diagnosis:**

1. Check startup logs for:
   * ✅ `"Language detection model (FastText) preloaded successfully"`
   * ❌ `"Failed to preload language detection model - language_detection rules will fail open!"`
2.  Check model status endpoint:

    ```bash
    curl http://localhost:8000/api/v1/health/models
    ```

    If `"language_detection": {"loaded": false}`, the model is not loaded.
3. Check runtime logs for:
   * `"Language detection returned None - model may not be loaded!"`

**Solutions:**

1. **Network access:** Ensure the server can reach `dl.fbaipublicfiles.com` to download the model
2. **Disk space:** Ensure \~2MB free for the model file
3. **Write permissions:** Verify cache directory is writable:
   * Default: `~/.cache/fasttext/`
   * Override with: `FASTTEXT_MODEL_DIR=/path/to/dir`
4. **Docker/containers:** Ensure the cache directory is on persistent storage or pre-download the model
5.  **Manual download:**

    ```bash
    mkdir -p ~/.cache/fasttext
    curl -o ~/.cache/fasttext/lid.176.ftz \
      https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
    ```

### Why is the detected language unexpected?

1. Use the test endpoint to see all predictions
2. Check confidence scores - low confidence may indicate mixed content
3. Consider adjusting threshold based on use case

### Production Deployment Checklist

1. ✅ `PRELOAD_MODELS=true` (default) to preload model at startup
2. ✅ Persistent storage for `~/.cache/fasttext/` or set `FASTTEXT_MODEL_DIR`
3. ✅ Network access to `dl.fbaipublicfiles.com` (or pre-download model)
4. ✅ Monitor startup logs for successful model loading
5. ✅ Use `/api/v1/health/models` to verify model status

## Limitations

* Detection is per-message (not per-sentence)
* Mixed-language content may produce unexpected results
* Very short messages may be unreliable
* Some similar languages may be confused (e.g., Norwegian/Danish, Serbian/Croatian)
* Code snippets and URLs may affect detection accuracy

## Best Practices

1. **Start with blocklist mode** for security-focused filtering
2. **Use allowlist mode** for strict language enforcement
3. **Set appropriate min\_length** to avoid false positives on short messages
4. **Test with real data** before deploying to production
5. **Monitor rule triggers** to fine-tune threshold
6. **Use fail-open** (`decision_on_error: allow`) unless security requires otherwise

***

## Language-Based Routing

The language detection rule can be used to **route messages to language-specific ML models** without blocking any languages. This is achieved through **context sharing** between rules.

### Use Case: Apply Different ML Models by Language

**Pipeline Configuration:**

```
Order 10: language_detection (detects language, writes to context)
Order 20: lightweight_model for English (reads from context, uses DeBERTa v3)
Order 30: lightweight_model for Russian (reads from context, uses Sentinel v2)
Order 100: lightweight_model catch-all (no language filter, processes remaining)
```

**Step 1: Language Detection (order=10)**

Configure to detect language without blocking:

```json
{
  "name": "Detect Language",
  "rule_type": "language_detection",
  "order": 10,
  "direction": "inbound",
  "decision": "allow",
  "config": {
    "mode": "blocklist",
    "languages": ["xx"],
    "threshold": 0.3
  }
}
```

> The `blocklist` mode with a non-existent language code (`"xx"`) ensures all real languages pass through while still writing detection results to context.

**Step 2: Language-Specific ML Rules (order=20+)**

Downstream `lightweight_model` rules can then use the `languages` configuration to process only specific languages:

```json
{
  "name": "English Prompt Guard",
  "rule_type": "lightweight_model",
  "order": 20,
  "config": {
    "model_id": "deepset/deberta-v3-base-injection",
    "languages": ["en"],
    "threshold": 0.80,
    "labels_to_block": ["INJECTION"]
  }
}
```

See [Lightweight Model - Language-Based Routing](language-detection.md) for complete configuration examples.

### Benefits

1. **No code changes** - Configure routing entirely through rule configuration
2. **Model optimization** - Use the best model for each language
3. **Performance** - Skip ML inference for languages a model wasn't trained on
4. **Flexibility** - Easy to add or modify language-specific models

### Frequently asked questions

**Can CollieAi detect and restrict the language of messages?** Yes. CollieAi's language detection rule identifies a message's language across 176 languages using FastText lid.176, and in allowlist or blocklist mode it can permit or block specific languages with a configurable confidence threshold.

**Can I route messages to different models by language?** Yes. Language detection writes the detected language to a shared context, so downstream ML rules can apply language-specific models — for example DeBERTa for English and Sentinel for Russian — without code changes.

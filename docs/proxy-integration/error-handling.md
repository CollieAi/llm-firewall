---
description: >-
  How CollieAi reports errors — the OpenAI-compatible error format, error types,
  policy-violation responses with triggered rules, and troubleshooting steps.
icon: lightbulb-exclamation-on
---

# Error handling

CollieAi returns all errors in the OpenAI-compatible format, so existing error handling code in your application works without changes. This page covers the error format, CollieAi-specific error types, and practical patterns for handling them.

## Error Response Format

Every error response follows the same structure:

```json
{
  "error": {
    "message": "Human-readable description of the error",
    "type": "error_type",
    "code": "specific_error_code"
  }
}
```

| Field     | Type           | Description                                              |
| --------- | -------------- | -------------------------------------------------------- |
| `message` | string         | A human-readable explanation of what went wrong.         |
| `type`    | string         | The category of error (see table below).                 |
| `code`    | string or null | A machine-readable error code for programmatic handling. |

## Error Types

| HTTP Status | Type                    | Code               | Description                                                 |
| ----------- | ----------------------- | ------------------ | ----------------------------------------------------------- |
| 400         | `policy_violation`      | `content_blocked`  | An input rule blocked the user's message.                   |
| 400         | `policy_violation`      | `response_blocked` | An output rule blocked the model's response.                |
| 400         | `invalid_request_error` | --                 | The request body is malformed or missing required fields.   |
| 401         | `authentication_error`  | `invalid_api_key`  | The API key is missing, malformed, or does not exist.       |
| 401         | `authentication_error`  | `expired_api_key`  | The API key has passed its expiration date.                 |
| 403         | `permission_error`      | `project_inactive` | The project associated with the API key is disabled.        |
| 403         | `permission_error`      | `ip_not_allowed`   | The request IP is not in the account's IP allowlist.        |
| 429         | `rate_limit_exceeded`   | --                 | Too many requests. Back off and retry.                      |
| 500         | `internal_error`        | --                 | An unexpected error on the CollieAi side.                   |
| 502         | `upstream_error`        | --                 | The upstream provider returned an error or was unreachable. |

## Policy Violation Responses

When a security rule blocks content, the error response includes a `triggered_rules` array with details about which rules fired and why.

### Input Block (content\_blocked)

This occurs when a user's message violates an input rule:

```json
{
  "error": {
    "message": "Message blocked by security policy: Potential prompt injection detected",
    "type": "policy_violation",
    "code": "content_blocked",
    "triggered_rules": [
      {
        "name": "Prompt Injection Detection",
        "type": "lightweight_model",
        "decision": "block",
        "match_info": {
          "label": "jailbreak",
          "confidence": 0.97
        }
      }
    ]
  }
}
```

### Output Block (response\_blocked)

This occurs when the model's response violates an output rule:

```json
{
  "error": {
    "message": "Response blocked by security policy: Restricted content detected in model output",
    "type": "policy_violation",
    "code": "response_blocked",
    "triggered_rules": [
      {
        "name": "Sensitive Topic Filter",
        "type": "aho_corasick",
        "decision": "block",
        "match_info": {
          "matched_keywords": ["restricted_term"]
        }
      }
    ]
  }
}
```

### Multiple Rules Triggered

More than one rule can fire on a single request. All triggered rules are listed:

```json
{
  "error": {
    "message": "Message blocked by security policy: Multiple rules triggered",
    "type": "policy_violation",
    "code": "content_blocked",
    "triggered_rules": [
      {
        "name": "PII Detection",
        "type": "structured_id",
        "decision": "block",
        "match_info": {
          "detected": ["credit_card"]
        }
      },
      {
        "name": "Email Filter",
        "type": "regex",
        "decision": "block",
        "match_info": {
          "pattern": "email",
          "matches": 2
        }
      }
    ]
  }
}
```

## Masked Content Responses

When a rule's action is **mask** instead of **block**, the request is not rejected. Instead, the sensitive content is redacted and the response is returned normally with HTTP 200:

```json
{
  "id": "chatcmpl-abc123def456",
  "object": "chat.completion",
  "created": 1709145600,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "I've noted your email [EMAIL_REDACTED] and phone [PHONE_REDACTED]. How can I help?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 28,
    "completion_tokens": 19,
    "total_tokens": 47
  }
}
```

Masked responses use the standard completion format. The redacted placeholders (e.g. `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, `[CREDIT_CARD_REDACTED]`) replace the original sensitive content. Your application receives a successful response and does not need special error handling for masked content.

## Python Error Handling

The OpenAI Python SDK maps HTTP errors to specific exception classes. Use these to handle CollieAi errors:

```python
from openai import OpenAI, APIError, AuthenticationError, RateLimitError

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

def send_message(user_input: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message.content

    except AuthenticationError:
        # 401: Invalid or expired API key
        return "Authentication failed. Please check your API key."

    except RateLimitError:
        # 429: Too many requests
        return "Rate limit exceeded. Please wait and try again."

    except APIError as e:
        if e.code == "content_blocked":
            # Input rule blocked the user's message
            return "Your message was blocked by a security policy."

        if e.code == "response_blocked":
            # Output rule blocked the model's response
            return "The model's response was blocked by a security policy."

        if e.code == "project_inactive":
            return "This project is currently disabled."

        # Catch-all for other API errors (upstream_error, internal_error, etc.)
        return f"An error occurred: {e.message}"
```

### Accessing Triggered Rules

The `triggered_rules` array is available in the error body. You can access it through the raw response:

```python
from openai import OpenAI, APIError

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Some message..."}]
    )
except APIError as e:
    if e.code in ("content_blocked", "response_blocked"):
        # Parse the error body for triggered rules
        if e.body and isinstance(e.body, dict):
            error_detail = e.body.get("error", {})
            triggered = error_detail.get("triggered_rules", [])
            for rule in triggered:
                print(f"Rule: {rule['name']} ({rule['type']})")
                print(f"Decision: {rule['decision']}")
                print(f"Details: {rule.get('match_info', {})}")
```

### Streaming Error Handling (Python)

Errors can occur mid-stream when output rules block a response. Wrap your streaming loop in a try/except:

```python
from openai import OpenAI, APIError

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

try:
    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Tell me a story."}],
        stream=True
    )

    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)

    print()

except APIError as e:
    if e.code == "response_blocked":
        print("\nThe response was blocked by a security policy.")
    else:
        print(f"\nStream error: {e.message}")
```

## Node.js Error Handling

The OpenAI Node.js SDK provides typed error classes:

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://app.collieai.io/v1",
  apiKey: "clai_your_api_key_here",
});

async function sendMessage(userInput) {
  try {
    const response = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        { role: "system", content: "You are a helpful assistant." },
        { role: "user", content: userInput },
      ],
    });
    return response.choices[0].message.content;
  } catch (error) {
    if (error instanceof OpenAI.AuthenticationError) {
      return "Authentication failed. Please check your API key.";
    }

    if (error instanceof OpenAI.RateLimitError) {
      return "Rate limit exceeded. Please wait and try again.";
    }

    if (error instanceof OpenAI.APIError) {
      if (error.code === "content_blocked") {
        return "Your message was blocked by a security policy.";
      }
      if (error.code === "response_blocked") {
        return "The model's response was blocked by a security policy.";
      }
      if (error.code === "project_inactive") {
        return "This project is currently disabled.";
      }
      return `An error occurred: ${error.message}`;
    }

    throw error; // Re-throw unexpected errors
  }
}
```

### Accessing Triggered Rules (Node.js)

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://app.collieai.io/v1",
  apiKey: "clai_your_api_key_here",
});

try {
  const response = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: "Some message..." }],
  });
} catch (error) {
  if (error instanceof OpenAI.APIError) {
    if (error.code === "content_blocked" || error.code === "response_blocked") {
      const triggeredRules = error.error?.triggered_rules ?? [];
      for (const rule of triggeredRules) {
        console.log(`Rule: ${rule.name} (${rule.type})`);
        console.log(`Decision: ${rule.decision}`);
        console.log(`Details:`, rule.match_info);
      }
    }
  }
}
```

### Streaming Error Handling (Node.js)

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://app.collieai.io/v1",
  apiKey: "clai_your_api_key_here",
});

try {
  const stream = await client.chat.completions.create({
    model: "gpt-4o-mini",
    messages: [{ role: "user", content: "Tell me a story." }],
    stream: true,
  });

  for await (const chunk of stream) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) {
      process.stdout.write(content);
    }
  }
  console.log();
} catch (error) {
  if (error instanceof OpenAI.APIError && error.code === "response_blocked") {
    console.log("\nThe response was blocked by a security policy.");
  } else {
    console.error("Stream error:", error.message);
  }
}
```

## Troubleshooting

### Why was my request blocked unexpectedly?

**Symptom:** You receive a `content_blocked` error for a message you believe is legitimate.

**Steps to resolve:**

1. Check the `triggered_rules` array in the error response to see which rule fired.
2. Review the rule's configuration in the CollieAi dashboard -- it may be too broad.
3. Test the rule with different inputs using the rule testing feature in the dashboard.
4. Adjust the rule's sensitivity, update its patterns, or add exceptions for your use case.

### Why am I getting authentication errors?

**Symptom:** You receive a 401 error with `invalid_api_key` or `expired_api_key`.

**Steps to resolve:**

1. Verify your API key starts with `clai_`.
2. Confirm the key has not expired by checking the dashboard.
3. Ensure the associated project is active (an inactive project returns `project_inactive`).
4. Check that the `Authorization` header is formatted as `Bearer clai_your_api_key_here`.
5. If using environment variables, confirm `OPENAI_API_KEY` is set to your CollieAi key (not your OpenAI key).

### Why are my requests timing out?

**Symptom:** Requests take too long or time out.

**Steps to resolve:**

1. CollieAi adds a small amount of latency for filtering (typically 50-200ms). Increase your client timeout to account for this.
2. If you have machine learning-based rules enabled (e.g. prompt injection detection), these add more latency than pattern-based rules. Consider whether all ML rules are necessary for your use case.
3. For streaming with output rules, the first chunk is delayed while the full response is accumulated and filtered. Set a higher timeout for streaming requests.
4. Check the CollieAi status page for any ongoing incidents.

### Why isn't streaming working?

**Symptom:** Streaming does not work, hangs, or produces unexpected output.

**Steps to resolve:**

1. Confirm `stream: true` is set in your request body.
2. Ensure your HTTP client or reverse proxy does not buffer SSE responses. Common culprits include Nginx (set `proxy_buffering off;`) and cloud load balancers.
3. If the stream terminates early with an error, check whether an output rule blocked the response. See [Streaming](streaming.md) for details on how output filtering interacts with streaming.
4. Verify your client correctly handles the `data: [DONE]` termination signal.

### Why am I getting a rate limit (429) error?

**Symptom:** You receive a 429 error with type `rate_limit_exceeded`.

**Steps to resolve:**

1. Check the `X-RateLimit-Remaining` header on your responses to see how many requests you have left.
2. Use the `Retry-After` header to know when to retry.
3. Increase the project's `rate_limit_rpm` setting if the current limit is too low.
4. If `rate_limit_rpm` is null (unlimited), the 429 is being proxied from your upstream provider — check your provider quota.

{% hint style="info" %}
A 429 error can come from CollieAi's own per-project rate limiter or from the upstream OpenAI API. Check whether your project has `rate_limit_rpm` configured to distinguish the two.
{% endhint %}

### Why am I getting an upstream (502) error?

**Symptom:** You receive a 502 error with type `upstream_error`.

**Steps to resolve:**

1. This means your upstream provider returned an error or was unreachable. Check your provider's status page (for example, the [OpenAI status page](https://status.openai.com/)) for outages.
2. Verify that your project's provider token (e.g. your OpenAI or Anthropic API key).
3. Confirm the model you are requesting is available (e.g. `gpt-4o-mini` vs a model that requires special access).
4. Retry the request -- transient upstream errors are common.

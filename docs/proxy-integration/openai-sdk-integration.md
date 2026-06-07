---
description: >-
  Connect your app to CollieAi with the OpenAI SDK — Python, Node.js, cURL, and
  function calling. Point the OpenAI client at CollieAi by changing the
  base_url.
icon: openai
---

# OpenAI SDK Integration

This guide covers how to connect your application to CollieAi using the official OpenAI SDKs, cURL, or environment variables. Every example on this page works identically to a direct OpenAI call - the only difference is the base URL and API key.

## Install the OpenAI SDK

{% hint style="info" %}
This guide covers the OpenAI SDK. If you use Anthropic's Claude, see Anthropic SDK Integration — CollieAi supports the native Messages API too.
{% endhint %}

{% tabs %}
{% tab title="Python" %}
Install the OpenAI Python package if you have not already:

```bash
pip install openai
```
{% endtab %}

{% tab title="Node.js" %}
Install the OpenAI Node.js package:

```bash
npm install openai
```
{% endtab %}
{% endtabs %}

## Python SDK

Create a client pointed at CollieAi:

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python with Error Handling

A production-ready example that handles all CollieAi-specific error cases:

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
        return "Authentication failed. Please check your CollieAi API key."

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

### Python Async Streaming

```python
import asyncio
from openai import AsyncOpenAI

client = AsyncOpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

async def stream_response():
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me a short story about a brave dog."}
        ],
        stream=True
    )

    async for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            print(content, end="", flush=True)

    print()

asyncio.run(stream_response())
```

## Node.js SDK

Create a client pointed at CollieAI:

```javascript
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://app.collieai.io/v1",
  apiKey: "clai_your_api_key_here",
});

const response = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "Hello, how are you?" },
  ],
});

console.log(response.choices[0].message.content);
```

### Node.js with Error Handling

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
      return "Authentication failed. Please check your CollieAI API key.";
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

## cURL

```bash
curl -X POST "https://app.collieai.io/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer clai_your_api_key_here" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 256
  }'
```

## Function Calling (Tools)

CollieAI passes tool definitions and tool call responses through transparently. Security rules are applied to message content; tool schemas are forwarded as-is.

{% stepper %}
{% step %}
### Step 1: Send the user message with tool definitions

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_your_api_key_here"
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City name, e.g. San Francisco"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto"
)

message = response.choices[0].message
```
{% endstep %}

{% step %}
### Step 2: If the model wants to call a tool, execute it and send the result back

```python
if message.tool_calls:
    tool_call = message.tool_calls[0]
    print(f"Tool: {tool_call.function.name}")
    print(f"Args: {tool_call.function.arguments}")

    # Execute the function (your implementation)
    result = '{"temperature": 18, "unit": "celsius", "condition": "partly cloudy"}'
```
{% endstep %}

{% step %}
### Step 3: Send the tool result back to the model

```python
    follow_up = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "What's the weather in Paris?"},
            message,
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            }
        ],
        tools=tools
    )
    print(follow_up.choices[0].message.content)
```
{% endstep %}
{% endstepper %}

## Migration from Direct OpenAI

{% columns %}
{% column %}
#### Before (direct OpenAI)

```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-your-openai-key"
)
```
{% endcolumn %}

{% column %}
#### After (CollieAi proxy)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",  # Add this line
    api_key="clai_your_collieai_key"          # Replace your OpenAI key
)
```
{% endcolumn %}
{% endcolumns %}

Everything else stays the same. Your `chat.completions.create()` calls, streaming logic, error handling, and tool definitions all work without modification.

### Environment Variables

The OpenAI SDKs for both Python and Node.js read configuration from environment variables automatically. This is the recommended approach for production deployments.

**Before:**

```bash
OPENAI_API_KEY=sk-your-openai-key
```

**After:**

```bash
OPENAI_BASE_URL=https://app.collieai.io/v1
OPENAI_API_KEY=clai_your_collieai_key
```

With these set, you do not need to pass `base_url` or `api_key` when creating the client:

```python
from openai import OpenAI

# Reads OPENAI_BASE_URL and OPENAI_API_KEY from the environment
client = OpenAI()

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

```javascript
import OpenAI from "openai";

// Reads OPENAI_BASE_URL and OPENAI_API_KEY from the environment
const client = new OpenAI();

const response = await client.chat.completions.create({
  model: "gpt-4o-mini",
  messages: [{ role: "user", content: "Hello!" }],
});
```

This makes it easy to switch between direct OpenAI and CollieAi by changing environment variables -- no code changes at all.

---
description: >-
  CollieAi quick start — sign up, and Get Started gives you a project, an API
  key and the Starter Monitor policy. Connect your app and see your first
  checked request in about five minutes.
icon: bolt-auto
---

# Quick start

This CollieAi quick start gets your first secured LLM call running in about five minutes. When you sign up, CollieAi creates a project, an API key and a ready-made policy for you. You connect your app, send a request and see what the policy found.

Prefer to build everything yourself? See [Set up by hand](quick-start.md#set-up-by-hand) below.

{% stepper %}
{% step %}
### Sign Up

Go to [app.collieai.io](https://app.collieai.io/) and create an account. You can sign in with **Google** (your account is created automatically on first login) or register with **email and password**.

All new accounts start on the **Free plan** - 20,000 API calls/month with full access to every security feature. See [Plans & Billing](plans-and-billing.md) for details.

See [Authentication](authentication.md) for more details on sign-in methods.
{% endstep %}

{% step %}
### Open Get Started

After your first sign-in CollieAi opens **Get Started** and creates three things for you:

* a project, **My project**;
* an API key for it, starting with `clai_`. It is shown once, so copy it now — **Copy .env line** gives you `COLLIEAI_API_KEY=clai_...` for your app's environment;
* the **Starter Monitor** policy, which becomes the project's policy and your default policy.

Starter Monitor runs in **Monitor** mode: nothing is blocked or changed, and every finding appears in **Logs**. When you have seen what it finds, open **Configure rules** and switch the policy to **Enforce**.

| Rule                         | What it checks                                        | Direction       |
| ---------------------------- | ----------------------------------------------------- | --------------- |
| Language Allowlist (Europe)  | the input language — European languages pass          | Input           |
| Prompt Security (Dictionary) | known prompt-injection phrases                        | Input           |
| PII (Structured IDs)         | card numbers, IBANs and BICs — masked in Enforce      | Input and Output |
| Malicious URLs (ThreatFox)   | links to known malware and command-and-control hosts  | Input and Output |
| Malicious URLs (URLhaus)     | links to known malware downloads                      | Input and Output |
| Hidden Payloads (Base64)     | base64-encoded payloads hidden in text                | Input and Output |
| Prompt Injection (LLM)       | prompt injection, judged by an LLM                    | Input           |
| Output Safety                | unsafe model output                                   | Output          |

{% hint style="info" %}
If your CollieAi server cannot run one of these rules yet — its model or feed is not available there — Get Started lists it under **Not added on this server**, and the policy is created without it. Your copy of the policy is yours: a rule skipped today is not added later by itself.
{% endhint %}
{% endstep %}

{% step %}
### Connect your app

Get Started lists the ways to connect. Pick one; **All options** takes you back to the list at any time.

| Option                            | Your provider key                    | What CollieAi checks                |
| --------------------------------- | ------------------------------------ | ----------------------------------- |
| OpenAI-compatible proxy           | OpenAI                               | input and output                    |
| Anthropic proxy                   | Anthropic                            | input and output                    |
| CollieAi SDK (Python, Node, .NET) | not needed — you call your own model | input and output, streams included  |
| Async Jobs API                    | not needed — you call your own model | input, and output if you send it    |
| Playground                        | not needed                           | a prompt and a model answer you paste |

Each option walks you through the same steps:

1. **Add your provider key** (proxies only). CollieAi forwards your requests to OpenAI or Anthropic with your own key, stored encrypted. Without it every proxied request is refused.
2. **Put your CollieAi key in the app's environment** as `COLLIEAI_API_KEY`.
3. **Let a coding agent do it.** Using Claude Code, Codex or Cursor? Copy the instruction and paste it into the agent. The instruction contains no key.
4. **Or add the code yourself.** Get Started shows the code for each language, with the line that points your app at CollieAi highlighted.

For the OpenAI-compatible proxy that line is the `base_url`:

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["COLLIEAI_API_KEY"],
    base_url="https://app.collieai.io/v1",
)
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello through CollieAi"}],
)
print(resp.choices[0].message.content)
```

The Playground needs no code: requests from it show in Logs, but do not count as a connected app.
{% endstep %}

{% step %}
### See your first request

The **Last request** card on Get Started shows your latest request within seconds: when it arrived, through which option, and whether it went through, was blocked by the policy, is still being processed or failed — with the reason. If the provider key is missing or the provider refused it, the card says so, with a button to **Provider tokens**.

**Open Logs** shows the full record of the request and what each rule found.
{% endstep %}
{% endstepper %}

## Set up by hand

Everything Get Started creates can also be made by hand — for example, a second project with a policy of your own.

{% stepper %}
{% step %}
### Add a Provider Token

CollieAi needs your LLM provider's API key to forward requests on your behalf.

1. Open **Settings > Provider Tokens** in the dashboard.
2. Click **Add Token**.
3. Select the provider (e.g., OpenAI) and paste your API key (`sk-...`).
4. Check **Set as default** so CollieAi uses this token when proxying requests.

Your key is encrypted at rest and never exposed in logs or responses.

See [Provider Tokens](../projects-and-policies/provider-tokens.md) for more details.
{% endstep %}

{% step %}
### Create a Project

Projects group your policies, rules, and API keys together.

1. Go to **Projects** in the dashboard.
2. Click **New Project**.
3. Give it a name (e.g., `my-chatbot`) and an optional description.

See [Projects](../projects-and-policies/projects.md) for more details.
{% endstep %}

{% step %}
### Create a Policy and Add Rules

Policies contain the security rules that filter your traffic.

1. Inside your project, go to **Policies** and click **Create Policy**.
2. Give it a name (e.g., `default-policy`) and set it as the active policy.
3. Click **Add Rule** and create a regex rule to mask email addresses:

| Field     | Value                                            |
| --------- | ------------------------------------------------ |
| Name      | `mask-emails`                                    |
| Type      | Regex                                            |
| Direction | All                                              |
| Decision  | Mask                                             |
| Pattern   | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` |

See [Policies](../projects-and-policies/policies.md) and [Security Rules](../security-rules/overview.md) for more details.
{% endstep %}

{% step %}
### Generate an API Key

1. Inside your project, go to **API Keys** and click **Create Key**.
2. Give it a descriptive name (e.g., `dev-key`).
3. Copy the key immediately -- it starts with `clai_` and is shown only once.

```
clai_AbCdEfGhSwDWWArWWDcpQrStUvWxYz012345678901234
```

Store it securely in an environment variable or secrets manager.

See [API Keys](api-keys.md) for more details.
{% endstep %}

{% step %}
### Make Your First Request

Install the OpenAI Python SDK if you have not already:

```bash
pip install openai
```

Point it at CollieAi by changing the `base_url` and using your CollieAi API key:

```python
from openai import OpenAI

client = OpenAI(
    api_key="clai_AbAddEfGhIjwADnOpQrStUvWxYz012345678901234",
    base_url="https://app.collieai.io/v1",
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Summarize our Q4 roadmap."}
    ],
)

print(response.choices[0].message.content)
```

{% hint style="info" %}
This example uses the OpenAI SDK, but CollieAi is provider-agnostic. You can also use the Anthropic SDK against the native Messages API to route to Anthropic Claude, and point CollieAi at any OpenAI-compatible endpoint (including self-hosted models) via a custom base URL — the same security pipeline applies.
{% endhint %}

That is it. Your request now flows through CollieAi's security pipeline before reaching OpenAI.
{% endstep %}

{% step %}
### See It in Action

With the email-masking rule active, try sending a message that contains a PII:

```python
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "My email is alice@example.com, can you help me?"}
    ],
)
```

CollieAi intercepts the request, masks the email address before it reaches OpenAI, and returns the model's response. Open the **Logs** page in the dashboard to see the request with the triggered `mask-emails` rule and the redacted content.
{% endstep %}
{% endstepper %}

## Next Steps

* [Proxy Integration](../proxy-integration/overview.md) -- Streaming, error handling, and advanced SDK usage.
* [Async Jobs](../async-jobs/overview.md) -- Submit requests and receive results via webhooks.
* [Security Rules](../security-rules/overview.md) -- Explore every rule type: PII detection, prompt injection blocking, URL filtering, and more.
* [Monitoring](../monitoring/overview.md) -- View logs, analytics, and configure alerts.

### Frequently asked questions

**How long does it take to integrate CollieAi?** Integrating CollieAi takes about five minutes. You change a single `base_url` in your existing OpenAI or Anthropic SDK — no rewrite, no new client library — and your requests immediately flow through the CollieAi AI firewall.

**Do I need to change my application code to use CollieAi?** No. CollieAi is a drop-in, provider-agnostic proxy, so you only change the `base_url` your SDK points at. Your existing request and response code works as-is, which is why it is compatible with most existing LLM infrastructure.

**Can a small dev team integrate CollieAi quickly?** Yes. CollieAi is built for rapid integration by small dev teams and startups: there is no infrastructure to deploy, no SDK to swap, and the full guardrail stack works from the first request through a single proxy endpoint.

**Is there a free plan to get started with CollieAi?** Yes. Every new CollieAi account starts on the Free plan with 20,000 API calls per month and full access to every security feature. The Growth plan is $49/month — an AI firewall for well under the $500/month many teams budget.

**Is my provider API key secure with CollieAi?** Yes. CollieAi stores your provider token AES-encrypted at rest and never exposes it in logs or responses. CollieAi uses the token only to forward your filtered requests to the provider.

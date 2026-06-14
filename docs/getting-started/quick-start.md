---
description: >-
  CollieAi quick start — get your first secured LLM call running in about five
  minutes. Sign up, add a provider token, create a policy, and send a request.
icon: bolt-auto
---

# Quick start

This CollieAi quick start gets your first secured LLM call running in about five minutes. You will sign up, add a provider token, create a project and policy, generate an API key, and send your first request through the CollieAi AI firewall.

{% stepper %}
{% step %}
### Sign Up

Go to [app.collieai.io](https://app.collieai.io/) and create an account. You can sign in with **Google** (your account is created automatically on first login) or register with **email and password**.

All new accounts start on the **Free plan** - 20,000 API calls/month with full access to every security feature. See [Plans & Billing](plans-and-billing.md) for details.

See [Authentication](authentication.md) for more details on sign-in methods.
{% endstep %}

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

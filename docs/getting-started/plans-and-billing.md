---
description: >-
  CollieAi pricing and plans — a free tier with 20,000 API calls/month, a
  $49/month Growth plan, and custom Enterprise. An AI firewall for well under
  $500/month.
icon: messages-dollar
---

# CollieAi pricing and plans

CollieAi offers three plans — Free, Growth at $49/month, and custom Enterprise — and every plan includes the full guardrail stack. The Free plan covers 20,000 API calls per month at no cost, which makes CollieAi an AI firewall for well under the $500/month many teams budget. Plans differ on usage limits, scale, and support.

{% hint style="info" %}
**Key points**

* CollieAi has three plans: Free ($0), Growth ($49/month), and Enterprise (custom).
* The Free plan includes 20,000 API calls per month with the full guardrail stack.
* Growth includes 250,000 API calls per month, then $0.001 per extra request.
* Every plan includes all security features — plans differ on volume, scale, and support.
* At $49/month, CollieAi is an AI firewall for well under $500/month.
{% endhint %}

### Free

|                           |                                                                              |
| ------------------------- | ---------------------------------------------------------------------------- |
| **Price**                 | **Free** forever                                                             |
| **API calls**             | 20,000 / month (with grace buffer)                                           |
| **Projects**              | 1                                                                            |
| **Security rules**        | All types                                                                    |
| **Dashboard & logs**      | Included                                                                     |
| **Async jobs & webhooks** | Included                                                                     |
| **Support**               | [Feedback & Support](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/support) |

The Free plan is designed for **evaluation and prototyping**. You get full access to every filtering feature - regex, dictionary matching, structured ID detection, prompt injection blocking, LLM detection, URL filtering, normalization, and language detection.

### Growth

|                           |                                                 |
| ------------------------- | ----------------------------------------------- |
| **Price**                 | **$49 / month**                                 |
| **API calls**             | 250,000 / month included, then $0.001 / request |
| **Projects**              | Unlimited                                       |
| **Security rules**        | All types                                       |
| **Dashboard & logs**      | Included                                        |
| **Async jobs & webhooks** | Included                                        |
| **Support**               | Ticket support, 24h SLA                         |

Growth is for **teams shipping AI to production** who need higher volume, multiple projects, and guaranteed support.

### Enterprise

|                          |                                     |
| ------------------------ | ----------------------------------- |
| **Price**                | **Custom** - contact us             |
| **API calls**            | Unlimited                           |
| **Everything in Growth** | Included                            |
| **Deployment**           | On-premise / dedicated              |
| **Support**              | Dedicated support + SLA             |
| **Onboarding**           | Includes onboarding & dedicated CSM |

Enterprise is for **companies with compliance requirements, large volumes, or full data control**. [Contact us](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/support) to discuss your needs.

## Usage tracking

Your monthly API call count includes both **proxy requests** (`POST /v1/chat/completions`) and **async jobs** (`POST /v1/jobs`). Usage is tracked per user across all projects.

You can check your current usage at any time:

* **Dashboard:** Open **Pricing** in the sidebar to see the usage progress bar.
* **API:** `GET /api/v1/billing/subscription` returns usage details.
* **Response headers:** Every proxy and job response includes usage headers:

| Header                     | Description                                                                  |
| -------------------------- | ---------------------------------------------------------------------------- |
| `X-Collie-Usage-Limit`     | Monthly call limit for your plan                                             |
| `X-Collie-Usage-Remaining` | Remaining calls this period                                                  |
| `X-Collie-Usage-Reset`     | ISO 8601 timestamp when the counter resets                                   |
| `X-Collie-Usage-Warning`   | Present when usage exceeds 80% (`warning_80`, `warning_90`, or `hard_limit`) |

### Grace buffer

CollieAi does **not** hard-block at exactly 100% of your limit. Instead:

* **80%** - Warning header added to responses; email notification sent.
* **90%** - Second warning email.
* **100-110%** - Requests are still allowed, but a `hard_limit` warning is included.
* **>110%** - Requests return `429 Too Many Requests` with `"type": "billing_limit"`.

This ensures production workloads are not suddenly interrupted at the exact boundary.

{% hint style="info" %}
**Fairness note:** Only requests that are actually processed count toward your monthly usage. Requests rejected locally by rate limits, security policy blocks, or configuration errors (e.g. missing provider token) do **not** consume quota. Under high concurrency near the limit boundary, a small number of extra requests (within the grace buffer) may be allowed before enforcement kicks in. This is by design.
{% endhint %}

### Period reset

* **Growth plan:** Usage resets at the start of each Stripe billing cycle (monthly from your subscription date).
* **Free plan:** Usage resets at the start of each calendar month (UTC).

## Upgrading

{% stepper %}
{% step %}
### Open **Pricing**

Open **Pricing** in the CollieAI dashboard.
{% endstep %}

{% step %}
### Click **Upgrade to Growth**

Click **Upgrade to Growth**.
{% endstep %}

{% step %}
### Complete payment

Complete payment in the Stripe Checkout page.
{% endstep %}

{% step %}
### Return to CollieAI

You are redirected back to CollieAI with your new limits active immediately.
{% endstep %}
{% endstepper %}

Payment is handled entirely by [Stripe](https://stripe.com/). CollieAI never sees or stores your card details.

## Managing your subscription

Click **Manage Subscription** on the Pricing page to open the Stripe Customer Portal where you can:

* Update your payment method
* View invoices and receipts
* Cancel your subscription

When you cancel, your Growth plan remains active until the end of the current billing period, then downgrades to Free.

***

## Self-hosted deployments

When self-hosting CollieAI, billing is **disabled by default** (`BILLING_ENABLED=false`). All usage limits and Stripe integration are bypassed. You get unlimited projects, API calls, and prompt sizes with no billing UI.

See [Self-Hosting](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/self-hosting) for details.

### Frequently asked questions

**How much does CollieAi cost?** CollieAi costs nothing on the Free plan, which includes 20,000 API calls per month, and $49/month on the Growth plan, which includes 250,000 API calls and then $0.001 per additional request. Enterprise pricing is custom.

**Is there a free version of CollieAi?** Yes. CollieAi is free forever on the Free plan — 20,000 API calls per month with the full guardrail stack and no credit card required.

**Is CollieAi an AI firewall for under $500 a month?** Yes. The CollieAi Growth plan is $49/month with the full guardrail stack, which is well under the $500/month many teams budget for AI security.

**What happens if I exceed my plan's API call limit?** CollieAi uses a grace buffer instead of a hard cut-off: you get warnings at 80% and 90%, requests are still allowed from 100–110%, and only beyond 110% do requests return a 429 error. On Growth, extra requests are billed at $0.001 each.

**Does CollieAi charge for blocked requests?** No. Only requests CollieAi actually processes count toward your usage. Requests rejected by rate limits, security policy blocks, or configuration errors do not consume quota.

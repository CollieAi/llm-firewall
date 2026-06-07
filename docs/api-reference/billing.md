---
description: >-
  CollieAi Billing API — get subscription plan and usage, create Stripe Checkout
  and Customer   Portal sessions, and handle Stripe webhooks via
  /api/v1/billing.
icon: comment-dollar
---

# Billing

Subscription and usage management endpoints. These endpoints are only available when `BILLING_ENABLED=true` (cloud deployment). Self-hosted instances return `404` for all billing endpoints.

{% hint style="info" %}
**Plan retention during `past_due`:** A user on Growth whose status flips to `past_due` keeps their Growth limits until Stripe ultimately reports `canceled`/`unpaid`/etc. (which map to local `canceled`). This is intentional grace covering Stripe's payment-retry schedule — typically around three weeks — so a transient card issue doesn't immediately cut off a paying customer. Use `status` to surface a payment-issue UI; use `plan` to reason about what the user is entitled to right now.
{% endhint %}

## Plans

The hosted product offers two plans, Free and Growth. Enterprise is delivered as a separate dedicated deployment and is not a plan within the hosted dashboard. See [Plans & Billing](../getting-started/plans-and-billing.md) for full details.

| Plan       | API Calls              | Projects  | How to Subscribe        |
| ---------- | ---------------------- | --------- | ----------------------- |
| **Free**   | 20,000/month           | 1         | Automatic on signup     |
| **Growth** | 250,000/month included | Unlimited | Stripe Checkout (below) |

Enterprise customers run on a dedicated deployment of CollieAi with the hosted plan limits disabled. The endpoints documented here apply to the hosted product only. [Contact us](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/support) to discuss Enterprise.

## Stripe Status Mapping

Stripe subscriptions can be in many states. CollieAi maps them to three simplified local statuses:

| Stripe Status        | Local Status | Meaning                            |
| -------------------- | ------------ | ---------------------------------- |
| `active`             | `active`     | Subscription is paid and current   |
| `trialing`           | `active`     | Trial period (treated as active)   |
| `past_due`           | `past_due`   | Payment failed, Stripe is retrying |
| `incomplete`         | `past_due`   | Initial payment pending            |
| `canceled`           | `canceled`   | Subscription ended                 |
| `incomplete_expired` | `canceled`   | Initial payment expired            |
| `unpaid`             | `canceled`   | All retries exhausted              |
| `paused`             | `canceled`   | Subscription paused                |

When a subscription's local status becomes `canceled`, the user is downgraded to the Free plan.

## GET /api/v1/billing/subscription

Get the current user's subscription plan, usage, and limits.

**URL:** `https://app.collieai.io/api/v1/billing/subscription`

**Auth:** Session cookie

**Query Parameters:**

| Parameter | Type    | Description                                                                                                                                                                   |
| --------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `refresh` | boolean | Pass `true` to force a Stripe API fetch (useful after checkout when the webhook may not have arrived yet). The pricing page sends this automatically after checkout redirect. |

### Response -- `200 OK`

```json
{
  "plan": "free",
  "status": "active",
  "usage": {
    "api_calls_used": 8420,
    "api_calls_limit": 15000,
    "percentage": 56.1,
    "warning_level": null,
    "reset_at": "2026-05-01T00:00:00Z"
  },
  "limits": {
    "monthly_api_calls": 15000,
    "max_prompt_tokens": 10000,
    "max_projects": 1
  },
  "current_period_start": null,
  "current_period_end": null,
  "can_upgrade": true,
  "can_manage": false
}
```

| Field                      | Description                                                        |
| -------------------------- | ------------------------------------------------------------------ |
| `plan`                     | `"free"` or `"growth"`                                             |
| `status`                   | `"active"`, `"past_due"`, or `"canceled"`                          |
| `usage.percentage`         | Current usage as a percentage of the monthly limit                 |
| `usage.warning_level`      | `null`, `"warning_80"`, `"warning_90"`, or `"hard_limit"`          |
| `limits.max_prompt_tokens` | `0` means no platform cap (configurable by user)                   |
| `limits.max_projects`      | `0` means unlimited                                                |
| `current_period_start`     | Stripe billing cycle start (always `null` for Free users)          |
| `current_period_end`       | Stripe billing cycle end (always `null` for Free users)            |
| `can_upgrade`              | `true` if the user is on the Free plan                             |
| `can_manage`               | `true` if the user has a Stripe customer account (can open portal) |

## POST /api/v1/billing/checkout

Create a Stripe Checkout Session for the Growth plan. Returns a URL to redirect the user to.

**URL:** `https://app.collieai.io/api/v1/billing/checkout`

**Auth:** Session cookie

### Response -- `200 OK`

```json
{
  "checkout_url": "https://checkout.stripe.com/c/pay/cs_test_..."
}
```

Redirect the user to `checkout_url`. After payment, the user is redirected back to `/app/pricing?checkout_success=true`.

### Errors

| Code | Description                                    |
| ---- | ---------------------------------------------- |
| 400  | User already has an active Stripe subscription |
| 500  | Stripe Growth price not configured             |

## POST /api/v1/billing/portal

Create a Stripe Customer Portal session for subscription management (update payment method, view invoices, cancel).

**URL:** `https://app.collieai.io/api/v1/billing/portal`

**Auth:** Session cookie

### Response -- `200 OK`

```json
{
  "portal_url": "https://billing.stripe.com/p/session/..."
}
```

### Errors

| Code | Description                                          |
| ---- | ---------------------------------------------------- |
| 400  | No billing account found. Subscribe to a plan first. |

## POST /api/v1/billing/webhook

Stripe webhook endpoint. This endpoint is **unauthenticated** -- it verifies incoming events using the Stripe webhook signature.

**URL:** `https://app.collieai.io/api/v1/billing/webhook`

**Auth:** Stripe signature (`stripe-signature` header)

### Handled Events

| Event                           | Action                                                                     |
| ------------------------------- | -------------------------------------------------------------------------- |
| `checkout.session.completed`    | Links Stripe customer to CollieAI user, activates Growth plan              |
| `customer.subscription.created` | Activates Growth plan, sets billing period                                 |
| `customer.subscription.updated` | Updates plan/status, resets usage on plan transition or new billing period |
| `customer.subscription.deleted` | Downgrades to Free plan, resets usage                                      |
| `invoice.payment_failed`        | Sets subscription status to `past_due`                                     |
| `invoice.paid`                  | Restores `active` status after past\_due recovery                          |

### Responses

```json
{"status": "ok"}
```

For duplicate events (already processed):

```json
{"status": "already_processed"}
```

### Idempotency

Each event ID is tracked in Redis with a 48-hour TTL. Duplicate deliveries are acknowledged with `already_processed` without reprocessing.

## Admin Plan Management

Admins can manually change a user's plan via `PATCH /api/v1/admin/users/{user_id}` with the `plan` field (`free` or `growth`). See [Admin API Reference](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/api-reference) for details. This is used for manual overrides — for example, comping a customer to Growth-level limits without going through Stripe Checkout.

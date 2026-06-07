---
description: >-
  How CollieAi enforcement mode works — run security rules in monitor mode to
  observe their impact on live traffic, then promote them to enforce when you're
  confident.
icon: '1'
---

# Enforcement Mode

Enforcement mode lets you safely deploy security rules without affecting live traffic. New rules can evaluate in the background while you review their impact, then promote them to active enforcement when you are confident in the results.

{% hint style="info" %}
**Key points**

* Enforcement mode controls whether a security rule's decision is applied (`enforce`) or only recorded (`monitor`).
* It is set at two levels — policy and rule — and **monitor always wins** if either is set to monitor.
* In monitor mode rules evaluate and report triggers (`"monitoring": true`) but never mask or block content.
* The typical workflow is: deploy in monitor, review triggers, then promote to enforce.
{% endhint %}

## How does enforcement mode work?

Enforcement mode is configured at two levels:

* **Policy level** -- `enforce` (default) or `monitor`
* **Rule level** -- `inherit` (default), `enforce`, or `monitor`

The effective mode for each rule is determined by combining both settings. The key principle is that **monitor always wins** -- if either level is set to monitor, the rule runs in monitor mode.

| Policy Mode | Rule Mode | Effective Mode |
| ----------- | --------- | -------------- |
| `monitor`   | `inherit` | monitor        |
| `monitor`   | `enforce` | monitor        |
| `monitor`   | `monitor` | monitor        |
| `enforce`   | `inherit` | enforce        |
| `enforce`   | `enforce` | enforce        |
| `enforce`   | `monitor` | monitor        |

This design ensures that a policy-level monitor cannot be overridden by individual rules, making it safe to put an entire policy into observation mode.

## What happens in monitor mode?

When a rule runs in monitor mode:

1. The rule **evaluates normally** -- pattern matching, classification, and all other logic runs exactly as it would in enforce mode.
2. If triggered, it appears in the `triggered_rules` array of the response with `"monitoring": true`.
3. Rule statistics (trigger counts, match counts) **update as usual**.
4. The rule's decision is **suppressed** -- no blocking or masking is applied to the message.

The message passes through as if the rule did not exist, but you get full visibility into what _would have_ happened.

### Example: Triggered Rule in Monitoring Mode

In a proxy response or webhook payload, a monitoring rule appears like this:

```json
{
  "triggered_rules": [
    {
      "rule_id": "b3f1a2c4-...",
      "rule_name": "block-profanity",
      "decision": "block",
      "monitoring": true
    }
  ],
  "blocked": false
}
```

The `decision` field shows what _would_ have happened. The `monitoring: true` flag and `blocked: false` confirm the decision was suppressed.

## Typical Deployment Workflow

{% stepper %}
{% step %}
### 1. Deploy in Monitor Mode

Start by creating a policy in monitor mode to observe how rules behave against real traffic:

```bash
curl -X POST https://your-instance.example.com/api/v1/policies \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Content Security",
    "enforcement_mode": "monitor"
  }'
```
{% endstep %}

{% step %}
### 2. Review Triggers

Let the policy run for a period of time, then check rule statistics and logs. Look for:

* **Trigger frequency** -- is the rule firing as often as you expect?
* **False positives** -- are legitimate messages being flagged?
* **Coverage** -- are there messages that should match but do not?

Use the Analytics and Logs pages, or query the API for rule stats.
{% endstep %}

{% step %}
### 3. Promote to Enforce Mode

Once you are satisfied with the rule behavior, switch the policy to enforce mode:

```bash
curl -X PUT https://your-instance.example.com/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enforcement_mode": "enforce"
  }'
```

All rules with `inherit` mode will immediately begin enforcing their decisions.
{% endstep %}

{% step %}
### 4. Gradual Rollout for New Rules

When adding new rules to an enforcing policy, set individual rules to monitor mode while keeping the policy in enforce:

```bash
curl -X POST https://your-instance.example.com/api/v1/rules \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "New Prompt Injection Rule",
    "rule_type": "lightweight_model",
    "policy_id": "POLICY_ID",
    "direction": "inbound",
    "decision": "block",
    "enforcement_mode": "monitor",
    "config": {
      "model_id": "sentinel_v2",
      "threshold": 0.80
    }
  }'
```

This rule evaluates every input message and reports triggers, but does not block anything. Once validated, update the rule to `inherit` or `enforce` to activate it:

```bash
curl -X PUT https://your-instance.example.com/api/v1/rules/{rule_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enforcement_mode": "inherit"
  }'
```
{% endstep %}
{% endstepper %}

## API Examples

### Create a Policy in Monitor Mode

```bash
curl -X POST https://your-instance.example.com/api/v1/policies \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "new-threat-policy",
    "enforcement_mode": "monitor"
  }'
```

### Switch a Policy from Monitor to Enforce

```bash
curl -X PUT https://your-instance.example.com/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "enforcement_mode": "enforce"
  }'
```

### Create a Rule with Monitor Mode

```bash
curl -X POST https://your-instance.example.com/api/v1/rules \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "experimental-injection-detector",
    "rule_type": "lightweight_model",
    "policy_id": "POLICY_ID",
    "direction": "inbound",
    "decision": "block",
    "enforcement_mode": "monitor",
    "config": {
      "model_id": "sentinel_v2",
      "threshold": 0.70
    }
  }'
```

## Integration Notes

### Drop-in Proxy

Enforcement mode is transparent to clients. Whether a rule is in monitor or enforce mode, the proxy API behaves the same way -- no client-side changes are needed. The only difference is whether matched rules actually affect the message content.

### Async Jobs

When a monitored rule fires during an async job, the webhook payload includes the monitoring flag (`"monitoring": true`) in `triggered_rules` and `blocked` remains `false`. Your webhook handler can use this information for alerting or dashboarding without changing its processing logic.

### Frequently asked questions

**What is monitor mode in CollieAi?** Monitor mode is a CollieAi enforcement mode in which a security rule evaluates normally and records every trigger, but its decision is suppressed — no content is masked or blocked. It lets you observe rule impact on real traffic safely.

**What is the difference between monitor and enforce mode?** In enforce mode a rule's decision is applied, so content is masked or blocked. In monitor mode the same rule evaluates and reports what would have happened, but the message passes through unchanged.

**Can I test a single new rule without affecting live traffic?** Yes. Set an individual rule to monitor mode while keeping the policy in enforce mode. The rule evaluates and reports triggers without blocking anything, and you promote it to enforce once validated.

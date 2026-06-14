---
description: >-
  How CollieAi policies work — a reusable collection of security rules with an
  enforce or monitor mode that you can share across multiple projects and switch
  instantly.
icon: building-shield
---

# Policies

A policy is a named collection of [security rules](../security-rules/overview.md). Policies are the central organizing unit in CollieAi — they define what to filter, how to filter it, and whether to enforce or monitor.

{% hint style="info" %}
**Key points**

* A policy is a reusable collection of security rules — it defines what to filter, how, and whether to enforce or monitor.
* Policies are independent from projects and user-scoped: build one once and assign it to many projects.
* Each policy has an enforcement mode (`enforce` or `monitor`), which individual rules can override.
* Switching a project's active policy takes effect instantly, and you can't delete a policy that's active on a project.
{% endhint %}

## Independence from projects

Policies are **independent from projects**. You can create, edit, and delete policies without any project existing. This means:

* You can build and test a policy before creating a project.
* You can maintain a library of policies and assign them to projects as needed.
* Deleting a project does not delete its associated policy.

Policies belong to the user who created them. They are **user-scoped** — other users cannot see or use your policies.

## Shared policies

By default, policies are **shared** (`project_id = null`). A shared policy is not tied to any specific project and can be assigned as the active policy on multiple projects simultaneously.

```bash
# Create a shared policy (the default behavior)
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "standard-pii-protection",
    "enforcement_mode": "enforce"
  }'
```

This is the recommended approach for most use cases. Define your rules once in a shared policy, then assign it to every project that needs the same protection.

{% hint style="info" %}
Shared policies are scoped to your user account. Other users cannot access your policies — there is no cross-user sharing.
{% endhint %}

## Policy types

CollieAI has two types of policies:

| Type              | Owner  | Editable by users | Description                                         |
| ----------------- | ------ | ----------------- | --------------------------------------------------- |
| **User policy**   | You    | Yes               | Created and fully managed by you.                   |
| **System policy** | Admins | No (read-only)    | Pre-built by CollieAI admins. Visible to all users. |

You can assign a system policy directly to a project, or **copy** it to create your own editable version.

## Default policy

You can **star** a policy to mark it as your default. The default policy is automatically assigned as the active policy when you create a new project.

```bash
# Toggle a policy as the default (star / un-star)
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/set-default \
  -H "Authorization: Bearer clai_..."
```

Calling `set-default` on a policy that is already the default will **un-star** it (toggle behavior). Setting a new default automatically un-stars the previous one. You always have at most one default policy.

## Enforcement mode

Every policy has an **enforcement mode** that controls whether its rules have real consequences:

| Mode                | Behavior                                                                                        |
| ------------------- | ----------------------------------------------------------------------------------------------- |
| `enforce` (default) | Rules apply their configured decisions — blocking, masking, or allowing messages.               |
| `monitor`           | Rules evaluate and log matches, but decisions are suppressed. Traffic passes through unchanged. |

Individual rules can override the policy-level mode. See [Enforcement Mode](../security-rules/enforcement-mode.md) for the full precedence table and workflow guidance.

```bash
# Create a policy in monitor mode for safe testing
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "experimental-threat-detection",
    "enforcement_mode": "monitor"
  }'
```

## Active policy assignment

A [project](projects.md) has exactly one active policy at a time. Switching the active policy changes which rules apply to all subsequent requests.

One shared policy can be active on **multiple projects** simultaneously. Changes to the policy's rules take effect across all projects that use it.

```bash
# Switch a project's active policy
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "active_policy_id": "new-policy-uuid"
  }'
```

## Deletion guard

You cannot delete a policy that is currently active on any project. The API returns an error if you try:

```json
{
  "error": {
    "message": "Cannot delete policy: it is active on 2 project(s). Switch those projects to a different policy first.",
    "type": "conflict",
    "code": 409
  }
}
```

To delete the policy, first switch all projects that use it to a different active policy, then retry the delete.

```bash
# Step 1: Switch projects to another policy
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "active_policy_id": "replacement-policy-uuid"
  }'

# Step 2: Delete the now-unused policy
curl -X DELETE https://app.collieai.io/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer clai_..."
```

## API reference

Policies have their own top-level endpoints, independent from projects.

### List all policies

```bash
curl https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..."
```

### Get a policy

```bash
curl https://app.collieai.io/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer clai_..."
```

### Create a policy

```bash
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-policy",
    "enforcement_mode": "enforce"
  }'
```

### Update a policy

```bash
curl -X PATCH https://app.collieai.io/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "renamed-policy",
    "enforcement_mode": "monitor"
  }'
```

### Delete a policy

```bash
curl -X DELETE https://app.collieai.io/api/v1/policies/{policy_id} \
  -H "Authorization: Bearer clai_..."
```

### Toggle default policy

```bash
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/set-default \
  -H "Authorization: Bearer clai_..."
```

### Project-scoped endpoints

You can also access the active policy through a project:

```bash
# Get the active policy for a project
curl https://app.collieai.io/api/v1/projects/{project_id}/policy \
  -H "Authorization: Bearer clai_..."
```

## Examples

### Build a shared policy library

```bash
# 1. Create a base PII policy
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "pii-masking-standard",
    "enforcement_mode": "enforce"
  }'

# 1b. Star it as the default
curl -X POST https://app.collieai.io/api/v1/policies/{pii_policy_id}/set-default \
  -H "Authorization: Bearer clai_..."

# 2. Create a strict threat-blocking policy
curl -X POST https://app.collieai.io/api/v1/policies \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "threat-blocking-strict",
    "enforcement_mode": "enforce"
  }'

# 3. Assign the strict policy to a high-security project
curl -X PATCH https://app.collieai.io/api/v1/projects/{project_id} \
  -H "Authorization: Bearer clai_..." \
  -H "Content-Type: application/json" \
  -d '{
    "active_policy_id": "{strict_policy_id}"
  }'
```

New projects automatically get `pii-masking-standard` (the default). High-security projects are manually switched to `threat-blocking-strict`.

## Next steps

* [Security Rules](../security-rules/overview.md) — learn about the 10 rule types you can add to a policy.
* [Enforcement Mode](../security-rules/enforcement-mode.md) — monitor vs. enforce and the precedence table.
* [Projects](projects.md) — manage the environments that use your policies.
* [Dictionaries](dictionaries.md) — word lists used by dictionary matching rules.

### Frequently asked questions

**What is a policy in CollieAi?** A policy in CollieAi is a named, reusable collection of security rules with an enforce or monitor mode. It defines what content to filter and how, and a single policy can be the active policy on multiple projects at once.

**Can I reuse the same security rules across projects?** Yes. Policies are shared by default and independent from projects, so you can define rules once in a policy and assign it as the active policy on every project that needs the same protection.

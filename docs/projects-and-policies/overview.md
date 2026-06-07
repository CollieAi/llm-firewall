---
description: >-
  How CollieAi organizes work with projects and policies — a multi-tenant model
  where projects isolate workloads and reusable policies define the security
  rules applied to each.
icon: diagram-subtask
---

# Projects and policies overview

CollieAi uses a multi-tenancy model built around **projects** and **policies**. Projects isolate your workloads. Policies define the security rules applied to each workload. This section explains how they fit together and covers the supporting concepts - API keys, provider tokens, and dictionaries.

{% hint style="info" %}
**Key points**

* CollieAi uses a multi-tenant model built around projects and policies.
* A project is an isolated workload with its own API keys, settings, and one active policy.
* A policy is a reusable collection of security rules that can be shared across multiple projects.
* Provider tokens and dictionaries are user-scoped, so they are shared across all your projects.
{% endhint %}

## Core concepts

### Projects

A project is an isolated environment with its own API keys, settings, and active policy. Each project represents a distinct workload - for example, a customer-facing chatbot, an internal copilot, or a document summarization service.

Every request to the CollieAi proxy or async jobs API is scoped to a project via the API key used to authenticate it.

{% hint style="info" %}
The **Free plan** includes 1 project. Upgrade to **Growth** for unlimited projects. See [Plans & Billing](../getting-started/plans-and-billing.md).
{% endhint %}

[Read more about Projects](projects.md)

### Policies

A policy is a named collection of [security rules](https://app.gitbook.com/s/xKzkxBScfGXAbqoqyEbd/security-rules). Policies are independent from projects -- you can create, edit, and delete policies without any project existing. A single policy can be shared across multiple projects.

Each policy has an [enforcement mode](../security-rules/enforcement-mode.md) (`enforce` or `monitor`) that controls whether matched rules act on traffic or only log.

[Read more about Policies ->](policies.md)

### API Keys

API keys authenticate requests to the CollieAi proxy and API. Keys are prefixed with `clai_` and are scoped to a single project. When a request arrives, CollieAi uses the API key to determine which project (and therefore which policy and rules) applies.

API keys are created inside a project. You can have multiple keys per project -- for example, one for staging and one for production. See [Authentication](../getting-started/authentication.md) and [API Keys](../getting-started/api-keys.md) for details.

### Provider Tokens

Provider tokens are the API keys for your LLM provider (OpenAI, Anthropic, Azure OpenAI, Google Gemini). They are stored in CollieAi and used when proxying requests to the upstream model. Provider tokens are **user-scoped** -- they belong to your account, not to a specific project.

Tokens are encrypted at rest when encryption is configured.

[Read more about Provider Tokens ->](provider-tokens.md)

### Dictionaries

Dictionaries are word lists used by [dictionary matching](../security-rules/detecting-pii/dictionary-matching.md) rules. CollieAi provides system dictionaries (profanity filters, PII keyword lists) and lets you create custom dictionaries with your own terms.

[Read more about Dictionaries ->](dictionaries.md)

## How do projects and policies relate?

```
User
 ├── Projects
 │    ├── API Keys (project-scoped)
 │    └── Active Policy ─┐
 │                       │  (references)
 ├── Policies ───────────┘
 │    └── Rules
 │
 ├── Provider Tokens (user-scoped)
 │
 └── Dictionaries (user-scoped)
      └── Used by dictionary matching rules
```

Key relationships:

* A **user** owns projects, policies, provider tokens, and custom dictionaries.
* **Projects** and **policies** are independent branches of the data model. A policy can exist without any project, and deleting a project does not delete its policy.
* A **project** has one active policy at a time. Switching the active policy changes which rules apply instantly.
* A **policy** can be shared across multiple projects simultaneously.
* One policy can be starred as the **user-level default** -- it is automatically assigned to new projects.
* **Provider tokens** are user-level -- your default token is used for all proxy requests regardless of project.
* **Dictionaries** are user-level. System dictionaries are available to everyone; custom dictionaries belong to the user who created them.

## In this section

* [Projects](projects.md) - creating and managing isolated environments.
* [Policies](policies.md) - building rule collections and sharing them across projects.
* [Dictionaries](dictionaries.md) - word lists for Dictionary Match rules.
* [Provider Tokens](provider-tokens.md) - storing and managing LLM provider API keys.

### Frequently asked questions

**How does CollieAi support multi-tenancy?** CollieAi organizes work into projects, each an isolated workload with its own API keys, settings, and active policy, so you can run a customer chatbot, an internal copilot, and a document service with separate rules under one account.

**What is the difference between a project and a policy in CollieAi?** A project is an isolated workload that requests are scoped to via its API key, while a policy is a reusable collection of security rules. A project has one active policy at a time, and a single policy can be shared across multiple projects.

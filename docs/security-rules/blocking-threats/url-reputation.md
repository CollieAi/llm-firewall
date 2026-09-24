---
description: >-
  How CollieAi URL reputation blocks known-malicious links — exact matching
  against the abuse.ch ThreatFox and URLhaus threat-intelligence feeds, with
  freshness, failure policy and exclusions you control.
icon: shield-virus
---

# URL reputation

## What is the URL reputation rule type?

The URL Reputation rule checks every URL in a message against a continuously
re-imported threat-intelligence feed and blocks the ones the feed already
knows to be malicious. It answers one question — **is this exact address in
the feed?** — and it answers it locally, without ever visiting the URL.

**Ideal for:**

* Blocking links to known malware payloads that a user pastes into a chat
* Blocking known command-and-control addresses a model reproduces in output
* Catching a malicious link your own `url_filter` deny-list has never heard of

{% hint style="info" %}
**Key points**

* Two feeds, both from abuse.ch: **ThreatFox** (C2 and malware IOCs — URLs, domains and `ip:port`) and **URLhaus** (malware distribution URLs). One rule references exactly one feed.
* Matching is **exact**: a match means this precise address is in the feed. `evil.test` does not match `a.evil.test`, and a no-match never means "this URL is safe".
* The rule is **block-only** and never rewrites content: `allow` and `mask` are refused by the API.
* You decide what happens when the check cannot run — `on_unavailable` is `allow` (continue) or `block` (fail closed).
* No URL is ever fetched, resolved or unwound. There is no DNS lookup, no redirect following and no request to the address.
{% endhint %}

## How it works

1. Every explicit `http://` or `https://` URL in the text is extracted with its exact position.
2. Each one is canonicalized into a comparable identity: host lowercased, IDN converted to A-labels, the default port for the scheme dropped, the fragment dropped. The path and query are preserved — case, `;params`, `//`, dot segments and existing `%` escapes are all kept as they are, and non-ASCII characters are percent-encoded as UTF-8.
3. The identity is looked up in the feed snapshot the deployment currently serves.
4. A hit blocks the message. A miss lets it through. A check that could not run applies your `on_unavailable` policy.

The feed itself is imported and validated by CollieAi on a schedule; your
request never waits on abuse.ch.

## What it does not do

This list is deliberate, and it is the difference between a reputation feed
and a scanner:

* No classification of unknown URLs — if the address is not in the feed, the rule says nothing about it.
* No bare domains (`evil.test`), no `www.`-without-scheme, no defanged forms (`hxxp://`, `evil[.]test`).
* No DNS resolution, no URL visiting, no redirect or shortener unwinding, no file scanning.
* No subdomain inheritance: a feed entry for `evil.test` does not block `login.evil.test`.
* One feed per rule — two feeds means two rules.

## Rule Configuration

### Properties

| Property                      | Type             | Default             | Description                                                                                                      |
| ----------------------------- | ---------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `source`                      | string           | required            | `threatfox` or `urlhaus`. Cannot be mixed in one rule.                                                            |
| `on_unavailable`              | string           | `allow`             | What to do when the check cannot run: `allow` (continue, the failure is recorded) or `block` (fail closed).        |
| `max_feed_age_seconds`        | integer          | `86400`             | How old the served feed may be before this rule treats it as unusable. Between `900` and `86400`.                  |
| `excluded_domains`            | array of strings | none                | Exact hosts this rule never flags. No wildcards, no subdomain inheritance.                                         |
| `excluded_urls`               | array of strings | none                | Exact URLs this rule never flags.                                                                                  |
| `ioc_types`                   | array of strings | all three           | **ThreatFox only.** Any of `url`, `domain`, `ip:port`.                                                              |
| `min_confidence`              | integer          | `90`                | **ThreatFox only.** Ignore feed entries below this confidence (0–100).                                             |
| `include_compromised_domains` | boolean          | `false`             | **ThreatFox only.** Also match domains the feed marks as compromised — legitimate sites currently serving malware. |
| `url_status`                  | array of strings | `online`, `offline`, `unknown` | **URLhaus only.** Which URL statuses to match. An offline URL is still a known distribution point.   |

A field that belongs to the other source is refused, even when it is `false`.
`excluded_domains` and `excluded_urls` share one budget of 100 entries.

### ThreatFox example

```json
{
  "name": "Known malware infrastructure",
  "rule_type": "url_reputation",
  "decision": "block",
  "direction": "all",
  "config": {
    "source": "threatfox",
    "ioc_types": ["url", "domain", "ip:port"],
    "min_confidence": 90,
    "on_unavailable": "allow",
    "max_feed_age_seconds": 86400,
    "excluded_domains": ["cdn.partner.example"]
  }
}
```

### URLhaus example

```json
{
  "name": "Known malware downloads",
  "rule_type": "url_reputation",
  "decision": "block",
  "direction": "all",
  "config": {
    "source": "urlhaus",
    "url_status": ["online", "offline"],
    "on_unavailable": "block",
    "max_feed_age_seconds": 3600
  }
}
```

## Freshness and the failure policy

A feed snapshot has an age, and each rule judges it by its own
`max_feed_age_seconds`:

| Freshness | Meaning                                                | Effect on the rule            |
| --------- | ------------------------------------------------------ | ----------------------------- |
| ready     | verified within the last 15 minutes                    | matches normally              |
| aging     | older than that, still inside your `max_feed_age_seconds` | matches normally           |
| expired   | older than your `max_feed_age_seconds`                 | the check cannot run          |

A check can also fail to run because the deployment does not serve that feed
yet, or because only part of the message could be examined. In every one of
those cases `on_unavailable` decides:

* `allow` — the message continues and the failure is recorded in the request log. This is the default, and it is the right choice for most deployments.
* `block` — the rule blocks on the failed check. The log says `fail-closed`, and **it is never reported as found malware**: a blocked-on-failure request is not a detection.

{% hint style="warning" %}
`on_unavailable: "block"` means an expired or unavailable feed blocks every
message that contains a URL. Choose it only where a missed malicious link is
worse than a blocked conversation, and watch the feed's freshness.
{% endhint %}

## Exclusions

Exclusions are exact values, not patterns:

* `excluded_domains` holds exact HOSTS (`cdn.partner.example`). An entry suppresses every match for that host, of any IOC type. Subdomains are not covered — list them separately.
* `excluded_urls` holds complete `http(s)` URLs, and an entry suppresses that one URL. A URL may contain a comma or a literal `*` — those are ordinary characters in a path or query, and they are matched as typed.
* Refused: a wildcard (`*.partner.example`), a URL in the domain list, a bare host in the URL list, and any value containing an ASCII space, tab or control character. The host is canonicalized the same way as a URL's host, so an IDN may be written either way.

## Input, output and streaming

The rule runs wherever you point it with `direction`:

* **Input** — a user pasting a known-malicious link is blocked before the model sees it.
* **Output** — a model reproducing a known-malicious link is blocked before the client sees it.

On a streamed response a URL cannot be judged before it is complete, and
nothing can be un-sent once the client has it. So on the proxy and native
streaming paths a policy that contains a URL reputation rule is delivered
**buffered**: CollieAi accumulates the response, checks it, then replays it.
That costs time-to-first-token.

**Monitor mode suppresses the enforcement, not the buffering.** A Monitor rule
records its finding and never blocks, but today the delivery gate still
buffers these streams. If time-to-first-token matters more than checking model
output, put the rule on input only (`direction: "inbound"`).

[Customer-owned streaming](../../async-jobs/customer-owned-streaming.md) is the
separate path: there CollieAi never holds your chunks, and the check runs at
finalize over the completed response.

## Context analysis

When context analysis is enabled, the rule also examines URLs inside
structured documents — each leaf of the document is checked on its own, and a
match records which leaf it came from.

## What you see in the logs

Every evaluation on the proxy, native and job paths is recorded, including the
ones that found nothing, so you can always tell "the check found nothing" from
"the check did not happen" (the one exception is the customer-owned finalize
observation — see that page):

| In the log                     | Means                                                                |
| ------------------------------ | -------------------------------------------------------------------- |
| IOC found                      | the address is in the feed; the evidence names the feed's own IOC id, its type, its confidence and its malware label |
| no match                       | the check ran and found nothing                                       |
| no match (coverage partial)    | the check ran, but not every URL in the message could be examined     |
| check unavailable — *reason*   | the check could not run; the reason is named                          |
| fail-closed: block on failure  | your `on_unavailable: "block"` turned that failed check into a block  |
| nothing to check               | the message contained no supported URL                                |
| reused verdict                 | the answer came from the cache of an identical, recent request        |

The evidence is the FEED's data — an IOC id, a type, a confidence, a malware
label. Two boundaries hold there: **the URL from your own traffic is never
copied into the evidence**, and the feed's free text (a malware label, a
provider reference) is rendered as text, never as a link. A numeric IOC id
whose shape the dashboard has verified does link to that feed's own entry on
abuse.ch, so you can read the provider's record of it.

You can filter the log by these outcomes with the **URL reputation** facet,
including negatively ("not IOC found").

## URL filtering or URL reputation?

They answer different questions and work well together:

| | `url_filter` | `url_reputation` |
| --- | --- | --- |
| Judges | the SHAPE of a URL — domain, scheme, port, encoding | the IDENTITY of a URL against a feed |
| Knows about | what you listed | what abuse.ch published |
| Needs maintenance | yes, the lists are yours | no, the feed is re-imported for you |
| Catches a brand-new malicious domain | only if you listed it | if the feed has it |
| Can allow or mask | yes | no — block only |

Enable both: `url_filter` for your own structural policy (no `file:` scheme, no
IP literals, only these partner domains), `url_reputation` for the links
neither of you has seen before. Rule order decides which one reports a message
that both would flag.

## Availability

URL reputation is enabled per deployment. If the rule type is not available in
your project, or a rule reports that the feed is not served, contact support —
the feeds are imported by the CollieAi deployment, not by your project.

URLhaus data is published by abuse.ch under its own terms; depending on your
deployment, rules that use it may be restricted to Monitor.

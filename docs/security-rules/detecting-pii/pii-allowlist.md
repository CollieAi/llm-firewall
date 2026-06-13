---
icon: shield-check
---

# PII Allowlist

The PII allowlist lets **known-good** sensitive values pass through a response
unmasked, while everything else the rule detects is still masked or blocked.

The motivating case is **cross-tenant leak prevention**: a user's own IBAN
should be allowed to appear in the model's reply to that user, but an IBAN that
belongs to someone else must still be masked. Your integration sends **keyed
hashes** of the values you want to allow — not the plaintext — and CollieAi
hashes each detected value the same way and compares. (The one exception is the
Playground, a dashboard preview that accepts plaintext samples and hashes them
server-side — see [Testing in the Playground](#testing-in-the-playground).)

It plugs into the [Structured IDs](structured-ids.md) and
[Regex patterns](regex-patterns.md) rule types — there is no separate "allowlist
rule". When a rule's allowlist is enabled, a detected value whose hash is on the
request's allowlist is **passed through unchanged** (not masked, and it does not
trigger a `block`).

## How it works

```
your app ──► hash known-good values with your project secret
             attach them on the X-CollieAi-PII-Allowlist header
                    │
                    ▼
CollieAi detects PII in the OUTPUT
   for each detected value:
     hash it with the same project secret
     on the allowlist? ──► pass through unchanged
     not on the allowlist? ──► mask / block as usual
```

Suppression runs on the **output** only. If every detected value in a message
is allowlisted, the rule does not trigger at all — so a `block`-decision rule
won't block a response that contains only known-good values.

## Setup

1. **Generate a project secret.** In the dashboard, open your project and use
   **PII Allowlist Secret → Generate**. The secret is shown once — copy it and
   store it with your application config. It is the HMAC key both you and
   CollieAi use; CollieAi stores only an encrypted copy.
2. **Enable the allowlist on a rule.** On a Structured ID or Regex rule, turn on
   **PII Allowlist**. The rule must run on the **output** — set its Direction to
   **Output** or **All**.
3. **Send hashes per request** (below), or turn on **Auto-allowlist from input**
   to skip hashing entirely.

> The feature is also gated per host by your operator. If it is enabled for your
> project but not yet on the host, the secret is stored but suppression does not
> take effect yet.

## The contract

To match, you must hash a value **byte-identically** to CollieAi. The contract
is versioned (`norm=v1`); it will only change under a new version with an
explicit migration. Committed
[test vectors](pii-allowlist-test-vectors.json) let your SDK self-verify.

### Secret

The secret is an **opaque ASCII string** (URL-safe, ~43 chars). The HMAC key is
the **UTF-8 bytes of that exact string** — do **not** base64-decode or
hex-decode it first. HMAC the displayed string as-is.

### Hash

```
hash = lowercase_hex( HMAC-SHA256( key = utf8(secret), message = utf8(canonical) ) )
```

`canonical` is the value after the canonicalization for its type (below).
CollieAi accepts upper- or lower-case hex on input and compares
case-insensitively.

### Canonicalization (`norm=v1`)

**Structured IDs** — fixed per entity type:

| Entity type   | Canonical form                          | Example                                            |
| ------------- | --------------------------------------- | -------------------------------------------------- |
| `iban`        | remove spaces & hyphens, **uppercase**  | `DE89 3704 0044 0532 0130 00` → `DE89370400440532013000` |
| `credit_card` | remove spaces & hyphens (digits only)   | `4111 1111 1111 1111` → `4111111111111111`         |
| `bic`         | remove spaces & hyphens, **uppercase**  | `DEUT DE FF 500` → `DEUTDEFF500`                    |

**Regex rules** — each rule chooses a `normalization` mode (a regex match has no
fixed type):

| Mode        | Canonical form                                  | Notes                                           |
| ----------- | ----------------------------------------------- | ----------------------------------------------- |
| `minimal`   | Unicode **NFC** + trim surrounding whitespace   | Default. Case-sensitive.                         |
| `lowercase` | `minimal` then **simple** `lower()`             | Simple lowercase, **not** Unicode case folding (`ß` stays `ß`). |
| `exact`     | the value unchanged                             | Byte-for-byte.                                  |

### Scope (which bucket a hash goes in)

Hashes are grouped by **family** in the request payload:

* Structured IDs use the family name: `iban`, `credit_card`, or `bic`.
* Regex rules are **scoped per rule**: the family is `regex:<rule_id>`, where
  `<rule_id>` is the rule's **UUID** (as shown in the dashboard / returned by
  the API — not a name or slug). A non-UUID family is rejected with `400`. A
  value allowlisted for one regex rule never affects another.

### Request header

Send the allowlist as a single HTTP header on each request — it is read from the
header only, never from the request body, so it is never forwarded to the model
provider.

```
X-CollieAi-PII-Allowlist: <base64url(JSON)>
```

The JSON envelope:

```json
{
  "v": 1,
  "alg": "HMAC-SHA256",
  "norm": "v1",
  "entries": {
    "iban": ["ef5cf819672383117df2ebccce59c05cc5bc20dba88604d58c8a3ce84a5a868d"],
    "credit_card": ["86b8efc3f470672de80feea7028cb84f642b71d3c9020a27a6edc4508ff8b040"],
    "regex:11111111-2222-3333-4444-555555555555": ["..."]
  }
}
```

Base64url-encode the JSON (padding optional). Limits: at most **256** entries
total, and the decoded payload must be **≤ 16 KB**. A malformed, duplicated, or
empty header — or one sent to a project with no secret — is rejected with
`400`; the request never "fails open".

## Worked example

Allowlist the IBAN `DE89 3704 0044 0532 0130 00` using the example secret
`Nf3kP9wQ2vX7zB1cD5gH8jL0mR4sT6yA3eU7iO2pK9s`:

1. Canonicalize for `iban`: remove spaces/hyphens, uppercase →
   `DE89370400440532013000`
2. HMAC-SHA256 with the UTF-8 secret, lowercase hex →
   `ef5cf819672383117df2ebccce59c05cc5bc20dba88604d58c8a3ce84a5a868d`
3. Put it in the `iban` bucket, build the envelope, base64url-encode, and send
   it on `X-CollieAi-PII-Allowlist`.

This exact vector is in the committed
[test vectors](pii-allowlist-test-vectors.json), so you can confirm your
implementation matches before going live.

```python
import hashlib, hmac, re, base64, json

SECRET = "Nf3kP9wQ2vX7zB1cD5gH8jL0mR4sT6yA3eU7iO2pK9s"

def canonical_iban(v):        return re.sub(r"[-\s]", "", v).upper()
def canonical_credit_card(v): return re.sub(r"[-\s]", "", v)
def canonical_bic(v):         return re.sub(r"[-\s]", "", v).upper()

def hash_value(canonical):
    return hmac.new(SECRET.encode("utf-8"),
                    canonical.encode("utf-8"),
                    hashlib.sha256).hexdigest()

entries = {"iban": [hash_value(canonical_iban("DE89 3704 0044 0532 0130 00"))]}
payload = {"v": 1, "alg": "HMAC-SHA256", "norm": "v1", "entries": entries}
header = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()
# -> send header as X-CollieAi-PII-Allowlist
```

## Auto-allowlist from input (no hashing)

Turn on **Auto-allowlist from input** on the rule to release a user's own values
that appear in the **output**, without sending hashes. On the **input** pass,
CollieAi records the values it detects in the end user's own message (user-role
messages only); on the **output** pass, those same values pass through unmasked —
no client-side hashing required.

For auto to work end to end, the rule must run on **both** input and output, so
set its Direction to **All**.

> **Important — auto-allowlist does not bypass input masking.** CollieAi still
> masks the value in the **input** before the model sees it (PII protection is
> intentional and is not turned off). The model therefore never receives the raw
> value and **cannot echo it back** — a "repeat the IBAN I just sent" prompt
> returns the masked form, not the original. Auto-allowlist releases the value
> only when it reaches the **output from another source**: typically your
> assistant looking the user's own IBAN up from your backend or a tool and
> including it in the reply. If you need a value released on a literal echo of
> the prompt, auto-allowlist cannot do that — the value must arrive in the output
> independently of the (masked) input.

> Auto-allowlist works for the synchronous proxy (`/v1/chat/completions`,
> `/v1/messages`), drop-in SDKs, the Playground, **and** async
> [`/v1/jobs`](../../async-jobs/creating-jobs.md). For async jobs, CollieAi
> records the values detected on the input step and carries them to the output
> step internally (persisted on the job), so a user's own values are released on
> the output (subject to the same input-masking caveat above) without any client
> hashing.

## Async jobs and drop-in SDKs

The request **header** is honored by the async
[`/v1/jobs`](../../async-jobs/creating-jobs.md) API: send
`X-CollieAi-PII-Allowlist` when you create the job and CollieAi persists it for
the worker to apply on the output. Drop-in SDKs attach the header on the proxied
request; it is stripped before the upstream provider call.

Async jobs support **both** the request-header hashes above and
**auto-allowlist-from-input**: even though a job's input and output run as
separate steps, CollieAi persists the input-derived values on the job so the
output step can suppress them.

## Testing in the Playground

The Playground has a **Known-good PII (allowlist)** field. Type plaintext sample
values (comma-separated) and run — CollieAi hashes
them server-side with your project's secret so you can preview which detections
would be suppressed, without computing hashes by hand. (Your real client still
sends hashes via the header.) The trace verdict shows how many detections were
allowlisted.

## Test vectors

[`pii-allowlist-test-vectors.json`](pii-allowlist-test-vectors.json) is a frozen
set of `input → expected_canonical → expected_hmac` cases (structured and
regex), keyed with a fixed example secret. Run your SDK against every vector
before trusting it in production; if a value drifts, your canonicalization or
HMAC does not match the contract and your allowlist would silently fail to
match.

## Security notes

* Entries are **keyed** (HMAC), not bare hashes, so an intercepted or logged
  entry cannot be brute-forced back to the low-entropy value without the secret.
* **Rotating or revoking the secret invalidates every previously distributed
  hash.** After a rotation, recompute your allowlist with the new secret, or
  your known-good values will be masked again (fail-closed — never leaked).
* Allowlist entries sent on the request header are **hashes, not plaintext** —
  CollieAi can compare them but cannot recover the original values.
* The project **secret** is encrypted at rest and never logged in clear text.
* The Playground's plaintext "known-good values" field is a dashboard
  convenience — those values are HMAC'd server-side for the preview and are not
  persisted as an allowlist.
* Separately from this feature, your prompts and responses may be retained per
  your project's
  [data-retention settings](../../projects-and-policies/data-retention.md). That
  is independent of the allowlist and governed by your logging configuration.

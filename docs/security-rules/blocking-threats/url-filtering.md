---
description: >-
  How CollieAi URL filtering blocks malicious links — normalize URLs (RFC 3986)
  and filter by domain, scheme, and port to stop phishing, exfiltration,
  IP-literal, and SSRF attempts.
icon: filter-list
---

# URL filtering

## What is the URL filter rule type?

The URL Filter rule type enables detection and processing of URLs in messages according to configurable policies. It performs automatic URL normalization following RFC 3986 before applying filtering rules.

**Ideal for:**

* Blocking malicious or untrusted domains
* Restricting URL schemes (e.g., blocking `javascript:`, `file:`, `data:`)
* Preventing data exfiltration via URL parameters
* Blocking direct IP address access
* Detecting URL obfuscation and encoding attacks

{% hint style="info" %}
**Key points**

* URL filtering detects and filters URLs in messages by domain, scheme, and port, with automatic RFC 3986 normalization.
* It can block malicious or untrusted domains, restrict schemes (`file:`, `javascript:`, `data:`), and block IP-literal URLs to prevent SSRF.
* Encoded-pattern detection catches obfuscation like `%2e%2e` path traversal and double-encoding.
* `deny_domains` always takes priority over `allow_domains`, and domain matches include subdomains.
{% endhint %}

## How does URL filtering work?

1. URLs are extracted from the message text using pattern matching
2. Each URL is normalized according to RFC 3986 standards
3. Normalized URLs are checked against configured policies
4. Based on the rule's decision setting, URLs may be allowed, masked, or blocked

## URL Normalization

All URLs are automatically normalized before filtering. This process:

| Step                | Description                                                      |
| ------------------- | ---------------------------------------------------------------- |
| Parse URL           | Strict parsing into components (scheme, host, port, path, query) |
| Lowercase           | Convert scheme and host to lowercase                             |
| IDN Conversion      | Convert Unicode hostnames to Punycode (`xn--...`)                |
| Default Ports       | Remove default ports (80 for HTTP, 443 for HTTPS)                |
| Path Normalization  | Collapse `.` and `..` segments, normalize slashes                |
| Percent-Encoding    | Decode once to detect hidden sequences, re-encode safely         |
| Query Normalization | Sort keys alphabetically, apply length limits                    |
| Strip Userinfo      | Remove `user:pass@` credentials from URL                         |

Normalization helps detect URL obfuscation attempts and ensures consistent filtering.

## Rule Configuration

### Properties

| Property                 | Type    | Required | Default | Description                                                                       |
| ------------------------ | ------- | -------- | ------- | --------------------------------------------------------------------------------- |
| `allow_schemes`          | list    | No       | -       | Allowed URL schemes (e.g., `["https", "http"]`). If set, all others are blocked.  |
| `deny_schemes`           | list    | No       | -       | Blocked URL schemes (e.g., `["file", "javascript"]`).                             |
| `allow_domains`          | list    | No       | -       | Allowed domains (includes subdomains). If set, all others are blocked.            |
| `deny_domains`           | list    | No       | -       | Blocked domains (includes subdomains). Takes priority over `allow_domains`.       |
| `allow_ports`            | list    | No       | -       | Allowed ports. If set, all others are blocked.                                    |
| `block_ip_literals`      | boolean | No       | false   | Block URLs with direct IP addresses.                                              |
| `block_encoded_patterns` | boolean | No       | false   | Block URLs with suspicious encoded patterns.                                      |
| `detect_bare_domains`    | boolean | No       | false   | Detect bare domain names without scheme (e.g., `example.com` without `https://`). |

### Example Configuration

```json
{
  "allow_schemes": ["https", "http"],
  "deny_domains": ["evil.com", "malware.net"],
  "block_ip_literals": true,
  "block_encoded_patterns": true
}
```

### Detect Bare Domains

Enable `detect_bare_domains` to catch domain references without `http://` or `https://` prefix:

```json
{
  "deny_domains": ["competitor.com", "malware.net"],
  "detect_bare_domains": true
}
```

| Input                      | `detect_bare_domains` | Detected? |
| -------------------------- | --------------------- | --------- |
| `https://malware.net/page` | `false`               | Yes       |
| `visit malware.net today`  | `false`               | No        |
| `visit malware.net today`  | `true`                | Yes       |

## Domain Matching

Domain matching includes subdomains automatically:

| Config                           | URL                            | Match? |
| -------------------------------- | ------------------------------ | ------ |
| `allow_domains: ["example.com"]` | `https://example.com/page`     | Yes    |
| `allow_domains: ["example.com"]` | `https://sub.example.com/page` | Yes    |
| `allow_domains: ["example.com"]` | `https://a.b.example.com/page` | Yes    |
| `allow_domains: ["example.com"]` | `https://notexample.com/page`  | No     |

The `deny_domains` list takes priority over `allow_domains`. If a domain matches both lists, it will be blocked.

## Scheme Filtering

Common schemes and their typical handling:

| Scheme       | Typical Policy               | Risk Level |
| ------------ | ---------------------------- | ---------- |
| `https`      | Allow                        | Low        |
| `http`       | Allow (or deny for security) | Medium     |
| `file`       | Deny                         | High       |
| `javascript` | Deny                         | High       |
| `data`       | Deny                         | High       |
| `blob`       | Deny                         | Medium     |
| `ws`, `wss`  | Context-dependent            | Medium     |

## IP Literal Blocking

When `block_ip_literals` is enabled, URLs with IP addresses instead of domain names are blocked:

* IPv4: `http://192.168.1.1/admin`
* IPv6: `http://[::1]/admin`

This prevents:

* Bypassing domain-based allow lists
* Access to internal network resources
* SSRF (Server-Side Request Forgery) attacks

## Encoded Pattern Detection

When `block_encoded_patterns` is enabled, the rule detects:

| Pattern              | Example     | Description             |
| -------------------- | ----------- | ----------------------- |
| Encoded `..`         | `%2e%2e`    | Path traversal attempt  |
| Encoded `/`          | `%2f`       | Hidden path separator   |
| Encoded `\`          | `%5c`       | Hidden backslash        |
| NULL byte            | `%00`       | Null byte injection     |
| Double encoding      | `%252e`     | Obfuscation attempt     |
| Credential injection | `@` in path | Potential URL confusion |

## Example Rules

{% stepper %}
{% step %}
#### Block Malicious Domains

```json
{
  "name": "Block Malicious Domains",
  "rule_type": "url_filter",
  "order": 5,
  "direction": "all",
  "decision": "block",
  "config": {
    "deny_domains": ["evil.com", "malware.net", "phishing.org"]
  },
  "block_message": "URL blocked: domain is not allowed"
}
```
{% endstep %}

{% step %}
#### Allow Only Trusted Domains

```json
{
  "name": "Trusted Domains Only",
  "rule_type": "url_filter",
  "order": 10,
  "direction": "outbound",
  "decision": "block",
  "config": {
    "allow_domains": ["company.com", "trusted-partner.com"],
    "allow_schemes": ["https"]
  },
  "block_message": "Only trusted domains are allowed"
}
```
{% endstep %}

{% step %}
#### Mask External URLs (Input)

```json
{
  "name": "Mask External URLs",
  "rule_type": "url_filter",
  "order": 15,
  "direction": "inbound",
  "decision": "mask",
  "config": {
    "allow_domains": ["internal.company.com"]
  }
}
```
{% endstep %}

{% step %}
#### Security-Focused Filter

```json
{
  "name": "Security URL Filter",
  "rule_type": "url_filter",
  "order": 1,
  "direction": "all",
  "decision": "block",
  "config": {
    "deny_schemes": ["file", "javascript", "data", "blob"],
    "block_ip_literals": true,
    "block_encoded_patterns": true
  },
  "block_message": "URL blocked for security reasons"
}
```
{% endstep %}

{% step %}
#### API Endpoint Restriction

```json
{
  "name": "Restrict API Ports",
  "rule_type": "url_filter",
  "order": 20,
  "direction": "outbound",
  "decision": "block",
  "config": {
    "allow_ports": [443, 80],
    "allow_schemes": ["https", "http"]
  },
  "block_message": "Only standard HTTP/HTTPS ports are allowed"
}
```
{% endstep %}
{% endstepper %}

## Processing Flow

```
1. Extract all URLs from message
2. For each URL:
   a. Normalize URL (RFC 3986)
   b. Check deny_schemes -> if match, apply decision
   c. Check allow_schemes -> if not in list, apply decision
   d. Check deny_domains -> if match, apply decision
   e. Check allow_domains -> if not in list, apply decision
   f. Check allow_ports -> if not in list, apply decision
   g. Check block_ip_literals -> if IP detected, apply decision
   h. Check block_encoded_patterns -> if detected, apply decision
3. Apply rule decision (allow/mask/block)
```

## Decision Types

| Decision | Behavior                                                               |
| -------- | ---------------------------------------------------------------------- |
| `allow`  | URLs pass through unchanged, rule processing stops                     |
| `mask`   | URLs replaced with `[URL_REDACTED]`, processing continues to next rule |
| `block`  | Message rejected with configured `block_message`                       |

## Metadata

When a URL filter rule matches, the metadata includes:

```json
{
  "matched_urls": [
    {
      "original": "https://Evil.COM/path",
      "normalized": "https://evil.com/path",
      "original_hash": "a1b2c3d4e5f6g7h8",
      "violation": "denied_domain: evil.com"
    }
  ],
  "url_count": 1,
  "violations": ["denied_domain: evil.com"]
}
```

## Best Practices

1. **Layer your rules**: Use multiple URL filter rules with different orders for defense in depth
2. **Start restrictive**: Begin with allow lists and expand as needed
3. **Enable security options**: Always enable `block_ip_literals` and `block_encoded_patterns` for security-sensitive applications
4. **Use HTTPS-only**: Consider denying `http` scheme in production environments
5. **Monitor violations**: Review matched URLs to refine your rules
6. **Combine with other rules**: Use URL filtering alongside regex and dictionary rules for comprehensive protection

## Comparison with Other Rules

| Aspect          | URL Filter                      | Regex              | Dictionary Match |
| --------------- | ------------------------------- | ------------------ | ---------------- |
| Best for        | URL-specific policies           | Pattern matching   | Keyword lists    |
| Normalization   | Automatic RFC 3986              | Manual patterns    | None             |
| Domain matching | Built-in with subdomain support | Pattern-based      | Exact match      |
| Performance     | Fast for URL-focused checks     | Depends on pattern | O(n) dictionary  |

## Troubleshooting

### Why aren't URLs being detected?

1. Verify the URL format is standard (`http://` or `https://`)
2. Check if the URL is malformed or truncated
3. Test with the `/test` endpoint to see extraction results

### Why is a URL being blocked unexpectedly?

1. Check if domain is in both allow and deny lists (`deny` takes priority)
2. Verify port numbers match your allow list
3. Check if `block_ip_literals` is blocking legitimate IP-based URLs
4. Review normalized URL in metadata for case/encoding differences

### Why aren't subdomains matching as expected?

1. Remember that `allow_domains: ["example.com"]` allows all subdomains
2. Use `deny_domains` to block specific subdomains of allowed domains
3. Check for typos in domain names

### Does URL filtering affect performance?

1. URL extraction and normalization add minimal overhead
2. Large allow/deny lists are still fast (string comparison)
3. Consider placing URL filter rules early in the order to catch malicious URLs quickly

### Frequently asked questions

**How does CollieAi block malicious URLs?** CollieAi's URL filter extracts and normalizes URLs (RFC 3986), then allows, masks, or blocks them by domain, scheme, and port — stopping untrusted domains, dangerous schemes, IP-literal URLs, and encoded obfuscation patterns.

**Can CollieAi prevent data exfiltration through URLs?** Yes. You can restrict outbound URLs to an allowlist of trusted domains and block IP literals and encoded patterns, which helps prevent exfiltration and SSRF via crafted links.

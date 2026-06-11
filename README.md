<p align="center">
  <a href="https://collieai.io">
    <img src="https://collieai.io/logo-1.svg" alt="CollieAi" width="80" />
  </a>
</p>

<h1 align="center">LLM Firewall — AI Security Proxy & Guardrails for GPT, Claude, Gemini</h1>

<h4 align="center">
Drop-in, provider-agnostic AI guardrails proxy that masks PII, blocks prompt injection & jailbreaks, and logs every LLM call. 
One line change. Works with OpenAI, Anthropic Claude, Google Gemini, Azure OpenAI, AWS Bedrock, and self-hosted models.
</h4>

<p align="center">
  <a href="https://collieai.io"><img src="https://img.shields.io/badge/website-collieai.io-blue" alt="CollieAi Website" /></a>
  <a href="https://docs.collieai.io"><img src="https://img.shields.io/badge/docs-docs.collieai.io-green" alt="Documentation" /></a>
  <a href="https://app.collieai.io"><img src="https://img.shields.io/badge/free_tier-20K_calls/month-brightgreen" alt="Free Tier" /></a>
</p>

<p align="center">
  <a href="https://docs.collieai.io/getting-started/quick-start">Quick Start</a> · <a href="https://docs.collieai.io">Docs</a> · <a href="https://docs.collieai.io/api-reference">API Reference</a> · <a href="https://app.collieai.io">Try Free</a> · <a href="https://docs.collieai.io/self-hosting">Self-Host</a>
</p>

## Why LLM Firewall?

You're building with GPT-4, Claude, Gemini — but every API call is a potential data leak. Users paste credit cards into chat. Attackers inject malicious prompts. Sensitive data flows to third-party models without any filtering.

**LLM Firewall** by [CollieAi](https://collieai.io) is a **drop-in security proxy** that sits between your application and the LLM provider. It inspects, masks, and blocks — in real time, with zero code changes beyond swapping the base URL.

<!-- GIF: dashboard, policy engine, real-time logs -->

<img width="1000" height="561" alt="CollieAi LLM firewall blocking a prompt injection attack in real time — demo" src="https://github.com/user-attachments/assets/de356d6e-6483-4d30-aa80-d8c36482816e" />



## Key Features

- **Drop-in OpenAI-compatible proxy** — change `base_url`, keep your SDK. Python, Node.js, Go, curl — anything that speaks OpenAI works with CollieAi
- **PII detection & masking** — regex patterns, structured ID validation (Luhn, MOD-97), and dictionary matching via Aho-Corasick
- **Prompt injection protection** — ML classifier (10-50 ms) plus optional LLM-based analysis for sophisticated attacks
- **Flexible policy engine** — 6 configurable rule categories, each with monitor (log only) or enforce (mask/block) mode. Custom regex, dictionaries, thresholds — tune everything per project
- **Input + output filtering** — scan both user prompts and model responses with independent policies
- **User satisfaction tracking** — detect negative sentiment, monitor dissatisfaction metrics, get alerts when something goes wrong
- **Full audit trail** — every request logged with triggered rules, latency, and token counts. Filter by project, time range, or rule type
- **Dashboard** — create projects, configure rules, add provider tokens, review logs. No config files, no deployments

> **Works with:** OpenAI · Claude · deepseek · Gemini · Azure OpenAI · AWS Bedrock · any OpenAI-compatible endpoint

## Quick Start — 3 Steps

<table>
<tr>
<td width="40%">

**1. Point your client at CollieAi**

Sign up for a free API key and change your `base_url`. No SDK required, no architecture changes.

</td>
<td width="60%">

```python
# Change two config values
base_url = "https://app.collieai.io/v1"
api_key  = "clai_your_project_key"

# Free: 20,000 calls/month
```

</td>
</tr>
<tr>
<td width="40%">

**2. Your code stays the same**

CollieAi is a transparent proxy. Use the standard OpenAI SDK — every request is filtered by your policy rules automatically.

</td>
<td width="60%">

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://app.collieai.io/v1",
    api_key="clai_...",
)
client.chat.completions.create(...)
```

</td>
</tr>
<tr>
<td width="40%">

**3. Threats blocked, full audit trail**

Only safe, compliant responses reach your users. Dashboard shows every blocked request with triggered rules and context.

</td>
<td width="60%">

```json
{
  "error": {
    "message": "Content blocked by policy",
    "type":    "content_blocked",
    "code":    400
  }
}
```

</td>
</tr>
</table>

Or set environment variables — **zero code changes**:

```bash
export OPENAI_BASE_URL=https://app.collieai.io/v1
export OPENAI_API_KEY=clai_your_project_key
# Your existing code works unchanged
```

**[Get Started Free — 20,000 calls/month, no credit card](https://app.collieai.io)**

## How It Works

<img width="1341" height="548" alt="How CollieAi AI firewall works: security proxy between your app and the LLM provider" src="https://github.com/user-attachments/assets/cf40c56e-a7d9-4255-9a21-a3c30e7a06cf" />


## AI Guardrails & Security Rules — Fully Configurable

Select the threats you want to protect against. Each rule category is independently configurable — choose enforcement mode, set thresholds, add custom patterns, and apply rules to input prompts, output responses, or both. Start in **monitor** mode to observe, switch to **enforce** when ready.

## OWASP LLM Top 10 Coverage

LLM Firewall addresses the most critical risks from the OWASP Top 10 for LLM Applications:

| OWASP Risk | How CollieAi protects |
|---|---|
| LLM01: Prompt Injection | ML classifier + dictionaries + optional LLM-based analysis |
| LLM02: Sensitive Information Disclosure | PII detection & masking, secrets & API key filtering |
| LLM05: Improper Output Handling | Output filtering with independent policies |
| LLM09: Misinformation | User satisfaction & sentiment monitoring |

### Prompt Injection <kbd>#1 LLM threat</kbd>

Detect and block prompt injection & jailbreak attempts using dictionaries, ML models, and language detection. Lightweight ML classifier runs in 10-50 ms — catches jailbreaks, role hijacking, and instruction override before the request ever reaches the LLM. Optional secondary LLM-based analysis for sophisticated attacks that evade pattern matching.

### PII & Financial Data <kbd>Compliance</kbd>

Detect credit cards, IBANs, SSNs, emails, and other personal data. Three complementary methods: configurable regex patterns for any format, checksum validation (Luhn for credit cards, MOD-97 for IBANs) for structural verification, and Aho-Corasick dictionary matching for names and org-specific terms.

### Profanity & Sensitive Words <kbd>Brand safety</kbd>

Filter profanity and sensitive content using multi-language dictionary groups. Upload custom word lists per project — block or mask offensive terms, competitor names, internal codenames, or any content that violates your brand policy.

### Secrets & API Keys <kbd>Data leak risk</kbd>

Detect API keys, tokens, private keys, and credentials via regex patterns. Catches `sk-...`, `ghp_...`, `AKIA...`, PEM keys, JWT tokens, and other secret formats before they leak to third-party models.

### Malicious URLs <kbd>Common threat</kbd>

Filter suspicious URLs by scheme, domain, IP literals, and encoded patterns. Block phishing links, data exfiltration endpoints, and obfuscated URLs that try to bypass simple string matching.

### Hidden Payloads <kbd>Advanced threat</kbd>

Detect hidden base64-encoded payloads and file data in messages. Automatically decode and inspect embedded content — catches hidden instructions, encoded exploits, and smuggled data that looks like innocent text.

> **Flexible enforcement:** Every rule supports `monitor` mode (log detections, pass through) or `enforce` mode (mask PII / block request). Rules run bidirectionally — configure input and output independently. Add your own regex patterns, upload custom dictionaries, set ML confidence thresholds, and define different policies per project.

---

## Works With Every Provider

CollieAi routes to any OpenAI-compatible LLM provider. Configure your provider token in the dashboard — CollieAi handles the rest.

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 |
| **Anthropic** | Claude Sonnet, Opus, Haiku |
| **Google** | Gemini Pro, Flash |
| **deepseek** | deepseek-chat, deepseek-coder |
| **Azure OpenAI** | All Azure-hosted models |
| **AWS Bedrock** | Via OpenAI-compat wrapper |
| **Self-hosted** | vLLM, Ollama, LocalAI |

Full SSE streaming support for all providers. Async webhook mode available for batch processing.

---

## Documentation

Full documentation at **[docs.collieai.io](https://docs.collieai.io)**

| Section | What you'll learn |
|---------|------------------|
| [**Quick Start**](https://docs.collieai.io/getting-started/quick-start) | Sign up → first secured request in 5 minutes |
| [**Proxy Integration**](https://docs.collieai.io/proxy-integration) | Python, Node.js, cURL, streaming, error handling |
| [**Security Rules**](https://docs.collieai.io/security-rules) | All rule types, pipeline ordering, enforcement modes |
| [**Async Jobs**](https://docs.collieai.io/async-jobs) | Webhooks, job lifecycle, two-hook pattern |
| [**Projects & Policies**](https://docs.collieai.io/projects-and-policies) | Multi-tenancy, data retention, provider tokens |
| [**Monitoring**](https://docs.collieai.io/monitoring) | Logs, analytics dashboards, alerts |
| [**API Reference**](https://docs.collieai.io/api-reference) | Full endpoint docs for 14 API groups |
| [**Self-Hosting**](https://docs.collieai.io/self-hosting) | Docker Compose, ML model config, local dev |

---

<p align="center">
  <b>Secure your LLM calls in 5 minutes. Free forever, no credit card.</b><br/><br/>
  <a href="https://app.collieai.io">
    <img src="https://img.shields.io/badge/Get_Started_Free-→-brightgreen?style=for-the-badge" alt="Get Started Free" />
  </a>
</p>

## FAQ

### What is an LLM firewall?
An LLM firewall is a security layer that sits between your application and LLM providers, inspecting every prompt and response in real time. It blocks prompt injection and jailbreak attempts, masks PII and secrets, and filters unsafe content before it reaches the model — or your users.

### What is the difference between an LLM firewall and AI guardrails?
AI guardrails are the individual rules (block prompt injection, redact PII, filter profanity). An LLM firewall is the enforcement layer that runs those guardrails on live traffic. CollieAi combines both: a configurable guardrail policy engine deployed as a transparent proxy — no SDK or framework integration required.

### How does CollieAi differ from guardrails libraries like LLM Guard or NeMo Guardrails?
Libraries run inside your application code — you install, configure, and maintain them per service. CollieAi works at the network level: change your `base_url` and every app, language, and framework is protected by centrally managed policies, with a shared audit trail and dashboard.

### How does prompt injection detection work?
Three layers: dictionary and pattern matching, a lightweight ML classifier (10–50 ms) that catches jailbreaks, role hijacking, and instruction override, and optional LLM-based analysis for sophisticated or paraphrased attacks that evade pattern matching.

### Can it detect indirect prompt injection in RAG pipelines?
Yes. Malicious instructions hidden in retrieved documents, web pages, or file content pass through the same inspection pipeline as user input, including base64-decoded hidden payloads.

### Does it work with AI agents and agentic workflows?
Yes. Any agent framework that calls an OpenAI-compatible endpoint — LangChain, LlamaIndex, CrewAI, custom agents — is secured by changing the base URL. Both the agent's prompts and the model's responses are filtered.

### What PII can it redact?
Credit cards (Luhn-validated), IBANs (MOD-97), SSNs and national IDs for 8 countries, emails, phone numbers, plus custom regex patterns and dictionary lists for names or org-specific terms. Each rule can mask, block, or just monitor.

### Does it cover the OWASP Top 10 for LLM Applications?
Yes — including LLM01 Prompt Injection, LLM02 Sensitive Information Disclosure, and LLM05 Improper Output Handling. See the [OWASP coverage table](#owasp-llm-top-10-coverage) above.

### Which LLM providers are supported?
CollieAi is provider-agnostic: OpenAI, Anthropic Claude, Google Gemini, DeepSeek, Azure OpenAI, AWS Bedrock, and self-hosted models (vLLM, Ollama, LocalAI). OpenAI-compatible API plus Anthropic's native Messages API.

### How much latency does it add?
10–50 ms for ML-based detection on the free tier, ≤20 ms on paid plans. Pattern and checksum rules run faster. Full SSE streaming is supported.

### Can I self-host the LLM firewall?
Yes — Docker Compose deployment with local ML models is documented in the [self-hosting guide](https://docs.collieai.io/self-hosting). Enterprise plans add on-premise deployment, SSO (OIDC/SAML), and SIEM integration.

### Is there a free tier?
Yes — 20,000 API calls/month, free forever, no credit card. Includes the full guardrail stack: prompt injection detection, PII masking, secrets filtering, and AI content moderation in 23 languages.

<p align="center">
  <a href="https://collieai.io">Website</a> · 
  <a href="https://app.collieai.io">Dashboard</a> · 
  <a href="https://docs.collieai.io">Docs</a> · 
  <a href="https://github.com/CollieAi/llm-firewall/issues">Issues</a>
</p>

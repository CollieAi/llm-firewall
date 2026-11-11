---
description: >-
  How the CollieAi file_policy rule decides what the structural signals of a
  file attached to a job do — hidden text, hidden sheets, active content, a
  mismatched type: block, monitor or ignore. Preview: needs enabling.
icon: file-shield
---

# File policy

{% hint style="info" %}
**Status: preview — needs enabling.** File analysis is off on every deployment for now,
including app.collieai.io: creating a `file_policy` rule answers `422 file_policy_disabled`
until the deployment enables it. In this step a job tracks its files but does not read them
yet, so no structural signal is produced and the rule decides nothing; it takes effect with the
step that reads the content.
{% endhint %}

## What is the file policy rule type?

A `file_policy` rule says what the **structure** of a file attached to a job decides —
whatever its text says. Files reach a policy as
[attachments](../../api-reference/jobs.md#attachments-preview); while CollieAi reads a file it
reports structural signals: text a reader does not see, hidden sheets, active content, a type
that is not what the file claims. For each signal the rule chooses `block`, `monitor` or
`ignore`.

What the **text** of a file says is not this rule's job: the policy's `llm_detection` rule
judges the content of files (see [`file_system_prompt`](llm-detection.md#attached-files-file_system_prompt)),
including text hidden in them.

{% hint style="info" %}
**Key points**

* One enabled `file_policy` rule per policy; it runs on attached files only, never on message text.
* `direction` is `inbound` and `decision` is `block` — each signal's own action is in `config`.
* No `targeting`: the rule is not selected by surfaces.
* Without the rule, the signals are recorded and decide nothing; the policy's `file_analysis_warnings` say so.
{% endhint %}

## The signals

| Signal                   | When it is present                                                       | Default   |
| ------------------------ | ------------------------------------------------------------------------ | --------- |
| `hidden_text`            | Text a reader does not see: white on white, a tiny font, off the page, invisible rendering, Unicode tag characters | `monitor` |
| `hidden_sheets_or_cells` | Hidden or very hidden sheets, hidden rows or columns in a spreadsheet    | `monitor` |
| `layer_ocr_mismatch`     | A PDF whose text layer says something its rendered page does not        | `monitor` |
| `type_class_mismatch`    | The file is not what its declared type says (an "image" that is a PDF)   | `block`   |
| `active_content`         | JavaScript or launch actions in a PDF, macros in a workbook               | `monitor` |
| `embedded_or_external`   | Embedded files, external links, OLE objects                              | `monitor` |

`block` blocks the job when the signal is present — on a policy whose
[`file_analysis`](../../api-reference/files.md#file-analysis-in-a-policy) `decision` is `block`
and whose `enforcement_mode` is `enforce`; otherwise it is recorded as `monitor`. `monitor`
records the signal. `ignore` drops it. A signal you leave out takes its default; the saved
rule keeps only what you set, so a later change of a default applies to it.

## Create the rule

```bash
curl -X POST https://app.collieai.io/api/v1/policies/{policy_id}/rules \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Attached files",
    "rule_type": "file_policy",
    "direction": "inbound",
    "decision": "block",
    "config": {"active_content": "block", "embedded_or_external": "ignore"}
  }'
```

| Status | `error` contains                    | When                                                                 |
| ------ | ----------------------------------- | -------------------------------------------------------------------- |
| `409`  | `file_policy_already_exists`        | The policy already has an enabled `file_policy` rule — edit it, or disable it before enabling another. |
| `422`  | `file_policy_disabled`              | File analysis is not enabled on this deployment.                     |
| `422`  | `file_policy_requires_policy`       | The project has no active policy (project-level route).              |
| `422`  | `file_policy_inbound_only`          | `direction` is not `inbound`.                                        |
| `422`  | `file_policy_decision_unsupported`  | `decision` is not `block`.                                           |
| `422`  | `file_policy_targeting_unsupported` | The request carries `targeting`.                                     |

The rule tester (`POST /api/v1/policies/{policy_id}/rules/{rule_id}/test`) does not apply to
a `file_policy` rule — it answers `422 file_policy_not_testable`: the rule judges a file's
structure, not message text.

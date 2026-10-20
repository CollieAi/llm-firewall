---
description: >-
  Give colleagues their own sign-in to your CollieAi account as an Editor or a
  Viewer, instead of sharing one login and password.
icon: users
---

# Team members

Team members let colleagues work in your CollieAi account with their own
sign-in, so nobody shares a login and password. You decide for each person
whether they may change things (**Editor**) or only look (**Viewer**), and you
can take access away at any time.

{% hint style="info" %}
**Key points**

* A colleague signs in as themselves and works in **your** account: your
  projects, policies, rules, dictionaries, provider tokens, logs and analytics.
* Two roles: **Editor** changes things, **Viewer** only reads.
* Billing, the IP allowlist, deleting projects and the team list stay with the
  account owner.
* Removing someone or changing their role takes effect on their next request.
* Up to 20 members per account.
{% endhint %}

## Roles

| What | Owner | Editor | Viewer |
| --- | --- | --- | --- |
| See projects, policies, rules, dictionaries, logs, analytics and alerts | yes | yes | yes |
| Change projects, policies, rules, dictionaries and alerts | yes | yes | no |
| Create and revoke API keys and provider tokens | yes | yes | no |
| Use the Playground and test a rule | yes | yes | no |
| Delete a project | yes | no | no |
| Change the IP allowlist | yes | no | no |
| Change the plan and billing | yes | no | no |
| Add and remove members, change their role | yes | no | no |

Everything a member creates belongs to your account: a project an Editor
creates is your project, and requests made with its API keys count toward your
plan.

A Viewer sees no secrets: an API key and the PII allowlist secret are shown
only once, to whoever creates them, and provider tokens are always masked.

## Add a colleague

1. Go to **Settings > Team**.
2. Enter the colleague's email address and choose **Editor** or **Viewer**.
3. Click **Add**.

CollieAi emails them that they have access. The member shows as **Pending**
until someone signs in with that address, then as **Active**. The address must
be the one they sign in with — it is compared without regard to letter case,
but `jane.doe@` and `janedoe@` are different addresses.

A colleague who has no CollieAi sign-in yet does not need a Google account:

* the email has a link to choose a name and a password — it works for
  7 days, and opens your account right away;
* or, if their address is a Google account, they click **Sign in with Google**
  on that page or on the sign-in page.

A colleague who already signs in to CollieAi (with their own account) simply
finds yours in the account menu. If an invitation link has expired, remove the
member and add them again — a new email goes out.

To change a role, pick another one next to the member. To remove someone,
click the bin icon and confirm.

## Work in another account

A person can be a member of several accounts and still has their own. Open the
account menu at the bottom of the sidebar and pick the account under
**Accounts**. While you work in someone else's account, the sidebar shows its
address and your role there.

If the account changes in another browser tab, or the owner removes you, the
next action in an open tab reloads the dashboard instead of acting in the wrong
account.

## What stays personal

Each person keeps their own password, sign-in and support tickets. Setting a
password, signing out and writing to support work the same in any account and
in any role. A password sign-in asks for a code sent to the person's own
email, see [Authentication](authentication.md#sign-in-code).

Forgot your password? **Forgot password?** on the sign-in page emails a link
to the address you sign in with. It works once, for one hour. A colleague who
joined by an invitation link keeps their password: it may be their only way to
sign in, so it can be changed but not removed.

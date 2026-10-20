---
description: >-
  How authentication works in CollieAi — sign in to the dashboard with Google  
  OAuth or email and password, and authenticate API requests with clai_ API
  keys.
icon: fingerprint
---

# Authentication

CollieAi supports two sign-in methods for the dashboard — Google OAuth and email/password — and authenticates application requests separately with API keys.

## Google OAuth

Click **Sign in with Google** on the login page and authorize with your Google account.

* **Auto-registration:** The first time you sign in, CollieAi creates your account automatically using your Google profile (name, email, and picture). No separate registration step is required.
* **Returning users:** Subsequent logins refresh your session.

## Email and Password

You can register with an email address and password on the sign-up page.

**Already signed in with Google?** You can add a password to your existing account from the **Settings** page. This lets you sign in with either method going forward.

### What are the password requirements?

Passwords must meet all of the following:

* Between **8** and **72** characters
* At least one **uppercase** letter
* At least one **lowercase** letter
* At least one **digit**

### Sign-in code

After a correct password, CollieAi emails a 6-digit code to your address and
signs you in only when you enter it. The code is also in the email's subject,
so a notification on your phone or lock screen is enough to read it.

* A code works for **10 minutes**, once.
* Five wrong codes end the sign-in: enter your password again for a new code.
* **Send a new code** works once a minute, up to five codes for one sign-in.
* At most **10 codes per hour** for one account. After that, signing in with a
  password waits until the hour is up; **Sign in with Google** still works.

Signing in with Google asks for no code: your Google account's own two-step
verification protects that sign-in.

Forgot your password? **Forgot password?** on the sign-in page emails a link
to set a new one. It works once, for one hour.

### How are sign-in attempts rate-limited?

To protect against brute-force attacks, sign-in attempts are rate-limited:

| Scope             | Limit                  |
| ----------------- | ---------------------- |
| Per IP address    | 10 attempts per minute |
| Per email address | 5 attempts per minute  |

If you hit the limit, wait 60 seconds and try again.

## Session Cookies

After a successful sign-in (Google or email/password), CollieAi sets a session cookie in your browser. All subsequent requests to the dashboard are authenticated using this cookie.

Session cookies are:

* **httpOnly** -- Not accessible to JavaScript, which protects against XSS.
* **Secure** -- Transmitted only over HTTPS in production environments.

#### How do sessions work?

1. You sign in (Google, or email/password and the emailed code).
2. The server creates a session and returns a cookie. A session lasts 7 days.
3. Your browser sends the cookie automatically with every request.
4. When you sign out, the session is invalidated.

## API Key Authentication

Dashboard sessions and API keys are separate authentication mechanisms:

* **Session cookies** authenticate you in the CollieAi dashboard.
* **API keys** (`clai_` prefix) authenticate proxy and API requests from your application.

For details on API key authentication, see [API Keys](api-keys.md).

***

## Summary

| Context       | Method           | Details                                       |
| ------------- | ---------------- | --------------------------------------------- |
| Web dashboard | Google OAuth     | Auto-registration on first login              |
| Web dashboard | Email + password | Optional; set in Settings after Google signup. A code sent to your email completes each sign-in |
| API requests  | `clai_` API key  | Bearer token; scoped to a single project      |

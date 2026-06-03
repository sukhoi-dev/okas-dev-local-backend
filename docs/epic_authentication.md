# EPIC — Authentication & Session Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers all authentication flows and session management for the WE.OKAS platform. Users can authenticate via OTP, password, Google OAuth, or a first-time secure email activation link. Session persistence (Keep me logged in) is also managed here.

---

## STORY 1 — Authenticate User using OTP Login

### User Story
> As a **User**,
> I want to **login using OTP verification**,
> So that **I can securely access the platform without remembering a password**.

### Acceptance Criteria
1. Users can initiate login using a valid email address
2. OTP is generated and delivered successfully to the entered email address
3. OTP remains valid for 5 minutes after generation
4. Users can request OTP resend only after 30 seconds from the previous OTP request
5. Expired OTPs are rejected securely
6. Invalid OTP submissions display meaningful validation feedback
7. Successfully verified users are authenticated and redirected appropriately
8. Unauthorized or suspicious authentication attempts are restricted safely
9. OTP verification activities are logged successfully for audit and troubleshooting purposes
10. User session persists correctly when "Keep me logged in" is enabled
11. User session expires securely when "Keep me logged in" is disabled
12. Multiple OTP requests do not create inconsistent authentication states
13. System remains stable during simultaneous OTP generation and verification operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/otp/send` | Send OTP to provided email |
| POST | `/auth/otp/verify` | Verify OTP and issue session token |
| POST | `/auth/otp/resend` | Resend OTP (30s cooldown enforced) |

### Request Body — Send OTP
```json
{
  "email": "string (required)"
}
```

### Request Body — Verify OTP
```json
{
  "email": "string (required)",
  "otp": "string (required)",
  "keep_me_logged_in": "boolean"
}
```

---

## STORY 2 — Authenticate User using Password Login

### User Story
> As a **User**,
> I want to **login using my email and password**,
> So that **I can securely access the platform using my account credentials**.

### Acceptance Criteria
14. Users can login successfully using valid email and password credentials
15. Invalid email or password submissions display meaningful authentication errors
16. Password fields support secure masked input
17. Successfully authenticated users are redirected to the appropriate dashboard or landing screen
18. Existing user roles, projects, and permissions remain preserved after login
19. Unauthorized or suspicious login attempts are restricted safely
20. User session persists correctly when "Keep me logged in" is enabled
21. User session expires securely when "Keep me logged in" is disabled
22. Authentication activities are logged successfully for audit and troubleshooting purposes
23. Password authentication remains secure during simultaneous login attempts
24. System remains stable during repeated authentication operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate via email + password |

### Request Body
```json
{
  "email": "string (required)",
  "password": "string (required)",
  "keep_me_logged_in": "boolean"
}
```

---

## STORY 3 — Recover Account using Forgot Password

### User Story
> As a **User**,
> I want to **recover my account using forgot password**,
> So that **I can regain access when I forget my password**.

### Acceptance Criteria
25. Users can initiate forgot password flow using a valid email address
26. Forgot password requests trigger secure password reset email delivery
27. Password reset links are uniquely generated and securely validated
28. Expired or invalid reset links are rejected safely
29. Users can create a new password successfully using valid reset links
30. Password reset workflow supports:
    - New Password
    - Confirm Password
31. Password and confirm password values must match before submission
32. Successfully updated passwords invalidate previous active sessions securely
33. Invalid or incomplete password reset submissions display meaningful validation feedback
34. Password reset activities are logged successfully for audit and troubleshooting purposes
35. Unauthorized or suspicious password reset attempts are restricted safely
36. System remains stable during simultaneous password reset requests

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/forgot-password` | Send password reset email |
| POST | `/auth/reset-password` | Reset password using token |
| GET | `/auth/reset-password/validate` | Validate reset token before use |

### Request Body — Reset Password
```json
{
  "token": "string (required)",
  "new_password": "string (required)",
  "confirm_password": "string (required)"
}
```

---

## STORY 4 — Authenticate User using Google Login

### User Story
> As a **User**,
> I want to **login using my Google account**,
> So that **I can securely access the platform without creating separate credentials**.

### Acceptance Criteria
37. Users can authenticate successfully using valid Google accounts
38. Only authorized Google authentication requests are accepted
39. Successfully authenticated users are redirected appropriately after login
40. New users authenticated through Google are onboarded successfully into the platform
41. Existing users retain assigned roles, projects, and permissions after authentication
42. Authentication failures display meaningful error information
43. Unauthorized or invalid authentication attempts are restricted safely
44. User session persists correctly when "Keep me logged in" is enabled
45. User session expires securely when "Keep me logged in" is disabled
46. Authentication activities are logged successfully for audit and troubleshooting purposes
47. System remains stable during simultaneous Google authentication operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/google` | Initiate Google OAuth flow |
| GET | `/auth/google/callback` | Handle Google OAuth callback |

---

## STORY 5 — Complete First-Time User Login using Secure Email Link

### User Story
> As a **Newly Created User**,
> I want to **activate my account using a secure email link**,
> So that **I can create my password and access the platform securely for the first time**.

### Acceptance Criteria
48. Newly created users receive an onboarding email successfully after account creation
49. Onboarding email contains a secure first-time activation link
50. Clicking the activation link redirects users to the Create Password screen
51. Create Password workflow supports:
    - New Password
    - Confirm Password
52. Password and confirm password values must match before submission
53. Invalid or incomplete password submissions display meaningful validation feedback
54. Expired or invalid activation links are rejected safely
55. Successfully created passwords activate the user account immediately
56. Successfully activated users are redirected to login screen after password creation
57. Activation links cannot be reused after successful activation
58. Existing user roles, permissions, and project assignments remain preserved after activation
59. Account activation activities are logged successfully for audit and troubleshooting purposes
60. System remains stable during simultaneous first-time activation operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/activate/validate` | Validate activation token |
| POST | `/auth/activate` | Set password and activate account |

### Request Body — Activate Account
```json
{
  "token": "string (required)",
  "new_password": "string (required)",
  "confirm_password": "string (required)"
}
```

---

## STORY 6 — Manage User Session Persistence

### User Story
> As a **User**,
> I want to **manage my authenticated session when I enable "Keep me logged in"**,
> So that **I do not need to login repeatedly on trusted devices**.

### Acceptance Criteria
61. Users can enable or disable the "Keep me logged in" option during authentication
62. Authenticated sessions persist correctly across browser refreshes and reopen events when enabled
63. Sessions expire securely after inactivity when "Keep me logged in" is disabled
64. Users can logout successfully from active sessions
65. Logout clears active authentication states securely
66. Invalid or expired sessions redirect users back to login screen
67. Unauthorized session reuse attempts are restricted safely
68. Session handling remains consistent across connected platforms and environments
69. Session activities are logged successfully for audit and troubleshooting purposes
70. System remains stable during simultaneous session validation requests

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/logout` | Invalidate current session |
| POST | `/auth/refresh` | Refresh session token |
| GET | `/auth/session` | Validate current session state |

---

## Technical Notes

### DB Tables Involved
- `app_users`
- `app_sessions`
- `otp_requests`
- `password_reset_tokens`
- `activation_tokens`
- `audit_logs`

### Business Rules
- OTP validity: **5 minutes**
- OTP resend cooldown: **30 seconds**
- Activation links are **single-use only** — invalidated after successful activation
- Password reset links are **single-use only** — invalidated after use
- On "Keep me logged in" disabled: session expires on browser close / inactivity
- On logout: all active session tokens for the user must be invalidated
- On password reset: all previous active sessions must be invalidated
- Soft-deleted users must not be able to authenticate — return meaningful account-access feedback

### Validation Rules
- `email` must be a valid email format
- `password` must meet platform complexity requirements
- `new_password` and `confirm_password` must match before submission
- Reset/activation tokens must be validated for expiry and single-use status before processing

### Permission Rules
- All auth endpoints are **public** (no authentication required)
- Logged-in users attempting to re-access login should be redirected to their dashboard
- Unauthorized or suspicious attempts must be logged to `audit_logs`

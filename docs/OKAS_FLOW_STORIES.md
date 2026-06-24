# OKAS Platform — Flow & Task Stories

**Project:** OKAS Cloud (Smart Home B2B SaaS)  
**Stack:** FastAPI + SQLAlchemy (Python 3.8) · MySQL · React/Vite · Zustand · React Query · Tailwind CSS  
**Date:** June 2026

---

## Table of Contents

1. [Platform Architecture Overview](#1-platform-architecture-overview)
2. [Authentication Flow](#2-authentication-flow)
3. [Permission System](#3-permission-system)
4. [Member Management Flow](#4-member-management-flow)
5. [System Integrators (SI) Flow](#5-system-integrators-si-flow)
6. [Multi-tenancy (Org Scoping)](#6-multi-tenancy-org-scoping)
7. [Frontend Navigation Gate](#7-frontend-navigation-gate)
8. [API Reference](#8-api-reference)
9. [Test Credentials](#9-test-credentials)
10. [Task Stories Index](#10-task-stories-index)

---

## 1. Platform Architecture Overview

```
OKAS Platform (Super Admin)
│
├── Manages System Integrators (SI organisations)
│     └── Each SI has: org record + users + roles + permissions
│
└── Each SI Organisation
      ├── Admin user (can manage their own members)
      ├── Project Manager user
      └── Viewer user
```

### User Types

| Type | Description | Key Permission |
|---|---|---|
| **Super Admin** | Platform-level user, manages all SIs | `organizations.manage` |
| **SI Admin** | Admin of a single SI organisation | `members.create`, `members.edit`, `members.delete` |
| **Project Manager** | Can view + limited edit within org | `members.view`, `members.edit` |
| **Viewer** | Read-only access within org | `members.view` |

---

## 2. Authentication Flow

### Story AUTH-1 — Email + Password Login

**Actor:** Any registered user  
**Endpoint:** `POST /we-okas/auth/login`

**Request:**
```json
{ "email": "admin@okas-demo.com", "password": "Admin@123" }
```

**Flow:**
1. Backend fetches `app_users` row joined with `organizations` and latest `roles`.
2. Checks `active_ind = TRUE` — returns `403` if inactive.
3. Verifies bcrypt `password_hash` — returns `401` if mismatch.
4. Queries `role_permissions` for all allowed `feature.action` pairs.
5. Mints a HS256 JWT (24h TTL) with payload: `{sub, user_id, full_name, organization_id, iat, exp}`.
6. Returns token + full user profile + flat permissions list.

**Success Response:**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": 5,
    "email": "admin@okas-demo.com",
    "full_name": "Demo Admin",
    "organization_id": 2,
    "org_name": "OKAS Demo Systems",
    "org_slug": "okas-demo",
    "role": { "id": 2, "name": "Admin" }
  },
  "permissions": ["members.view", "members.create", "members.edit", "members.delete"]
}
```

**Frontend handling:**
- `loginAuthService.js` calls `POST /we-okas/auth/login`.
- On success: `storeLogin(user, token, null, permissions)` → Zustand persists all 4 values.
- JWT stored in `localStorage` under key `okas_access_token`.

**Files:**
- Backend: [app/we_okas/routes/auth.py](../app/we_okas/routes/auth.py)
- Frontend service: [okasfrontend/src/features/auth/loginAuthService.js](../okasfrontend/src/features/auth/loginAuthService.js)
- Auth store: [okasfrontend/src/features/auth/authStore.js](../okasfrontend/src/features/auth/authStore.js)

---

### Story AUTH-2 — Get Current User (`/me`)

**Actor:** Any authenticated user  
**Endpoint:** `GET /we-okas/auth/me`  
**Auth:** Bearer JWT required

Re-validates the token and returns fresh user profile + permissions. Used to restore auth state after page reload.

---

## 3. Permission System

Permissions are stored as rows in `role_permissions(role_id, feature, action, is_allowed)`.

After login, the backend returns a **flat string array**:

```json
["members.view", "members.create", "members.edit", "members.delete"]
```

The frontend checks permissions via:
```js
permissions.includes('members.create')   // from Zustand authStore
```

### Permission Matrix

| Permission Key | Super Admin | SI Admin | Project Manager | Viewer |
|---|:---:|:---:|:---:|:---:|
| `organizations.manage` | ✓ | — | — | — |
| `members.view` | ✓ | ✓ | ✓ | ✓ |
| `members.create` | ✓ | ✓ | — | — |
| `members.edit` | ✓ | ✓ | ✓ | — |
| `members.delete` | ✓ | ✓ | — | — |
| `design_studio.access` | ✓ | ✓ | — | — |

---

## 4. Member Management Flow

### Story MEM-1 — View Members List

**Actor:** Any user with `members.view`  
**Page:** `/we-okas/users`  
**Endpoint:** `GET /we-okas/members`

**Key behaviour:**
- Members are **org-scoped** — users only see members belonging to their own organisation.
- `organization_id` is read from the **JWT token** (never from request body).
- Supports filters: `search` (name/email), `status` (active/inactive/all), `role` (name or ID).

**Backend query (simplified):**
```sql
SELECT app_users.*, roles.name AS role_name
FROM app_users
JOIN app_user_roles ON ...latest role per user...
LEFT JOIN roles ON roles.id = app_user_roles.role_id
WHERE app_users.organization_id = :org_id_from_jwt
  AND app_users.active_ind = TRUE
ORDER BY created_at DESC
```

**Files:**
- Backend: [app/we_okas/routes/members.py](../app/we_okas/routes/members.py) — `list_members()`
- Frontend page: [okasfrontend/src/features/we-okas/users/UsersPage.js](../okasfrontend/src/features/we-okas/users/UsersPage.js)

---

### Story MEM-2 — Create Member

**Actor:** User with `members.create`  
**Endpoint:** `POST /we-okas/members`

**Request:**
```json
{
  "full_name": "Ravi Sharma",
  "email": "ravi@example.com",
  "phone": "+91-9000000001",
  "role_id": 3,
  "status": "active"
}
```

**Important:** `organization_id` in the request body is **ignored**. The backend always assigns the new member to the **caller's organisation** (from JWT). This prevents privilege escalation.

**Validations:**
- Email uniqueness across all users.
- `role_id` must exist in `roles` table.
- `full_name` must not be empty.
- `status` must be `active` or `inactive`.

**UI gate:** "Add Member" button is only rendered when `permissions.includes('members.create')`.

---

### Story MEM-3 — Edit Member

**Actor:** User with `members.edit`  
**Endpoint:** `PUT /we-okas/members/{id}` (full replace) or `PATCH /we-okas/members/{id}` (partial)

**Org scope enforced:** `WHERE app_users.id = :id AND app_users.organization_id = :org_id_from_jwt`  
A member from another org returns `404`, not `403` — intentionally opaque.

**Role update:** Existing `app_user_roles` rows for the org are deleted and re-inserted with the new `role_id`.

**UI gate:** Edit menu item only rendered when `canEdit = permissions.includes('members.edit')`.

---

### Story MEM-4 — Deactivate Member

**Actor:** User with `members.delete`  
**Endpoint:** `DELETE /we-okas/members/{id}`

**Soft delete — does NOT remove any data:**
1. Sets `app_users.active_ind = FALSE`.
2. Deactivates all `project_members` rows for the user.
3. Deletes all `app_sessions` rows (immediate logout).
4. Writes an audit log entry.

**UI gate:**
- Delete menu item only rendered when `canDelete = permissions.includes('members.delete')`.
- If a user has neither edit nor delete, the entire `RowActions` kebab is hidden (`return null`).
- Confirmation modal shown before calling the API.

---

## 5. System Integrators (SI) Flow

> Only accessible to users with `organizations.manage` permission (Super Admin).

### Story SI-1 — View SI Organisations

**Actor:** Super Admin  
**Page:** `/we-okas/system-integrators`  
**Endpoint:** `GET /we-okas/organizations`

**Response shape per row:**
```json
{
  "id": 2,
  "name": "OKAS Demo Systems",
  "slug": "okas-demo",
  "email": "contact@okas-demo.com",
  "phone": "+91-9000000002",
  "status": "active",
  "member_count": 4,
  "created_at": "2026-06-05T12:19:32"
}
```

- `member_count` is a live subquery of active users in the org.
- Supports filters: `status` (active/inactive/all), `search` (name/email/phone).
- Stats bar shows: Total SIs, Active, Inactive, Total Members.

---

### Story SI-2 — Add SI Organisation

**Actor:** Super Admin  
**Endpoint:** `POST /we-okas/organizations`  
**UI:** "Add Organisation" button → opens `SIFormDrawer`

**Form sections:**
1. **Organisation Details** — Name (required), Email, Phone, Address.
2. **Admin Login** (optional toggle) — Full Name, Admin Email, Password.

**Payload with admin user:**
```json
{
  "name": "New Smart Systems",
  "email": "contact@newsi.com",
  "phone": "+91-9999999999",
  "admin_user": {
    "full_name": "Rajesh Kumar",
    "email": "rajesh@newsi.com",
    "password": "Admin@123"
  }
}
```

**Backend creates atomically (single transaction):**
1. Generates unique `slug` from name (e.g. `new-smart-systems`, `new-smart-systems-2` if taken).
2. Inserts `organizations` row.
3. If `admin_user` provided:
   - Checks email uniqueness → `409` if taken.
   - Inserts `app_users` row with bcrypt-hashed password.
   - Assigns "Admin" role via `app_user_roles`.

**Without admin user:** Org is created but has no login credentials. Admin login can be added later via Edit.

---

### Story SI-3 — Edit SI Organisation

**Actor:** Super Admin  
**Endpoint:** `PUT /we-okas/organizations/{id}`

- Updates org fields (name, email, phone, address, logo_url, status).
- If `admin_user` is included in payload: adds a new admin login (same creation flow as Story SI-2).
- Existing users in the org are unaffected unless org is set to `status: inactive`.

---

### Story SI-4 — Deactivate SI Organisation

**Actor:** Super Admin  
**Endpoint:** `DELETE /we-okas/organizations/{id}`

**Soft delete:**
1. Sets `organizations.active_ind = FALSE`.
2. Sets `active_ind = FALSE` on ALL users in the org (immediate loss of access).

**Reactivation:** Use Edit (`PUT`) to set `status: active`. Members must be individually reactivated.

**UI:** Confirmation modal warns: *"[Org name] and all its members will immediately lose platform access."*

---

## 6. Multi-tenancy (Org Scoping)

All member data is scoped to the caller's organisation. The `organization_id` is embedded in the JWT at login time and is **never trusted from the request body**.

```
JWT payload → organization_id
        ↓
Every member query adds:
  WHERE app_users.organization_id = :org_id
```

### Why this matters

| Scenario | Result |
|---|---|
| SI user tries to see another org's members | `WHERE org_id = caller's_org` → returns empty |
| SI user tries to create member in another org | Body's `organization_id` ignored; member created in caller's org |
| SI user tries to edit a member from another org | `404 Member not found` (not 403 — intentionally opaque) |

**Implementation:** [app/we_okas/routes/members.py](../app/we_okas/routes/members.py) — every endpoint reads `org_id = current_user["organization_id"]`.

---

## 7. Frontend Navigation Gate

The left sidebar filters nav items based on the user's permission array.

```js
// AppShell.js
const NAV_ITEMS = [
  { name: 'Home',               path: '/dashboard',                 Icon: Home       },
  { name: 'System Integrators', path: '/we-okas/system-integrators', Icon: Boxes,
    permission: 'organizations.manage' },            // ← hidden for SI users
  { name: 'Projects',           path: '/we-okas/projects',          Icon: FolderOpen },
  { name: 'Members',            path: '/we-okas/users',             Icon: Users      },
  { name: 'Roles & Permissions',path: '/we-okas/roles-permissions', Icon: UserCheck  },
  { name: 'Support',            path: '#',                          Icon: Headphones },
];

const visibleItems = NAV_ITEMS.filter(
  ({ permission }) => !permission || permissions.includes(permission)
);
```

**Result:**
- Super Admin → sees "System Integrators" menu item.
- Any SI user → does NOT see "System Integrators" menu item.

---

## 8. API Reference

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/we-okas/auth/login` | None | Email + password login |
| `GET` | `/we-okas/auth/me` | Bearer JWT | Get current user + permissions |
| `POST` | `/we-okas/auth/token` | None | Dev-only: token by email (no password) |

### Members

| Method | Path | Permission Required | Description |
|---|---|---|---|
| `GET` | `/we-okas/members` | `members.view` | List org-scoped members |
| `GET` | `/we-okas/members/{id}` | `members.view` | Get single member |
| `POST` | `/we-okas/members` | `members.create` | Create member in caller's org |
| `PUT` | `/we-okas/members/{id}` | `members.edit` | Full update |
| `PATCH` | `/we-okas/members/{id}` | `members.edit` | Partial update |
| `DELETE` | `/we-okas/members/{id}` | `members.delete` | Soft deactivate |

### System Integrators (Organisations)

| Method | Path | Permission Required | Description |
|---|---|---|---|
| `GET` | `/we-okas/organizations` | `organizations.manage` | List all orgs |
| `POST` | `/we-okas/organizations` | `organizations.manage` | Create org + optional admin user |
| `PUT` | `/we-okas/organizations/{id}` | `organizations.manage` | Update org + optional add admin |
| `DELETE` | `/we-okas/organizations/{id}` | `organizations.manage` | Soft deactivate org + all users |

### Common Response Envelope

```json
{
  "id": "<uuid>",
  "status": 200,
  "message": "...",
  "body": { ... }
}
```

Errors use the same envelope with `4xx` status codes, returned as `JSONResponse`.

---

## 9. Test Credentials

See [test_users.json](../test_users.json) for the full list.

| Email | Password | Role | Org | Can manage SIs? |
|---|---|---|---|:---:|
| `superadmin@mail.com` | `SuperAdmin@123` | Super Admin | OKAS Platform | Yes |
| `admin@okas-demo.com` | `Admin@123` | Admin | OKAS Demo Systems | No |
| `pm@okas-demo.com` | `PM@123` | Project Manager | OKAS Demo Systems | No |
| `viewer@okas-demo.com` | `Viewer@123` | Viewer | OKAS Demo Systems | No |

**To seed the database:**
```bash
cd d:\okasnewdev
venv\Scripts\python.exe scripts\seed_demo.py
```

---

## 10. Task Stories Index

| Story ID | Title | Status |
|---|---|---|
| AUTH-1 | Email + password login with JWT | Done |
| AUTH-2 | `/me` endpoint — refresh auth state | Done |
| PERM-1 | Flat permissions array in JWT + Zustand | Done |
| PERM-2 | Permission-gated UI buttons (Add/Edit/Delete) | Done |
| PERM-3 | Permission-gated nav (System Integrators hidden for SI users) | Done |
| MEM-1 | View members — org-scoped list | Done |
| MEM-2 | Create member — always in caller's org | Done |
| MEM-3 | Edit member — full + partial update | Done |
| MEM-4 | Soft-delete member — deactivate + revoke sessions | Done |
| SCOPE-1 | Multi-tenancy — `organization_id` from JWT on all queries | Done |
| SI-1 | List SI organisations with member count | Done |
| SI-2 | Add SI organisation + optional admin login (atomic) | Done |
| SI-3 | Edit SI organisation + add admin login | Done |
| SI-4 | Deactivate SI organisation + all its members | Done |
| SEED-1 | `scripts/seed_demo.py` — 4 roles, 2 orgs, 4 users | Done |

---

*Last updated: June 2026*

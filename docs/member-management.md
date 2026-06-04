# Member Management API — Documentation

**Platform:** WE.OKAS  
**Base URL:** `http://localhost:8000`  
**Version:** 1.0 | June 2026

---

## Table of Contents

1. [Overview](#overview)
2. [File Changes](#file-changes)
3. [Database Schema](#database-schema)
4. [Permission Model](#permission-model)
5. [API Endpoints](#api-endpoints)
   - [List Members](#1-list-members)
   - [Get Member by ID](#2-get-member-by-id)
   - [Create Member](#3-create-member)
   - [Full Update Member (PUT)](#4-full-update-member-put)
   - [Partial Update Member (PATCH)](#5-partial-update-member-patch)
   - [Delete Member (Soft)](#6-delete-member-soft)
6. [Soft-Delete Flow](#soft-delete-flow)
7. [has_design_studio_access Explained](#has_design_studio_access-explained)
8. [Error Reference](#error-reference)

---

## Overview

The Member Management module handles the full lifecycle of WE.OKAS platform users (SI staff, project managers, programmers). Members belong to an organisation, hold exactly one role, and can be assigned to one or more projects.

**Core rules:**
- Member deletion is **soft-only** — `active_ind` is set to `0`; data is retained for audit
- On delete: all project assignments are revoked and all active sessions are invalidated
- Every write operation is logged to `audit_logs` with the acting user's ID
- All endpoints require a **Bearer JWT token** with the corresponding `members` permission
- Unauthorized access returns `403 Forbidden` in the standard `{id, status, message, body}` envelope

---

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `app/we_okas/routes/members.py` | All 6 member CRUD endpoints with permission enforcement |

### Modified Files

| File | What Changed |
|------|-------------|
| `app/auth.py` | Added `require_permission(feature, action)` — a FastAPI dependency factory that validates the JWT **and** checks the caller's role permission in the DB before allowing the request through |
| `app/main.py` | Registered `we_okas_members_router` at `/we-okas/members` |

---

## Database Schema

### Tables Used

```
app_users          ← member records (soft-deleted via active_ind)
roles              ← named roles assigned to members
app_user_roles     ← maps each member to a role within an organisation
role_permissions   ← feature/action permission flags per role
project_members    ← project assignments (revoked on member delete)
app_sessions       ← active login sessions (purged on member delete)
audit_logs         ← immutable write log
app_users_ah       ← auto-populated by DB trigger on every INSERT/UPDATE/DELETE
```

### `app_users` (key columns)

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT UNSIGNED PK | auto-increment |
| `organization_id` | BIGINT UNSIGNED FK | required |
| `full_name` | VARCHAR(255) | required |
| `email` | VARCHAR(255) UNIQUE | required |
| `phone` | VARCHAR(50) | optional |
| `active_ind` | BOOLEAN | `1` = active, `0` = soft-deleted |
| `updated_by` | BIGINT UNSIGNED FK → app_users.id | set on every update |
| `created_at` | DATETIME(3) | server default |
| `updated_at` | DATETIME(3) | auto-updated on change |

### `project_members` (key columns)

| Column | Notes |
|--------|-------|
| `active_ind` | Set to `0` when the member is deleted |

### `app_sessions`

| Column | Notes |
|--------|-------|
| All rows for `user_id` | Hard-deleted on member soft-delete to revoke access immediately |

---

## Permission Model

Each endpoint is guarded by `Depends(require_permission(feature, action))`.

At request time, `require_permission` does two things in sequence:
1. Validates the Bearer JWT (via `get_current_user`)
2. Looks up `role_permissions` for the caller's role — checks `feature = 'members'` and the specific `action`

```
Incoming Request
      │
      ▼
  Validate JWT  ──fail──►  401 Unauthorized
      │ pass
      ▼
  Check role_permissions
  WHERE user_id = <me>
    AND feature = 'members'
    AND action  = <required>
    AND is_allowed = TRUE
      │
  not found / false ──►  403 Permission denied
      │ allowed
      ▼
  Route Handler
```

### Required Permission per Endpoint

| Endpoint | Required Permission |
|----------|-------------------|
| `GET /we-okas/members` | `members.view` |
| `GET /we-okas/members/{id}` | `members.view` |
| `POST /we-okas/members` | `members.create` |
| `PUT /we-okas/members/{id}` | `members.edit` |
| `PATCH /we-okas/members/{id}` | `members.edit` |
| `DELETE /we-okas/members/{id}` | `members.delete` |

### Seeded Role Permissions

| Role | view | create | edit | delete |
|------|------|--------|------|--------|
| **Admin** | ✓ | ✓ | ✓ | ✓ |
| **Project Manager** | ✓ | — | ✓ | — |
| **Viewer** | ✓ | — | — | — |

To get a token with a specific role, call `POST /we-okas/auth/token` with the matching email.

| Email | Role | Can do |
|-------|------|--------|
| `pankaj@vyom.ai` | Admin | All operations |
| `preeti.chauhan@okas.ai` | Project Manager | view + edit only |
| `rahul.kumar@okas.ai` | Viewer | view only |

---

## API Endpoints

### Response Envelope

All responses — success and error — use this shape:

```json
{
  "id":      "<uuid-v4>",
  "status":  200,
  "message": "...",
  "body":    { ... }
}
```

### Member Object (in `body`)

```json
{
  "id": 3,
  "full_name": "Pankaj Rana",
  "email": "pankaj@vyom.ai",
  "phone": null,
  "organization_id": 1,
  "status": "active",
  "has_design_studio_access": true,
  "role": {
    "id": 1,
    "name": "Admin"
  },
  "created_at": "2026-06-04T14:32:31.852000",
  "updated_at": "2026-06-04T14:32:31.852000"
}
```

---

### 1. List Members

Returns all members with optional search and filtering.

```
GET /we-okas/members
GET /we-okas/members?search=pankaj
GET /we-okas/members?role=Admin
GET /we-okas/members?status=inactive
Authorization: Bearer <token>        (requires members.view)
```

**Query Parameters**

| Param | Values | Default | Description |
|-------|--------|---------|-------------|
| `search` | any string | — | Filters `full_name` or `email` (LIKE) |
| `role` | role name or role ID | — | Filter by role |
| `status` | `active` \| `inactive` \| `all` | `active` | Show members by status |

**Response 200**
```json
{
  "id": "...",
  "status": 200,
  "message": "Members retrieved successfully",
  "body": [
    {
      "id": 3,
      "full_name": "Pankaj Rana",
      "email": "pankaj@vyom.ai",
      "phone": null,
      "organization_id": 1,
      "status": "active",
      "has_design_studio_access": true,
      "role": { "id": 1, "name": "Admin" },
      "created_at": "2026-06-04T14:32:31.852000",
      "updated_at": "2026-06-04T14:32:31.852000"
    }
  ]
}
```

---

### 2. Get Member by ID

```
GET /we-okas/members/{id}
Authorization: Bearer <token>        (requires members.view)
```

**Response 200** — single member object (same shape as list item)

**Response 404**
```json
{ "id": "...", "status": 404, "message": "Member not found", "body": null }
```

---

### 3. Create Member

```
POST /we-okas/members
Authorization: Bearer <token>        (requires members.create)
Content-Type: application/json
```

**Request Body**

```json
{
  "full_name": "Alex Johnson",
  "email": "alex.johnson@okas.ai",
  "phone": "+91-9876543210",
  "role_id": 2,
  "organization_id": 1,
  "status": "active",
  "has_design_studio_access": true
}
```

**Field Reference**

| Field | Required | Notes |
|-------|----------|-------|
| `full_name` | Yes | Non-empty string |
| `email` | Yes | Unique across platform |
| `phone` | No | — |
| `role_id` | Yes | Must reference an existing role |
| `organization_id` | Yes | Must reference an existing organisation |
| `status` | No | `"active"` (default) or `"inactive"` |
| `has_design_studio_access` | No | Informational only — actual access is derived from the assigned role |

**Response 201**
```json
{
  "id": "...",
  "status": 201,
  "message": "Member created successfully",
  "body": { ... }
}
```

**Response 409** — email already registered  
**Response 404** — role_id does not exist  
**Response 422** — Pydantic validation failure (missing required field, bad email, invalid status)

---

### 4. Full Update Member (PUT)

Replaces all member fields. All required fields of the create body must be provided.

```
PUT /we-okas/members/{id}
Authorization: Bearer <token>        (requires members.edit)
Content-Type: application/json
```

**Request Body** — same shape as Create

**Response 200** — returns updated member object  
**Response 404** — member not found or role not found  
**Response 409** — new email already taken by another member

---

### 5. Partial Update Member (PATCH)

Updates only the fields provided. Omitted fields retain their current values.

```
PATCH /we-okas/members/{id}
Authorization: Bearer <token>        (requires members.edit)
Content-Type: application/json
```

**Examples**

Update name only:
```json
{ "full_name": "Alexander Johnson" }
```

Update role only:
```json
{ "role_id": 1 }
```

Deactivate (without deleting):
```json
{ "status": "inactive" }
```

Update multiple fields:
```json
{
  "email": "alex.new@okas.ai",
  "role_id": 3,
  "status": "active"
}
```

**Response 200** — returns updated member object  
**Response 404** — member not found or new role_id not found  
**Response 409** — new email already registered to another member

---

### 6. Delete Member (Soft)

Deactivates the member. Data is **retained** for audit; the user loses all access immediately.

```
DELETE /we-okas/members/{id}
Authorization: Bearer <token>        (requires members.delete)
```

**Response 200**
```json
{
  "id": "...",
  "status": 200,
  "message": "Member deactivated successfully",
  "body": null
}
```

**Response 404** — member not found or already inactive

---

## Soft-Delete Flow

When `DELETE /we-okas/members/{id}` is called, three operations run **in the same transaction**:

```
1. app_users          → SET active_ind = 0          (deactivate account)
2. project_members    → SET active_ind = 0           (revoke project access)
3. app_sessions       → DELETE WHERE user_id = ?     (invalidate active sessions)
4. audit_logs         → INSERT (actor, action, email) (write audit trail)
```

The `app_users_ah` audit-history table is auto-populated by the database trigger on UPDATE, so a full snapshot of the user record before deactivation is also captured automatically.

A deactivated member:
- Cannot log in to WE.OKAS
- Cannot access Design Studio
- Does not appear in the default (`status=active`) member listing
- Can still be retrieved via `GET /we-okas/members?status=inactive` or by ID

---

## has_design_studio_access Explained

`has_design_studio_access` is a **computed** field. It is never stored on `app_users` — it is derived at query time from the member's assigned role permissions:

```sql
LEFT JOIN role_permissions rp_ds
       ON rp_ds.role_id = aur.role_id
      AND rp_ds.feature = 'design_studio'
      AND rp_ds.action  = 'access'
-- → COALESCE(rp_ds.is_allowed, FALSE) AS has_design_studio_access
```

| Role | has_design_studio_access |
|------|--------------------------|
| Admin | `true` |
| Project Manager | `true` |
| Viewer | `false` |

In `POST` and `PUT` request bodies, `has_design_studio_access` is **accepted but ignored** — the actual access is always determined by the role. To grant or revoke Design Studio access, change the member's role to one that has `design_studio.access = true`.

---

## Error Reference

| Status | Meaning | When |
|--------|---------|------|
| `401` | Unauthorized | Missing, expired, or invalid Bearer token |
| `403` | Forbidden | Token is valid but caller lacks the required `members.*` permission |
| `404` | Not Found | Member or Role ID does not exist; member already inactive on DELETE |
| `409` | Conflict | Email already registered to another member |
| `422` | Validation Error | Pydantic model failure (missing field, invalid email, bad status value) |

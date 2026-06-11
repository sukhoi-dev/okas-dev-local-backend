# Roles & Permissions API — Documentation

**Platform:** WE.OKAS  
**Base URL:** `http://localhost:8000`  
**Version:** 1.0 | June 2026

---

## Table of Contents

1. [Overview](#overview)
2. [File Changes](#file-changes)
3. [Database Schema](#database-schema)
4. [Authentication Flow](#authentication-flow)
5. [API Endpoints](#api-endpoints)
   - [Get Token](#1-get-token)
   - [List Roles](#2-list-roles)
   - [Get Role by ID](#3-get-role-by-id)
   - [Get Role Members](#4-get-role-members)
   - [Create Role](#5-create-role)
   - [Full Update Role (PUT)](#6-full-update-role-put)
   - [Partial Update Role (PATCH)](#7-partial-update-role-patch)
   - [Reassign Members](#8-reassign-members)
   - [Delete Role](#9-delete-role)
6. [Permissions Structure](#permissions-structure)
7. [Error Reference](#error-reference)
8. [Seed Users](#seed-users)

---

## Overview

The Roles & Permissions module lets platform administrators define custom access structures, assign them to users, and safely retire old roles via a reassignment workflow.

**Core rules:**
- Every role has a `permissions` object covering `projects`, `members`, and `design_studio`
- A role **cannot be deleted** while any member is still assigned to it — reassign first
- All mutating operations are logged to `audit_logs`
- Every response uses the envelope: `{ id, status, message, body }`
- All roles endpoints require a **Bearer JWT token**

---

## File Changes

### New Files

| File | Purpose |
|------|---------|
| `app/auth.py` | JWT utilities — `create_access_token()` and `get_current_user` FastAPI dependency |
| `app/we_okas/routes/auth.py` | `POST /we-okas/auth/token` — dev login endpoint that issues a JWT by email |
| `app/we_okas/routes/roles.py` | All 8 roles & permissions endpoints |

### Modified Files

| File | What Changed |
|------|-------------|
| `app/main.py` | Registered `auth` and `roles` routers; added unified `HTTPException` and `RequestValidationError` handlers so all errors return `{id, status, message, body}` |
| `requirements.txt` | Added `PyJWT==2.9.0` |
| `db/seed.sql` | Extended with 3 roles, 18 permission rows, 5 app users, 5 user-role assignments |
| `.env.example` | Added `JWT_SECRET` and `JWT_EXPIRY_HOURS` |

---

## Database Schema

### Tables Used

```
organizations        ← org context for user-role assignments
app_users            ← platform users who hold roles
roles                ← named role definitions
role_permissions     ← per-feature, per-action permission flags for each role
app_user_roles       ← many-to-many: user ↔ role ↔ org
audit_logs           ← immutable log of every create/update/delete action
```

### `roles`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT UNSIGNED PK | auto-increment |
| `name` | VARCHAR(50) UNIQUE | required, max 50 chars |
| `description` | TEXT | optional |
| `created_at` | DATETIME(3) | server default |

### `role_permissions`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT UNSIGNED PK | |
| `role_id` | BIGINT UNSIGNED FK | → `roles.id` |
| `feature` | VARCHAR(50) | `projects` / `members` / `design_studio` |
| `action` | VARCHAR(20) | feature-specific action name |
| `is_allowed` | BOOLEAN | |

### `app_user_roles`

| Column | Type | Notes |
|--------|------|-------|
| `id` | BIGINT UNSIGNED PK | |
| `user_id` | BIGINT UNSIGNED FK | → `app_users.id` |
| `role_id` | BIGINT UNSIGNED FK | → `roles.id` |
| `organization_id` | BIGINT UNSIGNED FK | → `organizations.id` |

---

## Authentication Flow

All roles endpoints are protected with **Bearer JWT authentication**.

```
Client                          Server
  │                               │
  │  POST /we-okas/auth/token     │
  │  { "email": "..." }           │
  │ ──────────────────────────►  │
  │                               │  lookup app_users by email
  │  { access_token, user }       │  create JWT (24h expiry)
  │ ◄────────────────────────── │
  │                               │
  │  GET /we-okas/roles           │
  │  Authorization: Bearer <tok>  │
  │ ──────────────────────────►  │
  │                               │  verify JWT signature + expiry
  │  { id, status, message, body }│
  │ ◄────────────────────────── │
```

### JWT Payload

```json
{
  "sub": "pankaj@vyom.ai",
  "user_id": 3,
  "full_name": "Pankaj Rana",
  "organization_id": 1,
  "iat": 1780563767,
  "exp": 1780650167
}
```

### Environment Variables

```env
JWT_SECRET=dev-secret-change-in-production
JWT_EXPIRY_HOURS=24
```

---

## API Endpoints

### Response Envelope

Every response — success and error — uses this shape:

```json
{
  "id": "<uuid-v4>",        // unique response trace ID
  "status": 200,            // HTTP status code
  "message": "...",         // human-readable outcome
  "body": { ... }           // payload (null on errors or empty deletes)
}
```

---

### 1. Get Token

**No auth required.** Dev/testing flow — accepts an email, returns a JWT if the user exists.

```
POST /we-okas/auth/token
Content-Type: application/json
```

**Request**
```json
{ "email": "pankaj@vyom.ai" }
```

**Response 200**
```json
{
  "id": "8c4fe609-...",
  "status": 200,
  "message": "Token issued successfully",
  "body": {
    "access_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 86400,
    "user": {
      "id": 3,
      "email": "pankaj@vyom.ai",
      "full_name": "Pankaj Rana",
      "role": "Admin",
      "organization_id": 1
    }
  }
}
```

**Response 404** — email not in `app_users` or `active_ind = 0`

---

### 2. List Roles

Returns all roles with their permissions and assigned member counts. Supports optional keyword search.

```
GET /we-okas/roles
GET /we-okas/roles?search=admin
Authorization: Bearer <token>
```

**Query Parameters**

| Param | Required | Description |
|-------|----------|-------------|
| `search` | No | Filters by `name` or `description` (case-insensitive LIKE) |

**Response 200**
```json
{
  "id": "69d87885-...",
  "status": 200,
  "message": "Roles retrieved successfully",
  "body": [
    {
      "id": 1,
      "name": "Admin",
      "description": "Full platform access",
      "created_at": "2026-06-04T14:32:31.852000",
      "member_count": 1,
      "permissions": {
        "projects": { "scope": "all_projects" },
        "members": { "create": true, "view": true, "edit": true, "delete": true },
        "design_studio": { "access": true }
      }
    }
  ]
}
```

---

### 3. Get Role by ID

```
GET /we-okas/roles/{id}
Authorization: Bearer <token>
```

**Response 200** — same shape as a single item from list roles

**Response 404**
```json
{
  "id": "...",
  "status": 404,
  "message": "Role not found",
  "body": null
}
```

---

### 4. Get Role Members

Lists all users currently assigned to a role. Used before the delete flow to show who needs reassignment.

```
GET /we-okas/roles/{id}/members
Authorization: Bearer <token>
```

**Response 200**
```json
{
  "id": "a7d2bbfd-...",
  "status": 200,
  "message": "Role members retrieved successfully",
  "body": [
    {
      "assignment_id": 1,
      "user_id": 3,
      "full_name": "Pankaj Rana",
      "email": "pankaj@vyom.ai",
      "avatar_url": null
    }
  ]
}
```

---

### 5. Create Role

```
POST /we-okas/roles
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**
```json
{
  "name": "Support Engineer",
  "description": "L1 support team",
  "permissions": {
    "projects": { "scope": "own_projects" },
    "members": {
      "create": false,
      "view": true,
      "edit": false,
      "delete": false
    },
    "design_studio": { "access": false }
  }
}
```

**Validation Rules**
- `name` — required, unique, max 50 characters
- `permissions` — at least one module must have a value that is not `none` / `false`
- `projects.scope` — must be `"all_projects"`, `"own_projects"`, or `"none"`

**Response 201**
```json
{
  "id": "89a18a7a-...",
  "status": 201,
  "message": "Role created successfully",
  "body": {
    "id": 4,
    "name": "Support Engineer",
    "description": "L1 support team",
    "created_at": "2026-06-04T14:33:15.572000",
    "member_count": 0,
    "permissions": { ... }
  }
}
```

**Response 409** — `name` already exists

---

### 6. Full Update Role (PUT)

Replaces the role's name, description, and **all** permissions. Any permission not specified is cleared.

```
PUT /we-okas/roles/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body** — same shape as Create (all fields required)
```json
{
  "name": "Support Lead",
  "description": "Updated description",
  "permissions": {
    "projects": { "scope": "all_projects" },
    "members": { "create": false, "view": true, "edit": true, "delete": false },
    "design_studio": { "access": true }
  }
}
```

**Response 200** — returns updated role  
**Response 404** — role not found  
**Response 409** — new name already taken by another role

---

### 7. Partial Update Role (PATCH)

Updates only the fields provided. Omitted fields keep their current values. If `permissions` is provided, it **replaces all** existing permissions for the role.

```
PATCH /we-okas/roles/{id}
Authorization: Bearer <token>
Content-Type: application/json
```

**Example — update description only**
```json
{ "description": "Updated description only" }
```

**Example — update name only**
```json
{ "name": "New Role Name" }
```

**Example — update permissions only**
```json
{
  "permissions": {
    "projects": { "scope": "none" },
    "members": { "create": false, "view": true, "edit": false, "delete": false },
    "design_studio": { "access": true }
  }
}
```

**Response 200** — returns updated role  
**Response 404** — role not found  
**Response 409** — new name already taken

---

### 8. Reassign Members

Bulk-moves members from one role to another. Required before a role with members can be deleted.

```
POST /we-okas/roles/{id}/reassign
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body**
```json
{
  "new_role_id": 2,
  "member_ids": [3, 4]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `new_role_id` | Yes | Target role — must exist and differ from source |
| `member_ids` | No | Specific user IDs to move. Omit or `null` to move **all** members |

**Response 200**
```json
{
  "id": "459265fd-...",
  "status": 200,
  "message": "1 member(s) reassigned successfully",
  "body": { "affected_count": 1 }
}
```

**Response 400** — `new_role_id` is the same as the source role  
**Response 404** — source or target role not found

---

### 9. Delete Role

Permanently deletes a role and its permissions. **Blocked if any member is still assigned.**

```
DELETE /we-okas/roles/{id}
Authorization: Bearer <token>
```

**Response 200** — role deleted
```json
{
  "id": "e17a36c3-...",
  "status": 200,
  "message": "Role deleted successfully",
  "body": null
}
```

**Response 409** — role still has assigned members
```json
{
  "id": "a99fc82d-...",
  "status": 409,
  "message": "Role has 1 assigned member(s). Reassign them before deleting.",
  "body": null
}
```

#### Safe Delete Flow

```
1. GET  /we-okas/roles/{id}/members     → see who is assigned
2. POST /we-okas/roles/{id}/reassign    → move them to a new role
3. DELETE /we-okas/roles/{id}           → now succeeds
```

---

## Permissions Structure

### `projects`

| Value | Meaning |
|-------|---------|
| `"all_projects"` | User can access every project in the organisation |
| `"own_projects"` | User can only access projects they are assigned to |
| `"none"` | No project access |

### `members`

| Action | Meaning |
|--------|---------|
| `create` | Can invite / add new members |
| `view` | Can see member list and profiles |
| `edit` | Can change member details and assignments |
| `delete` | Can remove members |

### `design_studio`

| Action | Meaning |
|--------|---------|
| `access` | Can open and use the Design Studio module |

### Seeded Role Profiles

| Role | projects.scope | members | design_studio |
|------|---------------|---------|---------------|
| **Admin** | `all_projects` | all true | `true` |
| **Project Manager** | `own_projects` | view + edit only | `true` |
| **Viewer** | `own_projects` | view only | `false` |

---

## Error Reference

| Status | Meaning | When |
|--------|---------|------|
| `400` | Bad Request | e.g. `new_role_id` equals source role in reassign |
| `401` | Unauthorized | Missing, expired, or invalid Bearer token |
| `404` | Not Found | Role or user does not exist |
| `409` | Conflict | Duplicate role name; or delete attempted while members are assigned |
| `422` | Validation Error | Pydantic model validation failed (missing field, bad value) |

---

## Seed Users

These users are pre-loaded by `db/seed.sql` and can be used with `POST /we-okas/auth/token`:

| Email | Full Name | Role |
|-------|-----------|------|
| `pankaj@vyom.ai` | Pankaj Rana | **Admin** |
| `preeti.chauhan@okas.ai` | Preeti Chauhan | **Project Manager** |
| `sarah.jones@okas.ai` | Sarah Jones | **Project Manager** |
| `rahul.kumar@okas.ai` | Rahul Kumar | **Viewer** |
| `mike.dev@okas.ai` | Mike Dev | **Viewer** |

### Re-seed (if tables were cleared)

```bash
# Windows
Get-Content db\seed.sql | & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -h 127.0.0.1 -P 3306 -u root -pokas okas_signature

# Linux / Mac
mysql -h 127.0.0.1 -P 3306 -u root -pokas okas_signature < db/seed.sql
```

### Start the Server

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Interactive API Docs

Swagger UI available at: `http://localhost:8000/docs`

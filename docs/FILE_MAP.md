# OKAS — File Map
## Members · Roles · Permissions

---

## BACKEND

### Core

| File | Purpose |
|---|---|
| `app/main.py` | FastAPI app entry point — registers all routers |
| `app/auth.py` | JWT creation, JWT decode, bcrypt hash/verify, `require_permission` dependency |
| `app/db.py` | DB connection — `get_db()` (raw PyMySQL) and `get_orm_session()` (SQLAlchemy) |

### Routes

| File | Prefix | Covers |
|---|---|---|
| `app/we_okas/routes/auth.py` | `/we-okas/auth` | Login, /me, /permissions |
| `app/we_okas/routes/members.py` | `/we-okas/members` | Member CRUD, org-scoped |
| `app/we_okas/routes/roles.py` | `/we-okas/roles` | Role CRUD, permissions, reassign |
| `app/we_okas/routes/organizations.py` | `/we-okas/organizations` | SI org CRUD (Super Admin only) |
| `app/we_okas/routes/projects.py` | `/we-okas/projects` | Project listing |

### Models

| File | Models defined |
|---|---|
| `app/models/auth.py` | `Organization`, `AppUser`, `Role`, `RolePermission`, `AppUserRole`, `AppSession` |
| `app/models/audit.py` | `AuditLog` |
| `app/models/access.py` | Access / homeowner models |

### Migrations

| File | What it adds |
|---|---|
| `alembic/versions/0001_initial_schema.py` | All base tables |
| `alembic/versions/0002_triggers_and_views.py` | DB triggers and views |
| `alembic/versions/0003_add_password_hash.py` | `password_hash` column on `app_users` |

### Seed

| File | Purpose |
|---|---|
| `scripts/seed_demo.py` | Creates 2 orgs, 4 roles, 4 users with passwords |

---

## FRONTEND

### Auth

| File | Purpose |
|---|---|
| `src/features/auth/LoginPage.js` | Login form — calls `loginWithPassword`, stores token + permissions |
| `src/features/auth/OtpPage.js` | OTP flow — calls `verifyOtp`, stores token + permissions |
| `src/features/auth/ForgotPasswordPage.js` | Forgot password UI |
| `src/features/auth/loginAuthService.js` | `loginWithPassword()`, `verifyOtp()`, `fetchPermissions()` — all auth API calls |
| `src/features/auth/authStore.js` | Zustand store — holds `user`, `accessToken`, `permissions` (flat), `permissionsGrouped` |
| `src/features/auth/authService.js` | Legacy auth helpers |
| `src/features/auth/useAuth.js` | Auth hook |

### Members

| File | Purpose |
|---|---|
| `src/features/we-okas/users/UsersPage.js` | Members list page — reads `canCreate`, `canEdit`, `canDelete` from Zustand |
| `src/features/we-okas/users/MemberFormDrawer.js` | Add / Edit member slide-in drawer — includes password field on create |
| `src/features/we-okas/users/useMembers.js` | React Query hooks — `useMembers`, `useCreateMember`, `useUpdateMember`, `useDeleteMember` |
| `src/features/we-okas/users/memberService.js` | API calls to `/we-okas/members` endpoints |

### Roles & Permissions

| File | Purpose |
|---|---|
| `src/features/we-okas/roles-permissions/RolesPage.js` | Roles list + create/edit/delete UI |
| `src/features/we-okas/roles-permissions/rolesService.js` | API calls to `/we-okas/roles` endpoints |

### System Integrators (SI Organisations)

| File | Purpose |
|---|---|
| `src/features/we-okas/system-integrators/SystemIntegratorsPage.js` | SI list — stats, table, search, filter, deactivate |
| `src/features/we-okas/system-integrators/SIFormDrawer.js` | Add / Edit SI org drawer — with optional admin user creation |
| `src/features/we-okas/system-integrators/useSIs.js` | React Query hooks — `useSIs`, `useCreateSI`, `useUpdateSI`, `useDeleteSI` |
| `src/features/we-okas/system-integrators/siService.js` | API calls to `/we-okas/organizations` endpoints |

### Layout & Navigation

| File | Purpose |
|---|---|
| `src/features/we-okas/_layout/AppShell.js` | Top nav + left sidebar — `LeftNav` filters nav items by `permissions` from Zustand |
| `src/routes/index.js` | React Router — all page routes including protected routes |

---

## How the files connect

```
LOGIN FLOW
LoginPage.js
  → loginAuthService.js  →  POST /we-okas/auth/login      (auth.py)
  → loginAuthService.js  →  GET  /we-okas/auth/permissions (auth.py)
  → authStore.js         stores: user, token, permissions (flat + grouped)

MEMBERS FLOW
UsersPage.js
  → useMembers.js  →  memberService.js  →  GET /we-okas/members    (members.py)
MemberFormDrawer.js
  → useCreateMember  →  memberService.js  →  POST /we-okas/members  (members.py)
  → useUpdateMember  →  memberService.js  →  PUT  /we-okas/members/{id}

ROLES FLOW
RolesPage.js
  → rolesService.js  →  GET  /we-okas/roles        (roles.py)
  → rolesService.js  →  POST /we-okas/roles         (roles.py)
  → rolesService.js  →  PUT  /we-okas/roles/{id}    (roles.py)
  → rolesService.js  →  DELETE /we-okas/roles/{id}  (roles.py)

SI ORGANISATIONS FLOW  (Super Admin only)
SystemIntegratorsPage.js
  → useSIs.js  →  siService.js  →  GET    /we-okas/organizations      (organizations.py)
SIFormDrawer.js
  → useCreateSI  →  siService.js  →  POST   /we-okas/organizations    (organizations.py)
  → useUpdateSI  →  siService.js  →  PUT    /we-okas/organizations/{id}
  → useDeleteSI  →  siService.js  →  DELETE /we-okas/organizations/{id}

PERMISSION GATING
authStore.js  →  permissions[]
  → AppShell.js      — hides "System Integrators" nav if no organizations.manage
  → UsersPage.js     — hides Add/Edit/Delete buttons per members.* permissions
  → SIFormDrawer.js  — only reachable if organizations.manage present
```

---

## DB Tables touched by these files

| Table | Used by |
|---|---|
| `organizations` | organizations.py, auth.py |
| `app_users` | members.py, auth.py, organizations.py |
| `roles` | roles.py, auth.py |
| `role_permissions` | roles.py, auth.py (`/permissions` endpoint) |
| `app_user_roles` | members.py, roles.py, auth.py |
| `app_sessions` | members.py (invalidated on member delete) |
| `audit_log` | members.py, roles.py, organizations.py |

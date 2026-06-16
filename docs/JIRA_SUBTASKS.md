 # OKAS — Jira Subtasks Reference
**Assigned Tasks: OKAI-272 to OKAI-305**
> Status legend: ✅ Done · 🔄 Partial · ⬜ Pending

---

## EPIC: Roles & Permissions

---

### OKAI-272 · Create API for Role creation after grouping permission ✅

**API:** `POST /we-okas/roles`

**Subtasks:**
- Define permission groups: Projects (scope), Members (CRUD), Design Studio (access)
- Build `RoleCreate` request schema with grouped `PermissionsBody`
- Validate role name: required, unique, max 50 chars
- Validate at least one permission is enabled
- Insert `roles` row, get auto ID
- Insert `role_permissions` rows per module
- Write audit log entry (`role_created`)
- Return created role with `member_count` and full permissions

---

### OKAI-273 · Implement UI selection checkboxes for permissions ✅

**Page:** `/we-okas/roles-permissions`

**Subtasks:**
- Render permission modules as grouped sections (Projects / Members / Design Studio)
- Projects — radio/select: All Projects · Own Projects · None
- Members — 4 checkboxes: View, Create, Edit, Delete
- Design Studio — single toggle: Access
- Disable dependent permissions (e.g. Edit disabled if View is off)
- Reflect checked state from API response when editing

---

### OKAI-274 · Implement UI forms for Roles creation ✅

**Component:** `RoleFormDrawer` or inline form on Roles page

**Subtasks:**
- Name field (required, max 50 chars, inline error)
- Description field (optional, textarea)
- Embed permission checkboxes from OKAI-273
- Validate at least one permission selected before submit
- Call `POST /we-okas/roles` on save
- Show success toast, refresh roles list
- Show `409` error if role name already exists

---

### OKAI-275 · Create Edit Roles API ✅

**APIs:** `PUT /we-okas/roles/{id}` · `PATCH /we-okas/roles/{id}`

**Subtasks:**
- `PUT` — full replace: update name + description + delete all old permissions + insert new ones
- `PATCH` — partial update: only update fields that are sent
- Validate role exists → `404` if not
- Validate name uniqueness (skip check if name unchanged)
- Delete existing `role_permissions` rows before re-inserting
- Write audit log (`role_updated` / `role_patched`)
- Return updated role with fresh permissions

---

### OKAI-276 · Create API for listing already selected permissions per Role ✅

**API:** `GET /we-okas/roles/{id}`

**Subtasks:**
- Fetch single role row by ID → `404` if not found
- Fetch all `role_permissions` rows for that role
- Count members assigned to role via `app_user_roles`
- Build structured response: `{ projects: {scope}, members: {create,view,edit,delete}, design_studio: {access} }`
- Return role detail with `member_count` and full permissions object

---

### OKAI-277 · Implement UI using these created APIs ✅

**Page:** Roles & Permissions page

**Subtasks:**
- On page load call `GET /we-okas/roles` → render roles list
- On row click / Edit button call `GET /we-okas/roles/{id}` → pre-fill form
- Pre-populate checkboxes from API permissions response
- On save call `PUT /we-okas/roles/{id}`
- Invalidate React Query cache after save to refresh list
- Show loading skeleton during fetch

---

### OKAI-278 · Create Roles reassign to Members API ✅

**API:** `POST /we-okas/roles/{id}/reassign`

**Subtasks:**
- Accept `{ new_role_id, member_ids? }` body
- Validate source role exists
- Validate target role exists and is not the same role
- If `member_ids` provided → reassign only those members; else reassign all
- Bulk update `app_user_roles.role_id` to `new_role_id`
- Write audit log with `affected_count`
- Return `{ affected_count: N }`

---

### OKAI-279 · Create API that checks whether Members assigned to a particular Role ✅

**API:** `GET /we-okas/roles/{id}/members`

**Subtasks:**
- Validate role exists → `404` if not
- Query `app_user_roles` joined with `app_users` for that `role_id`
- Return list: `{ assignment_id, user_id, full_name, email }`
- Used as pre-delete check — if list is non-empty, block delete and show reassign prompt

---

### OKAI-280 · Create Delete Roles API ✅

**API:** `DELETE /we-okas/roles/{id}`

**Subtasks:**
- Validate role exists → `404` if not
- Count members on this role via `app_user_roles`
- If `count > 0` → block with `409`: "Role has N member(s). Reassign them before deleting."
- Delete all `role_permissions` rows first (FK constraint)
- Delete `roles` row
- Write audit log (`role_deleted`)
- Return success `200`

---

### OKAI-281 · Implement UI form where Roles are assigned to Members ✅

**Component:** `MemberFormDrawer` (Role dropdown)

**Subtasks:**
- Fetch roles list via `GET /we-okas/roles` for dropdown options
- Show role name + description in dropdown
- On member create/edit — send `role_id` in payload
- If role has no members label, show "No members yet" indicator
- On delete role — show member count warning + redirect to Reassign flow

---

### OKAI-282 · Implement rest APIs on UI as per correct flow ✅

**Subtasks:**
- Wire Roles page list to `GET /we-okas/roles`
- Wire Add Role button to `POST /we-okas/roles`
- Wire Edit to `PUT /we-okas/roles/{id}`
- Wire Delete to `DELETE /we-okas/roles/{id}` (with members guard)
- Wire Reassign modal to `POST /we-okas/roles/{id}/reassign`
- Handle all error states: `404`, `409`, `422` with toast messages

---
---

## EPIC: Member Management

---

### OKAI-284 · Create API for filtration on the basis of mentioned details ✅

**API:** `GET /we-okas/members?status=active&role=3`

**Subtasks:**
- Add `status` query param: `active` (default) · `inactive` · `all`
- Add `role` query param: accepts role ID (numeric) or role name (string)
- Apply filters to SQLAlchemy query before execution
- Return filtered, org-scoped member list

---

### OKAI-285 · Create API to conduct search by Keywords on DB entry ✅

**API:** `GET /we-okas/members?search=ravi`

**Subtasks:**
- Add `search` query param
- Apply `ILIKE %keyword%` on `full_name` and `email` columns
- Search is combined with status/role filters (all applied together)
- Return matching members within caller's org only

---

### OKAI-286 · Implement Filter API on UI — fetching filtration params ✅

**Component:** Members page filter controls

**Subtasks:**
- Status dropdown: Active / Inactive / All — passed as `?status=`
- Role dropdown: populated from `GET /we-okas/roles` — passed as `?role=`
- On filter change → re-fetch members with updated params via React Query
- Show active filter indicators
- Clear filters button resets to defaults

---

### OKAI-287 · Implement Searching in UI and pass keywords to API ✅

**Component:** Members page search bar

**Subtasks:**
- Search input field with debounce (300ms)
- On input → append `?search=keyword` to `GET /we-okas/members` call
- Empty search removes the param (returns full list)
- Combined with status/role filters simultaneously
- Show "No members match your search" empty state

---

### OKAI-288 · Create API for Member creation ✅

**API:** `POST /we-okas/members`

**Subtasks:**
- Accept: `full_name`, `email`, `phone`, `role_id`, `status`, `password` (optional)
- Require `members.create` permission via JWT check
- Read `organization_id` from JWT — never trust request body
- Validate email uniqueness → `409` if duplicate
- Validate `role_id` exists → `404` if not
- If `password` provided → bcrypt hash and store in `password_hash`
- If no password → member created but cannot log in yet
- Insert `app_users` + `app_user_roles` rows
- Write audit log (`member_created`)
- Return created member with role

---

### OKAI-289 · Implement API on UI ✅

**Component:** `MemberFormDrawer` — Add Member flow

**Subtasks:**
- "Add Member" button gated by `members.create` permission
- Drawer: Full Name*, Email*, Phone, Role*, Status
- Section 02 (create only): Password field with show/hide toggle
- On submit → call `POST /we-okas/members`
- Show `409` toast if email already registered
- On success → close drawer, refresh member list

---

### OKAI-290 · Create API Route for Edit Member ✅

**APIs:** `PUT /we-okas/members/{id}` · `PATCH /we-okas/members/{id}`

**Subtasks:**
- Require `members.edit` permission
- Scope lookup: `WHERE id = :id AND organization_id = :org_from_jwt` → `404` if not found
- `PUT` — full replace: update all fields
- `PATCH` — partial: only update provided fields
- Email uniqueness check (skip if unchanged)
- Replace role assignment: delete old `app_user_roles` row, insert new
- Write audit log

---

### OKAI-291 · Identify editable and non-editable fields ✅

**Subtasks:**
- **Editable:** `full_name`, `phone`, `role_id`, `status` (`active`/`inactive`)
- **Non-editable after create:** `email` (changes allowed but uniqueness enforced), `organization_id` (always from JWT), `password_hash` (separate change-password flow needed)
- Apply this in API: `organization_id` always taken from JWT, never from body
- Apply in UI: Email field shown but locked/read-only on edit drawer

---

### OKAI-292 · Implement APIs on UI — editable and non-editable fields ✅

**Component:** `MemberFormDrawer` — Edit flow

**Subtasks:**
- Pre-fill all fields from selected member row
- Email shown but flagged (changes allowed with uniqueness warning)
- Password section hidden on edit (not editable here)
- Role dropdown shows current role pre-selected
- Status dropdown shows current status pre-selected
- On save → call `PUT /we-okas/members/{id}`
- Show success/error toast
- Refresh member list on success

---
---

## EPIC: Projects

---

### OKAI-299 · Create API for fetching project data and list as projects ⬜

**API:** `GET /we-okas/projects`

**Subtasks:**
- List all projects accessible to the logged-in user
- Apply org scope: filter by `organization_id` from JWT
- Add `status` filter: active / inactive / all
- Add `search` param: project name or description
- Return: `id`, `name`, `description`, `status`, `member_count`, `created_at`

---

### OKAI-300 · Create API for project listing based on logged-in email ⬜

**API:** `GET /we-okas/projects?scope=mine`

**Subtasks:**
- Filter projects where the logged-in user is a `project_member`
- Use `user_id` from JWT to query `project_members` table
- Differentiate: `scope=mine` (user's own projects) vs no scope (all org projects)
- Required for Project Manager role who only sees own projects

---

### OKAI-302 · UI implementation of implemented APIs 🔄

**Page:** Projects page

**Subtasks:**
- Wire page to `GET /we-okas/projects` via React Query
- Search bar → `?search=keyword`
- Status filter → `?status=active|inactive|all`
- Scope toggle → `?scope=mine` for Project Manager role
- Render project cards/table with name, member count, status badge
- Loading skeleton while fetching
- Empty state when no projects found

---

### OKAI-305 · Implement API that fetches Roles and Permissions for logged-in user ✅

**API:** `GET /we-okas/auth/permissions`

**Subtasks:**
- Require Bearer JWT (validated via `get_current_user`)
- Decode JWT → get `user_id`
- Query `app_user_roles → role_permissions` for all allowed permissions
- Build two formats:
  - `flat`: `["members.view", "members.create", ...]` — for `includes()` checks
  - `grouped`: `{ members: ["view","create"], projects: ["view"] }` — for feature-level checks
- Return `{ user_id, role: {id, name}, permissions: { flat, grouped } }`
- Frontend calls this immediately after login and stores both in Zustand
- UI permission gates (`canCreate`, `canEdit`, `canDelete`, nav items) read from Zustand `permissions` array

---

### OKAI-307 · Create condition for seamless access for Admin Role ✅

**Scope:** Backend — Admin role gets correct permissions automatically when an SI org is created with an admin user

**Subtasks:**
- Define what "Admin" access means: full `members.*` permissions (view, create, edit, delete) + `design_studio.access`
- Seed `roles` table with "Admin" role if not exists (via `scripts/seed_demo.py`)
- When creating an SI org via `POST /we-okas/organizations` with `admin_user` → auto-assign "Admin" role to the created user
- When creating a member via `POST /we-okas/members` with `role_id` pointing to Admin → they inherit all Admin permissions
- Ensure `role_permissions` table has correct rows for Admin role (`members.view`, `members.create`, `members.edit`, `members.delete`, `design_studio.access` all `is_allowed = TRUE`)
- Admin role does NOT get `organizations.manage` — that is Super Admin only
- Verify: Admin user logs in → `GET /we-okas/auth/permissions` returns full member permissions
- Verify: Admin user can add/edit/delete members within their own org only (org scope enforced via JWT)

---

### OKAI-308 · Implement UI as per cross model API integration (Auth and Roles) ✅

**Scope:** Frontend — Auth system and Roles/Permissions system work together seamlessly in the UI

**Subtasks:**

**Step 1 — Login → Permissions chain:**
- `POST /we-okas/auth/login` → JWT + user profile stored in Zustand
- Immediately call `GET /we-okas/auth/permissions` with the JWT
- Store `permissions.flat` and `permissions.grouped` in Zustand (`authStore`)
- Both values persisted in `localStorage` — survive page refresh

**Step 2 — Navigation gating (cross: Auth + Roles):**
- `LeftNav` reads `permissions` from Zustand
- Nav items with `permission` guard filtered via: `permissions.includes(permission)`
- Super Admin (has `organizations.manage`) → sees System Integrators menu
- SI/Admin/PM/Viewer → System Integrators menu hidden

**Step 3 — Members page gating (cross: Auth + Roles):**
- Read `canCreate`, `canEdit`, `canDelete` from Zustand flat permissions
- "Add Member" button: rendered only if `members.create` in permissions
- Edit row action: shown only if `members.edit` in permissions
- Delete row action: shown only if `members.delete` in permissions
- Entire row kebab: hidden if neither `members.edit` nor `members.delete`

**Step 4 — Roles page integration:**
- Roles page loads via `GET /we-okas/roles`
- Each role shows its permission set fetched from `GET /we-okas/roles/{id}`
- Edit role form pre-fills checkboxes from role's current permissions
- On save → `PUT /we-okas/roles/{id}` → clears and replaces permissions in DB
- Permission change takes effect for all users on that role on their next `/permissions` call

**Step 5 — Cross-model consistency:**
- JWT does NOT contain permissions — only `user_id`, `organization_id`, `full_name`
- Permissions always fetched fresh from DB via `/we-okas/auth/permissions`
- If an admin changes a role's permissions → affected users see new permissions on next page load
- `hasPermission(key)` helper in Zustand for single-key checks
- `hasFeature(feature)` helper for checking any permission under a module

---

## Status Summary

| Task | Title | Status |
|---|---|---|
| OKAI-272 | Create API for Role creation | ✅ Done |
| OKAI-273 | UI permission checkboxes | ✅ Done |
| OKAI-274 | UI form for Role creation | ✅ Done |
| OKAI-275 | Edit Roles API | ✅ Done |
| OKAI-276 | API listing permissions per Role | ✅ Done |
| OKAI-277 | Implement UI with created APIs | ✅ Done |
| OKAI-278 | Roles reassign to Members API | ✅ Done |
| OKAI-279 | API check Members on a Role | ✅ Done |
| OKAI-280 | Delete Role API | ✅ Done |
| OKAI-281 | UI form — Roles assigned to Members | ✅ Done |
| OKAI-282 | Implement rest APIs on UI | ✅ Done |
| OKAI-284 | Filter API for Members | ✅ Done |
| OKAI-285 | Search API by Keyword | ✅ Done |
| OKAI-286 | Filter UI implementation | ✅ Done |
| OKAI-287 | Search UI implementation | ✅ Done |
| OKAI-288 | Member creation API | ✅ Done |
| OKAI-289 | Member creation UI | ✅ Done |
| OKAI-290 | Edit Member API | ✅ Done |
| OKAI-291 | Editable vs non-editable fields | ✅ Done |
| OKAI-292 | Edit Member UI | ✅ Done |
| OKAI-299 | Fetch Projects list API | ⬜ Pending |
| OKAI-300 | Project listing by logged-in user | ⬜ Pending |
| OKAI-302 | Projects UI implementation | 🔄 Partial |
| OKAI-305 | Fetch Roles & Permissions API | ✅ Done |
| OKAI-307 | Condition for seamless Admin Role access | ✅ Done |
| OKAI-308 | UI cross-model integration (Auth + Roles) | ✅ Done |

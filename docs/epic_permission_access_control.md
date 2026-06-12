# EPIC — Permission-Based Access Control
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic governs how the platform enforces access control across all modules based on each user's assigned role and permissions. It ensures users can only access modules, projects, and actions that their role explicitly authorizes. Permission enforcement spans WE.OKAS, Design Studio, Mobile-connected workflows, and project-switching flows.

---

## STORY 1 — Restrict Platform Access based on User Permissions

### User Story
> As a **User**,
> I want to **have my platform access restricted according to my assigned permissions**,
> So that **I can access only the modules, projects, and actions authorized for my role**.

### Acceptance Criteria
218. Successfully authenticated users can access only modules permitted by their assigned role
219. Restricted modules remain:
     - Hidden from navigation
     - Disabled with restricted-access indication
220. Users without Design Studio permissions cannot access Design Studio functionality
221. Users without project permissions cannot access unauthorized projects
222. Project visibility respects configured permissions such as:
     - All Projects
     - Own Projects
223. Restricted actions such as:
     - Create
     - View
     - Edit
     - Delete
     are enforced consistently across modules
224. Unauthorized direct URL or route access attempts are restricted safely
225. Restricted-access attempts display meaningful permission-related feedback
226. Permission updates reflect immediately or after session refresh according to system rules
227. Existing authenticated sessions remain secure during permission changes
228. Navigation hierarchy updates dynamically based on effective user permissions
229. Users cannot perform restricted operations through indirect workflows or APIs
230. Permission enforcement remains consistent across:
     - WE.OKAS
     - Design Studio
     - Mobile-connected workflows
     - Project switching flows
231. Restricted modules and actions do not expose sensitive project or member information
232. Permission validation activities and unauthorized access attempts are logged successfully for audit and troubleshooting purposes
233. System remains stable during simultaneous permission validation and role-update operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/session` | Validate session and return effective user permissions |
| GET | `/we-okas/me/permissions` | Fetch the current user's resolved permissions |
| GET | `/we-okas/projects` | Returns only projects the user is authorized to see |

### Business Rules
- All API endpoints must validate the authenticated user's permissions on every request — no client-side-only enforcement
- Restricted modules are **hidden from navigation** entirely, not just visually disabled
- Direct URL access to a restricted module or resource must return `403 Forbidden` with a meaningful message
- Permission changes (e.g. role update) must take effect on the next session refresh or immediately per system configuration
- The system must not leak any data about restricted projects or members, even in error responses
- Permission enforcement must be consistent whether access is attempted via WE.OKAS UI, Design Studio, mobile-connected flows, or direct API calls

### Enforcement Layers
| Layer | Enforcement |
|-------|-------------|
| Navigation | Hidden items for unauthorized modules |
| UI Actions | Buttons/actions hidden or disabled based on permissions |
| API | `403 Forbidden` returned for all unauthorized requests |
| Data | Queries scoped to only authorized projects/members |

---

## Technical Notes

### DB Tables Involved
- `roles`
- `role_permissions`
- `app_user_roles`
- `app_users`
- `projects`
- `project_members`
- `app_sessions`
- `audit_logs`

### Permission Matrix

| Module | Permission Options |
|--------|--------------------|
| Projects | All Projects / Own Projects / None |
| Members | Create / View / Edit / Delete |
| Design Studio | Access / No Access |
| Roles & Permissions | View / Manage |

### Validation Rules
- Every protected API route must validate the JWT/session token AND the role permissions before processing
- `403 Forbidden` must be returned — never `404` — for resources the user is authenticated but not authorized to access
- Session tokens must be re-validated on each request; expired or invalidated tokens must redirect to login
- Permission checks must happen server-side — frontend visibility rules are supplementary only

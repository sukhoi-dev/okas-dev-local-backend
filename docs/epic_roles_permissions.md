# EPIC — Roles & Permissions Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers the full lifecycle of roles and permissions within WE.OKAS. Roles are custom-defined access structures that group module-level permissions. Each member is assigned a role, and that role determines what they can see and do across the platform. Roles cannot be deleted if members are still assigned — a reassignment workflow is enforced first.

---

## STORY 1 — View Roles and Permissions Listing

### User Story
> As a **User**,
> I want to **view available roles and permissions**,
> So that **I can understand access control and responsibility assignments**.

### Acceptance Criteria
175. Users can access Roles and Permissions module successfully
176. Role listing displays:
     - Role Name
     - Description
     - Permissions
     - Assigned Member Count
177. Permission information remains visually structured and readable
178. Assigned member counts update dynamically after member-role changes
179. Search and filtering functionality remain responsive and accurate
180. Unauthorized role visibility or modification is restricted safely
181. Empty states display meaningful guidance when no roles exist
182. Updated role information reflects correctly after modifications
183. Role listing remains responsive during large dataset loading
184. System remains stable during repeated role listing operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/roles` | List all roles in the organization |
| GET | `/we-okas/roles/{id}` | Get role details with permissions |
| GET | `/we-okas/roles?search=` | Search and filter roles |

---

## STORY 2 — Create New Role with Permissions

### User Story
> As a **User**,
> I want to **create custom roles with permissions**,
> So that **access control can be managed according to project responsibilities**.

### Acceptance Criteria
185. Users can access Add Role functionality successfully
186. Role creation supports:
     - Role Name
     - Description
     - Permissions
187. Permissions are grouped module-wise with selectable checkboxes
188. Supported permission modules include:
     - Projects
     - Members
     - Design Studio
     - Additional supported modules
189. Projects permissions support:
     - All Projects
     - Own Projects
190. Members permissions support:
     - Create
     - View
     - Edit
     - Delete
191. Duplicate or invalid role names are restricted safely
192. Successfully created roles appear immediately in role listing
193. Assigned permissions apply correctly after role creation
194. Invalid or incomplete submissions display meaningful validation feedback
195. Unauthorized role creation attempts are restricted safely
196. System remains stable during repeated role creation operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/we-okas/roles` | Create a new role |

### Request Body
```json
{
  "name": "string (required, unique)",
  "description": "string",
  "permissions": {
    "projects": {
      "scope": "all_projects | own_projects | none"
    },
    "members": {
      "create": "boolean",
      "view": "boolean",
      "edit": "boolean",
      "delete": "boolean"
    },
    "design_studio": {
      "access": "boolean"
    }
  }
}
```

---

## STORY 3 — Edit Existing Role and Permissions

### User Story
> As a **User**,
> I want to **edit roles and permissions**,
> So that **access control remains accurate and adaptable to changing requirements**.

### Acceptance Criteria
197. Users can access Edit Role functionality successfully
198. Existing role information and permissions are prefilled during editing
199. Users can modify:
     - Role Name
     - Description
     - Permissions
200. Permission selections update dynamically and consistently
201. Existing member-role assignments remain preserved unless modified explicitly
202. Invalid or duplicate role information is restricted safely
203. Successfully updated roles reflect immediately across connected modules
204. Unauthorized role update attempts are restricted safely
205. Validation errors display meaningful feedback for invalid updates
206. System remains stable during repeated role update operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/roles/{id}` | Fetch role for prefill |
| PUT | `/we-okas/roles/{id}` | Full update of role and permissions |
| PATCH | `/we-okas/roles/{id}` | Partial update of role |

---

## STORY 4 — Delete Existing Role

### User Story
> As a **User**,
> I want to **delete obsolete roles safely**,
> So that **outdated access structures can be removed without breaking user assignments**.

### Acceptance Criteria
207. Users can access Delete Role functionality successfully
208. Roles assigned to members cannot be deleted directly without reassignment
209. Deletion workflow displays a modal listing members assigned to the selected role
210. Users must reassign all affected members to another valid role before role deletion proceeds
211. Member reassignment updates consistently across connected modules
212. Successfully deleted roles are removed immediately from role listing
213. Unauthorized role deletion attempts are restricted safely
214. Invalid or incomplete reassignment attempts display meaningful validation feedback
215. Role deletion activities are logged successfully for audit and troubleshooting purposes
216. System prevents inconsistent permission states during role deletion operations
217. System remains stable during repeated role deletion and reassignment operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/roles/{id}/members` | List members assigned to the role before deletion |
| POST | `/we-okas/roles/{id}/reassign` | Bulk reassign members to a new role |
| DELETE | `/we-okas/roles/{id}` | Delete role (only allowed after all members are reassigned) |

### Request Body — Reassign Members
```json
{
  "new_role_id": "integer (required)",
  "member_ids": ["integer"]
}
```

### Business Rules
- A role **cannot be deleted** while any member is still assigned to it
- The deletion flow must display a **reassignment modal** listing all affected members
- All affected members must be reassigned to a valid existing role before deletion proceeds
- Role deletion actions must be logged to `audit_logs`

---

## Technical Notes

### DB Tables Involved
- `roles`
- `role_permissions`
- `app_user_roles`
- `app_users`
- `audit_logs`

### Permission Rules
- Only authenticated users with valid `roles and permissions` module access can manage roles
- `View` permission — required to view role listing
- `Create` permission — required to add new roles
- `Edit` permission — required to modify existing roles
- `Delete` permission — required to delete roles
- Unauthorized access must return `403 Forbidden`

### Validation Rules
- `name` must be unique within the organization
- `permissions` object must include at least one module with a valid value
- `new_role_id` during reassignment must reference a valid, existing, non-deleted role
- Mandatory fields: `name`, `permissions`

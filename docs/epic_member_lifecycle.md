# EPIC — Member Lifecycle & Access Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic governs what happens when a member is deleted from the platform. Deletion is a **soft delete only** — data is never hard-deleted. Deleted users lose all access immediately across WE.OKAS, Design Studio, and all assigned projects. However, project configurations, audit history, and historical activity are preserved for compliance and recovery purposes. Projects previously assigned to deleted users become unassigned and available for reassignment.

---

## STORY 1 — Handle User Deletion and Access Revocation

### User Story
> As a **User**,
> I want to **have deleted users lose platform access while preserving project and audit consistency**,
> So that **member management remains secure and recoverable without data loss**.

### Acceptance Criteria
234. Users can be deleted through a soft delete mechanism only
235. Soft deleted users are removed from active member listings
236. Soft deleted users are stored separately for audit, recovery, and historical reference purposes
237. Deleted users lose access to:
     - WE.OKAS
     - Design Studio
     - Assigned projects
     - Protected modules
238. Deleted users attempting authentication receive meaningful account-access validation feedback
239. Existing active sessions of deleted users are invalidated securely after deletion
240. Projects assigned to deleted users become unassigned automatically after deletion
241. Unassigned projects remain accessible for reassignment by authorized users
242. Existing project configurations, hierarchy, and historical activities remain preserved after user deletion
243. Deleted users cannot be assigned to new projects or roles
244. Unauthorized deletion attempts are restricted safely
245. Member deletion activities are logged successfully for audit and troubleshooting purposes
246. Deleted-user information remains recoverable according to system retention policies
247. Permission and project synchronization remain consistent after deletion operations
248. System prevents inconsistent project-assignment states during user deletion
249. System remains stable during repeated deletion and reassignment operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/we-okas/members/{id}` | Soft-delete the member |
| GET | `/we-okas/members/{id}/projects` | List projects assigned to the member before deletion |
| POST | `/we-okas/projects/{id}/reassign` | Reassign an unassigned project to a new member |

### Business Rules
- Deletion is **soft delete only** — `active_ind` is set to `FALSE`, the record is never removed
- On deletion, the following must happen atomically:
  1. `active_ind` set to `FALSE` on `app_users`
  2. All active sessions (`app_sessions`) for the user are invalidated immediately
  3. All project assignments (`project_members`) for the user are revoked automatically
  4. The user record is archived in the audit history table
- Deleted users **cannot authenticate** into WE.OKAS or Design Studio
- Deleted users **cannot be assigned** to any new projects or roles
- Projects that become unassigned after user deletion remain accessible to authorized admins for reassignment
- All project configurations, history, and audit records remain fully intact after user deletion
- Deleted user records remain **recoverable** according to system data retention policies
- All deletion activities must be logged to `audit_logs`

---

## Technical Notes

### DB Tables Involved
- `app_users` — `active_ind` set to `FALSE` on soft delete
- `app_sessions` — all active sessions for deleted user are invalidated
- `app_user_roles` — role assignments are preserved for audit but access is revoked
- `project_members` — all project assignments revoked on deletion
- `projects` — project configurations and history remain intact
- `audit_logs` — all deletion events logged
- `app_users_ah` — audit history table, auto-populated via trigger on delete

### Permission Rules
- Only authenticated users with `Delete` permission on the Members module can delete members
- Unauthorized deletion attempts must return `403 Forbidden`
- Deletion of own account must be restricted or require elevated confirmation

### Validation Rules
- Deletion must require **confirmation** before execution
- Confirmation workflow must display:
  - Affected project assignments
  - Impact on access (WE.OKAS, Design Studio, protected modules)
- `DELETE /we-okas/members/{id}` must validate that the requesting user has delete permission
- Hard delete of any user record is strictly prohibited — soft delete only

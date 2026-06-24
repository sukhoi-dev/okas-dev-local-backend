# EPIC — Member Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers all functionality related to managing members (SI staff, project managers, programmers)
within the WE.OKAS portal. Members are app-layer users who belong to an organization and can be
assigned to projects with specific roles.

---

## STORY 1 — View Member Listing

### User Story
> As a **User**,
> I want to **view all project members in a structured listing**,
> So that **I can manage access and responsibilities efficiently**.

### Acceptance Criteria
1. Users can access the Members module successfully
2. Member listing displays:
   - Name
   - Role
   - Email ID
   - Status
3. Member information remains visually consistent across listing states
4. Members with Design Studio access can authenticate using their registered email ID
5. Search and filtering functionality remain responsive and accurate
6. Unauthorized member visibility is restricted safely
7. Empty states display meaningful guidance when no members exist
8. Updated member information reflects correctly after modifications
9. Member listing remains responsive during large dataset loading
10. System remains stable during repeated member listing operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/members` | List all members in the organization |
| GET | `/we-okas/members/{id}` | Get member details |
| GET | `/we-okas/members?search=&role=&status=` | Search and filter members |

---

## STORY 2 — Create New Member

### User Story
> As a **User**,
> I want to **create new members**,
> So that **project access and responsibilities can be assigned appropriately**.

### Acceptance Criteria
1. Users can access Add Member functionality successfully
2. Member creation supports:
   - Name
   - Role
   - Email ID
   - Status
3. Email addresses remain unique across the platform
4. Members assigned Design Studio access can authenticate using their registered email ID
5. Mandatory fields are validated before saving
6. Invalid or duplicate member information is restricted safely
7. Successfully created members appear immediately in member listing
8. Assigned roles and permissions apply correctly after creation
9. Invalid or incomplete submissions display meaningful validation feedback
10. Unauthorized member creation attempts are restricted safely
11. Member creation activities are logged successfully for audit and troubleshooting purposes
12. System remains stable during repeated member creation operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/we-okas/members` | Create a new member |

### Request Body Fields
```json
{
  "full_name": "string (required)",
  "email": "string (required, unique)",
  "phone": "string",
  "role_id": "integer (required)",
  "organization_id": "integer (required)",
  "status": "active | inactive",
  "has_design_studio_access": "boolean"
}
```

---

## STORY 3 — Edit Existing Member Information

### User Story
> As a **User**,
> I want to **edit member information**,
> So that **user access and responsibilities remain accurate and updated**.

### Acceptance Criteria
1. Users can access Edit Member functionality successfully
2. Existing member information is prefilled during editing
3. Users can update:
   - Name
   - Role
   - Email ID
   - Status
4. Mandatory fields remain validated during updates
5. Invalid or duplicate member information is restricted safely
6. Successfully updated information reflects immediately in member listing
7. Existing project assignments remain preserved unless modified explicitly
8. Unauthorized member update attempts are restricted safely
9. Validation errors display meaningful feedback for invalid updates
10. System remains stable during repeated member update operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/members/{id}` | Fetch member for prefill |
| PUT | `/we-okas/members/{id}` | Full update of member |
| PATCH | `/we-okas/members/{id}` | Partial update of member |

---

## STORY 4 — Delete Existing Member

### User Story
> As a **User**,
> I want to **remove obsolete or inactive members**,
> So that **platform access remains accurate and secure**.

### Acceptance Criteria
1. Users can access Delete Member functionality successfully
2. Member deletion requires confirmation before execution
3. Confirmation workflow informs users about affected project assignments and access
4. Successfully deleted members lose platform access immediately
5. Member removal updates project assignments consistently across modules
6. Unauthorized member deletion attempts are restricted safely
7. Invalid or restricted deletion attempts display meaningful feedback
8. Member deletion activities are logged successfully for audit and troubleshooting purposes
9. System prevents inconsistent member-assignment states during deletion operations
10. System remains stable during repeated member deletion operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/we-okas/members/{id}` | Soft-delete member |

### Business Rules
- Member deletion is a **soft delete** only — `active_ind` set to `FALSE`
- On delete: all project assignments for the member are revoked automatically
- Deleted members cannot log in to WE.OKAS or Design Studio
- All deletion actions must be logged to `audit_logs`
- Deleted member data is retained for audit and recovery purposes

---

## Technical Notes

### DB Tables Involved
- `app_users`
- `roles`
- `app_user_roles`
- `project_members`
- `app_sessions` (sessions must be invalidated on delete)
- `audit_logs`
- `app_users_ah` (audit history — auto-populated via trigger)

### Permission Rules
- Only authenticated users with valid `members` permissions can access this epic
- `Create` permission — required to add new members
- `View` permission — required to view member listing
- `Edit` permission — required to modify member details
- `Delete` permission — required to remove members
- Unauthorized access must return `403 Forbidden`

### Validation Rules
- `email` must be unique across the platform (`app_users.email` UNIQUE constraint)
- `role_id` must reference a valid existing role
- `status` must be one of: `active`, `inactive`
- Mandatory fields: `full_name`, `email`, `role_id`, `organization_id`
- On update: if email is changed, uniqueness must be re-validated

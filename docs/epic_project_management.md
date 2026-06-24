# EPIC — Project Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers all functionality related to managing projects within the WE.OKAS portal.
A project represents a client site (residential, commercial, etc.) configured and managed by a System Integrator.

---

## STORY 1 — View Project Listing

### User Story
> As a **User**,
> I want to **view all accessible projects in a structured listing**,
> So that **I can monitor and manage project information efficiently**.

### Acceptance Criteria
1. Users can access the Projects module successfully from WE.OKAS navigation
2. Project listing displays:
   - Owner Name
   - Address
   - Serial Number
   - Manager
   - Installed Date and Time
3. Project information remains visually consistent across listing states
4. Users can navigate to project details successfully from listing
5. Search and filtering functionality remain responsive and accurate
6. Unauthorized project visibility is restricted safely
7. Empty states display meaningful guidance when no projects exist
8. Updated project information reflects correctly after modifications
9. Project listing remains responsive during large dataset loading
10. System remains stable during repeated project listing operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/projects` | List all accessible projects |
| GET | `/we-okas/projects/{id}` | Get project details |
| GET | `/we-okas/projects?search=&filter=` | Search and filter projects |

---

## STORY 2 — Create New Project

### User Story
> As a **User**,
> I want to **create projects in WE.OKAS**,
> So that **building automation projects can be configured and managed centrally**.

### Acceptance Criteria
1. Users can access Add Project functionality successfully
2. Project creation supports:
   - Building ID
   - Building Type
   - Address
   - Landmark
   - Assigned Member
3. Project creation supports Owner Details:
   - Name
   - Phone Number
   - Email ID
4. Project creation supports Processor Details:
   - Serial Number
5. Mandatory fields are validated before saving
6. Duplicate or invalid serial numbers are restricted safely
7. Successfully created projects appear immediately in project listing
8. Assigned members gain project access according to assigned permissions
9. Invalid or incomplete submissions display meaningful validation feedback
10. Project information remains synchronized across connected platforms
11. Unauthorized project creation attempts are restricted safely
12. System remains stable during repeated project creation operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/we-okas/projects` | Create a new project |

### Request Body Fields
```json
{
  "name": "string (required)",
  "organization_id": "integer (required)",
  "serial_number": "string (required, unique)",
  "project_type": "residential | commercial | hospitality | retail | other",
  "address": "string",
  "landmark": "string",
  "city": "string",
  "state": "string",
  "pincode": "string",
  "project_manager_id": "integer",
  "primary_contact": {
    "full_name": "string (required)",
    "email": "string (required)",
    "phone": "string"
  }
}
```

---

## STORY 3 — Edit Existing Project Information

### User Story
> As a **User**,
> I want to **edit project information**,
> So that **project details remain accurate and updated throughout the project lifecycle**.

### Acceptance Criteria
1. Users can access Edit Project functionality successfully
2. Existing project information is prefilled during editing
3. Users can update:
   - Project Details
   - Owner Details
   - Processor Details
   - Assigned Members
4. Mandatory fields remain validated during updates
5. Invalid or duplicate serial numbers are restricted safely
6. Successfully updated information reflects immediately in project listing and project details
7. Existing project hierarchy and assignments remain preserved after updates
8. Unauthorized project update attempts are restricted safely
9. Validation errors display meaningful feedback for invalid updates
10. System remains stable during repeated project update operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/projects/{id}` | Fetch project for prefill |
| PUT | `/we-okas/projects/{id}` | Update full project |
| PATCH | `/we-okas/projects/{id}` | Partial update project |

---

## STORY 4 — Delete / Archive Existing Project

### User Story
> As a **User**,
> I want to **delete/Archive obsolete projects**,
> So that **outdated or incorrect project information can be removed safely**.

### Acceptance Criteria
1. Users can access Delete/Archive Project functionality successfully
2. Project deletion requires confirmation before execution
3. Confirmation workflow informs users about associated project dependencies
4. Unauthorized project deletion attempts are restricted safely
5. Successfully deleted/Archived projects are removed/Archived for 45 days immediately in/from project listing
6. Deleted/Archived project access is revoked from assigned members automatically
7. Invalid or restricted deletion attempts display meaningful feedback
8. Project deletion/Archived activities are logged successfully for audit and troubleshooting purposes
9. System prevents inconsistent project states during deletion operations
10. System remains stable during repeated project deletion operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| DELETE | `/we-okas/projects/{id}` | Soft-delete / archive project |
| PATCH | `/we-okas/projects/{id}/restore` | Restore archived project |

### Business Rules
- Deleted projects are archived for **45 days** before permanent removal
- On delete: all assigned member access is revoked automatically
- All deletion actions must be logged to `audit_logs`

---

## Technical Notes

### DB Tables Involved
- `projects`
- `project_owners`
- `project_members`
- `project_manager_history`
- `homeowners`
- `app_users`
- `organization_locations`
- `audit_logs`
- `projects_ah` (audit history — auto-populated via trigger)

### Permission Rules
- Only authenticated users with valid `project` permissions can access this epic
- `All Projects` permission — can view/edit/delete any project
- `Own Projects` permission — can view/edit/delete only assigned projects
- Unauthorized access must return `403 Forbidden`

### Validation Rules
- `serial_number` must be unique across the platform
- `project_type` must be one of: `residential`, `commercial`, `hospitality`, `retail`, `other`
- `email` in primary contact must be a valid email format
- Mandatory fields: `name`, `organization_id`, `serial_number`, `project_type`

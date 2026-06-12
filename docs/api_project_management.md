# Project Management API — Implementation Document
**Epic:** Project Management (WE.OKAS)
**Date:** 2026-06-03
**Status:** Implemented & Tested

---

## 1. What We Built

Full CRUD + Archive/Restore API for the Project Management epic covering all 4 stories.

| # | Method | URL | Story |
|---|--------|-----|-------|
| 1 | GET | `/we-okas/projects` | Story 1 — List all projects |
| 2 | GET | `/we-okas/projects?search=delhi` | Story 1 — Search projects |
| 3 | GET | `/we-okas/projects?status=active` | Story 1 — Filter by status |
| 4 | GET | `/we-okas/projects?project_type=residential` | Story 1 — Filter by type |
| 5 | GET | `/we-okas/projects?include_archived=true` | Story 1 — Include archived |
| 6 | GET | `/we-okas/projects/{id}` | Story 1 — Get project detail |
| 7 | POST | `/we-okas/projects` | Story 2 — Create project |
| 8 | PUT | `/we-okas/projects/{id}` | Story 3 — Full update |
| 9 | PATCH | `/we-okas/projects/{id}` | Story 3 — Partial update |
| 10 | DELETE | `/we-okas/projects/{id}` | Story 4 — Archive project |
| 11 | PATCH | `/we-okas/projects/{id}/restore` | Story 4 — Restore archived |

---

## 2. Files Changed / Created

| File | Action | Reason |
|------|--------|--------|
| `app/we_okas/routes/projects.py` | Rewritten | Full CRUD implementation replacing the basic 2-endpoint file |
| `app/models/projects.py` | Updated | Added `landmark` column to `Project` model |
| `app/models/audit.py` | Updated | Added `landmark` column to `ProjectAh` model |
| `alembic/versions/0003_add_landmark_to_projects.py` | Created | New migration to add `landmark` to DB |

---

## 3. DB Change — Why `landmark` Was Added

### The Gap
The original DB schema (`Okas_DB_v1.html`) did not include a `landmark` field on the `projects` table. However, the WE.OKAS epic (Story 2 — Create New Project) explicitly requires `Landmark` as part of project creation.

### What Was Done
- Created migration `0003_add_landmark_to_projects.py`
- Added `landmark VARCHAR(255) NULL` to the `projects` table
- Added the same column to `projects_ah` (the audit history shadow table)

### Why `projects_ah` Also Needed It
`projects_ah` is a mirror of `projects` — every INSERT / UPDATE / DELETE on `projects` is automatically copied into `projects_ah` by a MySQL trigger (`trg_projects_ai`, `trg_projects_au`, `trg_projects_ad`). If `projects_ah` did not have the `landmark` column, the trigger would fail on any project write operation, breaking the entire audit trail.

---

## 4. How Data Gets Saved — Step by Step (POST)

When `POST /we-okas/projects` is called, the following happens in a single DB transaction:

```
Step 1 — Validate serial_number uniqueness
         → SELECT from projects WHERE serial_number = ?
         → Returns 409 Conflict if duplicate found

Step 2 — Validate processor serial_number uniqueness (if provided)
         → SELECT from controllers WHERE serial_number = ?
         → Returns 409 Conflict if duplicate found

Step 3 — Insert into projects
         → Saves: name, organization_id, serial_number, project_type,
                  address, landmark, city, state, pincode, notes,
                  project_manager_id, installed_at (NOW)

Step 4 — Create / Link Homeowner (if primary_contact provided)
         → SELECT from homeowners WHERE email = ?
         → If not found: INSERT new homeowner
         → INSERT into project_owners (project_id, homeowner_id, is_primary=1)

Step 5 — Assign Project Manager (if project_manager_id provided)
         → SELECT from roles WHERE name = 'project_manager'
         → INSERT into project_members (project_id, user_id, role_id)
         → INSERT into project_manager_history (project_id, user_id)

Step 6 — Create Controller / Processor (if processor.serial_number provided)
         → INSERT into controllers (project_id, serial_number, model='OKAS Signature', status='offline')

Step 7 — Fetch and return created project
         → SELECT with JOINs to homeowners, app_users, project_subscriptions, controllers
```

### Tables Written To on Create
| Table | What Gets Written |
|-------|-------------------|
| `projects` | Core project record |
| `homeowners` | New homeowner if email not found |
| `project_owners` | Links homeowner as primary contact |
| `project_members` | Links PM as a project member |
| `project_manager_history` | Logs PM assignment |
| `controllers` | Creates OKAS Signature box entry |
| `projects_ah` | Auto-populated by trigger (audit snapshot) |

---

## 5. How DELETE (Archive) Works

DELETE is a **soft delete** — data is never permanently removed immediately.

```
Step 1 — Verify project exists and is active (active_ind = 1)
Step 2 — Set projects.active_ind = 0  (hides from all listings)
Step 3 — Set project_members.active_ind = 0 for all members
         → Revokes all assigned member access immediately
Step 4 — Close open project_manager_history entry
         → Sets unassigned_at = NOW, reason = 'project_archived'
Step 5 — Write to audit_logs
         → action = 'project.archive', entity_type = 'project', entity_id = {id}
```

**Why soft delete?**
The epic states: *"Successfully deleted/Archived projects are removed/Archived for 45 days."*
This means data must be retained for 45 days for recovery. Hard delete would make restore impossible.

**Restore** simply sets `active_ind = 1` back on the project and logs `project.restore` to `audit_logs`.

---

## 6. Why Each Design Decision Was Made

### Raw pymysql instead of SQLAlchemy ORM
The existing codebase uses raw `pymysql` with `get_db()` context manager for all route handlers. Staying consistent avoids mixing two DB access patterns in the same layer. SQLAlchemy ORM is used only for model definitions and migrations.

### `processor` creates a `controllers` row
The epic says *"Project creation supports Processor Details: Serial Number."* In the DB schema, the OKAS Signature processor is the `controllers` table (`model = 'OKAS Signature'`). There is no separate "processor" table — controller IS the processor. So receiving a processor serial number during project creation creates a `controllers` entry linked to that project.

### `project_manager_id` writes to both `project_members` AND `project_manager_history`
The `projects` table has a `project_manager_id` FK for fast reads. But:
- `project_members` is the authoritative access control table — without a row here, the PM has no tracked access
- `project_manager_history` tracks every PM change over time for audit purposes
Both tables must be populated to keep data consistent.

### Search queries `homeowners` via JOIN
The list query JOINs `homeowners` so searching by owner name (`h.full_name LIKE ?`) works without a separate lookup. This matches the epic's listing requirement which shows "Owner Name."

### `include_archived=false` by default
By default the list only shows `active_ind = 1` projects. Archived projects are hidden unless explicitly requested with `?include_archived=true`. This matches the epic: *"archived projects are removed from project listing."*

---

## 7. Seed Data Inserted

Before the API could be tested, base seed data was required due to FK constraints. The following was inserted directly into `okas_signature`:

| Table | Records |
|-------|---------|
| `roles` | 4 (super_admin, si_admin, project_manager, programmer) |
| `organizations` | 1 (OKAS Systems) |
| `app_users` | 2 (Preeti Chauhan, Rahul Kumar) |
| `homeowners` | 2 (Manoj Agarwal, Shiv Bhansali) |
| `projects` | 2 (sample projects) |
| `project_owners` | 2 (linked to sample projects) |

---

## 8. Sample Request & Response

### POST `/we-okas/projects`

**Request:**
```json
{
  "name": "Manoj Agarwal - Shree KLG Farms",
  "organization_id": 1,
  "serial_number": "BLD-2026-001",
  "project_type": "residential",
  "address": "Hn 25, Shree KLG Farms, Sector 12",
  "landmark": "Near DLF Gate 3",
  "city": "Delhi",
  "state": "Delhi",
  "pincode": "110075",
  "notes": "3BHK villa with full KNX automation",
  "project_manager_id": 1,
  "primary_contact": {
    "full_name": "Manoj Agarwal",
    "email": "manoj.agarwal@example.com",
    "phone": "+91-9812345678"
  },
  "processor": {
    "serial_number": "OKAS-SIG-20260001"
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 4,
    "name": "Manoj Agarwal - Shree KLG Farms",
    "serial_number": "BLD-2026-001",
    "project_type": "residential",
    "status": "active",
    "address": "Hn 25, Shree KLG Farms, Sector 12",
    "landmark": "Near DLF Gate 3",
    "city": "Delhi",
    "state": "Delhi",
    "pincode": "110075",
    "installed_at": "2026-06-03T12:33:13.408000",
    "notes": "3BHK villa with full KNX automation",
    "active_ind": 1,
    "project_manager_id": 1,
    "owner_name": "Manoj Agarwal",
    "owner_email": "manoj.agarwal@example.com",
    "owner_phone": "+91-9812345678",
    "manager_name": "Preeti Chauhan",
    "subscription_status": null,
    "processor_serial_number": "OKAS-SIG-20260001",
    "processor_status": "offline"
  }
}
```

---

## 9. Live API Responses — All Endpoints

---

### GET `/we-okas/projects` — List All Projects

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects
```

**Response:**
```json
{
    "success": true,
    "total": 3,
    "data": [
        {
            "id": 4,
            "name": "Manoj Agarwal - Shree KLG Farms",
            "serial_number": "BLD-2026-001",
            "project_type": "residential",
            "status": "active",
            "address": "Hn 25, Shree KLG Farms, Sector 12",
            "landmark": "Near DLF Gate 3",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110075",
            "installed_at": "2026-06-03T12:33:13.408000",
            "notes": "3BHK villa with full KNX automation",
            "active_ind": 1,
            "project_manager_id": 1,
            "owner_name": "Manoj Agarwal",
            "owner_email": "manoj.new@example.com",
            "owner_phone": "+91-9812345678",
            "manager_name": "Preeti Chauhan",
            "subscription_status": null,
            "processor_serial_number": "OKAS-SIG-20260001",
            "processor_status": "offline"
        },
        {
            "id": 1,
            "name": "Manoj Agarwal - Shree KLG",
            "serial_number": "BLD-2025-001",
            "project_type": "residential",
            "status": "active",
            "address": "Hn 25, Shree KLG Farms, Sector 12",
            "landmark": null,
            "city": "Delhi",
            "state": null,
            "pincode": null,
            "installed_at": "2025-02-23T02:25:26",
            "notes": null,
            "active_ind": 1,
            "project_manager_id": 1,
            "owner_name": "Manoj Agarwal",
            "owner_email": "manoj.agarwal@example.com",
            "owner_phone": "+91-9812345678",
            "manager_name": "Preeti Chauhan",
            "subscription_status": null,
            "processor_serial_number": null,
            "processor_status": null
        },
        {
            "id": 2,
            "name": "Shiv Bhansali - Okhla",
            "serial_number": "BLD-2025-002",
            "project_type": "residential",
            "status": "active",
            "address": "D-102, Okhla Phase 2, New Delhi",
            "landmark": null,
            "city": "Delhi",
            "state": null,
            "pincode": null,
            "installed_at": "2025-02-23T02:25:26",
            "notes": null,
            "active_ind": 1,
            "project_manager_id": 1,
            "owner_name": "Shiv Bhansali",
            "owner_email": "shiv.bhansali@example.com",
            "owner_phone": "+91-9823456789",
            "manager_name": "Preeti Chauhan",
            "subscription_status": null,
            "processor_serial_number": null,
            "processor_status": null
        }
    ]
}
```

---

### GET `/we-okas/projects?search=shiv` — Search Projects

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects?search=shiv
```

**Response:**
```json
{
    "success": true,
    "total": 1,
    "data": [
        {
            "id": 2,
            "name": "Shiv Bhansali - Okhla",
            "serial_number": "BLD-2025-002",
            "project_type": "residential",
            "status": "active",
            "address": "D-102, Okhla Phase 2, New Delhi",
            "landmark": null,
            "city": "Delhi",
            "state": null,
            "pincode": null,
            "installed_at": "2025-02-23T02:25:26",
            "notes": null,
            "active_ind": 1,
            "project_manager_id": 1,
            "owner_name": "Shiv Bhansali",
            "owner_email": "shiv.bhansali@example.com",
            "owner_phone": "+91-9823456789",
            "manager_name": "Preeti Chauhan",
            "subscription_status": null,
            "processor_serial_number": null,
            "processor_status": null
        }
    ]
}
```

---

### GET `/we-okas/projects?status=active` — Filter by Status

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects?status=active
```

**Response:** *(returns all 3 active projects — same structure as list above)*
```json
{
    "success": true,
    "total": 3,
    "data": [ ... ]
}
```

---

### GET `/we-okas/projects?project_type=residential` — Filter by Type

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects?project_type=residential
```

**Response:** *(returns all 3 residential projects — same structure as list above)*
```json
{
    "success": true,
    "total": 3,
    "data": [ ... ]
}
```

---

### GET `/we-okas/projects/{id}` — Get Project by ID

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects/4
```

**Response (200 — found):**
```json
{
    "success": true,
    "data": {
        "id": 4,
        "name": "Manoj Agarwal - Shree KLG Farms",
        "serial_number": "BLD-2026-001",
        "project_type": "residential",
        "status": "active",
        "address": "Hn 25, Shree KLG Farms, Sector 12",
        "landmark": "Near DLF Gate 3",
        "city": "Delhi",
        "state": "Delhi",
        "pincode": "110075",
        "installed_at": "2026-06-03T12:33:13.408000",
        "notes": "3BHK villa with full KNX automation",
        "active_ind": 1,
        "project_manager_id": 1,
        "owner_name": "Manoj Agarwal",
        "owner_email": "manoj.new@example.com",
        "owner_phone": "+91-9812345678",
        "manager_name": "Preeti Chauhan",
        "subscription_status": null,
        "processor_serial_number": "OKAS-SIG-20260001",
        "processor_status": "offline"
    }
}
```

**Response (404 — not found):**
```json
{
    "detail": "Project not found"
}
```

---

### PUT `/we-okas/projects/{id}` — Full Update

**Request:**
```
PUT http://127.0.0.1:8000/we-okas/projects/4
```
```json
{
    "name": "Manoj Agarwal - Shree KLG Farms (Updated)",
    "serial_number": "BLD-2026-001",
    "project_type": "residential",
    "address": "Hn 25, Shree KLG Farms, Sector 12",
    "landmark": "Near DLF Gate 3",
    "city": "New Delhi",
    "state": "Delhi",
    "pincode": "110075",
    "notes": "Updated notes",
    "project_manager_id": 1
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 4,
        "name": "Manoj Agarwal - Shree KLG Farms (Updated)",
        "serial_number": "BLD-2026-001",
        "project_type": "residential",
        "status": "active",
        "address": "Hn 25, Shree KLG Farms, Sector 12",
        "landmark": "Near DLF Gate 3",
        "city": "New Delhi",
        "state": "Delhi",
        "pincode": "110075",
        "installed_at": "2026-06-03T12:33:13.408000",
        "notes": "Updated notes",
        "active_ind": 1,
        "project_manager_id": 1,
        "owner_name": "Manoj Agarwal",
        "owner_email": "manoj.new@example.com",
        "owner_phone": "+91-9812345678",
        "manager_name": "Preeti Chauhan",
        "subscription_status": null,
        "processor_serial_number": "OKAS-SIG-20260001",
        "processor_status": "offline"
    }
}
```

---

### PATCH `/we-okas/projects/{id}` — Partial Update

**Request:**
```
PATCH http://127.0.0.1:8000/we-okas/projects/4
```
```json
{
    "city": "Gurugram",
    "pincode": "122001"
}
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 4,
        "name": "Manoj Agarwal - Shree KLG Farms (Updated)",
        "serial_number": "BLD-2026-001",
        "project_type": "residential",
        "status": "active",
        "address": "Hn 25, Shree KLG Farms, Sector 12",
        "landmark": "Near DLF Gate 3",
        "city": "Gurugram",
        "state": "Delhi",
        "pincode": "122001",
        "installed_at": "2026-06-03T12:33:13.408000",
        "notes": "Updated notes",
        "active_ind": 1,
        "project_manager_id": 1,
        "owner_name": "Manoj Agarwal",
        "owner_email": "manoj.new@example.com",
        "owner_phone": "+91-9812345678",
        "manager_name": "Preeti Chauhan",
        "subscription_status": null,
        "processor_serial_number": "OKAS-SIG-20260001",
        "processor_status": "offline"
    }
}
```

---

### DELETE `/we-okas/projects/{id}` — Archive Project

**Request:**
```
DELETE http://127.0.0.1:8000/we-okas/projects/4
```

**Response:**
```json
{
    "success": true,
    "message": "Project 'Manoj Agarwal - Shree KLG Farms (Updated)' has been archived. It will be retained for 45 days."
}
```

---

### GET `/we-okas/projects?include_archived=true` — List Including Archived

**Request:**
```
GET http://127.0.0.1:8000/we-okas/projects?include_archived=true
```

**Response:** *(archived project appears with `active_ind: 0`)*
```json
{
    "success": true,
    "total": 3,
    "data": [
        {
            "id": 4,
            "name": "Manoj Agarwal - Shree KLG Farms (Updated)",
            "active_ind": 0,
            "status": "active",
            "processor_serial_number": "OKAS-SIG-20260001",
            "processor_status": "offline",
            "..."  : "..."
        },
        { "id": 1, "active_ind": 1, "...": "..." },
        { "id": 2, "active_ind": 1, "...": "..." }
    ]
}
```

---

### PATCH `/we-okas/projects/{id}/restore` — Restore Archived Project

**Request:**
```
PATCH http://127.0.0.1:8000/we-okas/projects/4/restore
```

**Response:**
```json
{
    "success": true,
    "data": {
        "id": 4,
        "name": "Manoj Agarwal - Shree KLG Farms (Updated)",
        "serial_number": "BLD-2026-001",
        "project_type": "residential",
        "status": "active",
        "address": "Hn 25, Shree KLG Farms, Sector 12",
        "landmark": "Near DLF Gate 3",
        "city": "Gurugram",
        "state": "Delhi",
        "pincode": "122001",
        "installed_at": "2026-06-03T12:33:13.408000",
        "notes": "Updated notes",
        "active_ind": 1,
        "project_manager_id": 1,
        "owner_name": "Manoj Agarwal",
        "owner_email": "manoj.new@example.com",
        "owner_phone": "+91-9812345678",
        "manager_name": "Preeti Chauhan",
        "subscription_status": null,
        "processor_serial_number": "OKAS-SIG-20260001",
        "processor_status": "offline"
    }
}
```

---

### POST `/we-okas/projects` — Duplicate Serial Number (Error Case)

**Request:**
```
POST http://127.0.0.1:8000/we-okas/projects
```
```json
{
    "name": "Dup Test",
    "organization_id": 1,
    "serial_number": "BLD-2026-001",
    "project_type": "residential"
}
```

**Response (409 — Conflict):**
```json
{
    "detail": "serial_number already exists"
}
```


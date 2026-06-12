# EPIC — Distributor Management & Multi-Tenant WE.OKAS Access
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers Distributor-level access within WE.OKAS. A Distributor is an organization that manages one or more System Integrators (SIs). Distributors authenticate into WE.OKAS using the same auth flows as regular users, but they see an additional "System Integrators" navigation module. Distributors can create, manage, and delete SIs, and view all projects grouped by SI across their organization.

---

## STORY 1 — Authenticate Distributor into WE.OKAS

### User Story
> As a **Distributor**,
> I want to **authenticate into WE.OKAS**,
> So that **I can manage System Integrators, projects, and platform access under my organization**.

### Acceptance Criteria
250. Distributor authentication follows the same authentication flow as other WE.OKAS users
251. Supported authentication methods include:
     - OTP Login
     - Password Login
     - Forgot Password
     - Google Login
     - First-Time User Activation
     - Session Persistence
252. Successfully authenticated distributors are redirected to WE.OKAS dashboard
253. Unauthorized authentication attempts are restricted safely
254. Authentication activities are logged successfully for audit and troubleshooting purposes
255. User session handling remains secure and consistent across the platform
256. System remains stable during simultaneous authentication requests

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/login` | Authenticate distributor via email + password |
| POST | `/auth/otp/send` | Send OTP to distributor email |
| POST | `/auth/otp/verify` | Verify OTP and issue session |
| GET | `/auth/google` | Initiate Google OAuth for distributor |
| POST | `/auth/activate` | First-time activation for distributor account |

> Distributor authentication reuses all auth endpoints from the Authentication & Session Management epic. No separate endpoints required.

---

## STORY 2 — Display Distributor Navigation Modules

### User Story
> As a **Distributor**,
> I want to **access distributor-specific modules from WE.OKAS navigation**,
> So that **I can manage System Integrators and monitor projects under my organization**.

### Acceptance Criteria
257. Distributor users can access the following navigation modules:
     - Home
     - System Integrators
     - Projects
     - Members
     - Roles and Permissions
     - Support
     - Help
258. Navigation hierarchy remains visually consistent with WE.OKAS standards
259. Logo remains sticky at the top of navigation
260. Help action remains sticky at the bottom of navigation
261. Unauthorized modules are restricted safely
262. Navigation remains responsive during rapid module switching
263. System remains stable during simultaneous navigation operations

### Business Rules
- Distributor navigation includes the **System Integrators** module, which is not visible to regular users
- All sticky navigation behavior from the Navigation epic applies here
- Unauthorized module access must return `403 Forbidden`

---

## STORY 3 — View System Integrator Listing

### User Story
> As a **Distributor**,
> I want to **view all System Integrators under my organization**,
> So that **I can monitor and manage SI accounts efficiently**.

### Acceptance Criteria
264. Distributor users can access System Integrators module successfully
265. SI listing displays:
     - Name
     - Company Name
     - Address
     - Email ID
     - Contact Number
     - GST / VAT Number
     - Status
266. Search and filtering functionality remain responsive and accurate
267. Unauthorized SI visibility is restricted safely
268. Empty states display meaningful guidance when no SIs exist
269. Updated SI information reflects correctly after modifications
270. SI listing remains responsive during large dataset loading
271. System remains stable during repeated SI listing operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/system-integrators` | List all SIs under the distributor's organization |
| GET | `/we-okas/system-integrators/{id}` | Get SI details |
| GET | `/we-okas/system-integrators?search=&status=` | Search and filter SIs |

---

## STORY 4 — Create New System Integrator

### User Story
> As a **Distributor**,
> I want to **create System Integrator accounts**,
> So that **I can onboard and manage automation partners under my organization**.

### Acceptance Criteria
272. Distributor users can access Add System Integrator functionality successfully
273. SI creation supports:
     - Name
     - Company Name
     - Address
     - Email ID
     - Contact Number
     - GST / VAT Number
274. Email addresses remain unique across the platform
275. Mandatory fields are validated before saving
276. Invalid or duplicate SI information is restricted safely
277. Successfully created SIs appear immediately in SI listing
278. Newly created SIs can authenticate into WE.OKAS according to assigned access rules
279. Invalid or incomplete submissions display meaningful validation feedback
280. Unauthorized SI creation attempts are restricted safely
281. SI creation activities are logged successfully for audit and troubleshooting purposes
282. System remains stable during repeated SI creation operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/we-okas/system-integrators` | Create a new System Integrator |

### Request Body
```json
{
  "name": "string (required)",
  "company_name": "string (required)",
  "address": "string",
  "email": "string (required, unique)",
  "contact_number": "string",
  "gst_vat_number": "string",
  "distributor_id": "integer (required)"
}
```

---

## STORY 5 — Edit Existing System Integrator

### User Story
> As a **Distributor**,
> I want to **edit System Integrator information**,
> So that **partner information remains accurate and updated**.

### Acceptance Criteria
283. Distributor users can access Edit System Integrator functionality successfully
284. Existing SI information is prefilled during editing
285. Users can update:
     - Name
     - Company Name
     - Address
     - Email ID
     - Contact Number
     - GST / VAT Number
     - Status
286. Mandatory fields remain validated during updates
287. Invalid or duplicate SI information is restricted safely
288. Successfully updated information reflects immediately in SI listing
289. Existing project and member relationships remain preserved after updates
290. Unauthorized SI update attempts are restricted safely
291. Validation errors display meaningful feedback for invalid updates
292. System remains stable during repeated SI update operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/system-integrators/{id}` | Fetch SI for prefill |
| PUT | `/we-okas/system-integrators/{id}` | Full update of SI |
| PATCH | `/we-okas/system-integrators/{id}` | Partial update of SI |

---

## STORY 6 — Delete System Integrator

### User Story
> As a **Distributor**,
> I want to **delete obsolete or inactive System Integrators**,
> So that **organization access remains accurate and manageable**.

### Acceptance Criteria
293. Distributor users can access Delete System Integrator functionality successfully
294. SI deletion requires confirmation before execution
295. Confirmation workflow informs users about:
     - Assigned projects
     - Members
     - Roles
     - Access dependencies
296. Deleted SI accounts lose platform access immediately
297. Existing projects under deleted SI remain preserved safely
298. Projects under deleted SI become unassigned for reassignment later
299. Existing project configurations and audit history remain preserved
300. Unauthorized SI deletion attempts are restricted safely
301. SI deletion activities are logged successfully for audit and troubleshooting purposes
302. System prevents inconsistent project-assignment states during deletion operations
303. System remains stable during repeated SI deletion operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/system-integrators/{id}/summary` | Get deletion impact summary (projects, members, roles) |
| DELETE | `/we-okas/system-integrators/{id}` | Soft-delete the SI |

### Business Rules
- SI deletion is a **soft delete** — `active_ind` set to `FALSE`, record is never hard-deleted
- On deletion:
  1. SI account loses all platform access immediately
  2. All projects under the SI become **unassigned** (available for reassignment)
  3. Existing project configurations and audit history are fully preserved
- Projects under a deleted SI must remain accessible to authorized distributors for reassignment
- All deletion events must be logged to `audit_logs`

---

## STORY 7 — View Projects Grouped by System Integrator

### User Story
> As a **Distributor**,
> I want to **view projects grouped by System Integrator**,
> So that **I can monitor project distribution and ownership across my organization**.

### Acceptance Criteria
304. Distributor users can access all projects associated with their System Integrators
305. Project listing supports grouping based on assigned System Integrator
306. Project listing displays:
     - Project Information
     - Assigned SI
     - Assigned Members
     - Installation Information
     - Processor Details
307. Users can filter projects based on selected System Integrator
308. Project grouping updates dynamically after SI reassignment
309. Unauthorized project visibility is restricted safely
310. Empty states display meaningful guidance when no projects exist under selected SI
311. Project information remains synchronized across listings and details screens
312. Project listing performance remains stable during large dataset loading
313. System remains stable during repeated filtering and grouping operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/we-okas/projects?group_by=si` | List all projects grouped by SI |
| GET | `/we-okas/projects?si_id={id}` | Filter projects by specific SI |
| GET | `/we-okas/projects/{id}` | Get project details |

---

## Technical Notes

### DB Tables Involved
- `distributors`
- `system_integrators`
- `si_members`
- `projects`
- `project_members`
- `app_users`
- `roles`
- `app_sessions`
- `audit_logs`
- `system_integrators_ah` (audit history — auto-populated via trigger)

### Permission Rules
- Only authenticated users with **Distributor** role can access the System Integrators module
- Regular WE.OKAS users (non-distributors) must not see or access the System Integrators navigation item
- Unauthorized access must return `403 Forbidden`
- Distributor can only manage SIs and projects within their own organization — cross-organization access is forbidden

### Validation Rules
- `email` must be unique across the platform
- `gst_vat_number` must follow valid format if provided
- `distributor_id` must reference a valid, active distributor organization
- Mandatory fields: `name`, `company_name`, `email`, `distributor_id`
- On SI update: if email is changed, uniqueness must be re-validated

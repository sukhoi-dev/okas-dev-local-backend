-- Dev seed data for okas-cloud-backend local testing
-- Run once after alembic upgrade head:
--   mysql -h 127.0.0.1 -P 3307 -u okasdev -p okascloud < db/seed.sql
--
-- Safe to re-run: INSERT IGNORE on explicit IDs skips existing rows.

USE okascloud;

-- ── Organization ──────────────────────────────────────────────────────────────
INSERT IGNORE INTO organizations (id, name, slug, email, phone)
VALUES (1, 'OKAS Systems', 'okas-systems', 'admin@okas.ai', '+91-9999999999');

-- ── Roles ─────────────────────────────────────────────────────────────────────
INSERT IGNORE INTO roles (id, name, description)
VALUES
  (1, 'Admin',           'Full platform access — all modules and permissions'),
  (2, 'Project Manager', 'Manage own projects, view and edit team members'),
  (3, 'Viewer',          'Read-only access to assigned projects');

-- ── Role Permissions ──────────────────────────────────────────────────────────
-- Admin (role_id = 1) — everything ON
INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
VALUES
  ( 1, 1, 'projects',      'all_projects', TRUE),
  ( 2, 1, 'members',       'create',       TRUE),
  ( 3, 1, 'members',       'view',         TRUE),
  ( 4, 1, 'members',       'edit',         TRUE),
  ( 5, 1, 'members',       'delete',       TRUE),
  ( 6, 1, 'design_studio', 'access',       TRUE);

-- Project Manager (role_id = 2) — own projects, limited member ops
INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
VALUES
  ( 7, 2, 'projects',      'own_projects', TRUE),
  ( 8, 2, 'members',       'create',       FALSE),
  ( 9, 2, 'members',       'view',         TRUE),
  (10, 2, 'members',       'edit',         TRUE),
  (11, 2, 'members',       'delete',       FALSE),
  (12, 2, 'design_studio', 'access',       TRUE);

-- Viewer (role_id = 3) — read-only
INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
VALUES
  (13, 3, 'projects',      'own_projects', TRUE),
  (14, 3, 'members',       'create',       FALSE),
  (15, 3, 'members',       'view',         TRUE),
  (16, 3, 'members',       'edit',         FALSE),
  (17, 3, 'members',       'delete',       FALSE),
  (18, 3, 'design_studio', 'access',       FALSE);

-- ── App Users ─────────────────────────────────────────────────────────────────
-- pankaj@vyom.ai  →  Admin      (use this email to get a token)
-- preeti / sarah  →  Project Manager
-- rahul / mike    →  Viewer
INSERT IGNORE INTO app_users (id, organization_id, email, full_name)
VALUES
  (1, 1, 'preeti.chauhan@okas.ai', 'Preeti Chauhan'),
  (2, 1, 'rahul.kumar@okas.ai',    'Rahul Kumar'),
  (3, 1, 'pankaj@vyom.ai',         'Pankaj Rana'),
  (4, 1, 'sarah.jones@okas.ai',    'Sarah Jones'),
  (5, 1, 'mike.dev@okas.ai',       'Mike Dev');

-- ── App User Roles ────────────────────────────────────────────────────────────
INSERT IGNORE INTO app_user_roles (id, user_id, role_id, organization_id)
VALUES
  (1, 3, 1, 1),   -- pankaj@vyom.ai          → Admin
  (2, 1, 2, 1),   -- preeti.chauhan@okas.ai  → Project Manager
  (3, 4, 2, 1),   -- sarah.jones@okas.ai     → Project Manager
  (4, 2, 3, 1),   -- rahul.kumar@okas.ai     → Viewer
  (5, 5, 3, 1);   -- mike.dev@okas.ai        → Viewer

-- ── Homeowners ────────────────────────────────────────────────────────────────
INSERT IGNORE INTO homeowners (id, full_name, email, phone)
VALUES
  (1, 'Manoj Agarwal', 'manoj.agarwal@example.com', '+91-9812345678'),
  (2, 'Shiv Bhansali',  'shiv.bhansali@example.com',  '+91-9823456789');

-- ── Projects ──────────────────────────────────────────────────────────────────
INSERT IGNORE INTO projects
  (id, organization_id, project_manager_id, name, serial_number,
   project_type, address, city, installed_at)
VALUES
  (1, 1, 1, 'Manoj Agarwal - Shree KLG', '202036', 'residential',
   'Hn 25, Shree KLG Farms, Sector 12', 'Delhi', '2025-02-23 02:25:26'),
  (2, 1, 1, 'Shiv Bhansali - Okhla',     '202036', 'residential',
   'D-102, Okhla Phase 2, New Delhi',   'Delhi', '2025-02-23 02:25:26');

-- ── Project Owners ────────────────────────────────────────────────────────────
INSERT IGNORE INTO project_owners (project_id, homeowner_id, is_primary)
VALUES (1, 1, 1), (2, 2, 1);

-- ── Distributor setup ─────────────────────────────────────────────────────
-- Distributor organization
INSERT IGNORE INTO organizations (id, org_type, name, slug, email, phone)
VALUES (2, 'distributor', 'Super Distributor Co.', 'super-distributor', 'superadmin@mail.com', '+91-9800000000');
-- Ensure org_type is set correctly if row already exists
UPDATE organizations SET org_type = 'distributor' WHERE id = 2;

-- Distributor role
INSERT IGNORE INTO roles (id, name, description)
VALUES (1, 'distributor', 'Distributor who manages system integrators');

-- SI role
INSERT IGNORE INTO roles (id, name, description)
VALUES (4, 'si', 'System integrator managed by a distributor');

-- Distributor user  (login: sumit@vyom.ai via OTP)
INSERT INTO app_users (id, organization_id, email, full_name)
VALUES (3, 2, 'sumit@vyom.ai', 'Sumit')
ON DUPLICATE KEY UPDATE email = 'sumit@vyom.ai', full_name = 'Sumit';

-- Link user to distributor role
INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
VALUES (3, 1, 2);

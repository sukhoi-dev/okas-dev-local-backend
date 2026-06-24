-- Dev seed data for okas-cloud-backend local testing
-- Run once after alembic upgrade head:
--   mysql -h 127.0.0.1 -P 3307 -u okasdev -p okascloud < db/seed.sql
--
-- Safe to re-run: INSERT IGNORE on explicit IDs skips existing rows.

USE okascloud;

-- ── Organization ──────────────────────────────────────────────────────────────
-- INSERT IGNORE INTO organizations (id, name, slug, email, phone)
-- VALUES (1, 'OKAS Systems', 'okas-systems', 'admin@okas.ai', '+91-9999999999');

-- ── Roles (legacy — superseded by Default roles section below) ────────────────
-- INSERT IGNORE INTO roles (id, name, description)
-- VALUES
--   (1, 'Admin',           'Full platform access — all modules and permissions'),
--   (2, 'Project Manager', 'Manage own projects, view and edit team members'),
--   (3, 'Viewer',          'Read-only access to assigned projects');

-- ── Role Permissions (legacy — superseded by Default roles section below) ─────
-- Admin (role_id = 1) — everything ON
-- INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
-- VALUES
--   ( 1, 1, 'projects',      'all_projects', TRUE),
--   ( 2, 1, 'members',       'create',       TRUE),
--   ( 3, 1, 'members',       'view',         TRUE),
--   ( 4, 1, 'members',       'edit',         TRUE),
--   ( 5, 1, 'members',       'delete',       TRUE),
--   ( 6, 1, 'design_studio', 'access',       TRUE);

-- Project Manager (role_id = 2) — own projects, limited member ops
-- INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
-- VALUES
--   ( 7, 2, 'projects',      'own_projects', TRUE),
--   ( 8, 2, 'members',       'create',       FALSE),
--   ( 9, 2, 'members',       'view',         TRUE),
--   (10, 2, 'members',       'edit',         TRUE),
--   (11, 2, 'members',       'delete',       FALSE),
--   (12, 2, 'design_studio', 'access',       TRUE);

-- Viewer (role_id = 3) — read-only
-- INSERT IGNORE INTO role_permissions (id, role_id, feature, action, is_allowed)
-- VALUES
--   (13, 3, 'projects',      'own_projects', TRUE),
--   (14, 3, 'members',       'create',       FALSE),
--   (15, 3, 'members',       'view',         TRUE),
--   (16, 3, 'members',       'edit',         FALSE),
--   (17, 3, 'members',       'delete',       FALSE),
--   (18, 3, 'design_studio', 'access',       FALSE);

-- ── App Users ─────────────────────────────────────────────────────────────────
-- pankaj@vyom.ai  →  Admin      (use this email to get a token)
-- preeti / sarah  →  Project Manager
-- rahul / mike    →  Viewer
-- INSERT IGNORE INTO app_users (id, organization_id, email, full_name)
-- VALUES
--   (1, 1, 'preeti.chauhan@okas.ai', 'Preeti Chauhan'),
--   (2, 1, 'rahul.kumar@okas.ai',    'Rahul Kumar'),
--   (3, 1, 'pankaj@vyom.ai',         'Pankaj Rana'),
--   (4, 1, 'sarah.jones@okas.ai',    'Sarah Jones'),
--   (5, 1, 'mike.dev@okas.ai',       'Mike Dev');

-- ── App User Roles ────────────────────────────────────────────────────────────
-- INSERT IGNORE INTO app_user_roles (id, user_id, role_id, organization_id)
-- VALUES
--   (1, 3, 1, 1),   -- pankaj@vyom.ai          → Admin
--   (2, 1, 2, 1),   -- preeti.chauhan@okas.ai  → Project Manager
--   (3, 4, 2, 1),   -- sarah.jones@okas.ai     → Project Manager
--   (4, 2, 3, 1),   -- rahul.kumar@okas.ai     → Viewer
--   (5, 5, 3, 1);   -- mike.dev@okas.ai        → Viewer

-- ── Homeowners ────────────────────────────────────────────────────────────────
-- INSERT IGNORE INTO homeowners (id, full_name, email, phone)
-- VALUES
--   (1, 'Manoj Agarwal', 'manoj.agarwal@example.com', '+91-9812345678'),
--   (2, 'Shiv Bhansali',  'shiv.bhansali@example.com',  '+91-9823456789');

-- ── Projects ──────────────────────────────────────────────────────────────────
-- INSERT IGNORE INTO projects
--   (id, organization_id, project_manager_id, name, serial_number,
--    project_type, address, city, installed_at)
-- VALUES
--   (1, 1, 1, 'Manoj Agarwal - Shree KLG', '202036', 'residential',
--    'Hn 25, Shree KLG Farms, Sector 12', 'Delhi', '2025-02-23 02:25:26'),
--   (2, 1, 1, 'Shiv Bhansali - Okhla',     '202036', 'residential',
--    'D-102, Okhla Phase 2, New Delhi',   'Delhi', '2025-02-23 02:25:26');

-- ── Project Owners ────────────────────────────────────────────────────────────
-- INSERT IGNORE INTO project_owners (project_id, homeowner_id, is_primary)
-- VALUES (1, 1, 1), (2, 2, 1);

-- -- ── Distributor setup ─────────────────────────────────────────────────────
-- -- Distributor organization
-- INSERT IGNORE INTO organizations (id, org_type, name, slug, email, phone)
-- VALUES (2, 'distributor', 'Super Distributor Co.', 'super-distributor', 'superadmin@mail.com', '+91-9800000000');
-- -- Ensure org_type is set correctly if row already exists
-- UPDATE organizations SET org_type = 'distributor' WHERE id = 2;


INSERT IGNORE INTO organizations (id, name, slug, email, phone)
VALUES (1, 'OKAS Systems', 'okas-systems', 'rajat@vyom.ai', '+91-9999999999');

-- ── Default roles ─────────────────────────────────────────────────────────────
INSERT IGNORE INTO roles (id, name, description) VALUES
  (1, 'distributor',       'Distributor admin — manages SIs, PMs, projects and members under their org'),
  (2, 'si',                'System Integrator — manages buildings, devices, automation and members under their org'),
  (3, 'Master Programmer', 'Full SI-level access — all modules and permissions'),
  (4, 'Programmer',        'SI-level access without SI management permissions');

-- Clear and reinsert permissions for all 4 default roles (safe for re-runs)
DELETE FROM role_permissions WHERE role_id IN (1, 2, 3, 4);

-- distributor (role_id = 1)
INSERT INTO role_permissions (role_id, feature, action, is_allowed) VALUES
  (1, 'dashboard',     'view',    TRUE),
  (1, 'projects',      'view',    TRUE),
  (1, 'projects',      'create',  TRUE),
  (1, 'projects',      'edit',    TRUE),
  (1, 'si',            'view',    TRUE),
  (1, 'si',            'create',  TRUE),
  (1, 'si',            'edit',    TRUE),
  (1, 'pm',            'view',    TRUE),
  (1, 'pm',            'create',  TRUE),
  (1, 'pm',            'edit',    TRUE),
  (1, 'users',         'view',    TRUE),
  (1, 'users',         'create',  TRUE),
  (1, 'users',         'edit',    TRUE),
  (1, 'organizations', 'view',    TRUE),
  (1, 'reports',       'view',    TRUE),
  (1, 'notifications', 'view',    TRUE),
  (1, 'settings',      'view',    TRUE),
  (1, 'buildings',     'view',    TRUE),
  (1, 'floors',        'view',    TRUE),
  (1, 'rooms',         'view',    TRUE),
  (1, 'devices',       'view',    TRUE),
  (1, 'roles',         'view',    TRUE),
  (1, 'roles',         'manage',  TRUE),
  (1, 'members',       'view',    TRUE),
  (1, 'members',       'create',  TRUE),
  (1, 'members',       'edit',    TRUE),
  (1, 'members',       'delete',  TRUE);

-- si (role_id = 2)
INSERT INTO role_permissions (role_id, feature, action, is_allowed) VALUES
  (2, 'dashboard',     'view',      TRUE),
  (2, 'projects',      'view',      TRUE),
  (2, 'projects',      'configure', TRUE),
  (2, 'pm',            'view',      TRUE),
  (2, 'users',         'view',      TRUE),
  (2, 'users',         'create',    TRUE),
  (2, 'users',         'edit',      TRUE),
  (2, 'reports',       'view',      TRUE),
  (2, 'notifications', 'view',      TRUE),
  (2, 'settings',      'view',      TRUE),
  (2, 'buildings',     'view',      TRUE),
  (2, 'buildings',     'create',    TRUE),
  (2, 'buildings',     'edit',      TRUE),
  (2, 'floors',        'view',      TRUE),
  (2, 'floors',        'create',    TRUE),
  (2, 'floors',        'edit',      TRUE),
  (2, 'rooms',         'view',      TRUE),
  (2, 'rooms',         'create',    TRUE),
  (2, 'rooms',         'edit',      TRUE),
  (2, 'devices',       'view',      TRUE),
  (2, 'devices',       'create',    TRUE),
  (2, 'devices',       'edit',      TRUE),
  (2, 'devices',       'configure', TRUE),
  (2, 'automation',    'view',      TRUE),
  (2, 'automation',    'manage',    TRUE),
  (2, 'scenes',        'view',      TRUE),
  (2, 'scenes',        'manage',    TRUE),
  (2, 'scenes',        'activate',  TRUE),
  (2, 'scheduling',    'view',      TRUE),
  (2, 'scheduling',    'manage',    TRUE),
  (2, 'mqtt',          'view',      TRUE),
  (2, 'mqtt',          'manage',    TRUE),
  (2, 'layout',        'view',      TRUE),
  (2, 'layout',        'manage',    TRUE),
  (2, 'roles',         'view',      TRUE),
  (2, 'roles',         'manage',    TRUE),
  (2, 'members',       'view',      TRUE),
  (2, 'members',       'create',    TRUE),
  (2, 'members',       'edit',      TRUE),
  (2, 'members',       'delete',    TRUE);

-- Master Programmer (role_id = 3) — same as si
INSERT INTO role_permissions (role_id, feature, action, is_allowed) VALUES
  (3, 'dashboard',     'view',      TRUE),
  (3, 'projects',      'view',      TRUE),
  (3, 'projects',      'configure', TRUE),
  (3, 'pm',            'view',      TRUE),
  (3, 'users',         'view',      TRUE),
  (3, 'users',         'create',    TRUE),
  (3, 'users',         'edit',      TRUE),
  (3, 'reports',       'view',      TRUE),
  (3, 'notifications', 'view',      TRUE),
  (3, 'settings',      'view',      TRUE),
  (3, 'buildings',     'view',      TRUE),
  (3, 'buildings',     'create',    TRUE),
  (3, 'buildings',     'edit',      TRUE),
  (3, 'floors',        'view',      TRUE),
  (3, 'floors',        'create',    TRUE),
  (3, 'floors',        'edit',      TRUE),
  (3, 'rooms',         'view',      TRUE),
  (3, 'rooms',         'create',    TRUE),
  (3, 'rooms',         'edit',      TRUE),
  (3, 'devices',       'view',      TRUE),
  (3, 'devices',       'create',    TRUE),
  (3, 'devices',       'edit',      TRUE),
  (3, 'devices',       'configure', TRUE),
  (3, 'automation',    'view',      TRUE),
  (3, 'automation',    'manage',    TRUE),
  (3, 'scenes',        'view',      TRUE),
  (3, 'scenes',        'manage',    TRUE),
  (3, 'scenes',        'activate',  TRUE),
  (3, 'scheduling',    'view',      TRUE),
  (3, 'scheduling',    'manage',    TRUE),
  (3, 'mqtt',          'view',      TRUE),
  (3, 'mqtt',          'manage',    TRUE),
  (3, 'layout',        'view',      TRUE),
  (3, 'layout',        'manage',    TRUE),
  (3, 'roles',         'view',      TRUE),
  (3, 'roles',         'manage',    TRUE),
  (3, 'members',       'view',      TRUE),
  (3, 'members',       'create',    TRUE),
  (3, 'members',       'edit',      TRUE),
  (3, 'members',       'delete',    TRUE);

-- Programmer (role_id = 4) — same as si without si management permissions
INSERT INTO role_permissions (role_id, feature, action, is_allowed) VALUES
  (4, 'dashboard',     'view',      TRUE),
  (4, 'projects',      'view',      TRUE),
  (4, 'projects',      'configure', TRUE),
  (4, 'pm',            'view',      TRUE),
  (4, 'users',         'view',      TRUE),
  (4, 'users',         'create',    TRUE),
  (4, 'users',         'edit',      TRUE),
  (4, 'reports',       'view',      TRUE),
  (4, 'notifications', 'view',      TRUE),
  (4, 'settings',      'view',      TRUE),
  (4, 'buildings',     'view',      TRUE),
  (4, 'buildings',     'create',    TRUE),
  (4, 'buildings',     'edit',      TRUE),
  (4, 'floors',        'view',      TRUE),
  (4, 'floors',        'create',    TRUE),
  (4, 'floors',        'edit',      TRUE),
  (4, 'rooms',         'view',      TRUE),
  (4, 'rooms',         'create',    TRUE),
  (4, 'rooms',         'edit',      TRUE),
  (4, 'devices',       'view',      TRUE),
  (4, 'devices',       'create',    TRUE),
  (4, 'devices',       'edit',      TRUE),
  (4, 'devices',       'configure', TRUE),
  (4, 'automation',    'view',      TRUE),
  (4, 'automation',    'manage',    TRUE),
  (4, 'scenes',        'view',      TRUE),
  (4, 'scenes',        'manage',    TRUE),
  (4, 'scenes',        'activate',  TRUE),
  (4, 'scheduling',    'view',      TRUE),
  (4, 'scheduling',    'manage',    TRUE),
  (4, 'mqtt',          'view',      TRUE),
  (4, 'mqtt',          'manage',    TRUE),
  (4, 'layout',        'view',      TRUE),
  (4, 'layout',        'manage',    TRUE),
  (4, 'roles',         'view',      TRUE),
  (4, 'members',       'view',      TRUE),
  (4, 'members',       'create',    TRUE),
  (4, 'members',       'edit',      TRUE),
  (4, 'members',       'delete',    TRUE);

-- Distributor user  (login: sumit@vyom.ai via OTP)
INSERT INTO app_users (id, organization_id, email, full_name)
VALUES (1, 1, 'rajat@vyom.ai', 'Rajat')
ON DUPLICATE KEY UPDATE email = 'rajat@vyom.ai', full_name = 'Rajat';

-- Link user to distributor role
INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
VALUES (1, 1, 1);

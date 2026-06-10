-- Dev seed data for okas-cloud-backend local testing
-- Run once after loading schema.sql:
--   mysql -h 127.0.0.1 -P 3307 -u okasdev -p okascloud < db/seed.sql

USE okascloud;

-- Default organization
INSERT IGNORE INTO organizations (id, name, slug, email, phone)
VALUES (1, 'OKAS Systems', 'okas-systems', 'admin@okas.ai', '+91-9999999999');

-- Two app users (project managers / SI staff)
INSERT IGNORE INTO app_users (id, organization_id, email, full_name)
VALUES
  (1, 1, 'preeti.chauhan@okas.ai', 'Preeti Chauhan'),
  (2, 1, 'rahul.kumar@okas.ai',    'Rahul Kumar');

-- Two homeowners (property owners / primary contacts)
INSERT IGNORE INTO homeowners (id, full_name, email, phone)
VALUES
  (1, 'Manoj Agarwal', 'manoj.agarwal@example.com', '+91-9812345678'),
  (2, 'Shiv Bhansali',  'shiv.bhansali@example.com',  '+91-9823456789');

-- Two sample projects
INSERT IGNORE INTO projects
  (id, organization_id, project_manager_id, name, serial_number, project_type, address, city, installed_at)
VALUES
  (1, 1, 1, 'Manoj Agarwal - Shree KLG', '202036', 'residential', 'Hn 25, Shree KLG Farms, Sector 12', 'Delhi',   '2025-02-23 02:25:26'),
  (2, 1, 1, 'Shiv Bhansali - Okhla',     '202036', 'residential', 'D-102, Okhla Phase 2, New Delhi',   'Delhi',   '2025-02-23 02:25:26');

-- Link homeowners as primary contacts
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

-- Distributor user  (login: superadmin@mail.com)
INSERT IGNORE INTO app_users (id, organization_id, email, full_name)
VALUES (3, 2, 'superadmin@mail.com', 'Super Admin');

-- Link user to distributor role
INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
VALUES (3, 1, 2);

-- Dev session token — hardcoded for easy testing
-- Use in requests: Authorization: Bearer dist-dev-token-001
INSERT IGNORE INTO app_sessions (user_id, token_hash, expires_at)
VALUES (3, 'dist-dev-token-001', '2030-01-01 00:00:00.000');

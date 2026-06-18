"""Seed default roles: distributor, si, Master Programmer, Programmer

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-18
"""
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET FOREIGN_KEY_CHECKS=0")

    # Insert 4 system-wide roles (organization_id = NULL means global)
    op.execute("""
        INSERT IGNORE INTO roles (id, name, description, organization_id) VALUES
          (1, 'distributor',       'Distributor admin — manages SIs, PMs, projects and members under their org', NULL),
          (2, 'si',                'System Integrator — manages buildings, devices, automation and members under their org', NULL),
          (3, 'Master Programmer', 'Full SI-level access — all modules and permissions', NULL),
          (4, 'Programmer',        'SI-level access without SI management permissions', NULL)
    """)

    # # Clear and reinsert permissions (idempotent)
    # op.execute("DELETE FROM role_permissions WHERE role_id IN (1, 2, 3, 4)")

    # distributor (role_id = 1)
    op.execute("""
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
          (1, 'members',       'delete',  TRUE)
    """)

    # si (role_id = 2)
    op.execute("""
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
          (2, 'members',       'delete',    TRUE)
    """)

    # Master Programmer (role_id = 3) — identical to si
    op.execute("""
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
          (3, 'members',       'delete',    TRUE)
    """)

    # Programmer (role_id = 4) — si permissions minus roles/manage
    op.execute("""
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
          (4, 'members',       'delete',    TRUE)
    """)

    # Distributor organization
    op.execute("""
        INSERT IGNORE INTO organizations (id, name, slug, email, phone, parent_organization_id, org_type)
        VALUES (1, 'OKAS Systems', 'okas-systems', 'rajat@vyom.ai', '+91-9999999999', 1, 'distributor')
    """)

    # Distributor admin user
    op.execute("""
        INSERT INTO app_users (id, organization_id, email, full_name)
        VALUES (1, 1, 'rajat@vyom.ai', 'Rajat')
        ON DUPLICATE KEY UPDATE email = 'rajat@vyom.ai', full_name = 'Rajat'
    """)

    # Assign distributor role to the admin user
    op.execute("""
        INSERT IGNORE INTO app_user_roles (user_id, role_id, organization_id)
        VALUES (1, 1, 1)
    """)

    op.execute("SET FOREIGN_KEY_CHECKS=1")


def downgrade() -> None:
    op.execute("DELETE FROM app_user_roles WHERE user_id = 1 AND role_id = 1 AND organization_id = 1")
    op.execute("DELETE FROM app_users WHERE id = 1")
    op.execute("DELETE FROM organizations WHERE id = 1")
    op.execute("DELETE FROM role_permissions WHERE role_id IN (1, 2, 3, 4)")
    op.execute("DELETE FROM roles WHERE id IN (1, 2, 3, 4)")

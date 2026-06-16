-- 1. Insert distributor role
INSERT INTO roles (id, name, description)
VALUES (1, 'distributor', 'Distributor admin — manages SIs, PMs, projects and members under their org');

-- 2. Distributor permissions (matches frontend ROLES.DISTRIBUTOR permission set)
INSERT INTO role_permissions (role_id, feature, action, is_allowed) VALUES
  (1, 'dashboard',     'view',      TRUE),
  (1, 'projects',      'view',      TRUE),
  (1, 'projects',      'create',    TRUE),
  (1, 'projects',      'edit',      TRUE),
  (1, 'si',            'view',      TRUE),
  (1, 'si',            'create',    TRUE),
  (1, 'si',            'edit',      TRUE),
  (1, 'pm',            'view',      TRUE),
  (1, 'pm',            'create',    TRUE),
  (1, 'pm',            'edit',      TRUE),
  (1, 'users',         'view',      TRUE),
  (1, 'users',         'create',    TRUE),
  (1, 'users',         'edit',      TRUE),
  (1, 'organizations', 'view',      TRUE),
  (1, 'reports',       'view',      TRUE),
  (1, 'notifications', 'view',      TRUE),
  (1, 'settings',      'view',      TRUE),
  (1, 'buildings',     'view',      TRUE),
  (1, 'floors',        'view',      TRUE),
  (1, 'rooms',         'view',      TRUE),
  (1, 'devices',       'view',      TRUE),
  (1, 'roles',         'view',      TRUE),
  (1, 'roles',         'manage',    TRUE),
  (1, 'members',       'view',      TRUE),
  (1, 'members',       'create',    TRUE),
  (1, 'members',       'edit',      TRUE),
  (1, 'members',       'delete',    TRUE);

-- 3. Assign distributor role to user 1 in org 1
INSERT INTO app_user_roles (user_id, role_id, organization_id)
VALUES (1, 1, 1);

-- 4. Insert SI role
INSERT INTO roles (id, name, description)
VALUES (2, 'si', 'System Integrator admin — manages buildings, devices, automation and members under their org');

-- 5. SI permissions (matches frontend ROLES.SYSTEM_INTEGRATOR permission set)
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

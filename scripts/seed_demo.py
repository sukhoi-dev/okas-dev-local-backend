"""
Seed script — idempotent.  Run once (or re-run to reset passwords).

Usage:
    python scripts/seed_demo.py

Creates:
  Organisations
    - OKAS Platform   (platform-level, for super admins)
    - OKAS Demo Systems (demo SI organisation)

  Roles
    - Super Admin     -> organizations.manage + full access
    - Admin           -> full SI access (no org management)
    - Project Manager -> limited SI access
    - Viewer          -> read-only SI access

  Users (see test_users.json for the full table)
    superadmin@mail.com   / SuperAdmin@123   Super Admin  (Platform org)
    admin@okas-demo.com   / Admin@123        Admin        (Demo SI org)
    pm@okas-demo.com      / PM@123           Project Manager (Demo SI org)
    viewer@okas-demo.com  / Viewer@123       Viewer       (Demo SI org)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import pymysql
import pymysql.cursors
import bcrypt

_DB = {
    "host":        os.getenv("DB_HOST", "127.0.0.1"),
    "port":        int(os.getenv("DB_PORT", "3307")),
    "user":        os.getenv("DB_USER", "okasdev"),
    "password":    os.getenv("DB_PASSWORD", ""),
    "database":    os.getenv("DB_NAME", "okascloud"),
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "autocommit":  False,
}

# ── Organisations ─────────────────────────────────────────────────────────────

ORGS = {
    "okas-platform": {
        "name":  "OKAS Platform",
        "email": "platform@okas.ai",
        "phone": "+91-9000000001",
    },
    "okas-demo": {
        "name":  "OKAS Demo Systems",
        "email": "info@okas-demo.com",
        "phone": "+91-9000000000",
    },
}

# ── Roles & permissions ───────────────────────────────────────────────────────
# format: role_name -> { "feature.action": is_allowed }

ROLES = {
    "Super Admin": {
        "organizations.manage": True,
        "members.view":         True,
        "members.create":       True,
        "members.edit":         True,
        "members.delete":       True,
        "projects.view":        True,
        "projects.create":      True,
        "design_studio.access": True,
    },
    "Admin": {
        "organizations.manage": False,
        "members.view":         True,
        "members.create":       True,
        "members.edit":         True,
        "members.delete":       True,
        "projects.view":        True,
        "projects.create":      True,
        "design_studio.access": True,
    },
    "Project Manager": {
        "organizations.manage": False,
        "members.view":         True,
        "members.create":       False,
        "members.edit":         False,
        "members.delete":       False,
        "projects.view":        True,
        "projects.create":      True,
        "design_studio.access": True,
    },
    "Viewer": {
        "organizations.manage": False,
        "members.view":         True,
        "members.create":       False,
        "members.edit":         False,
        "members.delete":       False,
        "projects.view":        True,
        "projects.create":      False,
        "design_studio.access": False,
    },
}

# ── Users to seed ─────────────────────────────────────────────────────────────

USERS = [
    {
        "email":     "superadmin@mail.com",
        "password":  "SuperAdmin@123",
        "full_name": "Platform Super Admin",
        "org_slug":  "okas-platform",
        "role_name": "Super Admin",
    },
    {
        "email":     "admin@okas-demo.com",
        "password":  "Admin@123",
        "full_name": "Demo Admin",
        "org_slug":  "okas-demo",
        "role_name": "Admin",
    },
    {
        "email":     "pm@okas-demo.com",
        "password":  "PM@123",
        "full_name": "Demo Project Manager",
        "org_slug":  "okas-demo",
        "role_name": "Project Manager",
    },
    {
        "email":     "viewer@okas-demo.com",
        "password":  "Viewer@123",
        "full_name": "Demo Viewer",
        "org_slug":  "okas-demo",
        "role_name": "Viewer",
    },
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _upsert_org(cur, slug, data):
    cur.execute("SELECT id FROM organizations WHERE slug = %s", (slug,))
    row = cur.fetchone()
    if row:
        print(f"  org exists    '{data['name']}'  id={row['id']}")
        return row["id"]
    cur.execute(
        "INSERT INTO organizations (name, slug, email, phone) VALUES (%s,%s,%s,%s)",
        (data["name"], slug, data["email"], data["phone"]),
    )
    oid = cur.lastrowid
    print(f"  org created   '{data['name']}'  id={oid}")
    return oid


def _upsert_roles(cur):
    role_ids = {}
    for name in ROLES:
        cur.execute("SELECT id FROM roles WHERE name = %s", (name,))
        row = cur.fetchone()
        if row:
            role_ids[name] = row["id"]
            print(f"  role exists   '{name}'  id={row['id']}")
        else:
            cur.execute("INSERT INTO roles (name) VALUES (%s)", (name,))
            role_ids[name] = cur.lastrowid
            print(f"  role created  '{name}'  id={role_ids[name]}")
    return role_ids


def _upsert_permissions(cur, role_ids):
    for role_name, perms in ROLES.items():
        rid = role_ids[role_name]
        for key, allowed in perms.items():
            feature, action = key.split(".", 1)
            cur.execute(
                "SELECT id FROM role_permissions WHERE role_id=%s AND feature=%s AND action=%s",
                (rid, feature, action),
            )
            existing = cur.fetchone()
            if existing:
                cur.execute(
                    "UPDATE role_permissions SET is_allowed=%s WHERE id=%s",
                    (allowed, existing["id"]),
                )
            else:
                cur.execute(
                    "INSERT INTO role_permissions (role_id,feature,action,is_allowed) VALUES (%s,%s,%s,%s)",
                    (rid, feature, action, allowed),
                )
    print(f"  permissions seeded for {len(ROLES)} roles")


def _upsert_user(cur, u, org_ids, role_ids):
    email     = u["email"]
    org_id    = org_ids[u["org_slug"]]
    role_id   = role_ids[u["role_name"]]
    pw_hash   = bcrypt.hashpw(u["password"].encode(), bcrypt.gensalt(rounds=12)).decode()

    cur.execute("SELECT id FROM app_users WHERE email = %s", (email,))
    row = cur.fetchone()
    if row:
        uid = row["id"]
        cur.execute(
            "UPDATE app_users SET password_hash=%s WHERE id=%s",
            (pw_hash, uid),
        )
        print(f"  user exists   '{email}'  id={uid}  (password refreshed)")
    else:
        cur.execute(
            """
            INSERT INTO app_users (organization_id, email, full_name, password_hash, active_ind)
            VALUES (%s,%s,%s,%s,TRUE)
            """,
            (org_id, email, u["full_name"], pw_hash),
        )
        uid = cur.lastrowid
        print(f"  user created  '{email}'  id={uid}")

    # Ensure exactly one role assignment
    cur.execute(
        "SELECT id FROM app_user_roles WHERE user_id=%s AND organization_id=%s",
        (uid, org_id),
    )
    if not cur.fetchone():
        cur.execute(
            "INSERT INTO app_user_roles (user_id,role_id,organization_id) VALUES (%s,%s,%s)",
            (uid, role_id, org_id),
        )
        print(f"    -> assigned '{u['role_name']}'")
    else:
        cur.execute(
            "UPDATE app_user_roles SET role_id=%s WHERE user_id=%s AND organization_id=%s",
            (role_id, uid, org_id),
        )
        print(f"    -> role confirmed '{u['role_name']}'")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("\n=== OKAS Demo Seed ===\n")
    conn = pymysql.connect(**_DB)
    try:
        with conn.cursor() as cur:
            print("[1] Organisations")
            org_ids = {slug: _upsert_org(cur, slug, data) for slug, data in ORGS.items()}

            print("\n[2] Roles")
            role_ids = _upsert_roles(cur)

            print("\n[3] Permissions")
            _upsert_permissions(cur, role_ids)

            print("\n[4] Users")
            for u in USERS:
                _upsert_user(cur, u, org_ids, role_ids)

        conn.commit()
        print("\n[OK] Seed complete\n")
        print("  Credentials (also in test_users.json)")
        print("  -------------------------------------------------------")
        for u in USERS:
            print(f"  {u['email']:<30}  {u['password']:<18}  {u['role_name']}")
        print()

    except Exception as exc:
        conn.rollback()
        print(f"\n[ERR] Seed failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()

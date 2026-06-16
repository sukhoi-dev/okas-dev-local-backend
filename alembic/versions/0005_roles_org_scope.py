"""Add organization_id to roles for org-scoped custom roles

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("SET FOREIGN_KEY_CHECKS=0")

    # Add organization_id — NULL means system-wide role (distributor, si, etc.)
    op.execute("""
        ALTER TABLE roles
        ADD COLUMN organization_id BIGINT UNSIGNED NULL
            REFERENCES organizations(id)
    """)

    # Drop old global-unique name constraint and add per-org unique constraint
    op.execute("ALTER TABLE roles DROP INDEX uq_role_name")
    op.execute("""
        ALTER TABLE roles
        ADD UNIQUE KEY uq_role_name_org (name, organization_id)
    """)

    op.execute("SET FOREIGN_KEY_CHECKS=1")


def downgrade() -> None:
    op.execute("ALTER TABLE roles DROP INDEX uq_role_name_org")
    op.execute("ALTER TABLE roles ADD UNIQUE KEY uq_role_name (name)")
    op.execute("ALTER TABLE roles DROP COLUMN organization_id")

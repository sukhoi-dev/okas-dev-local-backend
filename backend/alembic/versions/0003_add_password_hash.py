"""add password_hash to app_users

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-05
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE app_users ADD COLUMN password_hash VARCHAR(255) AFTER google_id"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE app_users DROP COLUMN password_hash"
    )

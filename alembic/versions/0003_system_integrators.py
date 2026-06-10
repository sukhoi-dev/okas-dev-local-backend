"""add system_integrators table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-05
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _exec(sql: str) -> None:
    op.execute(sql.strip())


def upgrade() -> None:
    _exec("""
    CREATE TABLE system_integrators (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        distributor_id  BIGINT UNSIGNED NOT NULL,
        organization_id BIGINT UNSIGNED NOT NULL,
        name            VARCHAR(255)    NOT NULL,
        gst             VARCHAR(50),
        status          ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
        is_archived     BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_si_distributor  FOREIGN KEY (distributor_id)  REFERENCES organizations (id),
        CONSTRAINT fk_si_organization FOREIGN KEY (organization_id) REFERENCES organizations (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)


def downgrade() -> None:
    _exec("DROP TABLE IF EXISTS system_integrators")

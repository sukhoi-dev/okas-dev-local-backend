"""update organizations — add org_type, parent, contact_name, gst_vat_number, is_archived; drop system_integrators

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-09
"""
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _exec(sql: str) -> None:
    op.execute(sql.strip())


def upgrade() -> None:
    _exec("SET FOREIGN_KEY_CHECKS=0")

    _exec("""
    ALTER TABLE organizations
      ADD COLUMN org_type                ENUM('distributor', 'si') NOT NULL DEFAULT 'si'   AFTER id,
      ADD COLUMN parent_organization_id  BIGINT UNSIGNED                                    AFTER org_type,
      ADD COLUMN contact_name            VARCHAR(255)                                       AFTER name,
      ADD COLUMN gst_vat_number          VARCHAR(50)                                        AFTER address,
      ADD COLUMN is_archived             BOOLEAN NOT NULL DEFAULT FALSE                     AFTER active_ind
    """)

    _exec("""
    ALTER TABLE organizations
      ADD CONSTRAINT fk_org_parent
        FOREIGN KEY (parent_organization_id) REFERENCES organizations (id) ON DELETE RESTRICT
    """)

    _exec("DROP TABLE IF EXISTS system_integrators")

    _exec("SET FOREIGN_KEY_CHECKS=1")


def downgrade() -> None:
    _exec("SET FOREIGN_KEY_CHECKS=0")

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

    _exec("ALTER TABLE organizations DROP FOREIGN KEY fk_org_parent")

    _exec("""
    ALTER TABLE organizations
      DROP COLUMN is_archived,
      DROP COLUMN gst_vat_number,
      DROP COLUMN contact_name,
      DROP COLUMN parent_organization_id,
      DROP COLUMN org_type
    """)

    _exec("SET FOREIGN_KEY_CHECKS=1")

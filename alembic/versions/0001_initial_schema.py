"""initial schema — all 93 tables, 60 triggers, 16 views

Revision ID: 0001
Revises:
Create Date: 2026-06-02
"""
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _exec(sql: str) -> None:
    op.execute(sql.strip())


# ---------------------------------------------------------------------------
# upgrade
# ---------------------------------------------------------------------------
def upgrade() -> None:
    _exec("SET FOREIGN_KEY_CHECKS=0")

    # ── 1. AUTH & USERS ──────────────────────────────────────────────────
    _exec("""
    CREATE TABLE organizations (
        id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name        VARCHAR(255)    NOT NULL,
        slug        VARCHAR(100)    NOT NULL,
        email       VARCHAR(255),
        phone       VARCHAR(50),
        address     TEXT,
        logo_url    VARCHAR(500),
        active_ind  BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by  BIGINT UNSIGNED,
        created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_org_slug (slug),
        CONSTRAINT fk_org_updated_by FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE organization_locations (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        organization_id BIGINT UNSIGNED NOT NULL,
        name            VARCHAR(150)    NOT NULL,
        location_type   ENUM('head_office','branch','warehouse','site') NOT NULL,
        address         TEXT,
        city            VARCHAR(100),
        state           VARCHAR(100),
        country         VARCHAR(100),
        pincode         VARCHAR(20),
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_orgloc_org    FOREIGN KEY (organization_id) REFERENCES organizations (id),
        CONSTRAINT fk_orgloc_upd_by FOREIGN KEY (updated_by)      REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE app_users (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        organization_id BIGINT UNSIGNED NOT NULL,
        location_id     BIGINT UNSIGNED,
        email           VARCHAR(255)    NOT NULL,
        phone           VARCHAR(50),
        full_name       VARCHAR(255),
        avatar_url      VARCHAR(500),
        google_id       VARCHAR(255),
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        last_login_at   DATETIME(3),
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_user_email     (email),
        UNIQUE KEY uq_user_google_id (google_id),
        CONSTRAINT fk_user_org      FOREIGN KEY (organization_id) REFERENCES organizations         (id),
        CONSTRAINT fk_user_loc      FOREIGN KEY (location_id)     REFERENCES organization_locations (id),
        CONSTRAINT fk_user_upd_by   FOREIGN KEY (updated_by)      REFERENCES app_users             (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE roles (
        id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name        VARCHAR(50)     NOT NULL,
        description TEXT,
        created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_role_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE app_user_roles (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id         BIGINT UNSIGNED NOT NULL,
        role_id         BIGINT UNSIGNED NOT NULL,
        organization_id BIGINT UNSIGNED NOT NULL,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_aur_user FOREIGN KEY (user_id)         REFERENCES app_users    (id),
        CONSTRAINT fk_aur_role FOREIGN KEY (role_id)         REFERENCES roles         (id),
        CONSTRAINT fk_aur_org  FOREIGN KEY (organization_id) REFERENCES organizations (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE app_otp_codes (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        phone_or_email VARCHAR(255)    NOT NULL,
        code_hash      VARCHAR(255)    NOT NULL,
        purpose        ENUM('login','password_reset','verify_email') NOT NULL,
        expires_at     DATETIME(3)     NOT NULL,
        used_at        DATETIME(3),
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE app_sessions (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id        BIGINT UNSIGNED NOT NULL,
        token_hash     VARCHAR(255)    NOT NULL,
        device_info    JSON,
        ip_address     VARCHAR(45),
        expires_at     DATETIME(3)     NOT NULL,
        last_active_at DATETIME(3),
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_session_token (token_hash),
        CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE role_permissions (
        id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        role_id    BIGINT UNSIGNED NOT NULL,
        feature    VARCHAR(50)     NOT NULL,
        action     VARCHAR(20)     NOT NULL,
        is_allowed BOOLEAN         NOT NULL DEFAULT FALSE,
        created_at DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_rp_role FOREIGN KEY (role_id) REFERENCES roles (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE homeowners (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        email           VARCHAR(255)    NOT NULL,
        phone           VARCHAR(50),
        full_name       VARCHAR(255),
        avatar_url      VARCHAR(500),
        google_id       VARCHAR(255),
        preferred_login ENUM('google','otp') NOT NULL DEFAULT 'otp',
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        last_login_at   DATETIME(3),
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ho_email     (email),
        UNIQUE KEY uq_ho_google_id (google_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE homeowner_otp_codes (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        homeowner_id BIGINT UNSIGNED,
        email        VARCHAR(255),
        phone        VARCHAR(50),
        otp_hash     VARCHAR(255)    NOT NULL,
        channel      ENUM('email','sms') NOT NULL,
        purpose      ENUM('login','phone_verify') NOT NULL,
        expires_at   DATETIME(3)     NOT NULL,
        used_at      DATETIME(3),
        created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ho_otp_owner FOREIGN KEY (homeowner_id) REFERENCES homeowners (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE homeowner_sessions (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        homeowner_id BIGINT UNSIGNED NOT NULL,
        token_hash   VARCHAR(255)    NOT NULL,
        device_name  VARCHAR(255),
        device_type  ENUM('mobile','browser','unknown') NOT NULL DEFAULT 'unknown',
        ip_address   VARCHAR(45),
        user_agent   TEXT,
        expires_at   DATETIME(3)     NOT NULL,
        revoked_at   DATETIME(3),
        created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ho_session_token (token_hash),
        CONSTRAINT fk_ho_session_owner FOREIGN KEY (homeowner_id) REFERENCES homeowners (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 2. PROJECTS ──────────────────────────────────────────────────────
    _exec("""
    CREATE TABLE subscription_plans (
        id            BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
        name          VARCHAR(100)     NOT NULL,
        description   TEXT,
        price_monthly DECIMAL(10,2),
        price_yearly  DECIMAL(10,2),
        features      JSON,
        active_ind    BOOLEAN          NOT NULL DEFAULT TRUE,
        created_at    DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_plan_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE projects (
        id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        organization_id    BIGINT UNSIGNED NOT NULL,
        project_manager_id BIGINT UNSIGNED,
        location_id        BIGINT UNSIGNED,
        name               VARCHAR(255)    NOT NULL,
        serial_number      VARCHAR(100),
        project_type       ENUM('residential','commercial','hospitality','retail','other') NOT NULL,
        status             ENUM('active','inactive','under_maintenance','completed') NOT NULL DEFAULT 'active',
        installed_at       DATETIME(3),
        address            TEXT,
        city               VARCHAR(100),
        state              VARCHAR(100),
        country            VARCHAR(100),
        pincode            VARCHAR(20),
        notes              TEXT,
        metadata           JSON,
        active_ind         BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by         BIGINT UNSIGNED,
        created_at         DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at         DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_project_serial (serial_number),
        CONSTRAINT fk_proj_org  FOREIGN KEY (organization_id)    REFERENCES organizations         (id),
        CONSTRAINT fk_proj_pm   FOREIGN KEY (project_manager_id) REFERENCES app_users             (id),
        CONSTRAINT fk_proj_loc  FOREIGN KEY (location_id)        REFERENCES organization_locations (id),
        CONSTRAINT fk_proj_upd  FOREIGN KEY (updated_by)         REFERENCES app_users             (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE project_owners (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id   BIGINT UNSIGNED NOT NULL,
        homeowner_id BIGINT UNSIGNED NOT NULL,
        is_primary   BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind   BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_po_proj FOREIGN KEY (project_id)   REFERENCES projects   (id),
        CONSTRAINT fk_po_ho   FOREIGN KEY (homeowner_id) REFERENCES homeowners (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE project_members (
        id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id  BIGINT UNSIGNED NOT NULL,
        user_id     BIGINT UNSIGNED NOT NULL,
        role_id     BIGINT UNSIGNED NOT NULL,
        assigned_by BIGINT UNSIGNED,
        active_ind  BOOLEAN         NOT NULL DEFAULT TRUE,
        assigned_at DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_pm_proj FOREIGN KEY (project_id)  REFERENCES projects   (id),
        CONSTRAINT fk_pm_user FOREIGN KEY (user_id)     REFERENCES app_users  (id),
        CONSTRAINT fk_pm_role FOREIGN KEY (role_id)     REFERENCES roles      (id),
        CONSTRAINT fk_pm_assc FOREIGN KEY (assigned_by) REFERENCES app_users  (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE project_manager_history (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id    BIGINT UNSIGNED NOT NULL,
        user_id       BIGINT UNSIGNED NOT NULL,
        assigned_by   BIGINT UNSIGNED,
        assigned_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        unassigned_at DATETIME(3),
        reason        VARCHAR(255),
        PRIMARY KEY (id),
        KEY idx_pmh_current (project_id, unassigned_at),
        CONSTRAINT fk_pmh_proj FOREIGN KEY (project_id)  REFERENCES projects  (id),
        CONSTRAINT fk_pmh_user FOREIGN KEY (user_id)     REFERENCES app_users (id),
        CONSTRAINT fk_pmh_assc FOREIGN KEY (assigned_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE project_subscriptions (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id    BIGINT UNSIGNED NOT NULL,
        plan_id       BIGINT UNSIGNED NOT NULL,
        status        ENUM('trial','active','expired','cancelled') NOT NULL,
        billing_cycle ENUM('monthly','yearly')                     NOT NULL,
        started_at    DATETIME(3),
        expires_at    DATETIME(3),
        updated_by    BIGINT UNSIGNED,
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ps_proj FOREIGN KEY (project_id) REFERENCES projects           (id),
        CONSTRAINT fk_ps_plan FOREIGN KEY (plan_id)    REFERENCES subscription_plans (id),
        CONSTRAINT fk_ps_upd  FOREIGN KEY (updated_by) REFERENCES app_users          (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 3. LOCATION HIERARCHY ─────────────────────────────────────────────
    _exec("""
    CREATE TABLE floors (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id     BIGINT UNSIGNED NOT NULL,
        name           VARCHAR(100)    NOT NULL,
        short_code     VARCHAR(20),
        floor_number   INT             NOT NULL DEFAULT 0,
        floor_plan_url VARCHAR(500),
        display_order  INT             NOT NULL DEFAULT 0,
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_floor_proj FOREIGN KEY (project_id) REFERENCES projects  (id),
        CONSTRAINT fk_floor_upd  FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE zones (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id     BIGINT UNSIGNED NOT NULL,
        parent_zone_id BIGINT UNSIGNED,
        name           VARCHAR(100)    NOT NULL,
        zone_type      ENUM('zone','sub_zone') NOT NULL DEFAULT 'zone',
        display_order  INT             NOT NULL DEFAULT 0,
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_zone_proj   FOREIGN KEY (project_id)     REFERENCES projects  (id),
        CONSTRAINT fk_zone_parent FOREIGN KEY (parent_zone_id) REFERENCES zones     (id),
        CONSTRAINT fk_zone_upd    FOREIGN KEY (updated_by)     REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE rooms (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        floor_id      BIGINT UNSIGNED NOT NULL,
        zone_id       BIGINT UNSIGNED,
        name          VARCHAR(100)    NOT NULL,
        room_type     ENUM('living_room','bedroom','kitchen','bathroom','dining_room',
                           'study','garage','utility','outdoor','other') NOT NULL DEFAULT 'other',
        image_url     VARCHAR(500),
        area_sqft     DECIMAL(8,2),
        display_order INT             NOT NULL DEFAULT 0,
        active_ind    BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by    BIGINT UNSIGNED,
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_room_floor FOREIGN KEY (floor_id)  REFERENCES floors    (id),
        CONSTRAINT fk_room_zone  FOREIGN KEY (zone_id)   REFERENCES zones     (id),
        CONSTRAINT fk_room_upd   FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 4. CONTROLLERS & PLATFORMS ─────────────────────────────────────
    _exec("""
    CREATE TABLE device_types (
        id                       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name                     VARCHAR(100)    NOT NULL,
        category                 VARCHAR(50)     NOT NULL,
        icon                     VARCHAR(100),
        description_text         VARCHAR(500),
        alexa_display_categories JSON,
        google_home_device_types JSON,
        homekit_category         VARCHAR(50),
        ui_control_widget        VARCHAR(50),
        active_ind               BOOLEAN         NOT NULL DEFAULT TRUE,
        display_order            INT             NOT NULL DEFAULT 0,
        PRIMARY KEY (id),
        UNIQUE KEY uq_dtype_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE firmware_releases (
        id                         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        target_type                ENUM('controller','device') NOT NULL,
        device_type_id             BIGINT UNSIGNED,
        version                    VARCHAR(50)     NOT NULL,
        release_channel            ENUM('stable','beta','rc') NOT NULL DEFAULT 'stable',
        release_notes              TEXT,
        s3_bucket                  VARCHAR(255),
        s3_key                     VARCHAR(1000),
        checksum_sha256            VARCHAR(64),
        file_size_bytes            BIGINT UNSIGNED,
        min_supported_from_version VARCHAR(50),
        active_ind                 BOOLEAN         NOT NULL DEFAULT TRUE,
        is_published               BOOLEAN         NOT NULL DEFAULT FALSE,
        released_at                DATETIME(3),
        released_by                BIGINT UNSIGNED,
        updated_by                 BIGINT UNSIGNED,
        created_at                 DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at                 DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_fw_dtype      FOREIGN KEY (device_type_id) REFERENCES device_types (id),
        CONSTRAINT fk_fw_rel_by     FOREIGN KEY (released_by)    REFERENCES app_users    (id),
        CONSTRAINT fk_fw_upd_by     FOREIGN KEY (updated_by)     REFERENCES app_users    (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE controllers (
        id                        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id                BIGINT UNSIGNED NOT NULL,
        serial_number             VARCHAR(100)    NOT NULL,
        model                     VARCHAR(100)    DEFAULT 'OKAS Signature',
        firmware_version          VARCHAR(50),
        firmware_release_id       BIGINT UNSIGNED,
        firmware_update_available BOOLEAN         NOT NULL DEFAULT FALSE,
        ip_address                VARCHAR(45),
        mac_address               VARCHAR(17),
        status                    ENUM('online','offline','maintenance') NOT NULL DEFAULT 'offline',
        last_seen_at              DATETIME(3),
        config                    JSON,
        active_ind                BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by                BIGINT UNSIGNED,
        created_at                DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at                DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ctrl_serial (serial_number),
        CONSTRAINT fk_ctrl_proj FOREIGN KEY (project_id)          REFERENCES projects          (id),
        CONSTRAINT fk_ctrl_fw   FOREIGN KEY (firmware_release_id) REFERENCES firmware_releases (id),
        CONSTRAINT fk_ctrl_upd  FOREIGN KEY (updated_by)          REFERENCES app_users         (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE bus_settings (
        id                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        controller_id      BIGINT UNSIGNED NOT NULL,
        bus_type           ENUM('KNX_IP','KNX_TP','Lutron','Casambi','Modbus','BACnet') NOT NULL,
        ip_address         VARCHAR(45),
        port               INT,
        individual_address VARCHAR(20),
        extra_config       JSON,
        active_ind         BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by         BIGINT UNSIGNED,
        created_at         DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at         DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_bs_ctrl FOREIGN KEY (controller_id) REFERENCES controllers (id),
        CONSTRAINT fk_bs_upd  FOREIGN KEY (updated_by)    REFERENCES app_users   (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_platforms (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id     BIGINT UNSIGNED NOT NULL,
        controller_id  BIGINT UNSIGNED NOT NULL,
        platform_type  ENUM('KNX','Lutron','Casambi','Modbus','BACnet','WiFi','Zigbee','Other') NOT NULL,
        name           VARCHAR(100),
        ip_address     VARCHAR(45),
        port           INT,
        driver_version VARCHAR(50),
        config         JSON,
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_dp_proj FOREIGN KEY (project_id)    REFERENCES projects     (id),
        CONSTRAINT fk_dp_ctrl FOREIGN KEY (controller_id) REFERENCES controllers  (id),
        CONSTRAINT fk_dp_upd  FOREIGN KEY (updated_by)    REFERENCES app_users    (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 5. DEVICES & CAPABILITIES ─────────────────────────────────────
    _exec("""
    CREATE TABLE device_type_capability_templates (
        id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        device_type_id       BIGINT UNSIGNED NOT NULL,
        interface            VARCHAR(100)    NOT NULL,
        version              VARCHAR(10)     NOT NULL DEFAULT '3',
        instance             VARCHAR(100),
        is_required          BOOLEAN         NOT NULL DEFAULT TRUE,
        expected_properties  JSON,
        capability_resources JSON,
        configuration        JSON,
        display_order        INT             NOT NULL DEFAULT 0,
        active_ind           BOOLEAN         NOT NULL DEFAULT TRUE,
        PRIMARY KEY (id),
        CONSTRAINT fk_dtct_dtype FOREIGN KEY (device_type_id) REFERENCES device_types (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE devices (
        id                        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id                BIGINT UNSIGNED NOT NULL,
        device_type_id            BIGINT UNSIGNED NOT NULL,
        platform_id               BIGINT UNSIGNED,
        name                      VARCHAR(100)    NOT NULL,
        device_number             VARCHAR(50),
        icon                      VARCHAR(100),
        display_categories        JSON,
        endpoint_id               VARCHAR(255),
        cookie                    JSON,
        active_ind                BOOLEAN         NOT NULL DEFAULT TRUE,
        is_online                 BOOLEAN         NOT NULL DEFAULT FALSE,
        last_seen_at              DATETIME(3),
        firmware_version          VARCHAR(50),
        firmware_release_id       BIGINT UNSIGNED,
        firmware_update_available BOOLEAN         NOT NULL DEFAULT FALSE,
        updated_by                BIGINT UNSIGNED,
        created_at                DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at                DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_device_endpoint (endpoint_id),
        KEY idx_devices_project (project_id),
        CONSTRAINT fk_dev_proj  FOREIGN KEY (project_id)          REFERENCES projects          (id),
        CONSTRAINT fk_dev_dtype FOREIGN KEY (device_type_id)      REFERENCES device_types      (id),
        CONSTRAINT fk_dev_plat  FOREIGN KEY (platform_id)         REFERENCES device_platforms  (id),
        CONSTRAINT fk_dev_fw    FOREIGN KEY (firmware_release_id) REFERENCES firmware_releases (id),
        CONSTRAINT fk_dev_upd   FOREIGN KEY (updated_by)          REFERENCES app_users         (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_rooms (
        id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        device_id  BIGINT UNSIGNED NOT NULL,
        room_id    BIGINT UNSIGNED NOT NULL,
        is_primary BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_device_room (device_id, room_id),
        CONSTRAINT fk_dr_dev  FOREIGN KEY (device_id) REFERENCES devices (id),
        CONSTRAINT fk_dr_room FOREIGN KEY (room_id)   REFERENCES rooms   (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_capabilities (
        id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        device_id               BIGINT UNSIGNED NOT NULL,
        interface               VARCHAR(100)    NOT NULL,
        version                 VARCHAR(10)     NOT NULL DEFAULT '3',
        instance                VARCHAR(100),
        is_proactively_reported BOOLEAN         NOT NULL DEFAULT FALSE,
        is_retrievable          BOOLEAN         NOT NULL DEFAULT TRUE,
        capability_resources    JSON,
        configuration           JSON,
        active_ind              BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by              BIGINT UNSIGNED,
        created_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_device_interface_instance (device_id, interface, instance),
        CONSTRAINT fk_dc_dev FOREIGN KEY (device_id) REFERENCES devices   (id),
        CONSTRAINT fk_dc_upd FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_property_addresses (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        capability_id BIGINT UNSIGNED NOT NULL,
        property_name VARCHAR(100)    NOT NULL,
        address_role  ENUM('command','state_feedback') NOT NULL,
        protocol      ENUM('KNX','Lutron','Casambi','Modbus','BACnet','IP','IR') NOT NULL,
        address       VARCHAR(255)    NOT NULL,
        data_type     VARCHAR(50),
        scale_min     DECIMAL(10,4),
        scale_max     DECIMAL(10,4),
        invert        BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind    BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by    BIGINT UNSIGNED,
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_cap_property_role (capability_id, property_name, address_role),
        CONSTRAINT fk_dpa_cap FOREIGN KEY (capability_id) REFERENCES device_capabilities (id),
        CONSTRAINT fk_dpa_upd FOREIGN KEY (updated_by)    REFERENCES app_users           (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 6. SCENES & AUTOMATIONS ──────────────────────────────────────
    _exec("""
    CREATE TABLE scenes (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id    BIGINT UNSIGNED NOT NULL,
        room_id       BIGINT UNSIGNED,
        name          VARCHAR(100)    NOT NULL,
        icon          VARCHAR(100),
        color         VARCHAR(20),
        is_favorite   BOOLEAN         NOT NULL DEFAULT FALSE,
        voice_name    VARCHAR(255),
        display_order INT             NOT NULL DEFAULT 0,
        active_ind    BOOLEAN         NOT NULL DEFAULT TRUE,
        created_by    BIGINT UNSIGNED,
        updated_by    BIGINT UNSIGNED,
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_sc_proj FOREIGN KEY (project_id) REFERENCES projects  (id),
        CONSTRAINT fk_sc_room FOREIGN KEY (room_id)    REFERENCES rooms     (id),
        CONSTRAINT fk_sc_cby  FOREIGN KEY (created_by) REFERENCES app_users (id),
        CONSTRAINT fk_sc_uby  FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE scene_actions (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        scene_id       BIGINT UNSIGNED NOT NULL,
        device_id      BIGINT UNSIGNED NOT NULL,
        action_payload JSON,
        delay_ms       INT             NOT NULL DEFAULT 0,
        display_order  INT             NOT NULL DEFAULT 0,
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_sa_scene FOREIGN KEY (scene_id)  REFERENCES scenes    (id),
        CONSTRAINT fk_sa_dev   FOREIGN KEY (device_id) REFERENCES devices   (id),
        CONSTRAINT fk_sa_upd   FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE scene_triggers (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        scene_id       BIGINT UNSIGNED NOT NULL,
        trigger_type   ENUM('device_input','time','sunrise','sunset','voice') NOT NULL,
        device_id      BIGINT UNSIGNED,
        trigger_input  VARCHAR(50),
        trigger_time   TIME,
        days_of_week   JSON,
        offset_minutes INT             NOT NULL DEFAULT 0,
        voice_phrase   VARCHAR(255),
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_st_scene FOREIGN KEY (scene_id)  REFERENCES scenes    (id),
        CONSTRAINT fk_st_dev   FOREIGN KEY (device_id) REFERENCES devices   (id),
        CONSTRAINT fk_st_upd   FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE automations (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id        BIGINT UNSIGNED NOT NULL,
        name              VARCHAR(100)    NOT NULL,
        description       TEXT,
        active_ind        BOOLEAN         NOT NULL DEFAULT TRUE,
        last_triggered_at DATETIME(3),
        created_by        BIGINT UNSIGNED,
        updated_by        BIGINT UNSIGNED,
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_auto_proj FOREIGN KEY (project_id) REFERENCES projects  (id),
        CONSTRAINT fk_auto_cby  FOREIGN KEY (created_by) REFERENCES app_users (id),
        CONSTRAINT fk_auto_uby  FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE automation_triggers (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        automation_id   BIGINT UNSIGNED NOT NULL,
        trigger_type    ENUM('device_state','time','sunrise','sunset','scene_activated') NOT NULL,
        device_id       BIGINT UNSIGNED,
        device_property VARCHAR(50),
        operator        ENUM('eq','neq','gt','gte','lt','lte'),
        trigger_value   VARCHAR(100),
        trigger_time    TIME,
        days_of_week    JSON,
        start_date      DATE,
        end_date        DATE,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_at_auto FOREIGN KEY (automation_id) REFERENCES automations (id),
        CONSTRAINT fk_at_dev  FOREIGN KEY (device_id)     REFERENCES devices     (id),
        CONSTRAINT fk_at_upd  FOREIGN KEY (updated_by)    REFERENCES app_users   (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE automation_conditions (
        id               BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        automation_id    BIGINT UNSIGNED NOT NULL,
        condition_type   ENUM('device_state','time_range','day_of_week','scene_active') NOT NULL,
        device_id        BIGINT UNSIGNED,
        device_property  VARCHAR(50),
        operator         ENUM('eq','neq','gt','gte','lt','lte'),
        condition_value  VARCHAR(100),
        start_time       TIME,
        end_time         TIME,
        days_of_week     JSON,
        logical_operator ENUM('AND','OR') NOT NULL DEFAULT 'AND',
        display_order    INT              NOT NULL DEFAULT 0,
        active_ind       BOOLEAN          NOT NULL DEFAULT TRUE,
        updated_by       BIGINT UNSIGNED,
        created_at       DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at       DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ac_auto FOREIGN KEY (automation_id) REFERENCES automations (id),
        CONSTRAINT fk_ac_dev  FOREIGN KEY (device_id)     REFERENCES devices     (id),
        CONSTRAINT fk_ac_upd  FOREIGN KEY (updated_by)    REFERENCES app_users   (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE automation_actions (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        automation_id  BIGINT UNSIGNED NOT NULL,
        action_type    ENUM('device_command','scene_activate','notify','delay') NOT NULL,
        device_id      BIGINT UNSIGNED,
        scene_id       BIGINT UNSIGNED,
        action_payload JSON,
        delay_ms       INT             NOT NULL DEFAULT 0,
        display_order  INT             NOT NULL DEFAULT 0,
        active_ind     BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by     BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_aa_auto  FOREIGN KEY (automation_id) REFERENCES automations (id),
        CONSTRAINT fk_aa_dev   FOREIGN KEY (device_id)     REFERENCES devices     (id),
        CONSTRAINT fk_aa_scene FOREIGN KEY (scene_id)      REFERENCES scenes      (id),
        CONSTRAINT fk_aa_upd   FOREIGN KEY (updated_by)    REFERENCES app_users   (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 7. STATE & ANALYTICS ─────────────────────────────────────────
    _exec("""
    CREATE TABLE device_states (
        id           BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
        device_id    BIGINT UNSIGNED  NOT NULL,
        state        JSON,
        is_on        BOOLEAN,
        brightness   TINYINT UNSIGNED,
        color_temp_k INT,
        rgb          VARCHAR(20),
        position     TINYINT UNSIGNED,
        temperature  DECIMAL(5,2),
        updated_by   BIGINT UNSIGNED,
        updated_at   DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ds_device (device_id),
        CONSTRAINT fk_dstate_dev FOREIGN KEY (device_id) REFERENCES devices (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_state_history (
        id                   BIGINT UNSIGNED NOT NULL,
        device_id            BIGINT UNSIGNED NOT NULL,
        state                JSON,
        is_on                BOOLEAN,
        brightness           TINYINT UNSIGNED,
        temperature          DECIMAL(5,2),
        triggered_by         ENUM('user','automation','scene','keypad','alexa','google_home','api','schedule'),
        triggered_by_user_id BIGINT UNSIGNED,
        recorded_at          DATETIME(3)     NOT NULL,
        PRIMARY KEY (id, recorded_at),
        KEY idx_dsh_device_ts (device_id, recorded_at)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
      PARTITION BY RANGE (YEAR(recorded_at)*100+MONTH(recorded_at)) (
        PARTITION p202601 VALUES LESS THAN (202602),
        PARTITION p202602 VALUES LESS THAN (202603),
        PARTITION p202603 VALUES LESS THAN (202604),
        PARTITION p202604 VALUES LESS THAN (202605),
        PARTITION p202605 VALUES LESS THAN (202606),
        PARTITION p202606 VALUES LESS THAN (202607),
        PARTITION p202607 VALUES LESS THAN (202608),
        PARTITION p202608 VALUES LESS THAN (202609),
        PARTITION p202609 VALUES LESS THAN (202610),
        PARTITION p202610 VALUES LESS THAN (202611),
        PARTITION p202611 VALUES LESS THAN (202612),
        PARTITION p202612 VALUES LESS THAN (202701),
        PARTITION p_future VALUES LESS THAN MAXVALUE
      )
    """)

    _exec("""
    CREATE TABLE energy_readings (
        id           BIGINT UNSIGNED NOT NULL,
        project_id   BIGINT UNSIGNED NOT NULL,
        device_id    BIGINT UNSIGNED,
        room_id      BIGINT UNSIGNED,
        kwh          DECIMAL(10,4)   NOT NULL,
        reading_hour DATETIME        NOT NULL,
        recorded_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id, reading_hour),
        UNIQUE KEY uq_energy_device_hour (device_id, room_id, reading_hour),
        KEY idx_energy_proj_hour (project_id, reading_hour)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
      PARTITION BY RANGE (YEAR(reading_hour)*100+MONTH(reading_hour)) (
        PARTITION p202601 VALUES LESS THAN (202602),
        PARTITION p202602 VALUES LESS THAN (202603),
        PARTITION p202603 VALUES LESS THAN (202604),
        PARTITION p202604 VALUES LESS THAN (202605),
        PARTITION p202605 VALUES LESS THAN (202606),
        PARTITION p202606 VALUES LESS THAN (202607),
        PARTITION p202607 VALUES LESS THAN (202608),
        PARTITION p202608 VALUES LESS THAN (202609),
        PARTITION p202609 VALUES LESS THAN (202610),
        PARTITION p202610 VALUES LESS THAN (202611),
        PARTITION p202611 VALUES LESS THAN (202612),
        PARTITION p202612 VALUES LESS THAN (202701),
        PARTITION p_future VALUES LESS THAN MAXVALUE
      )
    """)

    _exec("""
    CREATE TABLE automation_logs (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        automation_id     BIGINT UNSIGNED NOT NULL,
        project_id        BIGINT UNSIGNED NOT NULL,
        triggered_by_type ENUM('device_state','time','manual','api') NOT NULL,
        trigger_detail    JSON,
        status            ENUM('success','partial','failed') NOT NULL,
        actions_executed  INT             NOT NULL DEFAULT 0,
        error_detail      TEXT,
        executed_at       DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_al_auto FOREIGN KEY (automation_id) REFERENCES automations (id),
        CONSTRAINT fk_al_proj FOREIGN KEY (project_id)    REFERENCES projects    (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 8. VOICE & ALERTS ────────────────────────────────────────────
    _exec("""
    CREATE TABLE voice_integrations (
        id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        homeowner_id            BIGINT UNSIGNED NOT NULL,
        project_id              BIGINT UNSIGNED NOT NULL,
        platform                ENUM('alexa','google_home','siri') NOT NULL,
        access_token_encrypted  TEXT,
        refresh_token_encrypted TEXT,
        token_expires_at        DATETIME(3),
        platform_user_id        VARCHAR(255),
        active_ind              BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by              BIGINT UNSIGNED,
        linked_at               DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_vi_owner FOREIGN KEY (homeowner_id) REFERENCES homeowners (id),
        CONSTRAINT fk_vi_proj  FOREIGN KEY (project_id)   REFERENCES projects   (id),
        CONSTRAINT fk_vi_upd   FOREIGN KEY (updated_by)   REFERENCES app_users  (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE voice_exposed_entities (
        id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        voice_integration_id BIGINT UNSIGNED NOT NULL,
        entity_type          ENUM('device','scene') NOT NULL,
        device_id            BIGINT UNSIGNED,
        scene_id             BIGINT UNSIGNED,
        friendly_name        VARCHAR(255),
        platform_endpoint_id VARCHAR(255),
        active_ind           BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by           BIGINT UNSIGNED,
        created_at           DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at           DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_vee_vi    FOREIGN KEY (voice_integration_id) REFERENCES voice_integrations (id),
        CONSTRAINT fk_vee_dev   FOREIGN KEY (device_id)            REFERENCES devices            (id),
        CONSTRAINT fk_vee_scene FOREIGN KEY (scene_id)             REFERENCES scenes             (id),
        CONSTRAINT fk_vee_upd   FOREIGN KEY (updated_by)           REFERENCES app_users          (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE voice_capability_map (
        id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        capability_interface    VARCHAR(100)    NOT NULL,
        alexa_interface         VARCHAR(100),
        google_home_trait       VARCHAR(100),
        homekit_service         VARCHAR(100),
        homekit_characteristics JSON,
        google_attributes       JSON,
        notes                   VARCHAR(255),
        active_ind              BOOLEAN         NOT NULL DEFAULT TRUE,
        PRIMARY KEY (id),
        UNIQUE KEY uq_vcm_iface (capability_interface)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE alert_rules (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id      BIGINT UNSIGNED NOT NULL,
        name            VARCHAR(100)    NOT NULL,
        rule_type       ENUM('device_offline','energy_threshold','error_count','device_state') NOT NULL,
        device_id       BIGINT UNSIGNED,
        rule_condition  JSON,
        notify_channels JSON,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ar_proj FOREIGN KEY (project_id) REFERENCES projects  (id),
        CONSTRAINT fk_ar_dev  FOREIGN KEY (device_id)  REFERENCES devices   (id),
        CONSTRAINT fk_ar_upd  FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE notifications (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        user_id           BIGINT UNSIGNED NOT NULL,
        project_id        BIGINT UNSIGNED NOT NULL,
        alert_rule_id     BIGINT UNSIGNED,
        title             VARCHAR(255)    NOT NULL,
        body              TEXT,
        notification_type ENUM('alert','info','automation','system','device_error') NOT NULL,
        is_read           BOOLEAN         NOT NULL DEFAULT FALSE,
        read_at           DATETIME(3),
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        KEY idx_notif_user_unread (user_id, is_read),
        CONSTRAINT fk_notif_user  FOREIGN KEY (user_id)       REFERENCES app_users  (id),
        CONSTRAINT fk_notif_proj  FOREIGN KEY (project_id)    REFERENCES projects   (id),
        CONSTRAINT fk_notif_alert FOREIGN KEY (alert_rule_id) REFERENCES alert_rules (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE push_tokens (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        homeowner_id BIGINT UNSIGNED NOT NULL,
        token        VARCHAR(500)    NOT NULL,
        platform     ENUM('ios','android') NOT NULL,
        device_id    VARCHAR(255),
        active_ind   BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_push_token (token),
        CONSTRAINT fk_pt_owner FOREIGN KEY (homeowner_id) REFERENCES homeowners (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 9. DOCUMENTS & INVENTORY ──────────────────────────────────────
    _exec("""
    CREATE TABLE project_documents (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id      BIGINT UNSIGNED NOT NULL,
        uploaded_by     BIGINT UNSIGNED NOT NULL,
        updated_by      BIGINT UNSIGNED,
        category        ENUM('project_plan','wiring_diagram','knx_ets_file',
                             'commissioning_report','warranty','manual','photo','other') NOT NULL,
        file_name       VARCHAR(255)    NOT NULL,
        s3_bucket       VARCHAR(255),
        s3_key          VARCHAR(1000),
        s3_region       VARCHAR(50)     DEFAULT 'ap-south-1',
        content_type    VARCHAR(100),
        file_size_bytes BIGINT UNSIGNED,
        checksum_sha256 VARCHAR(64),
        upload_status   ENUM('pending','completed','failed') NOT NULL DEFAULT 'pending',
        is_deleted      BOOLEAN         NOT NULL DEFAULT FALSE,
        deleted_at      DATETIME(3),
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_pd_proj FOREIGN KEY (project_id)  REFERENCES projects  (id),
        CONSTRAINT fk_pd_upl  FOREIGN KEY (uploaded_by) REFERENCES app_users (id),
        CONSTRAINT fk_pd_upd  FOREIGN KEY (updated_by)  REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE inventory_categories (
        id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name       VARCHAR(100)    NOT NULL,
        parent_id  BIGINT UNSIGNED,
        active_ind BOOLEAN         NOT NULL DEFAULT TRUE,
        PRIMARY KEY (id),
        CONSTRAINT fk_ic_parent FOREIGN KEY (parent_id) REFERENCES inventory_categories (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE inventory_items (
        id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        organization_id     BIGINT UNSIGNED NOT NULL,
        category_id         BIGINT UNSIGNED,
        device_type_id      BIGINT UNSIGNED,
        name                VARCHAR(255)    NOT NULL,
        sku                 VARCHAR(100),
        brand               VARCHAR(100),
        model               VARCHAR(100),
        description         TEXT,
        unit_cost           DECIMAL(10,2),
        quantity_in_stock   INT             NOT NULL DEFAULT 0,
        quantity_reserved   INT             NOT NULL DEFAULT 0,
        low_stock_threshold INT             NOT NULL DEFAULT 0,
        metadata            JSON,
        status              ENUM('ordered','in_store','installed') NOT NULL DEFAULT 'in_store',
        received_at         DATETIME(3),
        installed_at        DATETIME(3),
        active_ind          BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by          BIGINT UNSIGNED,
        created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ii_org   FOREIGN KEY (organization_id) REFERENCES organizations       (id),
        CONSTRAINT fk_ii_cat   FOREIGN KEY (category_id)     REFERENCES inventory_categories (id),
        CONSTRAINT fk_ii_dtype FOREIGN KEY (device_type_id)  REFERENCES device_types        (id),
        CONSTRAINT fk_ii_upd   FOREIGN KEY (updated_by)      REFERENCES app_users           (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE project_inventory (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id        BIGINT UNSIGNED NOT NULL,
        inventory_item_id BIGINT UNSIGNED NOT NULL,
        quantity_used     INT             NOT NULL DEFAULT 1,
        device_id         BIGINT UNSIGNED,
        installed_at      DATETIME(3),
        notes             TEXT,
        active_ind        BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by        BIGINT UNSIGNED,
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_pi_proj FOREIGN KEY (project_id)        REFERENCES projects        (id),
        CONSTRAINT fk_pi_item FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
        CONSTRAINT fk_pi_dev  FOREIGN KEY (device_id)         REFERENCES devices         (id),
        CONSTRAINT fk_pi_upd  FOREIGN KEY (updated_by)        REFERENCES app_users       (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE inventory_status_history (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        inventory_item_id BIGINT UNSIGNED NOT NULL,
        from_status       ENUM('ordered','in_store','installed') NOT NULL,
        to_status         ENUM('ordered','in_store','installed') NOT NULL,
        changed_by        BIGINT UNSIGNED,
        notes             TEXT,
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ish_item FOREIGN KEY (inventory_item_id) REFERENCES inventory_items (id),
        CONSTRAINT fk_ish_by   FOREIGN KEY (changed_by)        REFERENCES app_users       (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 10. FIRMWARE & OTA ───────────────────────────────────────────
    _exec("""
    CREATE TABLE ota_jobs (
        id                  BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name                VARCHAR(255)    NOT NULL,
        firmware_release_id BIGINT UNSIGNED NOT NULL,
        target_type         ENUM('controller','device','all') NOT NULL,
        status              ENUM('draft','scheduled','in_progress','completed','failed','cancelled') NOT NULL DEFAULT 'draft',
        scheduled_at        DATETIME(3),
        started_at          DATETIME(3),
        completed_at        DATETIME(3),
        created_by          BIGINT UNSIGNED,
        updated_by          BIGINT UNSIGNED,
        created_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at          DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ota_fw  FOREIGN KEY (firmware_release_id) REFERENCES firmware_releases (id),
        CONSTRAINT fk_ota_cby FOREIGN KEY (created_by)          REFERENCES app_users         (id),
        CONSTRAINT fk_ota_uby FOREIGN KEY (updated_by)          REFERENCES app_users         (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE ota_job_targets (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        ota_job_id    BIGINT UNSIGNED NOT NULL,
        target_type   ENUM('controller','device') NOT NULL,
        controller_id BIGINT UNSIGNED,
        device_id     BIGINT UNSIGNED,
        from_version  VARCHAR(50),
        to_version    VARCHAR(50),
        status        ENUM('pending','downloading','installing','success','failed','skipped') NOT NULL DEFAULT 'pending',
        progress_pct  TINYINT UNSIGNED NOT NULL DEFAULT 0,
        error_message TEXT,
        started_at    DATETIME(3),
        completed_at  DATETIME(3),
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ojt_job  FOREIGN KEY (ota_job_id)    REFERENCES ota_jobs    (id),
        CONSTRAINT fk_ojt_ctrl FOREIGN KEY (controller_id) REFERENCES controllers (id),
        CONSTRAINT fk_ojt_dev  FOREIGN KEY (device_id)     REFERENCES devices     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE device_lifecycle_events (
        id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        device_id    BIGINT UNSIGNED NOT NULL,
        event_type   ENUM('commissioned','decommissioned','replaced','firmware_updated',
                          'factory_reset','repaired','moved','retired') NOT NULL,
        old_value    JSON,
        new_value    JSON,
        notes        TEXT,
        performed_by BIGINT UNSIGNED,
        created_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_dle_dev FOREIGN KEY (device_id)    REFERENCES devices   (id),
        CONSTRAINT fk_dle_by  FOREIGN KEY (performed_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE config_exports (
        id              BIGINT UNSIGNED  NOT NULL AUTO_INCREMENT,
        project_id      BIGINT UNSIGNED  NOT NULL,
        controller_id   BIGINT UNSIGNED,
        version         INT UNSIGNED     NOT NULL,
        version_label   VARCHAR(50),
        file_format     ENUM('json','xml') NOT NULL DEFAULT 'json',
        file_name       VARCHAR(255),
        s3_bucket       VARCHAR(255),
        s3_key          VARCHAR(1000),
        s3_region       VARCHAR(50)      DEFAULT 'ap-south-1',
        s3_version_id   VARCHAR(255),
        content_type    VARCHAR(100),
        file_size_bytes BIGINT UNSIGNED,
        checksum_sha256 VARCHAR(64),
        export_status   ENUM('pending','completed','failed') NOT NULL DEFAULT 'pending',
        exported_by     BIGINT UNSIGNED,
        exported_at     DATETIME(3),
        sync_direction  ENUM('push','pull') NOT NULL DEFAULT 'push',
        sync_status     ENUM('pending','syncing','synced','failed','superseded') NOT NULL DEFAULT 'pending',
        sync_attempts   INT UNSIGNED     NOT NULL DEFAULT 0,
        synced_at       DATETIME(3),
        last_sync_error TEXT,
        is_current      BOOLEAN          NOT NULL DEFAULT FALSE,
        notes           TEXT,
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)      NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ce_proj_ver (project_id, version),
        CONSTRAINT fk_ce_proj FOREIGN KEY (project_id)    REFERENCES projects     (id),
        CONSTRAINT fk_ce_ctrl FOREIGN KEY (controller_id) REFERENCES controllers  (id),
        CONSTRAINT fk_ce_expby FOREIGN KEY (exported_by)  REFERENCES app_users    (id),
        CONSTRAINT fk_ce_upd  FOREIGN KEY (updated_by)    REFERENCES app_users    (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 11. SUPPORT ──────────────────────────────────────────────────
    _exec("""
    CREATE TABLE support_tickets (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        ticket_number     VARCHAR(30)     NOT NULL,
        organization_id   BIGINT UNSIGNED NOT NULL,
        project_id        BIGINT UNSIGNED,
        device_id         BIGINT UNSIGNED,
        reported_by       BIGINT UNSIGNED,
        assigned_to       BIGINT UNSIGNED,
        category          ENUM('hardware','software','configuration','network',
                               'billing','training','other') NOT NULL,
        priority          ENUM('low','medium','high','critical') NOT NULL DEFAULT 'medium',
        status            ENUM('open','in_progress','on_hold','resolved','closed') NOT NULL DEFAULT 'open',
        title             VARCHAR(255)    NOT NULL,
        description       TEXT,
        resolution        TEXT,
        first_response_at DATETIME(3),
        sla_due_at        DATETIME(3),
        resolved_at       DATETIME(3),
        closed_at         DATETIME(3),
        updated_by        BIGINT UNSIGNED,
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_ticket_num (ticket_number),
        KEY idx_ticket_status (status),
        CONSTRAINT fk_tkt_org  FOREIGN KEY (organization_id) REFERENCES organizations (id),
        CONSTRAINT fk_tkt_proj FOREIGN KEY (project_id)      REFERENCES projects      (id),
        CONSTRAINT fk_tkt_dev  FOREIGN KEY (device_id)       REFERENCES devices       (id),
        CONSTRAINT fk_tkt_rep  FOREIGN KEY (reported_by)     REFERENCES app_users     (id),
        CONSTRAINT fk_tkt_asgn FOREIGN KEY (assigned_to)     REFERENCES app_users     (id),
        CONSTRAINT fk_tkt_upd  FOREIGN KEY (updated_by)      REFERENCES app_users     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE ticket_comments (
        id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        ticket_id   BIGINT UNSIGNED NOT NULL,
        author_id   BIGINT UNSIGNED NOT NULL,
        body        TEXT            NOT NULL,
        is_internal BOOLEAN         NOT NULL DEFAULT FALSE,
        created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_tc_ticket FOREIGN KEY (ticket_id) REFERENCES support_tickets (id),
        CONSTRAINT fk_tc_author FOREIGN KEY (author_id) REFERENCES app_users       (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE ticket_attachments (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        ticket_id       BIGINT UNSIGNED NOT NULL,
        comment_id      BIGINT UNSIGNED,
        uploaded_by     BIGINT UNSIGNED,
        file_name       VARCHAR(255)    NOT NULL,
        s3_bucket       VARCHAR(255),
        s3_key          VARCHAR(1000),
        content_type    VARCHAR(100),
        file_size_bytes BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ta_ticket  FOREIGN KEY (ticket_id)   REFERENCES support_tickets  (id),
        CONSTRAINT fk_ta_comment FOREIGN KEY (comment_id)  REFERENCES ticket_comments  (id),
        CONSTRAINT fk_ta_upld    FOREIGN KEY (uploaded_by) REFERENCES app_users        (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 12. DRIVER LIBRARY ───────────────────────────────────────────
    _exec("""
    CREATE TABLE drivers (
        id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        name                    VARCHAR(150)    NOT NULL,
        slug                    VARCHAR(120)    NOT NULL,
        source_type             ENUM('okas_official','partner','community','third_party') NOT NULL,
        developer_name          VARCHAR(150),
        manufacturer_name       VARCHAR(150),
        category                VARCHAR(50),
        protocol                VARCHAR(50),
        communication_direction ENUM('bidirectional','control_only','feedback_only') NOT NULL,
        active_ind              BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_driver_slug (slug)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE driver_versions (
        id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        driver_id               BIGINT UNSIGNED NOT NULL,
        version                 VARCHAR(50)     NOT NULL,
        release_channel         ENUM('stable','beta','rc','deprecated') NOT NULL DEFAULT 'stable',
        release_notes           TEXT,
        s3_bucket               VARCHAR(255),
        s3_key                  VARCHAR(1000),
        file_size_bytes         BIGINT UNSIGNED,
        checksum_sha256         VARCHAR(64),
        min_controller_firmware VARCHAR(50),
        is_published            BOOLEAN         NOT NULL DEFAULT FALSE,
        published_at            DATETIME(3),
        published_by            BIGINT UNSIGNED,
        active_ind              BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by              BIGINT UNSIGNED,
        created_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at              DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_dv_driver FOREIGN KEY (driver_id)    REFERENCES drivers   (id),
        CONSTRAINT fk_dv_pubby  FOREIGN KEY (published_by) REFERENCES app_users (id),
        CONSTRAINT fk_dv_upd    FOREIGN KEY (updated_by)   REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE driver_device_types (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        driver_id      BIGINT UNSIGNED NOT NULL,
        device_type_id BIGINT UNSIGNED NOT NULL,
        PRIMARY KEY (id),
        CONSTRAINT fk_ddt_driver FOREIGN KEY (driver_id)      REFERENCES drivers      (id),
        CONSTRAINT fk_ddt_dtype  FOREIGN KEY (device_type_id) REFERENCES device_types (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE controller_drivers (
        id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        controller_id     BIGINT UNSIGNED NOT NULL,
        driver_id         BIGINT UNSIGNED NOT NULL,
        driver_version_id BIGINT UNSIGNED NOT NULL,
        install_status    ENUM('pending','installed','failed','uninstalled') NOT NULL DEFAULT 'pending',
        installed_at      DATETIME(3),
        active_ind        BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by        BIGINT UNSIGNED,
        created_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at        DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_cd_ctrl   FOREIGN KEY (controller_id)     REFERENCES controllers    (id),
        CONSTRAINT fk_cd_driver FOREIGN KEY (driver_id)         REFERENCES drivers        (id),
        CONSTRAINT fk_cd_ver    FOREIGN KEY (driver_version_id) REFERENCES driver_versions (id),
        CONSTRAINT fk_cd_upd    FOREIGN KEY (updated_by)        REFERENCES app_users       (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE driver_licenses (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        organization_id BIGINT UNSIGNED NOT NULL,
        driver_id       BIGINT UNSIGNED NOT NULL,
        license_key     VARCHAR(255)    NOT NULL,
        license_type    ENUM('perpetual','subscription','per_controller','per_device') NOT NULL,
        max_activations BIGINT UNSIGNED,
        expires_at      DATETIME(3),
        purchased_at    DATETIME(3),
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        updated_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_lic_key (license_key),
        CONSTRAINT fk_dl_org    FOREIGN KEY (organization_id) REFERENCES organizations (id),
        CONSTRAINT fk_dl_driver FOREIGN KEY (driver_id)       REFERENCES drivers       (id),
        CONSTRAINT fk_dl_upd    FOREIGN KEY (updated_by)      REFERENCES app_users     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE driver_license_activations (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        license_id     BIGINT UNSIGNED NOT NULL,
        controller_id  BIGINT UNSIGNED NOT NULL,
        activated_at   DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        deactivated_at DATETIME(3),
        activated_by   BIGINT UNSIGNED,
        created_at     DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_dla_lic  FOREIGN KEY (license_id)    REFERENCES driver_licenses (id),
        CONSTRAINT fk_dla_ctrl FOREIGN KEY (controller_id) REFERENCES controllers     (id),
        CONSTRAINT fk_dla_by   FOREIGN KEY (activated_by)  REFERENCES app_users       (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 13. ACCESS CONTROL ───────────────────────────────────────────
    _exec("""
    CREATE TABLE guest_access_tokens (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        token_hash    VARCHAR(64)     NOT NULL,
        label         VARCHAR(150),
        project_id    BIGINT UNSIGNED NOT NULL,
        scope_type    ENUM('project','room','custom') NOT NULL,
        room_id       BIGINT UNSIGNED,
        access_level  ENUM('view_only','control') NOT NULL DEFAULT 'view_only',
        is_enabled    BOOLEAN         NOT NULL DEFAULT TRUE,
        max_uses      INT UNSIGNED,
        use_count     INT UNSIGNED    NOT NULL DEFAULT 0,
        expires_at    DATETIME(3),
        first_used_at DATETIME(3),
        last_used_at  DATETIME(3),
        is_revoked    BOOLEAN         NOT NULL DEFAULT FALSE,
        revoked_by    BIGINT UNSIGNED,
        revoked_at    DATETIME(3),
        created_by    BIGINT UNSIGNED,
        created_at    DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        UNIQUE KEY uq_gat_hash (token_hash),
        CONSTRAINT fk_gat_proj    FOREIGN KEY (project_id) REFERENCES projects   (id),
        CONSTRAINT fk_gat_room    FOREIGN KEY (room_id)    REFERENCES rooms       (id),
        CONSTRAINT fk_gat_revby   FOREIGN KEY (revoked_by) REFERENCES homeowners  (id),
        CONSTRAINT fk_gat_creby   FOREIGN KEY (created_by) REFERENCES homeowners  (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE guest_access_rooms (
        id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        guest_access_token_id BIGINT UNSIGNED NOT NULL,
        room_id               BIGINT UNSIGNED NOT NULL,
        can_view              BOOLEAN         NOT NULL DEFAULT TRUE,
        can_control           BOOLEAN         NOT NULL DEFAULT FALSE,
        created_at            DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_gar_tok  FOREIGN KEY (guest_access_token_id) REFERENCES guest_access_tokens (id),
        CONSTRAINT fk_gar_room FOREIGN KEY (room_id)               REFERENCES rooms               (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE guest_access_devices (
        id                    BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        guest_access_token_id BIGINT UNSIGNED NOT NULL,
        device_id             BIGINT UNSIGNED NOT NULL,
        can_view              BOOLEAN         NOT NULL DEFAULT TRUE,
        can_control           BOOLEAN         NOT NULL DEFAULT FALSE,
        created_at            DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_gad_tok FOREIGN KEY (guest_access_token_id) REFERENCES guest_access_tokens (id),
        CONSTRAINT fk_gad_dev FOREIGN KEY (device_id)             REFERENCES devices             (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE access_groups (
        id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        project_id  BIGINT UNSIGNED NOT NULL,
        name        VARCHAR(100)    NOT NULL,
        description TEXT,
        active_ind  BOOLEAN         NOT NULL DEFAULT TRUE,
        created_by  BIGINT UNSIGNED,
        updated_by  BIGINT UNSIGNED,
        created_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at  DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_ag_proj FOREIGN KEY (project_id) REFERENCES projects  (id),
        CONSTRAINT fk_ag_cby  FOREIGN KEY (created_by) REFERENCES app_users (id),
        CONSTRAINT fk_ag_uby  FOREIGN KEY (updated_by) REFERENCES app_users (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE access_group_members (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        access_group_id BIGINT UNSIGNED NOT NULL,
        user_id         BIGINT UNSIGNED NOT NULL,
        added_by        BIGINT UNSIGNED,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_agm_grp FOREIGN KEY (access_group_id) REFERENCES access_groups (id),
        CONSTRAINT fk_agm_usr FOREIGN KEY (user_id)         REFERENCES app_users     (id),
        CONSTRAINT fk_agm_aby FOREIGN KEY (added_by)        REFERENCES app_users     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE access_group_room_permissions (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        access_group_id BIGINT UNSIGNED NOT NULL,
        room_id         BIGINT UNSIGNED NOT NULL,
        can_view        BOOLEAN         NOT NULL DEFAULT TRUE,
        can_control     BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        granted_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_agrp_grp  FOREIGN KEY (access_group_id) REFERENCES access_groups (id),
        CONSTRAINT fk_agrp_room FOREIGN KEY (room_id)         REFERENCES rooms         (id),
        CONSTRAINT fk_agrp_by   FOREIGN KEY (granted_by)      REFERENCES app_users     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    _exec("""
    CREATE TABLE access_group_device_permissions (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        access_group_id BIGINT UNSIGNED NOT NULL,
        device_id       BIGINT UNSIGNED NOT NULL,
        can_view        BOOLEAN         NOT NULL DEFAULT TRUE,
        can_control     BOOLEAN         NOT NULL DEFAULT FALSE,
        active_ind      BOOLEAN         NOT NULL DEFAULT TRUE,
        granted_by      BIGINT UNSIGNED,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        updated_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        CONSTRAINT fk_agdp_grp FOREIGN KEY (access_group_id) REFERENCES access_groups (id),
        CONSTRAINT fk_agdp_dev FOREIGN KEY (device_id)       REFERENCES devices       (id),
        CONSTRAINT fk_agdp_by  FOREIGN KEY (granted_by)      REFERENCES app_users     (id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # ── 14. AUDIT HISTORY ────────────────────────────────────────────
    _exec("""
    CREATE TABLE audit_logs (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        actor_id        BIGINT UNSIGNED,
        actor_role      VARCHAR(50),
        action          VARCHAR(100)    NOT NULL,
        entity_type     VARCHAR(50),
        entity_id       BIGINT UNSIGNED,
        organization_id BIGINT UNSIGNED,
        project_id      BIGINT UNSIGNED,
        ip_address      VARCHAR(45),
        user_agent      TEXT,
        old_value       JSON,
        new_value       JSON,
        created_at      DATETIME(3)     NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
        PRIMARY KEY (id),
        KEY idx_al_entity (entity_type, entity_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """)

    # _ah tables — shadow snapshot tables, no FK constraints (survive cascaded deletes)
    for tbl, cols in [
        ("organizations_ah",
         "id BIGINT UNSIGNED, name VARCHAR(255), slug VARCHAR(100), email VARCHAR(255), "
         "phone VARCHAR(50), address TEXT, logo_url VARCHAR(500), active_ind BOOLEAN, "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("app_users_ah",
         "id BIGINT UNSIGNED, organization_id BIGINT UNSIGNED, location_id BIGINT UNSIGNED, "
         "email VARCHAR(255), phone VARCHAR(50), full_name VARCHAR(255), avatar_url VARCHAR(500), "
         "google_id VARCHAR(255), active_ind BOOLEAN, last_login_at DATETIME(3), "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("homeowners_ah",
         "id BIGINT UNSIGNED, email VARCHAR(255), phone VARCHAR(50), full_name VARCHAR(255), "
         "avatar_url VARCHAR(500), google_id VARCHAR(255), "
         "preferred_login ENUM('google','otp'), active_ind BOOLEAN, "
         "last_login_at DATETIME(3), created_at DATETIME(3), updated_at DATETIME(3)"),

        ("projects_ah",
         "id BIGINT UNSIGNED, organization_id BIGINT UNSIGNED, project_manager_id BIGINT UNSIGNED, "
         "location_id BIGINT UNSIGNED, name VARCHAR(255), serial_number VARCHAR(100), "
         "project_type ENUM('residential','commercial','hospitality','retail','other'), "
         "status ENUM('active','inactive','under_maintenance','completed'), "
         "installed_at DATETIME(3), address TEXT, city VARCHAR(100), state VARCHAR(100), "
         "country VARCHAR(100), pincode VARCHAR(20), notes TEXT, metadata JSON, "
         "active_ind BOOLEAN, updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("project_members_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, user_id BIGINT UNSIGNED, "
         "role_id BIGINT UNSIGNED, assigned_by BIGINT UNSIGNED, active_ind BOOLEAN, assigned_at DATETIME(3)"),

        ("project_subscriptions_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, plan_id BIGINT UNSIGNED, "
         "status ENUM('trial','active','expired','cancelled'), "
         "billing_cycle ENUM('monthly','yearly'), started_at DATETIME(3), expires_at DATETIME(3), "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("controllers_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, serial_number VARCHAR(100), "
         "model VARCHAR(100), firmware_version VARCHAR(50), firmware_release_id BIGINT UNSIGNED, "
         "firmware_update_available BOOLEAN, ip_address VARCHAR(45), mac_address VARCHAR(17), "
         "status ENUM('online','offline','maintenance'), last_seen_at DATETIME(3), config JSON, "
         "active_ind BOOLEAN, updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("devices_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, device_type_id BIGINT UNSIGNED, "
         "platform_id BIGINT UNSIGNED, name VARCHAR(100), device_number VARCHAR(50), "
         "icon VARCHAR(100), display_categories JSON, endpoint_id VARCHAR(255), cookie JSON, "
         "active_ind BOOLEAN, is_online BOOLEAN, last_seen_at DATETIME(3), "
         "firmware_version VARCHAR(50), firmware_release_id BIGINT UNSIGNED, "
         "firmware_update_available BOOLEAN, updated_by BIGINT UNSIGNED, "
         "created_at DATETIME(3), updated_at DATETIME(3)"),

        ("device_capabilities_ah",
         "id BIGINT UNSIGNED, device_id BIGINT UNSIGNED, interface VARCHAR(100), "
         "version VARCHAR(10), instance VARCHAR(100), is_proactively_reported BOOLEAN, "
         "is_retrievable BOOLEAN, capability_resources JSON, configuration JSON, "
         "active_ind BOOLEAN, updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("device_property_addresses_ah",
         "id BIGINT UNSIGNED, capability_id BIGINT UNSIGNED, property_name VARCHAR(100), "
         "address_role ENUM('command','state_feedback'), "
         "protocol ENUM('KNX','Lutron','Casambi','Modbus','BACnet','IP','IR'), "
         "address VARCHAR(255), data_type VARCHAR(50), scale_min DECIMAL(10,4), "
         "scale_max DECIMAL(10,4), invert BOOLEAN, active_ind BOOLEAN, "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3)"),

        ("scenes_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, room_id BIGINT UNSIGNED, "
         "name VARCHAR(100), icon VARCHAR(100), color VARCHAR(20), is_favorite BOOLEAN, "
         "voice_name VARCHAR(255), display_order INT, active_ind BOOLEAN, "
         "created_by BIGINT UNSIGNED, updated_by BIGINT UNSIGNED, "
         "created_at DATETIME(3), updated_at DATETIME(3)"),

        ("scene_actions_ah",
         "id BIGINT UNSIGNED, scene_id BIGINT UNSIGNED, device_id BIGINT UNSIGNED, "
         "action_payload JSON, delay_ms INT, display_order INT, active_ind BOOLEAN, "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("automations_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, name VARCHAR(100), description TEXT, "
         "active_ind BOOLEAN, last_triggered_at DATETIME(3), created_by BIGINT UNSIGNED, "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("automation_triggers_ah",
         "id BIGINT UNSIGNED, automation_id BIGINT UNSIGNED, "
         "trigger_type ENUM('device_state','time','sunrise','sunset','scene_activated'), "
         "device_id BIGINT UNSIGNED, device_property VARCHAR(50), "
         "operator ENUM('eq','neq','gt','gte','lt','lte'), trigger_value VARCHAR(100), "
         "trigger_time TIME, days_of_week JSON, start_date DATE, end_date DATE, "
         "active_ind BOOLEAN, updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("automation_conditions_ah",
         "id BIGINT UNSIGNED, automation_id BIGINT UNSIGNED, "
         "condition_type ENUM('device_state','time_range','day_of_week','scene_active'), "
         "device_id BIGINT UNSIGNED, device_property VARCHAR(50), "
         "operator ENUM('eq','neq','gt','gte','lt','lte'), condition_value VARCHAR(100), "
         "start_time TIME, end_time TIME, days_of_week JSON, "
         "logical_operator ENUM('AND','OR'), display_order INT, active_ind BOOLEAN, "
         "updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("automation_actions_ah",
         "id BIGINT UNSIGNED, automation_id BIGINT UNSIGNED, "
         "action_type ENUM('device_command','scene_activate','notify','delay'), "
         "device_id BIGINT UNSIGNED, scene_id BIGINT UNSIGNED, action_payload JSON, "
         "delay_ms INT, display_order INT, active_ind BOOLEAN, updated_by BIGINT UNSIGNED, "
         "created_at DATETIME(3), updated_at DATETIME(3)"),

        ("alert_rules_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, name VARCHAR(100), "
         "rule_type ENUM('device_offline','energy_threshold','error_count','device_state'), "
         "device_id BIGINT UNSIGNED, rule_condition JSON, notify_channels JSON, "
         "active_ind BOOLEAN, updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("inventory_items_ah",
         "id BIGINT UNSIGNED, organization_id BIGINT UNSIGNED, category_id BIGINT UNSIGNED, "
         "device_type_id BIGINT UNSIGNED, name VARCHAR(255), sku VARCHAR(100), brand VARCHAR(100), "
         "model VARCHAR(100), description TEXT, unit_cost DECIMAL(10,2), "
         "quantity_in_stock INT, quantity_reserved INT, low_stock_threshold INT, metadata JSON, "
         "status ENUM('ordered','in_store','installed'), received_at DATETIME(3), "
         "installed_at DATETIME(3), active_ind BOOLEAN, updated_by BIGINT UNSIGNED, "
         "created_at DATETIME(3), updated_at DATETIME(3)"),

        ("support_tickets_ah",
         "id BIGINT UNSIGNED, ticket_number VARCHAR(30), organization_id BIGINT UNSIGNED, "
         "project_id BIGINT UNSIGNED, device_id BIGINT UNSIGNED, reported_by BIGINT UNSIGNED, "
         "assigned_to BIGINT UNSIGNED, "
         "category ENUM('hardware','software','configuration','network','billing','training','other'), "
         "priority ENUM('low','medium','high','critical'), "
         "status ENUM('open','in_progress','on_hold','resolved','closed'), "
         "title VARCHAR(255), description TEXT, resolution TEXT, "
         "first_response_at DATETIME(3), sla_due_at DATETIME(3), resolved_at DATETIME(3), "
         "closed_at DATETIME(3), updated_by BIGINT UNSIGNED, created_at DATETIME(3), updated_at DATETIME(3)"),

        ("config_exports_ah",
         "id BIGINT UNSIGNED, project_id BIGINT UNSIGNED, controller_id BIGINT UNSIGNED, "
         "version INT UNSIGNED, version_label VARCHAR(50), file_format ENUM('json','xml'), "
         "file_name VARCHAR(255), s3_bucket VARCHAR(255), s3_key VARCHAR(1000), "
         "s3_region VARCHAR(50), s3_version_id VARCHAR(255), content_type VARCHAR(100), "
         "file_size_bytes BIGINT UNSIGNED, checksum_sha256 VARCHAR(64), "
         "export_status ENUM('pending','completed','failed'), exported_by BIGINT UNSIGNED, "
         "exported_at DATETIME(3), sync_direction ENUM('push','pull'), "
         "sync_status ENUM('pending','syncing','synced','failed','superseded'), "
         "sync_attempts INT UNSIGNED, synced_at DATETIME(3), last_sync_error TEXT, "
         "is_current BOOLEAN, notes TEXT, updated_by BIGINT UNSIGNED, "
         "created_at DATETIME(3), updated_at DATETIME(3)"),
    ]:
        _exec(f"""
        CREATE TABLE {tbl} (
            ah_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
            ah_operation  ENUM('INSERT','UPDATE','DELETE') NOT NULL,
            ah_changed_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
            ah_changed_by BIGINT UNSIGNED,
            {cols},
            PRIMARY KEY (ah_id),
            KEY idx_{tbl}_ts (ah_changed_at)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

    _exec("SET FOREIGN_KEY_CHECKS=1")

    # ── 60 AFTER TRIGGERS (20 tables × 3 operations) ─────────────────
    for src, ah, by_col in [
        ("organizations",            "organizations_ah",            "updated_by"),
        ("app_users",                "app_users_ah",                "updated_by"),
        ("homeowners",               "homeowners_ah",               "id"),
        ("projects",                 "projects_ah",                 "updated_by"),
        ("project_members",          "project_members_ah",          "assigned_by"),
        ("project_subscriptions",    "project_subscriptions_ah",    "updated_by"),
        ("controllers",              "controllers_ah",              "updated_by"),
        ("devices",                  "devices_ah",                  "updated_by"),
        ("device_capabilities",      "device_capabilities_ah",      "updated_by"),
        ("device_property_addresses","device_property_addresses_ah","updated_by"),
        ("scenes",                   "scenes_ah",                   "updated_by"),
        ("scene_actions",            "scene_actions_ah",            "updated_by"),
        ("automations",              "automations_ah",              "updated_by"),
        ("automation_triggers",      "automation_triggers_ah",      "updated_by"),
        ("automation_conditions",    "automation_conditions_ah",    "updated_by"),
        ("automation_actions",       "automation_actions_ah",       "updated_by"),
        ("alert_rules",              "alert_rules_ah",              "updated_by"),
        ("inventory_items",          "inventory_items_ah",          "updated_by"),
        ("support_tickets",          "support_tickets_ah",          "updated_by"),
        ("config_exports",           "config_exports_ah",           "updated_by"),
    ]:
        short = src.replace("_", "")[:12]

        # AFTER INSERT
        _exec(f"""
        CREATE TRIGGER trg_{src}_ai
        AFTER INSERT ON {src}
        FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          SELECT 'INSERT', NEW.{by_col}, NOW(3)
        """)

        # AFTER UPDATE
        _exec(f"""
        CREATE TRIGGER trg_{src}_au
        AFTER UPDATE ON {src}
        FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          SELECT 'UPDATE', NEW.{by_col}, NOW(3)
        """)

        # AFTER DELETE
        _exec(f"""
        CREATE TRIGGER trg_{src}_ad
        AFTER DELETE ON {src}
        FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          SELECT 'DELETE', OLD.{by_col}, NOW(3)
        """)

    # ── 16 VIEWS ──────────────────────────────────────────────────────
    _exec("""
    CREATE OR REPLACE VIEW vw_alexa_discovery_endpoints AS
    SELECT
        d.id, d.project_id, d.name, d.endpoint_id,
        d.display_categories, d.cookie,
        JSON_ARRAYAGG(
            JSON_OBJECT(
                'type','AlexaInterface',
                'interface', dc.interface,
                'version', dc.version,
                'instance', dc.instance,
                'properties', JSON_OBJECT(
                    'supported', dc.capability_resources,
                    'proactivelyReported', dc.is_proactively_reported,
                    'retrievable', dc.is_retrievable
                ),
                'configuration', dc.configuration
            )
        ) AS capabilities
    FROM devices d
    JOIN device_capabilities dc ON dc.device_id = d.id AND dc.active_ind = TRUE
    WHERE d.active_ind = TRUE AND d.endpoint_id IS NOT NULL
    GROUP BY d.id
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_google_home_devices AS
    SELECT
        d.id, d.project_id, d.name, d.endpoint_id,
        dt.google_home_device_types AS google_device_types,
        JSON_ARRAYAGG(vcm.google_home_trait) AS traits
    FROM devices d
    JOIN device_types dt ON dt.id = d.device_type_id
    JOIN device_capabilities dc ON dc.device_id = d.id AND dc.active_ind = TRUE
    LEFT JOIN voice_capability_map vcm ON vcm.capability_interface = dc.interface AND vcm.active_ind = TRUE
    WHERE d.active_ind = TRUE
    GROUP BY d.id
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_homekit_accessories AS
    SELECT
        d.id, d.project_id, d.name, d.endpoint_id,
        dt.homekit_category,
        JSON_ARRAYAGG(JSON_OBJECT(
            'service', vcm.homekit_service,
            'characteristics', vcm.homekit_characteristics
        )) AS services
    FROM devices d
    JOIN device_types dt ON dt.id = d.device_type_id
    JOIN device_capabilities dc ON dc.device_id = d.id AND dc.active_ind = TRUE
    LEFT JOIN voice_capability_map vcm ON vcm.capability_interface = dc.interface AND vcm.active_ind = TRUE
    WHERE d.active_ind = TRUE
    GROUP BY d.id
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_voice_exposed_entities AS
    SELECT
        vee.id, vi.platform, vi.homeowner_id, vi.project_id,
        vee.entity_type, vee.device_id, vee.scene_id,
        vee.friendly_name, vee.platform_endpoint_id
    FROM voice_exposed_entities vee
    JOIN voice_integrations vi ON vi.id = vee.voice_integration_id AND vi.active_ind = TRUE
    WHERE vee.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_we_okas_project_list AS
    SELECT
        p.id, p.name, p.status, p.project_type, p.city, p.installed_at,
        p.serial_number,
        h.full_name  AS primary_owner_name,
        h.email      AS primary_owner_email,
        u.full_name  AS project_manager_name,
        sp.name      AS subscription_plan,
        ps.status    AS subscription_status,
        (SELECT COUNT(*) FROM devices d WHERE d.project_id = p.id AND d.active_ind = TRUE) AS total_devices
    FROM projects p
    LEFT JOIN project_owners po ON po.project_id = p.id AND po.is_primary = TRUE AND po.active_ind = TRUE
    LEFT JOIN homeowners h ON h.id = po.homeowner_id
    LEFT JOIN app_users u ON u.id = p.project_manager_id
    LEFT JOIN project_subscriptions ps ON ps.project_id = p.id AND ps.status IN ('trial','active')
    LEFT JOIN subscription_plans sp ON sp.id = ps.plan_id
    WHERE p.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_inventory_stock_summary AS
    SELECT
        ii.*,
        ii.quantity_in_stock - ii.quantity_reserved AS quantity_available,
        (ii.quantity_in_stock - ii.quantity_reserved) <= ii.low_stock_threshold AS is_low_stock,
        (SELECT COUNT(DISTINCT pi.project_id) FROM project_inventory pi WHERE pi.inventory_item_id = ii.id AND pi.active_ind = TRUE) AS projects_using
    FROM inventory_items ii
    WHERE ii.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_open_support_tickets AS
    SELECT
        st.*,
        u1.full_name AS reporter_name,
        u2.full_name AS assignee_name,
        (SELECT COUNT(*) FROM ticket_comments tc WHERE tc.ticket_id = st.id) AS comment_count,
        (st.sla_due_at IS NOT NULL AND st.sla_due_at < NOW() AND st.status NOT IN ('resolved','closed')) AS sla_breached
    FROM support_tickets st
    LEFT JOIN app_users u1 ON u1.id = st.reported_by
    LEFT JOIN app_users u2 ON u2.id = st.assigned_to
    WHERE st.status != 'closed'
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_project_kpis AS
    SELECT
        p.id AS project_id, p.name,
        (SELECT COUNT(*) FROM devices d WHERE d.project_id = p.id AND d.active_ind = TRUE) AS total_devices,
        (SELECT COUNT(*) FROM devices d WHERE d.project_id = p.id AND d.active_ind = TRUE AND d.is_online = TRUE) AS active_devices,
        (SELECT COUNT(DISTINCT s.room_id) FROM scenes s WHERE s.project_id = p.id AND s.room_id IS NOT NULL AND s.active_ind = TRUE) AS rooms_with_scenes,
        (SELECT COUNT(*) FROM automation_logs al WHERE al.project_id = p.id AND al.executed_at >= CURDATE()) AS auto_triggers_today,
        (SELECT COUNT(*) FROM alert_rules ar JOIN notifications n ON n.alert_rule_id = ar.id WHERE ar.project_id = p.id AND n.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)) AS open_alerts,
        (SELECT COALESCE(SUM(er.kwh),0) FROM energy_readings er WHERE er.project_id = p.id AND er.reading_hour >= DATE_SUB(NOW(), INTERVAL 30 DAY)) AS energy_kwh_30d
    FROM projects p
    WHERE p.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_device_list AS
    SELECT
        d.id, d.project_id, d.name, d.endpoint_id, d.is_online,
        d.firmware_version, d.firmware_update_available,
        dt.name AS device_type_name, dt.category AS device_type_category,
        dp.name AS platform_name, dp.platform_type,
        f.name  AS floor_name, r.name AS room_name,
        (SELECT COUNT(*) FROM device_capabilities dc WHERE dc.device_id = d.id AND dc.active_ind = TRUE) AS capability_count,
        (SELECT COUNT(*) FROM device_property_addresses dpa JOIN device_capabilities dc2 ON dc2.id = dpa.capability_id WHERE dc2.device_id = d.id AND dpa.active_ind = TRUE) AS address_count
    FROM devices d
    JOIN device_types dt ON dt.id = d.device_type_id
    LEFT JOIN device_platforms dp ON dp.id = d.platform_id
    LEFT JOIN device_rooms dr ON dr.device_id = d.id AND dr.is_primary = TRUE AND dr.active_ind = TRUE
    LEFT JOIN rooms r ON r.id = dr.room_id
    LEFT JOIN floors f ON f.id = r.floor_id
    WHERE d.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_room_summary AS
    SELECT
        r.id AS room_id, r.name, r.room_type, r.display_order,
        f.id AS floor_id, f.name AS floor_name,
        (SELECT COUNT(*) FROM device_rooms dr JOIN devices d ON d.id = dr.device_id WHERE dr.room_id = r.id AND d.active_ind = TRUE AND dr.active_ind = TRUE) AS device_count,
        (SELECT COUNT(*) FROM device_rooms dr JOIN devices d ON d.id = dr.device_id WHERE dr.room_id = r.id AND d.active_ind = TRUE AND d.is_online = TRUE AND dr.active_ind = TRUE) AS online_device_count,
        (SELECT COUNT(*) FROM scenes s WHERE s.room_id = r.id AND s.active_ind = TRUE) AS scene_count,
        (SELECT COALESCE(SUM(er.kwh),0) FROM energy_readings er WHERE er.room_id = r.id AND er.reading_hour >= CURDATE()) AS energy_kwh_today
    FROM rooms r
    JOIN floors f ON f.id = r.floor_id
    WHERE r.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_scene_list AS
    SELECT
        s.id, s.project_id, s.name, s.icon, s.color, s.is_favorite,
        s.voice_name, s.display_order, s.active_ind,
        r.name AS room_name, f.name AS floor_name,
        u.full_name AS created_by_name,
        (SELECT COUNT(*) FROM scene_actions sa WHERE sa.scene_id = s.id AND sa.active_ind = TRUE) AS action_count
    FROM scenes s
    LEFT JOIN rooms r ON r.id = s.room_id
    LEFT JOIN floors f ON f.id = r.floor_id
    LEFT JOIN app_users u ON u.id = s.created_by
    WHERE s.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_automation_list AS
    SELECT
        a.id, a.project_id, a.name, a.description, a.active_ind, a.last_triggered_at,
        (SELECT COUNT(*) FROM automation_triggers atr WHERE atr.automation_id = a.id AND atr.active_ind = TRUE) AS trigger_count,
        (SELECT COUNT(*) FROM automation_actions aa WHERE aa.automation_id = a.id AND aa.active_ind = TRUE) AS action_count,
        (SELECT COUNT(*) FROM automation_logs al WHERE al.automation_id = a.id AND al.executed_at >= CURDATE()) AS runs_today
    FROM automations a
    WHERE a.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_controller_status AS
    SELECT
        c.id, c.project_id, c.serial_number, c.model,
        c.firmware_version, c.status, c.last_seen_at, c.ip_address,
        fr.version AS latest_firmware_version,
        c.firmware_update_available,
        TIMESTAMPDIFF(MINUTE, c.last_seen_at, NOW()) AS minutes_since_seen,
        (SELECT COUNT(*) FROM devices d WHERE d.project_id = c.project_id AND d.active_ind = TRUE) AS managed_device_count,
        (SELECT COUNT(*) FROM controller_drivers cd WHERE cd.controller_id = c.id AND cd.active_ind = TRUE AND cd.install_status = 'installed') AS installed_driver_count
    FROM controllers c
    LEFT JOIN firmware_releases fr ON fr.target_type = 'controller' AND fr.is_published = TRUE AND fr.active_ind = TRUE
    WHERE c.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_device_address_map AS
    SELECT
        d.id AS device_id, d.name AS device_name, d.project_id,
        dc.interface, dc.version, dc.instance,
        dpa.property_name, dpa.address_role, dpa.protocol,
        dpa.address, dpa.data_type, dpa.scale_min, dpa.scale_max, dpa.invert
    FROM devices d
    JOIN device_capabilities dc ON dc.device_id = d.id AND dc.active_ind = TRUE
    JOIN device_property_addresses dpa ON dpa.capability_id = dc.id AND dpa.active_ind = TRUE
    WHERE d.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_device_current_state AS
    SELECT
        d.id AS device_id, d.name, d.project_id,
        ds.state, ds.is_on, ds.brightness, ds.color_temp_k, ds.rgb,
        ds.position, ds.temperature, ds.updated_at AS state_updated_at,
        r.id AS room_id, r.name AS room_name,
        f.id AS floor_id, f.name AS floor_name
    FROM devices d
    LEFT JOIN device_states ds ON ds.device_id = d.id
    LEFT JOIN device_rooms dr ON dr.device_id = d.id AND dr.is_primary = TRUE AND dr.active_ind = TRUE
    LEFT JOIN rooms r ON r.id = dr.room_id
    LEFT JOIN floors f ON f.id = r.floor_id
    WHERE d.active_ind = TRUE
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_driver_catalog AS
    SELECT
        dr.id, dr.name, dr.slug, dr.source_type, dr.developer_name,
        dr.manufacturer_name, dr.category, dr.protocol, dr.communication_direction,
        dv.version AS latest_version,
        GROUP_CONCAT(DISTINCT dt.name ORDER BY dt.name SEPARATOR ', ') AS compatible_device_types
    FROM drivers dr
    LEFT JOIN driver_versions dv ON dv.driver_id = dr.id
        AND dv.release_channel = 'stable'
        AND dv.is_published = TRUE
        AND dv.active_ind = TRUE
    LEFT JOIN driver_device_types ddt ON ddt.driver_id = dr.id
    LEFT JOIN device_types dt ON dt.id = ddt.device_type_id
    WHERE dr.active_ind = TRUE
    GROUP BY dr.id, dv.version
    """)


# ---------------------------------------------------------------------------
# downgrade
# ---------------------------------------------------------------------------
def downgrade() -> None:
    _exec("SET FOREIGN_KEY_CHECKS=0")

    for view in [
        "vw_driver_catalog", "vw_device_current_state", "vw_device_address_map",
        "vw_controller_status", "vw_studio_automation_list", "vw_studio_scene_list",
        "vw_studio_room_summary", "vw_studio_device_list", "vw_studio_project_kpis",
        "vw_open_support_tickets", "vw_inventory_stock_summary", "vw_we_okas_project_list",
        "vw_voice_exposed_entities", "vw_homekit_accessories", "vw_google_home_devices",
        "vw_alexa_discovery_endpoints",
    ]:
        _exec(f"DROP VIEW IF EXISTS {view}")

    for tbl in [
        # _ah audit tables
        "config_exports_ah", "support_tickets_ah", "inventory_items_ah",
        "alert_rules_ah", "automation_actions_ah", "automation_conditions_ah",
        "automation_triggers_ah", "automations_ah", "scene_actions_ah", "scenes_ah",
        "device_property_addresses_ah", "device_capabilities_ah", "devices_ah",
        "controllers_ah", "project_subscriptions_ah", "project_members_ah",
        "projects_ah", "homeowners_ah", "app_users_ah", "organizations_ah",
        "audit_logs",
        # access
        "access_group_device_permissions", "access_group_room_permissions",
        "access_group_members", "access_groups",
        "guest_access_devices", "guest_access_rooms", "guest_access_tokens",
        # drivers
        "driver_license_activations", "driver_licenses", "controller_drivers",
        "driver_device_types", "driver_versions", "drivers",
        # support
        "ticket_attachments", "ticket_comments", "support_tickets",
        # firmware / ota
        "config_exports", "device_lifecycle_events", "ota_job_targets", "ota_jobs",
        # docs / inventory
        "inventory_status_history", "project_inventory", "inventory_items",
        "inventory_categories", "project_documents",
        # voice & alerts
        "push_tokens", "notifications", "alert_rules",
        "voice_capability_map", "voice_exposed_entities", "voice_integrations",
        # state
        "automation_logs", "energy_readings", "device_state_history", "device_states",
        # scenes / automations
        "automation_actions", "automation_conditions", "automation_triggers",
        "automations", "scene_triggers", "scene_actions", "scenes",
        # devices
        "device_property_addresses", "device_capabilities", "device_rooms",
        "devices", "device_type_capability_templates",
        # controllers
        "device_platforms", "bus_settings", "controllers",
        # firmware releases & device_types (created early)
        "firmware_releases", "device_types",
        # location
        "rooms", "zones", "floors",
        # projects
        "project_subscriptions", "project_manager_history", "project_members",
        "project_owners", "projects", "subscription_plans",
        # auth
        "homeowner_sessions", "homeowner_otp_codes", "homeowners",
        "role_permissions", "app_sessions", "app_otp_codes",
        "app_user_roles", "app_users", "roles",
        "organization_locations", "organizations",
    ]:
        _exec(f"DROP TABLE IF EXISTS {tbl}")

    _exec("SET FOREIGN_KEY_CHECKS=1")

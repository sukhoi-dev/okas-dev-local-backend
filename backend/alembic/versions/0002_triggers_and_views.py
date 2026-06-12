"""triggers and views — 60 AFTER triggers + 16 views

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02

PREREQUISITE (run once in your terminal before upgrading):
    sudo mysql -e "SET GLOBAL log_bin_trust_function_creators = 1;"
"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None



def _exec(sql: str) -> None:
    op.execute(sql.strip())


def upgrade() -> None:
    # ── 60 AFTER TRIGGERS (20 tables × 3 operations) ─────────────────
    for src, ah, by_col in [
        ("organizations",             "organizations_ah",             "updated_by"),
        ("app_users",                 "app_users_ah",                 "updated_by"),
        ("homeowners",                "homeowners_ah",                "id"),
        ("projects",                  "projects_ah",                  "updated_by"),
        ("project_members",           "project_members_ah",           "assigned_by"),
        ("project_subscriptions",     "project_subscriptions_ah",     "updated_by"),
        ("controllers",               "controllers_ah",               "updated_by"),
        ("devices",                   "devices_ah",                   "updated_by"),
        ("device_capabilities",       "device_capabilities_ah",       "updated_by"),
        ("device_property_addresses", "device_property_addresses_ah", "updated_by"),
        ("scenes",                    "scenes_ah",                    "updated_by"),
        ("scene_actions",             "scene_actions_ah",             "updated_by"),
        ("automations",               "automations_ah",               "updated_by"),
        ("automation_triggers",       "automation_triggers_ah",       "updated_by"),
        ("automation_conditions",     "automation_conditions_ah",     "updated_by"),
        ("automation_actions",        "automation_actions_ah",        "updated_by"),
        ("alert_rules",               "alert_rules_ah",               "updated_by"),
        ("inventory_items",           "inventory_items_ah",           "updated_by"),
        ("support_tickets",           "support_tickets_ah",           "updated_by"),
        ("config_exports",            "config_exports_ah",            "updated_by"),
    ]:
        _exec(f"""
        CREATE TRIGGER trg_{src}_ai
        AFTER INSERT ON {src} FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          VALUES ('INSERT', NEW.{by_col}, NOW(3))
        """)

        _exec(f"""
        CREATE TRIGGER trg_{src}_au
        AFTER UPDATE ON {src} FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          VALUES ('UPDATE', NEW.{by_col}, NOW(3))
        """)

        _exec(f"""
        CREATE TRIGGER trg_{src}_ad
        AFTER DELETE ON {src} FOR EACH ROW
          INSERT INTO {ah} (ah_operation, ah_changed_by, ah_changed_at)
          VALUES ('DELETE', OLD.{by_col}, NOW(3))
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
        (SELECT COUNT(DISTINCT pi.project_id) FROM project_inventory pi
         WHERE pi.inventory_item_id = ii.id AND pi.active_ind = TRUE) AS projects_using
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
        (st.sla_due_at IS NOT NULL AND st.sla_due_at < NOW()
         AND st.status NOT IN ('resolved','closed')) AS sla_breached
    FROM support_tickets st
    LEFT JOIN app_users u1 ON u1.id = st.reported_by
    LEFT JOIN app_users u2 ON u2.id = st.assigned_to
    WHERE st.status != 'closed'
    """)

    _exec("""
    CREATE OR REPLACE VIEW vw_studio_project_kpis AS
    SELECT
        p.id AS project_id, p.name,
        (SELECT COUNT(*) FROM devices d
         WHERE d.project_id = p.id AND d.active_ind = TRUE) AS total_devices,
        (SELECT COUNT(*) FROM devices d
         WHERE d.project_id = p.id AND d.active_ind = TRUE AND d.is_online = TRUE) AS active_devices,
        (SELECT COUNT(DISTINCT s.room_id) FROM scenes s
         WHERE s.project_id = p.id AND s.room_id IS NOT NULL AND s.active_ind = TRUE) AS rooms_with_scenes,
        (SELECT COUNT(*) FROM automation_logs al
         WHERE al.project_id = p.id AND al.executed_at >= CURDATE()) AS auto_triggers_today,
        (SELECT COUNT(*) FROM alert_rules ar
         JOIN notifications n ON n.alert_rule_id = ar.id
         WHERE ar.project_id = p.id
           AND n.created_at >= DATE_SUB(NOW(), INTERVAL 24 HOUR)) AS open_alerts,
        (SELECT COALESCE(SUM(er.kwh),0) FROM energy_readings er
         WHERE er.project_id = p.id
           AND er.reading_hour >= DATE_SUB(NOW(), INTERVAL 30 DAY)) AS energy_kwh_30d
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
        (SELECT COUNT(*) FROM device_capabilities dc
         WHERE dc.device_id = d.id AND dc.active_ind = TRUE) AS capability_count,
        (SELECT COUNT(*) FROM device_property_addresses dpa
         JOIN device_capabilities dc2 ON dc2.id = dpa.capability_id
         WHERE dc2.device_id = d.id AND dpa.active_ind = TRUE) AS address_count
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
        (SELECT COUNT(*) FROM device_rooms dr
         JOIN devices d ON d.id = dr.device_id
         WHERE dr.room_id = r.id AND d.active_ind = TRUE AND dr.active_ind = TRUE) AS device_count,
        (SELECT COUNT(*) FROM device_rooms dr
         JOIN devices d ON d.id = dr.device_id
         WHERE dr.room_id = r.id AND d.active_ind = TRUE AND d.is_online = TRUE AND dr.active_ind = TRUE) AS online_device_count,
        (SELECT COUNT(*) FROM scenes s
         WHERE s.room_id = r.id AND s.active_ind = TRUE) AS scene_count,
        (SELECT COALESCE(SUM(er.kwh),0) FROM energy_readings er
         WHERE er.room_id = r.id AND er.reading_hour >= CURDATE()) AS energy_kwh_today
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
        (SELECT COUNT(*) FROM scene_actions sa
         WHERE sa.scene_id = s.id AND sa.active_ind = TRUE) AS action_count
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
        (SELECT COUNT(*) FROM automation_triggers atr
         WHERE atr.automation_id = a.id AND atr.active_ind = TRUE) AS trigger_count,
        (SELECT COUNT(*) FROM automation_actions aa
         WHERE aa.automation_id = a.id AND aa.active_ind = TRUE) AS action_count,
        (SELECT COUNT(*) FROM automation_logs al
         WHERE al.automation_id = a.id AND al.executed_at >= CURDATE()) AS runs_today
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
        (SELECT COUNT(*) FROM devices d
         WHERE d.project_id = c.project_id AND d.active_ind = TRUE) AS managed_device_count,
        (SELECT COUNT(*) FROM controller_drivers cd
         WHERE cd.controller_id = c.id AND cd.active_ind = TRUE
           AND cd.install_status = 'installed') AS installed_driver_count
    FROM controllers c
    LEFT JOIN firmware_releases fr
           ON fr.target_type = 'controller' AND fr.is_published = TRUE AND fr.active_ind = TRUE
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
    LEFT JOIN driver_versions dv
           ON dv.driver_id = dr.id AND dv.release_channel = 'stable'
          AND dv.is_published = TRUE AND dv.active_ind = TRUE
    LEFT JOIN driver_device_types ddt ON ddt.driver_id = dr.id
    LEFT JOIN device_types dt ON dt.id = ddt.device_type_id
    WHERE dr.active_ind = TRUE
    GROUP BY dr.id, dv.version
    """)


def downgrade() -> None:
    for view in [
        "vw_driver_catalog", "vw_device_current_state", "vw_device_address_map",
        "vw_controller_status", "vw_studio_automation_list", "vw_studio_scene_list",
        "vw_studio_room_summary", "vw_studio_device_list", "vw_studio_project_kpis",
        "vw_open_support_tickets", "vw_inventory_stock_summary", "vw_we_okas_project_list",
        "vw_voice_exposed_entities", "vw_homekit_accessories", "vw_google_home_devices",
        "vw_alexa_discovery_endpoints",
    ]:
        _exec(f"DROP VIEW IF EXISTS {view}")

    for src in [
        "organizations", "app_users", "homeowners", "projects", "project_members",
        "project_subscriptions", "controllers", "devices", "device_capabilities",
        "device_property_addresses", "scenes", "scene_actions", "automations",
        "automation_triggers", "automation_conditions", "automation_actions",
        "alert_rules", "inventory_items", "support_tickets", "config_exports",
    ]:
        for suffix in ("ai", "au", "ad"):
            _exec(f"DROP TRIGGER IF EXISTS trg_{src}_{suffix}")

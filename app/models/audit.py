from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, Integer, DECIMAL, Date, Time
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON, TINYINT
from app.models.base import Base

_AH_COLS = ("ah_id", "ah_operation", "ah_changed_at", "ah_changed_by")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    # actor_id        = Column(BIGINT(unsigned=True))   # not in live DB
    # actor_role      = Column(String(50))              # not in live DB
    user_id         = Column(BIGINT(unsigned=True))
    action          = Column(String(100), nullable=False)
    entity_type     = Column(String(50))
    entity_id       = Column(BIGINT(unsigned=True))
    organization_id = Column(BIGINT(unsigned=True))
    project_id      = Column(BIGINT(unsigned=True))
    old_value       = Column(JSON)
    new_value       = Column(JSON)
    ip_address      = Column(String(45))
    user_agent      = Column(Text)
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


def _ah_pk():
    return Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)

def _ah_op():
    return Column(Enum("INSERT", "UPDATE", "DELETE"), nullable=False)

def _ah_ts():
    return Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

def _ah_by():
    return Column(BIGINT(unsigned=True))


class OrganizationAh(Base):
    __tablename__ = "organizations_ah"
    ah_id         = _ah_pk()
    ah_operation  = _ah_op()
    ah_changed_at = _ah_ts()
    ah_changed_by = _ah_by()
    id            = Column(BIGINT(unsigned=True))
    name          = Column(String(255))
    slug          = Column(String(100))
    email         = Column(String(255))
    phone         = Column(String(50))
    address       = Column(Text)
    logo_url      = Column(String(500))
    active_ind    = Column(Boolean)
    updated_by    = Column(BIGINT(unsigned=True))
    created_at    = Column(DATETIME(fsp=3))
    updated_at    = Column(DATETIME(fsp=3))


class AppUserAh(Base):
    __tablename__ = "app_users_ah"
    ah_id           = _ah_pk()
    ah_operation    = _ah_op()
    ah_changed_at   = _ah_ts()
    ah_changed_by   = _ah_by()
    id              = Column(BIGINT(unsigned=True))
    organization_id = Column(BIGINT(unsigned=True))
    location_id     = Column(BIGINT(unsigned=True))
    email           = Column(String(255))
    phone           = Column(String(50))
    full_name       = Column(String(255))
    avatar_url      = Column(String(500))
    google_id       = Column(String(255))
    active_ind      = Column(Boolean)
    last_login_at   = Column(DATETIME(fsp=3))
    updated_by      = Column(BIGINT(unsigned=True))
    created_at      = Column(DATETIME(fsp=3))
    updated_at      = Column(DATETIME(fsp=3))


class HomeownerAh(Base):
    __tablename__ = "homeowners_ah"
    ah_id           = _ah_pk()
    ah_operation    = _ah_op()
    ah_changed_at   = _ah_ts()
    ah_changed_by   = _ah_by()
    id              = Column(BIGINT(unsigned=True))
    email           = Column(String(255))
    phone           = Column(String(50))
    full_name       = Column(String(255))
    avatar_url      = Column(String(500))
    google_id       = Column(String(255))
    preferred_login = Column(Enum("google", "otp"))
    active_ind      = Column(Boolean)
    last_login_at   = Column(DATETIME(fsp=3))
    created_at      = Column(DATETIME(fsp=3))
    updated_at      = Column(DATETIME(fsp=3))


class ProjectAh(Base):
    __tablename__ = "projects_ah"
    ah_id              = _ah_pk()
    ah_operation       = _ah_op()
    ah_changed_at      = _ah_ts()
    ah_changed_by      = _ah_by()
    id                 = Column(BIGINT(unsigned=True))
    organization_id    = Column(BIGINT(unsigned=True))
    project_manager_id = Column(BIGINT(unsigned=True))
    location_id        = Column(BIGINT(unsigned=True))
    name               = Column(String(255))
    serial_number      = Column(String(100))
    project_type       = Column(Enum("residential", "commercial", "hospitality", "retail", "other"))
    status             = Column(Enum("active", "inactive", "under_maintenance", "completed"))
    installed_at       = Column(DATETIME(fsp=3))
    address            = Column(Text)
    city               = Column(String(100))
    state              = Column(String(100))
    country            = Column(String(100))
    pincode            = Column(String(20))
    notes              = Column(Text)
    project_metadata   = Column("metadata", JSON)
    active_ind         = Column(Boolean)
    updated_by         = Column(BIGINT(unsigned=True))
    created_at         = Column(DATETIME(fsp=3))
    updated_at         = Column(DATETIME(fsp=3))


class ProjectMemberAh(Base):
    __tablename__ = "project_members_ah"
    ah_id         = _ah_pk()
    ah_operation  = _ah_op()
    ah_changed_at = _ah_ts()
    ah_changed_by = _ah_by()
    id            = Column(BIGINT(unsigned=True))
    project_id    = Column(BIGINT(unsigned=True))
    user_id       = Column(BIGINT(unsigned=True))
    role_id       = Column(BIGINT(unsigned=True))
    assigned_by   = Column(BIGINT(unsigned=True))
    active_ind    = Column(Boolean)
    assigned_at   = Column(DATETIME(fsp=3))


class ProjectSubscriptionAh(Base):
    __tablename__ = "project_subscriptions_ah"
    ah_id         = _ah_pk()
    ah_operation  = _ah_op()
    ah_changed_at = _ah_ts()
    ah_changed_by = _ah_by()
    id            = Column(BIGINT(unsigned=True))
    project_id    = Column(BIGINT(unsigned=True))
    plan_id       = Column(BIGINT(unsigned=True))
    status        = Column(Enum("trial", "active", "expired", "cancelled"))
    billing_cycle = Column(Enum("monthly", "yearly"))
    started_at    = Column(DATETIME(fsp=3))
    expires_at    = Column(DATETIME(fsp=3))
    updated_by    = Column(BIGINT(unsigned=True))
    created_at    = Column(DATETIME(fsp=3))
    updated_at    = Column(DATETIME(fsp=3))


class ControllerAh(Base):
    __tablename__ = "controllers_ah"
    ah_id                      = _ah_pk()
    ah_operation               = _ah_op()
    ah_changed_at              = _ah_ts()
    ah_changed_by              = _ah_by()
    id                         = Column(BIGINT(unsigned=True))
    project_id                 = Column(BIGINT(unsigned=True))
    serial_number              = Column(String(100))
    model                      = Column(String(100))
    firmware_version           = Column(String(50))
    firmware_release_id        = Column(BIGINT(unsigned=True))
    firmware_update_available  = Column(Boolean)
    ip_address                 = Column(String(45))
    mac_address                = Column(String(17))
    status                     = Column(Enum("online", "offline", "maintenance"))
    last_seen_at               = Column(DATETIME(fsp=3))
    config                     = Column(JSON)
    active_ind                 = Column(Boolean)
    updated_by                 = Column(BIGINT(unsigned=True))
    created_at                 = Column(DATETIME(fsp=3))
    updated_at                 = Column(DATETIME(fsp=3))


class DeviceAh(Base):
    __tablename__ = "devices_ah"
    ah_id                      = _ah_pk()
    ah_operation               = _ah_op()
    ah_changed_at              = _ah_ts()
    ah_changed_by              = _ah_by()
    id                         = Column(BIGINT(unsigned=True))
    project_id                 = Column(BIGINT(unsigned=True))
    device_type_id             = Column(BIGINT(unsigned=True))
    platform_id                = Column(BIGINT(unsigned=True))
    name                       = Column(String(100))
    device_number              = Column(String(50))
    icon                       = Column(String(100))
    display_categories         = Column(JSON)
    endpoint_id                = Column(String(255))
    cookie                     = Column(JSON)
    active_ind                 = Column(Boolean)
    is_online                  = Column(Boolean)
    last_seen_at               = Column(DATETIME(fsp=3))
    firmware_version           = Column(String(50))
    firmware_release_id        = Column(BIGINT(unsigned=True))
    firmware_update_available  = Column(Boolean)
    updated_by                 = Column(BIGINT(unsigned=True))
    created_at                 = Column(DATETIME(fsp=3))
    updated_at                 = Column(DATETIME(fsp=3))


class DeviceCapabilityAh(Base):
    __tablename__ = "device_capabilities_ah"
    ah_id                    = _ah_pk()
    ah_operation             = _ah_op()
    ah_changed_at            = _ah_ts()
    ah_changed_by            = _ah_by()
    id                       = Column(BIGINT(unsigned=True))
    device_id                = Column(BIGINT(unsigned=True))
    interface                = Column(String(100))
    version                  = Column(String(10))
    instance                 = Column(String(100))
    is_proactively_reported  = Column(Boolean)
    is_retrievable           = Column(Boolean)
    capability_resources     = Column(JSON)
    configuration            = Column(JSON)
    active_ind               = Column(Boolean)
    updated_by               = Column(BIGINT(unsigned=True))
    created_at               = Column(DATETIME(fsp=3))
    updated_at               = Column(DATETIME(fsp=3))


class DevicePropertyAddressAh(Base):
    __tablename__ = "device_property_addresses_ah"
    ah_id         = _ah_pk()
    ah_operation  = _ah_op()
    ah_changed_at = _ah_ts()
    ah_changed_by = _ah_by()
    id            = Column(BIGINT(unsigned=True))
    capability_id = Column(BIGINT(unsigned=True))
    property_name = Column(String(100))
    address_role  = Column(Enum("command", "state_feedback"))
    protocol      = Column(Enum("KNX", "Lutron", "Casambi", "Modbus", "BACnet", "IP", "IR"))
    address       = Column(String(255))
    data_type     = Column(String(50))
    scale_min     = Column(DECIMAL(10, 4))
    scale_max     = Column(DECIMAL(10, 4))
    invert        = Column(Boolean)
    active_ind    = Column(Boolean)
    updated_by    = Column(BIGINT(unsigned=True))
    created_at    = Column(DATETIME(fsp=3))


class SceneAh(Base):
    __tablename__ = "scenes_ah"
    ah_id         = _ah_pk()
    ah_operation  = _ah_op()
    ah_changed_at = _ah_ts()
    ah_changed_by = _ah_by()
    id            = Column(BIGINT(unsigned=True))
    project_id    = Column(BIGINT(unsigned=True))
    room_id       = Column(BIGINT(unsigned=True))
    name          = Column(String(100))
    icon          = Column(String(100))
    color         = Column(String(20))
    is_favorite   = Column(Boolean)
    voice_name    = Column(String(255))
    display_order = Column(Integer)
    active_ind    = Column(Boolean)
    created_by    = Column(BIGINT(unsigned=True))
    updated_by    = Column(BIGINT(unsigned=True))
    created_at    = Column(DATETIME(fsp=3))
    updated_at    = Column(DATETIME(fsp=3))


class SceneActionAh(Base):
    __tablename__ = "scene_actions_ah"
    ah_id          = _ah_pk()
    ah_operation   = _ah_op()
    ah_changed_at  = _ah_ts()
    ah_changed_by  = _ah_by()
    id             = Column(BIGINT(unsigned=True))
    scene_id       = Column(BIGINT(unsigned=True))
    device_id      = Column(BIGINT(unsigned=True))
    action_payload = Column(JSON)
    delay_ms       = Column(Integer)
    display_order  = Column(Integer)
    active_ind     = Column(Boolean)
    updated_by     = Column(BIGINT(unsigned=True))
    created_at     = Column(DATETIME(fsp=3))
    updated_at     = Column(DATETIME(fsp=3))


class AutomationAh(Base):
    __tablename__ = "automations_ah"
    ah_id              = _ah_pk()
    ah_operation       = _ah_op()
    ah_changed_at      = _ah_ts()
    ah_changed_by      = _ah_by()
    id                 = Column(BIGINT(unsigned=True))
    project_id         = Column(BIGINT(unsigned=True))
    name               = Column(String(100))
    description        = Column(Text)
    active_ind         = Column(Boolean)
    last_triggered_at  = Column(DATETIME(fsp=3))
    created_by         = Column(BIGINT(unsigned=True))
    updated_by         = Column(BIGINT(unsigned=True))
    created_at         = Column(DATETIME(fsp=3))
    updated_at         = Column(DATETIME(fsp=3))


class AutomationTriggerAh(Base):
    __tablename__ = "automation_triggers_ah"
    ah_id           = _ah_pk()
    ah_operation    = _ah_op()
    ah_changed_at   = _ah_ts()
    ah_changed_by   = _ah_by()
    id              = Column(BIGINT(unsigned=True))
    automation_id   = Column(BIGINT(unsigned=True))
    trigger_type    = Column(Enum("device_state", "time", "sunrise", "sunset", "scene_activated"))
    device_id       = Column(BIGINT(unsigned=True))
    device_property = Column(String(50))
    operator        = Column(Enum("eq", "neq", "gt", "gte", "lt", "lte"))
    trigger_value   = Column(String(100))
    trigger_time    = Column(Time)
    days_of_week    = Column(JSON)
    start_date      = Column(Date)
    end_date        = Column(Date)
    active_ind      = Column(Boolean)
    updated_by      = Column(BIGINT(unsigned=True))
    created_at      = Column(DATETIME(fsp=3))
    updated_at      = Column(DATETIME(fsp=3))


class AutomationConditionAh(Base):
    __tablename__ = "automation_conditions_ah"
    ah_id            = _ah_pk()
    ah_operation     = _ah_op()
    ah_changed_at    = _ah_ts()
    ah_changed_by    = _ah_by()
    id               = Column(BIGINT(unsigned=True))
    automation_id    = Column(BIGINT(unsigned=True))
    condition_type   = Column(Enum("device_state", "time_range", "day_of_week", "scene_active"))
    device_id        = Column(BIGINT(unsigned=True))
    device_property  = Column(String(50))
    operator         = Column(Enum("eq", "neq", "gt", "gte", "lt", "lte"))
    condition_value  = Column(String(100))
    start_time       = Column(Time)
    end_time         = Column(Time)
    days_of_week     = Column(JSON)
    logical_operator = Column(Enum("AND", "OR"))
    display_order    = Column(Integer)
    active_ind       = Column(Boolean)
    updated_by       = Column(BIGINT(unsigned=True))
    created_at       = Column(DATETIME(fsp=3))
    updated_at       = Column(DATETIME(fsp=3))


class AutomationActionAh(Base):
    __tablename__ = "automation_actions_ah"
    ah_id          = _ah_pk()
    ah_operation   = _ah_op()
    ah_changed_at  = _ah_ts()
    ah_changed_by  = _ah_by()
    id             = Column(BIGINT(unsigned=True))
    automation_id  = Column(BIGINT(unsigned=True))
    action_type    = Column(Enum("device_command", "scene_activate", "notify", "delay"))
    device_id      = Column(BIGINT(unsigned=True))
    scene_id       = Column(BIGINT(unsigned=True))
    action_payload = Column(JSON)
    delay_ms       = Column(Integer)
    display_order  = Column(Integer)
    active_ind     = Column(Boolean)
    updated_by     = Column(BIGINT(unsigned=True))
    created_at     = Column(DATETIME(fsp=3))
    updated_at     = Column(DATETIME(fsp=3))


class AlertRuleAh(Base):
    __tablename__ = "alert_rules_ah"
    ah_id           = _ah_pk()
    ah_operation    = _ah_op()
    ah_changed_at   = _ah_ts()
    ah_changed_by   = _ah_by()
    id              = Column(BIGINT(unsigned=True))
    project_id      = Column(BIGINT(unsigned=True))
    name            = Column(String(100))
    rule_type       = Column(Enum("device_offline", "energy_threshold", "error_count", "device_state"))
    device_id       = Column(BIGINT(unsigned=True))
    rule_condition  = Column(JSON)
    notify_channels = Column(JSON)
    active_ind      = Column(Boolean)
    updated_by      = Column(BIGINT(unsigned=True))
    created_at      = Column(DATETIME(fsp=3))
    updated_at      = Column(DATETIME(fsp=3))


class InventoryItemAh(Base):
    __tablename__ = "inventory_items_ah"
    ah_id               = _ah_pk()
    ah_operation        = _ah_op()
    ah_changed_at       = _ah_ts()
    ah_changed_by       = _ah_by()
    id                  = Column(BIGINT(unsigned=True))
    organization_id     = Column(BIGINT(unsigned=True))
    category_id         = Column(BIGINT(unsigned=True))
    device_type_id      = Column(BIGINT(unsigned=True))
    name                = Column(String(255))
    sku                 = Column(String(100))
    brand               = Column(String(100))
    model               = Column(String(100))
    description         = Column(Text)
    unit_cost           = Column(DECIMAL(10, 2))
    quantity_in_stock   = Column(Integer)
    quantity_reserved   = Column(Integer)
    low_stock_threshold = Column(Integer)
    item_metadata       = Column("metadata", JSON)
    status              = Column(Enum("ordered", "in_store", "installed"))
    received_at         = Column(DATETIME(fsp=3))
    installed_at        = Column(DATETIME(fsp=3))
    active_ind          = Column(Boolean)
    updated_by          = Column(BIGINT(unsigned=True))
    created_at          = Column(DATETIME(fsp=3))
    updated_at          = Column(DATETIME(fsp=3))


class SupportTicketAh(Base):
    __tablename__ = "support_tickets_ah"
    ah_id              = _ah_pk()
    ah_operation       = _ah_op()
    ah_changed_at      = _ah_ts()
    ah_changed_by      = _ah_by()
    id                 = Column(BIGINT(unsigned=True))
    ticket_number      = Column(String(30))
    organization_id    = Column(BIGINT(unsigned=True))
    project_id         = Column(BIGINT(unsigned=True))
    device_id          = Column(BIGINT(unsigned=True))
    reported_by        = Column(BIGINT(unsigned=True))
    assigned_to        = Column(BIGINT(unsigned=True))
    category           = Column(Enum("hardware", "software", "configuration", "network",
                                     "billing", "training", "other"))
    priority           = Column(Enum("low", "medium", "high", "critical"))
    status             = Column(Enum("open", "in_progress", "on_hold", "resolved", "closed"))
    title              = Column(String(255))
    description        = Column(Text)
    resolution         = Column(Text)
    first_response_at  = Column(DATETIME(fsp=3))
    sla_due_at         = Column(DATETIME(fsp=3))
    resolved_at        = Column(DATETIME(fsp=3))
    closed_at          = Column(DATETIME(fsp=3))
    updated_by         = Column(BIGINT(unsigned=True))
    created_at         = Column(DATETIME(fsp=3))
    updated_at         = Column(DATETIME(fsp=3))


class ConfigExportAh(Base):
    __tablename__ = "config_exports_ah"
    ah_id           = _ah_pk()
    ah_operation    = _ah_op()
    ah_changed_at   = _ah_ts()
    ah_changed_by   = _ah_by()
    id              = Column(BIGINT(unsigned=True))
    project_id      = Column(BIGINT(unsigned=True))
    controller_id   = Column(BIGINT(unsigned=True))
    version         = Column(Integer)
    version_label   = Column(String(50))
    file_format     = Column(Enum("json", "xml"))
    file_name       = Column(String(255))
    s3_bucket       = Column(String(255))
    s3_key          = Column(String(1000))
    s3_region       = Column(String(50))
    s3_version_id   = Column(String(255))
    content_type    = Column(String(100))
    file_size_bytes = Column(BIGINT(unsigned=True))
    checksum_sha256 = Column(String(64))
    export_status   = Column(Enum("pending", "completed", "failed"))
    exported_by     = Column(BIGINT(unsigned=True))
    exported_at     = Column(DATETIME(fsp=3))
    sync_direction  = Column(Enum("push", "pull"))
    sync_status     = Column(Enum("pending", "syncing", "synced", "failed", "superseded"))
    sync_attempts   = Column(Integer)
    synced_at       = Column(DATETIME(fsp=3))
    last_sync_error = Column(Text)
    is_current      = Column(Boolean)
    notes           = Column(Text)
    updated_by      = Column(BIGINT(unsigned=True))
    created_at      = Column(DATETIME(fsp=3))
    updated_at      = Column(DATETIME(fsp=3))

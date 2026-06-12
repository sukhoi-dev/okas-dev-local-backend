from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Integer, DECIMAL, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON, TINYINT
from app.models.base import Base


class DeviceType(Base):
    __tablename__ = "device_types"
    id                       = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name                     = Column(String(100), nullable=False, unique=True)
    category                 = Column(String(50), nullable=False)
    icon                     = Column(String(100))
    description              = Column("description_text", String(500))
    alexa_display_categories = Column(JSON)
    google_home_device_types = Column(JSON)
    homekit_category         = Column(String(50))
    ui_control_widget        = Column(String(50))
    active_ind               = Column(Boolean, nullable=False, default=True)
    display_order            = Column(Integer, default=0)


class DeviceTypeCapabilityTemplate(Base):
    __tablename__ = "device_type_capability_templates"
    id                  = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_type_id      = Column(BIGINT(unsigned=True), ForeignKey("device_types.id"), nullable=False)
    interface           = Column(String(100), nullable=False)
    version             = Column(String(10), default="3")
    instance            = Column(String(100))
    is_required         = Column(Boolean, nullable=False, default=True)
    expected_properties = Column(JSON)
    capability_resources = Column(JSON)
    configuration       = Column(JSON)
    display_order       = Column(Integer, default=0)
    active_ind          = Column(Boolean, nullable=False, default=True)


class Device(Base):
    __tablename__ = "devices"
    id                        = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id                = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    device_type_id            = Column(BIGINT(unsigned=True), ForeignKey("device_types.id"), nullable=False)
    platform_id               = Column(BIGINT(unsigned=True), ForeignKey("device_platforms.id"))
    name                      = Column(String(100), nullable=False)
    device_number             = Column(String(50))
    icon                      = Column(String(100))
    display_categories        = Column(JSON)
    endpoint_id               = Column(String(255), unique=True)
    cookie                    = Column(JSON)
    active_ind                = Column(Boolean, nullable=False, default=True)
    is_online                 = Column(Boolean, nullable=False, default=False)
    last_seen_at              = Column(DATETIME(fsp=3))
    firmware_version          = Column(String(50))
    firmware_release_id       = Column(BIGINT(unsigned=True), ForeignKey("firmware_releases.id"))
    firmware_update_available = Column(Boolean, nullable=False, default=False)
    updated_by                = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at                = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at                = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DeviceRoom(Base):
    __tablename__ = "device_rooms"
    __table_args__ = (UniqueConstraint("device_id", "room_id", name="uq_device_room"),)
    id         = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_id  = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    room_id    = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"), nullable=False)
    is_primary = Column(Boolean, nullable=False, default=False)
    active_ind = Column(Boolean, nullable=False, default=True)
    created_at = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class DeviceCapability(Base):
    __tablename__ = "device_capabilities"
    __table_args__ = (UniqueConstraint("device_id", "interface", "instance", name="uq_device_interface_instance"),)
    id                     = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_id              = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    interface              = Column(String(100), nullable=False)
    version                = Column(String(10), default="3")
    instance               = Column(String(100))
    is_proactively_reported = Column(Boolean, nullable=False, default=False)
    is_retrievable         = Column(Boolean, nullable=False, default=True)
    capability_resources   = Column(JSON)
    configuration          = Column(JSON)
    active_ind             = Column(Boolean, nullable=False, default=True)
    updated_by             = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at             = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at             = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DevicePropertyAddress(Base):
    __tablename__ = "device_property_addresses"
    __table_args__ = (UniqueConstraint("capability_id", "property_name", "address_role", name="uq_cap_property_role"),)
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    capability_id = Column(BIGINT(unsigned=True), ForeignKey("device_capabilities.id"), nullable=False)
    property_name = Column(String(100), nullable=False)
    address_role  = Column(Enum("command", "state_feedback"), nullable=False)
    protocol      = Column(Enum("KNX", "Lutron", "Casambi", "Modbus", "BACnet", "IP", "IR"), nullable=False)
    address       = Column(String(255), nullable=False)
    data_type     = Column(String(50))
    scale_min     = Column(DECIMAL(10, 4))
    scale_max     = Column(DECIMAL(10, 4))
    invert        = Column(Boolean, nullable=False, default=False)
    active_ind    = Column(Boolean, nullable=False, default=True)
    updated_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Integer
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class Controller(Base):
    __tablename__ = "controllers"
    id                       = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id               = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    serial_number            = Column(String(100), nullable=False, unique=True)
    model                    = Column(String(100), default="OKAS Signature")
    firmware_version         = Column(String(50))
    firmware_release_id      = Column(BIGINT(unsigned=True), ForeignKey("firmware_releases.id"))
    firmware_update_available = Column(Boolean, nullable=False, default=False)
    ip_address               = Column(String(45))
    mac_address              = Column(String(17))
    status                   = Column(Enum("online", "offline", "maintenance"), nullable=False, default="offline")
    last_seen_at             = Column(DATETIME(fsp=3))
    config                   = Column(JSON)
    active_ind               = Column(Boolean, nullable=False, default=True)
    updated_by               = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at               = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at               = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class BusSetting(Base):
    __tablename__ = "bus_settings"
    id                 = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    controller_id      = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"), nullable=False)
    bus_type           = Column(Enum("KNX_IP", "KNX_TP", "Lutron", "Casambi", "Modbus", "BACnet"), nullable=False)
    ip_address         = Column(String(45))
    port               = Column(Integer)
    individual_address = Column(String(20))
    extra_config       = Column(JSON)
    active_ind         = Column(Boolean, nullable=False, default=True)
    updated_by         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DevicePlatform(Base):
    __tablename__ = "device_platforms"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id     = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    controller_id  = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"), nullable=False)
    platform_type  = Column(Enum("KNX", "Lutron", "Casambi", "Modbus", "BACnet", "WiFi", "Zigbee", "Other"), nullable=False)
    name           = Column(String(100))
    ip_address     = Column(String(45))
    port           = Column(Integer)
    driver_version = Column(String(50))
    config         = Column(JSON)
    active_ind     = Column(Boolean, nullable=False, default=True)
    updated_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

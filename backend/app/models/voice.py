from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class VoiceIntegration(Base):
    __tablename__ = "voice_integrations"
    id                        = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    homeowner_id              = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"), nullable=False)
    project_id                = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    platform                  = Column(Enum("alexa", "google_home", "siri"), nullable=False)
    access_token_encrypted    = Column(Text)
    refresh_token_encrypted   = Column(Text)
    token_expires_at          = Column(DATETIME(fsp=3))
    platform_user_id          = Column(String(255))
    active_ind                = Column(Boolean, nullable=False, default=True)
    updated_by                = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    linked_at                 = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at                = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class VoiceExposedEntity(Base):
    __tablename__ = "voice_exposed_entities"
    id                   = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    voice_integration_id = Column(BIGINT(unsigned=True), ForeignKey("voice_integrations.id"), nullable=False)
    entity_type          = Column(Enum("device", "scene"), nullable=False)
    device_id            = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    scene_id             = Column(BIGINT(unsigned=True), ForeignKey("scenes.id"))
    friendly_name        = Column(String(255))
    platform_endpoint_id = Column(String(255))
    active_ind           = Column(Boolean, nullable=False, default=True)
    updated_by           = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at           = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at           = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class VoiceCapabilityMap(Base):
    __tablename__ = "voice_capability_map"
    id                    = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    capability_interface  = Column(String(100), nullable=False, unique=True)
    alexa_interface       = Column(String(100))
    google_home_trait     = Column(String(100))
    homekit_service       = Column(String(100))
    homekit_characteristics = Column(JSON)
    google_attributes     = Column(JSON)
    notes                 = Column(String(255))
    active_ind            = Column(Boolean, nullable=False, default=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id       = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    name             = Column(String(100), nullable=False)
    rule_type        = Column(Enum("device_offline", "energy_threshold", "error_count", "device_state"), nullable=False)
    device_id        = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    rule_condition   = Column(JSON)
    notify_channels  = Column(JSON)
    active_ind       = Column(Boolean, nullable=False, default=True)
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class Notification(Base):
    __tablename__ = "notifications"
    id                = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id           = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    project_id        = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    alert_rule_id     = Column(BIGINT(unsigned=True), ForeignKey("alert_rules.id"))
    title             = Column(String(255), nullable=False)
    body              = Column(Text)
    notification_type = Column(Enum("alert", "info", "automation", "system", "device_error"), nullable=False)
    is_read           = Column(Boolean, nullable=False, default=False)
    read_at           = Column(DATETIME(fsp=3))
    created_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class PushToken(Base):
    __tablename__ = "push_tokens"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    homeowner_id = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"), nullable=False)
    token        = Column(String(500), nullable=False, unique=True)
    platform     = Column(Enum("ios", "android"), nullable=False)
    device_id    = Column(String(255))
    active_ind   = Column(Boolean, nullable=False, default=True)
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, Integer, Date, Time
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class Scene(Base):
    __tablename__ = "scenes"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id    = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    room_id       = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"))
    name          = Column(String(100), nullable=False)
    icon          = Column(String(100))
    color         = Column(String(20))
    is_favorite   = Column(Boolean, nullable=False, default=False)
    voice_name    = Column(String(255))
    display_order = Column(Integer, default=0)
    active_ind    = Column(Boolean, nullable=False, default=True)
    created_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    updated_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class SceneAction(Base):
    __tablename__ = "scene_actions"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    scene_id       = Column(BIGINT(unsigned=True), ForeignKey("scenes.id"), nullable=False)
    device_id      = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    action_payload = Column(JSON)
    delay_ms       = Column(Integer, default=0)
    display_order  = Column(Integer, default=0)
    active_ind     = Column(Boolean, nullable=False, default=True)
    updated_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class SceneTrigger(Base):
    __tablename__ = "scene_triggers"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    scene_id        = Column(BIGINT(unsigned=True), ForeignKey("scenes.id"), nullable=False)
    trigger_type    = Column(Enum("device_input", "time", "sunrise", "sunset", "voice"), nullable=False)
    device_id       = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    trigger_input   = Column(String(50))
    trigger_time    = Column(Time)
    days_of_week    = Column(JSON)
    offset_minutes  = Column(Integer, default=0)
    voice_phrase    = Column(String(255))
    active_ind      = Column(Boolean, nullable=False, default=True)
    updated_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class Automation(Base):
    __tablename__ = "automations"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id       = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    name             = Column(String(100), nullable=False)
    description      = Column(Text)
    active_ind       = Column(Boolean, nullable=False, default=True)
    last_triggered_at = Column(DATETIME(fsp=3))
    created_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AutomationTrigger(Base):
    __tablename__ = "automation_triggers"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    automation_id   = Column(BIGINT(unsigned=True), ForeignKey("automations.id"), nullable=False)
    trigger_type    = Column(Enum("device_state", "time", "sunrise", "sunset", "scene_activated"), nullable=False)
    device_id       = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    device_property = Column(String(50))
    operator        = Column(Enum("eq", "neq", "gt", "gte", "lt", "lte"))
    trigger_value   = Column(String(100))
    trigger_time    = Column(Time)
    days_of_week    = Column(JSON)
    start_date      = Column(Date)
    end_date        = Column(Date)
    active_ind      = Column(Boolean, nullable=False, default=True)
    updated_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AutomationCondition(Base):
    __tablename__ = "automation_conditions"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    automation_id    = Column(BIGINT(unsigned=True), ForeignKey("automations.id"), nullable=False)
    condition_type   = Column(Enum("device_state", "time_range", "day_of_week", "scene_active"), nullable=False)
    device_id        = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    device_property  = Column(String(50))
    operator         = Column(Enum("eq", "neq", "gt", "gte", "lt", "lte"))
    condition_value  = Column(String(100))
    start_time       = Column(Time)
    end_time         = Column(Time)
    days_of_week     = Column(JSON)
    logical_operator = Column(Enum("AND", "OR"), nullable=False, default="AND")
    display_order    = Column(Integer, default=0)
    active_ind       = Column(Boolean, nullable=False, default=True)
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AutomationAction(Base):
    __tablename__ = "automation_actions"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    automation_id  = Column(BIGINT(unsigned=True), ForeignKey("automations.id"), nullable=False)
    action_type    = Column(Enum("device_command", "scene_activate", "notify", "delay"), nullable=False)
    device_id      = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    scene_id       = Column(BIGINT(unsigned=True), ForeignKey("scenes.id"))
    action_payload = Column(JSON)
    delay_ms       = Column(Integer, default=0)
    display_order  = Column(Integer, default=0)
    active_ind     = Column(Boolean, nullable=False, default=True)
    updated_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

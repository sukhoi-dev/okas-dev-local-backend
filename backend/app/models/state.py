from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Integer, DECIMAL
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON, TINYINT
from app.models.base import Base


class DeviceState(Base):
    __tablename__ = "device_states"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_id    = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False, unique=True)
    state        = Column(JSON)
    is_on        = Column(Boolean)
    brightness   = Column(TINYINT(unsigned=True))
    color_temp_k = Column(Integer)
    rgb          = Column(String(20))
    position     = Column(TINYINT(unsigned=True))
    temperature  = Column(DECIMAL(5, 2))
    updated_by   = Column(BIGINT(unsigned=True))
    updated_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DeviceStateHistory(Base):
    """Range-partitioned by YEAR(recorded_at)*100+MONTH(recorded_at).
    Composite PK (id, recorded_at) required by MySQL partitioning — ORM uses id only."""
    __tablename__ = "device_state_history"
    id                   = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_id            = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    state                = Column(JSON)
    is_on                = Column(Boolean)
    brightness           = Column(TINYINT(unsigned=True))
    temperature          = Column(DECIMAL(5, 2))
    triggered_by         = Column(Enum("user", "automation", "scene", "keypad", "alexa", "google_home", "api", "schedule"))
    triggered_by_user_id = Column(BIGINT(unsigned=True))
    recorded_at          = Column(DATETIME(fsp=3), primary_key=True, nullable=False)


class EnergyReading(Base):
    """Range-partitioned by YEAR(reading_hour)*100+MONTH(reading_hour).
    Composite PK (id, reading_hour) required by MySQL partitioning — ORM uses both."""
    __tablename__ = "energy_readings"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id   = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    device_id    = Column(BIGINT(unsigned=True))
    room_id      = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"))
    kwh          = Column(DECIMAL(10, 4), nullable=False)
    reading_hour = Column(DATETIME(fsp=0), primary_key=True, nullable=False)
    recorded_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AutomationLog(Base):
    __tablename__ = "automation_logs"
    id                 = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    automation_id      = Column(BIGINT(unsigned=True), ForeignKey("automations.id"), nullable=False)
    project_id         = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    triggered_by_type  = Column(Enum("device_state", "time", "manual", "api"), nullable=False)
    trigger_detail     = Column(JSON)
    status             = Column(Enum("success", "partial", "failed"), nullable=False)
    actions_executed   = Column(Integer, default=0)
    error_detail       = Column(String(1000))
    executed_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Integer, DECIMAL
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from app.models.base import Base


class Floor(Base):
    __tablename__ = "floors"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id     = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    name           = Column(String(100), nullable=False)
    short_code     = Column(String(20))
    floor_number   = Column(Integer, nullable=False, default=0)
    floor_plan_url = Column(String(500))
    display_order  = Column(Integer, default=0)
    active_ind     = Column(Boolean, nullable=False, default=True)
    updated_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class Zone(Base):
    __tablename__ = "zones"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id     = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    parent_zone_id = Column(BIGINT(unsigned=True), ForeignKey("zones.id"))
    name           = Column(String(100), nullable=False)
    zone_type      = Column(Enum("zone", "sub_zone"), nullable=False, default="zone")
    display_order  = Column(Integer, default=0)
    active_ind     = Column(Boolean, nullable=False, default=True)
    updated_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class Room(Base):
    __tablename__ = "rooms"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    floor_id      = Column(BIGINT(unsigned=True), ForeignKey("floors.id"), nullable=False)
    zone_id       = Column(BIGINT(unsigned=True), ForeignKey("zones.id"))
    name          = Column(String(100), nullable=False)
    room_type     = Column(Enum("living_room", "bedroom", "kitchen", "bathroom", "dining_room",
                                "study", "garage", "utility", "outdoor", "other"), nullable=False, default="other")
    image_url     = Column(String(500))
    area_sqft     = Column(DECIMAL(8, 2))
    display_order = Column(Integer, default=0)
    active_ind    = Column(Boolean, nullable=False, default=True)
    updated_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

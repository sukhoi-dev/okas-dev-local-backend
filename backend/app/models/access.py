from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, Integer
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from app.models.base import Base


class GuestAccessToken(Base):
    __tablename__ = "guest_access_tokens"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    token_hash   = Column(String(64), nullable=False, unique=True)
    label        = Column(String(150))
    project_id   = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    scope_type   = Column(Enum("project", "room", "custom"), nullable=False)
    room_id      = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"))
    access_level = Column(Enum("view_only", "control"), nullable=False, default="view_only")
    is_enabled   = Column(Boolean, nullable=False, default=True)
    max_uses     = Column(Integer)
    use_count    = Column(Integer, nullable=False, default=0)
    expires_at   = Column(DATETIME(fsp=3))
    first_used_at = Column(DATETIME(fsp=3))
    last_used_at  = Column(DATETIME(fsp=3))
    is_revoked   = Column(Boolean, nullable=False, default=False)
    revoked_by   = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"))
    revoked_at   = Column(DATETIME(fsp=3))
    created_by   = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"))
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class GuestAccessRoom(Base):
    __tablename__ = "guest_access_rooms"
    id                    = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    guest_access_token_id = Column(BIGINT(unsigned=True), ForeignKey("guest_access_tokens.id"), nullable=False)
    room_id               = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"), nullable=False)
    can_view              = Column(Boolean, nullable=False, default=True)
    can_control           = Column(Boolean, nullable=False, default=False)
    created_at            = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class GuestAccessDevice(Base):
    __tablename__ = "guest_access_devices"
    id                    = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    guest_access_token_id = Column(BIGINT(unsigned=True), ForeignKey("guest_access_tokens.id"), nullable=False)
    device_id             = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    can_view              = Column(Boolean, nullable=False, default=True)
    can_control           = Column(Boolean, nullable=False, default=False)
    created_at            = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AccessGroup(Base):
    __tablename__ = "access_groups"
    id          = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id  = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    name        = Column(String(100), nullable=False)
    description = Column(Text)
    active_ind  = Column(Boolean, nullable=False, default=True)
    created_by  = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    updated_by  = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AccessGroupMember(Base):
    __tablename__ = "access_group_members"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    access_group_id = Column(BIGINT(unsigned=True), ForeignKey("access_groups.id"), nullable=False)
    user_id         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    added_by        = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    active_ind      = Column(Boolean, nullable=False, default=True)
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AccessGroupRoomPermission(Base):
    __tablename__ = "access_group_room_permissions"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    access_group_id = Column(BIGINT(unsigned=True), ForeignKey("access_groups.id"), nullable=False)
    room_id         = Column(BIGINT(unsigned=True), ForeignKey("rooms.id"), nullable=False)
    can_view        = Column(Boolean, nullable=False, default=True)
    can_control     = Column(Boolean, nullable=False, default=False)
    active_ind      = Column(Boolean, nullable=False, default=True)
    granted_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AccessGroupDevicePermission(Base):
    __tablename__ = "access_group_device_permissions"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    access_group_id = Column(BIGINT(unsigned=True), ForeignKey("access_groups.id"), nullable=False)
    device_id       = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    can_view        = Column(Boolean, nullable=False, default=True)
    can_control     = Column(Boolean, nullable=False, default=False)
    active_ind      = Column(Boolean, nullable=False, default=True)
    granted_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class Organization(Base):
    __tablename__ = "organizations"
    id                     = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    org_type               = Column(Enum("distributor", "si"), nullable=False, default="si")
    parent_organization_id = Column(BIGINT(unsigned=True), ForeignKey("organizations.id", use_alter=True, name="fk_org_parent"))
    name                   = Column(String(255), nullable=False)
    contact_name           = Column(String(255))
    slug                   = Column(String(100), nullable=False, unique=True)
    email                  = Column(String(255))
    phone                  = Column(String(50))
    address                = Column(Text)
    gst_vat_number         = Column(String(50))
    logo_url               = Column(String(500))
    active_ind             = Column(Boolean, nullable=False, default=True)
    is_archived            = Column(Boolean, nullable=False, default=False)
    updated_by             = Column(BIGINT(unsigned=True), ForeignKey("app_users.id", use_alter=True, name="fk_org_updated_by"))
    created_at             = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at             = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class OrganizationLocation(Base):
    __tablename__ = "organization_locations"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    organization_id = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    name            = Column(String(150), nullable=False)
    location_type   = Column(Enum("head_office", "branch", "warehouse", "site"), nullable=False)
    address         = Column(Text)
    city            = Column(String(100))
    state           = Column(String(100))
    country         = Column(String(100))
    pincode         = Column(String(20))
    active_ind      = Column(Boolean, nullable=False, default=True)
    updated_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id", use_alter=True, name="fk_org_loc_updated_by"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class AppUser(Base):
    __tablename__ = "app_users"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    organization_id = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    location_id     = Column(BIGINT(unsigned=True), ForeignKey("organization_locations.id"))
    email           = Column(String(255), nullable=False, unique=True)
    phone           = Column(String(50))
    full_name       = Column(String(255))
    avatar_url      = Column(String(500))
    google_id       = Column(String(255), unique=True)
    active_ind      = Column(Boolean, nullable=False, default=True)
    last_login_at   = Column(DATETIME(fsp=3))
    updated_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class Role(Base):
    __tablename__ = "roles"
    id          = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name        = Column(String(50), nullable=False, unique=True)
    description = Column(Text)
    created_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AppUserRole(Base):
    __tablename__ = "app_user_roles"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    role_id         = Column(BIGINT(unsigned=True), ForeignKey("roles.id"), nullable=False)
    organization_id = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AppOtpCode(Base):
    __tablename__ = "app_otp_codes"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    phone_or_email = Column(String(255), nullable=False)
    code_hash      = Column(String(255), nullable=False)
    purpose        = Column(Enum("login", "password_reset", "verify_email"), nullable=False)
    expires_at     = Column(DATETIME(fsp=3), nullable=False)
    used_at        = Column(DATETIME(fsp=3))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class AppSession(Base):
    __tablename__ = "app_sessions"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    user_id        = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    token_hash     = Column(String(255), nullable=False, unique=True)
    device_info    = Column(JSON)
    ip_address     = Column(String(45))
    expires_at     = Column(DATETIME(fsp=3), nullable=False)
    last_active_at = Column(DATETIME(fsp=3))
    created_at     = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    id         = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    role_id    = Column(BIGINT(unsigned=True), ForeignKey("roles.id"), nullable=False)
    feature    = Column(String(50), nullable=False)
    action     = Column(String(20), nullable=False)
    is_allowed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class Homeowner(Base):
    __tablename__ = "homeowners"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    email           = Column(String(255), nullable=False, unique=True)
    phone           = Column(String(50))
    full_name       = Column(String(255))
    avatar_url      = Column(String(500))
    google_id       = Column(String(255), unique=True)
    preferred_login = Column(Enum("google", "otp"), nullable=False, default="otp")
    active_ind      = Column(Boolean, nullable=False, default=True)
    last_login_at   = Column(DATETIME(fsp=3))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class HomeownerOtpCode(Base):
    __tablename__ = "homeowner_otp_codes"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    homeowner_id = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"))
    email        = Column(String(255))
    phone        = Column(String(50))
    otp_hash     = Column(String(255), nullable=False)
    channel      = Column(Enum("email", "sms"), nullable=False)
    purpose      = Column(Enum("login", "phone_verify"), nullable=False)
    expires_at   = Column(DATETIME(fsp=3), nullable=False)
    used_at      = Column(DATETIME(fsp=3))
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class HomeownerSession(Base):
    __tablename__ = "homeowner_sessions"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    homeowner_id = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"), nullable=False)
    token_hash   = Column(String(255), nullable=False, unique=True)
    device_name  = Column(String(255))
    device_type  = Column(Enum("mobile", "browser", "unknown"), nullable=False, default="unknown")
    ip_address   = Column(String(45))
    user_agent   = Column(Text)
    expires_at   = Column(DATETIME(fsp=3), nullable=False)
    revoked_at   = Column(DATETIME(fsp=3))
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

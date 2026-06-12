from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, DECIMAL
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name          = Column(String(100), nullable=False, unique=True)
    description   = Column(Text)
    price_monthly = Column(DECIMAL(10, 2))
    price_yearly  = Column(DECIMAL(10, 2))
    features      = Column(JSON)
    active_ind    = Column(Boolean, nullable=False, default=True)
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class Project(Base):
    __tablename__ = "projects"
    id                 = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    organization_id    = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    project_manager_id = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    location_id        = Column(BIGINT(unsigned=True), ForeignKey("organization_locations.id"))
    name               = Column(String(255), nullable=False)
    serial_number      = Column(String(100), unique=True)
    project_type       = Column(Enum("residential", "commercial", "hospitality", "retail", "other"), nullable=False)
    status             = Column(Enum("active", "inactive", "under_maintenance", "completed"), nullable=False, default="active")
    installed_at       = Column(DATETIME(fsp=3))
    address            = Column(Text)
    city               = Column(String(100))
    state              = Column(String(100))
    country            = Column(String(100))
    pincode            = Column(String(20))
    notes              = Column(Text)
    project_metadata   = Column("metadata", JSON)
    active_ind         = Column(Boolean, nullable=False, default=True)
    updated_by         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class ProjectOwner(Base):
    __tablename__ = "project_owners"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id   = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    homeowner_id = Column(BIGINT(unsigned=True), ForeignKey("homeowners.id"), nullable=False)
    is_primary   = Column(Boolean, nullable=False, default=False)
    active_ind   = Column(Boolean, nullable=False, default=True)
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class ProjectMember(Base):
    __tablename__ = "project_members"
    id          = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id  = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    user_id     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    role_id     = Column(BIGINT(unsigned=True), ForeignKey("roles.id"), nullable=False)
    assigned_by = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    active_ind  = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class ProjectManagerHistory(Base):
    __tablename__ = "project_manager_history"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id    = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    user_id       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    assigned_by   = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    assigned_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    unassigned_at = Column(DATETIME(fsp=3))
    reason        = Column(String(255))


class ProjectSubscription(Base):
    __tablename__ = "project_subscriptions"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id    = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    plan_id       = Column(BIGINT(unsigned=True), ForeignKey("subscription_plans.id"), nullable=False)
    status        = Column(Enum("trial", "active", "expired", "cancelled"), nullable=False)
    billing_cycle = Column(Enum("monthly", "yearly"), nullable=False)
    started_at    = Column(DATETIME(fsp=3))
    expires_at    = Column(DATETIME(fsp=3))
    updated_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


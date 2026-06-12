from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, Integer, DECIMAL
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON
from app.models.base import Base


class ProjectDocument(Base):
    __tablename__ = "project_documents"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id       = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    uploaded_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    category         = Column(Enum("project_plan", "wiring_diagram", "knx_ets_file",
                                   "commissioning_report", "warranty", "manual", "photo", "other"), nullable=False)
    file_name        = Column(String(255), nullable=False)
    s3_bucket        = Column(String(255))
    s3_key           = Column(String(1000))
    s3_region        = Column(String(50), default="ap-south-1")
    content_type     = Column(String(100))
    file_size_bytes  = Column(BIGINT(unsigned=True))
    checksum_sha256  = Column(String(64))
    upload_status    = Column(Enum("pending", "completed", "failed"), nullable=False, default="pending")
    is_deleted       = Column(Boolean, nullable=False, default=False)
    deleted_at       = Column(DATETIME(fsp=3))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class InventoryCategory(Base):
    __tablename__ = "inventory_categories"
    id         = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name       = Column(String(100), nullable=False)
    parent_id  = Column(BIGINT(unsigned=True), ForeignKey("inventory_categories.id"))
    active_ind = Column(Boolean, nullable=False, default=True)


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id                  = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    organization_id     = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    category_id         = Column(BIGINT(unsigned=True), ForeignKey("inventory_categories.id"))
    device_type_id      = Column(BIGINT(unsigned=True), ForeignKey("device_types.id"))
    name                = Column(String(255), nullable=False)
    sku                 = Column(String(100))
    brand               = Column(String(100))
    model               = Column(String(100))
    description         = Column(Text)
    unit_cost           = Column(DECIMAL(10, 2))
    quantity_in_stock   = Column(Integer, nullable=False, default=0)
    quantity_reserved   = Column(Integer, nullable=False, default=0)
    low_stock_threshold = Column(Integer, default=0)
    item_metadata       = Column("metadata", JSON)
    status              = Column(Enum("ordered", "in_store", "installed"), nullable=False, default="in_store")
    received_at         = Column(DATETIME(fsp=3))
    installed_at        = Column(DATETIME(fsp=3))
    active_ind          = Column(Boolean, nullable=False, default=True)
    updated_by          = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at          = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at          = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class ProjectInventory(Base):
    __tablename__ = "project_inventory"
    id                = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id        = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    inventory_item_id = Column(BIGINT(unsigned=True), ForeignKey("inventory_items.id"), nullable=False)
    quantity_used     = Column(Integer, nullable=False, default=1)
    device_id         = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    installed_at      = Column(DATETIME(fsp=3))
    notes             = Column(Text)
    active_ind        = Column(Boolean, nullable=False, default=True)
    updated_by        = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class InventoryStatusHistory(Base):
    __tablename__ = "inventory_status_history"
    id                = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    inventory_item_id = Column(BIGINT(unsigned=True), ForeignKey("inventory_items.id"), nullable=False)
    from_status       = Column(Enum("ordered", "in_store", "installed"), nullable=False)
    to_status         = Column(Enum("ordered", "in_store", "installed"), nullable=False)
    changed_by        = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    notes             = Column(Text)
    created_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

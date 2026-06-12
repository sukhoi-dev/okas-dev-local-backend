from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum, Integer
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, JSON, TINYINT
from app.models.base import Base


class FirmwareRelease(Base):
    __tablename__ = "firmware_releases"
    id                        = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    target_type               = Column(Enum("controller", "device"), nullable=False)
    device_type_id            = Column(BIGINT(unsigned=True), ForeignKey("device_types.id"))
    version                   = Column(String(50), nullable=False)
    release_channel           = Column(Enum("stable", "beta", "rc"), nullable=False, default="stable")
    release_notes             = Column(Text)
    s3_bucket                 = Column(String(255))
    s3_key                    = Column(String(1000))
    checksum_sha256           = Column(String(64))
    file_size_bytes           = Column(BIGINT(unsigned=True))
    min_supported_from_version = Column(String(50))
    active_ind                = Column(Boolean, nullable=False, default=True)
    is_published              = Column(Boolean, nullable=False, default=False)
    released_at               = Column(DATETIME(fsp=3))
    released_by               = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    updated_by                = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at                = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at                = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class OtaJob(Base):
    __tablename__ = "ota_jobs"
    id                 = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name               = Column(String(255), nullable=False)
    firmware_release_id = Column(BIGINT(unsigned=True), ForeignKey("firmware_releases.id"), nullable=False)
    target_type        = Column(Enum("controller", "device", "all"), nullable=False)
    status             = Column(Enum("draft", "scheduled", "in_progress", "completed", "failed", "cancelled"), nullable=False, default="draft")
    scheduled_at       = Column(DATETIME(fsp=3))
    started_at         = Column(DATETIME(fsp=3))
    completed_at       = Column(DATETIME(fsp=3))
    created_by         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    updated_by         = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at         = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class OtaJobTarget(Base):
    __tablename__ = "ota_job_targets"
    id            = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    ota_job_id    = Column(BIGINT(unsigned=True), ForeignKey("ota_jobs.id"), nullable=False)
    target_type   = Column(Enum("controller", "device"), nullable=False)
    controller_id = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"))
    device_id     = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    from_version  = Column(String(50))
    to_version    = Column(String(50))
    status        = Column(Enum("pending", "downloading", "installing", "success", "failed", "skipped"), nullable=False, default="pending")
    progress_pct  = Column(TINYINT(unsigned=True), default=0)
    error_message = Column(Text)
    started_at    = Column(DATETIME(fsp=3))
    completed_at  = Column(DATETIME(fsp=3))
    created_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class DeviceLifecycleEvent(Base):
    __tablename__ = "device_lifecycle_events"
    id           = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    device_id    = Column(BIGINT(unsigned=True), ForeignKey("devices.id"), nullable=False)
    event_type   = Column(Enum("commissioned", "decommissioned", "replaced", "firmware_updated",
                               "factory_reset", "repaired", "moved", "retired"), nullable=False)
    old_value    = Column(JSON)
    new_value    = Column(JSON)
    notes        = Column(Text)
    performed_by = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at   = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")


class ConfigExport(Base):
    __tablename__ = "config_exports"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    project_id      = Column(BIGINT(unsigned=True), ForeignKey("projects.id"), nullable=False)
    controller_id   = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"))
    version         = Column(Integer, nullable=False)
    version_label   = Column(String(50))
    file_format     = Column(Enum("json", "xml"), nullable=False, default="json")
    file_name       = Column(String(255))
    s3_bucket       = Column(String(255))
    s3_key          = Column(String(1000))
    s3_region       = Column(String(50), default="ap-south-1")
    s3_version_id   = Column(String(255))
    content_type    = Column(String(100))
    file_size_bytes = Column(BIGINT(unsigned=True))
    checksum_sha256 = Column(String(64))
    export_status   = Column(Enum("pending", "completed", "failed"), nullable=False, default="pending")
    exported_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    exported_at     = Column(DATETIME(fsp=3))
    sync_direction  = Column(Enum("push", "pull"), nullable=False, default="push")
    sync_status     = Column(Enum("pending", "syncing", "synced", "failed", "superseded"), nullable=False, default="pending")
    sync_attempts   = Column(Integer, nullable=False, default=0)
    synced_at       = Column(DATETIME(fsp=3))
    last_sync_error = Column(Text)
    is_current      = Column(Boolean, nullable=False, default=False)
    notes           = Column(Text)
    updated_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")

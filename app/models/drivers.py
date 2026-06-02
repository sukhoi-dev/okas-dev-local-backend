from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from app.models.base import Base


class Driver(Base):
    __tablename__ = "drivers"
    id                      = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    name                    = Column(String(150), nullable=False)
    slug                    = Column(String(120), nullable=False, unique=True)
    source_type             = Column(Enum("okas_official", "partner", "community", "third_party"), nullable=False)
    developer_name          = Column(String(150))
    manufacturer_name       = Column(String(150))
    category                = Column(String(50))
    protocol                = Column(String(50))
    communication_direction = Column(Enum("bidirectional", "control_only", "feedback_only"), nullable=False)
    active_ind              = Column(Boolean, nullable=False, default=True)
    created_at              = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at              = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DriverVersion(Base):
    __tablename__ = "driver_versions"
    id                      = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    driver_id               = Column(BIGINT(unsigned=True), ForeignKey("drivers.id"), nullable=False)
    version                 = Column(String(50), nullable=False)
    release_channel         = Column(Enum("stable", "beta", "rc", "deprecated"), nullable=False, default="stable")
    release_notes           = Column(Text)
    s3_bucket               = Column(String(255))
    s3_key                  = Column(String(1000))
    file_size_bytes         = Column(BIGINT(unsigned=True))
    checksum_sha256         = Column(String(64))
    min_controller_firmware = Column(String(50))
    is_published            = Column(Boolean, nullable=False, default=False)
    published_at            = Column(DATETIME(fsp=3))
    published_by            = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    active_ind              = Column(Boolean, nullable=False, default=True)
    updated_by              = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at              = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at              = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DriverDeviceType(Base):
    __tablename__ = "driver_device_types"
    id             = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    driver_id      = Column(BIGINT(unsigned=True), ForeignKey("drivers.id"), nullable=False)
    device_type_id = Column(BIGINT(unsigned=True), ForeignKey("device_types.id"), nullable=False)


class ControllerDriver(Base):
    __tablename__ = "controller_drivers"
    id                = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    controller_id     = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"), nullable=False)
    driver_id         = Column(BIGINT(unsigned=True), ForeignKey("drivers.id"), nullable=False)
    driver_version_id = Column(BIGINT(unsigned=True), ForeignKey("driver_versions.id"), nullable=False)
    install_status    = Column(Enum("pending", "installed", "failed", "uninstalled"), nullable=False, default="pending")
    installed_at      = Column(DATETIME(fsp=3))
    active_ind        = Column(Boolean, nullable=False, default=True)
    updated_by        = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at        = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DriverLicense(Base):
    __tablename__ = "driver_licenses"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    organization_id  = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    driver_id        = Column(BIGINT(unsigned=True), ForeignKey("drivers.id"), nullable=False)
    license_key      = Column(String(255), nullable=False, unique=True)
    license_type     = Column(Enum("perpetual", "subscription", "per_controller", "per_device"), nullable=False)
    max_activations  = Column(BIGINT(unsigned=True))
    expires_at       = Column(DATETIME(fsp=3))
    purchased_at     = Column(DATETIME(fsp=3))
    active_ind       = Column(Boolean, nullable=False, default=True)
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class DriverLicenseActivation(Base):
    __tablename__ = "driver_license_activations"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    license_id      = Column(BIGINT(unsigned=True), ForeignKey("driver_licenses.id"), nullable=False)
    controller_id   = Column(BIGINT(unsigned=True), ForeignKey("controllers.id"), nullable=False)
    activated_at    = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    deactivated_at  = Column(DATETIME(fsp=3))
    activated_by    = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

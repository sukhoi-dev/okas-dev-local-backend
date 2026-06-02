from sqlalchemy import Column, String, Boolean, Text, ForeignKey, Enum
from sqlalchemy.dialects.mysql import BIGINT, DATETIME
from app.models.base import Base


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id               = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    ticket_number    = Column(String(30), nullable=False, unique=True)
    organization_id  = Column(BIGINT(unsigned=True), ForeignKey("organizations.id"), nullable=False)
    project_id       = Column(BIGINT(unsigned=True), ForeignKey("projects.id"))
    device_id        = Column(BIGINT(unsigned=True), ForeignKey("devices.id"))
    reported_by      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    assigned_to      = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    category         = Column(Enum("hardware", "software", "configuration", "network",
                                   "billing", "training", "other"), nullable=False)
    priority         = Column(Enum("low", "medium", "high", "critical"), nullable=False, default="medium")
    status           = Column(Enum("open", "in_progress", "on_hold", "resolved", "closed"), nullable=False, default="open")
    title            = Column(String(255), nullable=False)
    description      = Column(Text)
    resolution       = Column(Text)
    first_response_at = Column(DATETIME(fsp=3))
    sla_due_at       = Column(DATETIME(fsp=3))
    resolved_at      = Column(DATETIME(fsp=3))
    closed_at        = Column(DATETIME(fsp=3))
    updated_by       = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    created_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at       = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class TicketComment(Base):
    __tablename__ = "ticket_comments"
    id          = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    ticket_id   = Column(BIGINT(unsigned=True), ForeignKey("support_tickets.id"), nullable=False)
    author_id   = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"), nullable=False)
    body        = Column(Text, nullable=False)
    is_internal = Column(Boolean, nullable=False, default=False)
    created_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")
    updated_at  = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3) ON UPDATE CURRENT_TIMESTAMP(3)")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    id              = Column(BIGINT(unsigned=True), primary_key=True, autoincrement=True)
    ticket_id       = Column(BIGINT(unsigned=True), ForeignKey("support_tickets.id"), nullable=False)
    comment_id      = Column(BIGINT(unsigned=True), ForeignKey("ticket_comments.id"))
    uploaded_by     = Column(BIGINT(unsigned=True), ForeignKey("app_users.id"))
    file_name       = Column(String(255), nullable=False)
    s3_bucket       = Column(String(255))
    s3_key          = Column(String(1000))
    content_type    = Column(String(100))
    file_size_bytes = Column(BIGINT(unsigned=True))
    created_at      = Column(DATETIME(fsp=3), nullable=False, server_default="CURRENT_TIMESTAMP(3)")

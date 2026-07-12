"""
SQLAlchemy models mapped onto the tables created by schema.sql.

IMPORTANT: These models do NOT create tables (no Base.metadata.create_all()
is called anywhere). Tables already exist because you ran schema.sql
directly. These classes only describe the existing shape so the ORM can
read/write rows correctly, including Postgres-native types (UUID, JSONB,
ENUM) that a naive `Base.metadata.create_all()` wouldn't reproduce anyway
(functions, RLS policies, ltree, vector columns, etc. are DB-native and
intentionally not represented here).
"""
import uuid

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Column, ForeignKey, Integer,
    String, Text, TIMESTAMP, UniqueConstraint, text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import relationship

from app.database import Base

# ---------------------------------------------------------------------
# Enum types — created in Postgres by schema.sql; create_type=False tells
# SQLAlchemy "don't try to CREATE TYPE, it already exists."
# ---------------------------------------------------------------------
org_role_enum = ENUM("owner", "admin", "member", name="org_role", create_type=False)
user_status_enum = ENUM("invited", "active", "suspended", "deactivated", name="user_status", create_type=False)
doc_status_enum = ENUM("uploaded", "processing", "processed", "failed", name="doc_status", create_type=False)
doc_source_type_enum = ENUM("pdf", "docx", "txt", "scanned_image", "html", "other", name="doc_source_type", create_type=False)
grantee_type_enum = ENUM("user", "organization", name="grantee_type", create_type=False)
permission_level_enum = ENUM("view", "edit", "admin", name="permission_level", create_type=False)
job_status_enum = ENUM("queued", "running", "succeeded", "failed", name="job_status", create_type=False)
invitation_status_enum = ENUM("pending", "accepted", "expired", "revoked", name="invitation_status", create_type=False)
credit_txn_type_enum = ENUM("topup", "usage", "refund", "adjustment", "subscription_grant", name="credit_txn_type", create_type=False)
credit_hold_status_enum = ENUM("active", "captured", "released", "expired", name="credit_hold_status", create_type=False)

UUID_PK = lambda: Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
TS_NOW = lambda: Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))


class Organization(Base):
    __tablename__ = "organizations"

    id = UUID_PK()
    name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    plan_tier = Column(Text, nullable=False, server_default="free")
    region = Column(Text, nullable=False, server_default="us")
    created_at = TS_NOW()
    updated_at = TS_NOW()
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


class User(Base):
    __tablename__ = "users"

    id = UUID_PK()
    email = Column(Text, nullable=False, unique=True)  # citext in DB, str works fine here
    password_hash = Column(Text, nullable=True)
    full_name = Column(Text, nullable=True)
    status = Column(user_status_enum, nullable=False, server_default="active")
    created_at = TS_NOW()
    updated_at = TS_NOW()
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


class OrgMembership(Base):
    __tablename__ = "org_memberships"
    __table_args__ = (UniqueConstraint("organization_id", "user_id"),)

    id = UUID_PK()
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(org_role_enum, nullable=False, server_default="member")
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    joined_at = TS_NOW()


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (UniqueConstraint("organization_id", "email", "status"),)

    id = UUID_PK()
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(Text, nullable=False)
    role = Column(org_role_enum, nullable=False, server_default="member")
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    status = Column(invitation_status_enum, nullable=False, server_default="pending")
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = TS_NOW()


class Document(Base):
    __tablename__ = "documents"

    id = UUID_PK()
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title = Column(Text, nullable=True)
    original_filename = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    mime_type = Column(Text, nullable=False)
    source_type = Column(doc_source_type_enum, nullable=False)
    status = Column(doc_status_enum, nullable=False, server_default="uploaded")
    page_count = Column(Integer, nullable=True)
    checksum_sha256 = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = TS_NOW()
    updated_at = TS_NOW()
    deleted_at = Column(TIMESTAMP(timezone=True), nullable=True)


class DocumentPermission(Base):
    __tablename__ = "document_permissions"
    __table_args__ = (UniqueConstraint("document_id", "grantee_type", "grantee_id"),)

    id = UUID_PK()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    grantee_type = Column(grantee_type_enum, nullable=False)
    grantee_id = Column(UUID(as_uuid=True), nullable=False)
    permission = Column(permission_level_enum, nullable=False, server_default="view")
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = TS_NOW()


class DocumentNode(Base):
    __tablename__ = "document_nodes"

    id = UUID_PK()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    parent_node_id = Column(UUID(as_uuid=True), ForeignKey("document_nodes.id", ondelete="CASCADE"), nullable=True)
    path = Column(Text, nullable=False)  # ltree — plain string I/O works fine via psycopg2
    node_type = Column(Text, nullable=False)
    order_index = Column(Integer, nullable=False, server_default="0")
    text_content = Column(Text, nullable=True)
    table_data = Column(JSONB, nullable=True)
    bbox = Column(JSONB, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = TS_NOW()
    updated_at = TS_NOW()


class NodeEmbedding(Base):
    __tablename__ = "node_embeddings"
    __table_args__ = (UniqueConstraint("node_id", "model_name"),)

    id = UUID_PK()
    node_id = Column(UUID(as_uuid=True), ForeignKey("document_nodes.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(Text, nullable=False)
    # Stored as pgvector VECTOR(1536) in Postgres. Represented here as a
    # plain list[float] via the `pgvector` package's SQLAlchemy type.
    embedding = Column(Text, nullable=False)  # see note in schemas.py re: swapping to pgvector.sqlalchemy.Vector
    created_at = TS_NOW()


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = UUID_PK()
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    job_type = Column(Text, nullable=False)
    status = Column(job_status_enum, nullable=False, server_default="queued")
    error_message = Column(Text, nullable=True)
    started_at = Column(TIMESTAMP(timezone=True), nullable=True)
    finished_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = TS_NOW()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    # Composite PK (id, created_at) because the table is partitioned by
    # created_at. id alone is still effectively unique in practice.
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    created_at = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False, server_default=text("now()"))
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(Text, nullable=False)
    resource_type = Column(Text, nullable=False)
    resource_id = Column(UUID(as_uuid=True), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("owner_type", "owner_id"),)

    id = UUID_PK()
    owner_type = Column(grantee_type_enum, nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    balance_credits = Column(BigInteger, nullable=False, server_default="0")
    held_credits = Column(BigInteger, nullable=False, server_default="0")
    low_balance_threshold = Column(BigInteger, nullable=False, server_default="0")
    created_at = TS_NOW()
    updated_at = TS_NOW()


class CreditPricing(Base):
    __tablename__ = "credit_pricing"

    id = UUID_PK()
    action_type = Column(Text, nullable=False, unique=True)
    cost_credits = Column(BigInteger, nullable=False)
    unit = Column(Text, nullable=False, server_default="per_action")
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = TS_NOW()
    updated_at = TS_NOW()


class CreditHold(Base):
    __tablename__ = "credit_holds"

    id = UUID_PK()
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    reserved_credits = Column(BigInteger, nullable=False)
    status = Column(credit_hold_status_enum, nullable=False, server_default="active")
    reference_type = Column(Text, nullable=False)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = TS_NOW()
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id = UUID_PK()
    wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id", ondelete="CASCADE"), nullable=False)
    amount_credits = Column(BigInteger, nullable=False)
    balance_after = Column(BigInteger, nullable=False)
    txn_type = Column(credit_txn_type_enum, nullable=False)
    reference_type = Column(Text, nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    hold_id = Column(UUID(as_uuid=True), ForeignKey("credit_holds.id", ondelete="SET NULL"), nullable=True)
    actor_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, server_default="{}")
    created_at = TS_NOW()

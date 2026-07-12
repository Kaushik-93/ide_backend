"""
Pydantic schemas: one Create / Update / Read trio per table.
Create = fields required to insert a new row (no id/timestamps).
Update = same fields, all optional (PATCH semantics).
Read   = full row as returned to the client.
"""
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

ORG_ROLES = ("owner", "admin", "member")
USER_STATUSES = ("invited", "active", "suspended", "deactivated")
DOC_STATUSES = ("uploaded", "processing", "processed", "failed")
DOC_SOURCE_TYPES = ("pdf", "docx", "txt", "scanned_image", "html", "other")
GRANTEE_TYPES = ("user", "organization")
PERMISSION_LEVELS = ("view", "edit", "admin")
JOB_STATUSES = ("queued", "running", "succeeded", "failed")
INVITATION_STATUSES = ("pending", "accepted", "expired", "revoked")
CREDIT_TXN_TYPES = ("topup", "usage", "refund", "adjustment", "subscription_grant")
CREDIT_HOLD_STATUSES = ("active", "captured", "released", "expired")


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------
# Organizations
# ---------------------------------------------------------------------
class OrganizationCreate(BaseModel):
    name: str
    slug: str
    plan_tier: str = "free"
    region: str = "us"


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    plan_tier: Optional[str] = None
    region: Optional[str] = None


class OrganizationRead(ORMBase):
    id: UUID
    name: str
    slug: str
    plan_tier: str
    region: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


# ---------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------
class UserCreate(BaseModel):
    email: EmailStr
    password_hash: Optional[str] = None
    full_name: Optional[str] = None
    status: str = Field(default="active")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password_hash: Optional[str] = None
    full_name: Optional[str] = None
    status: Optional[str] = None


class UserRead(ORMBase):
    id: UUID
    email: EmailStr
    full_name: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


# ---------------------------------------------------------------------
# Org memberships
# ---------------------------------------------------------------------
class OrgMembershipCreate(BaseModel):
    organization_id: UUID
    user_id: UUID
    role: str = "member"
    invited_by: Optional[UUID] = None


class OrgMembershipUpdate(BaseModel):
    role: Optional[str] = None


class OrgMembershipRead(ORMBase):
    id: UUID
    organization_id: UUID
    user_id: UUID
    role: str
    invited_by: Optional[UUID] = None
    joined_at: datetime


# ---------------------------------------------------------------------
# Invitations
# ---------------------------------------------------------------------
class InvitationCreate(BaseModel):
    organization_id: UUID
    email: EmailStr
    role: str = "member"
    invited_by: UUID
    token: str
    status: str = "pending"
    expires_at: datetime


class InvitationUpdate(BaseModel):
    status: Optional[str] = None


class InvitationRead(ORMBase):
    id: UUID
    organization_id: UUID
    email: EmailStr
    role: str
    invited_by: UUID
    status: str
    expires_at: datetime
    created_at: datetime


# ---------------------------------------------------------------------
# Documents
# ---------------------------------------------------------------------
class DocumentCreate(BaseModel):
    organization_id: Optional[UUID] = None
    owner_user_id: UUID
    title: Optional[str] = None
    original_filename: str
    storage_path: str
    mime_type: str
    source_type: str
    status: str = "uploaded"
    page_count: Optional[int] = None
    checksum_sha256: Optional[str] = None


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    page_count: Optional[int] = None
    error_message: Optional[str] = None


class DocumentRead(ORMBase):
    id: UUID
    organization_id: Optional[UUID] = None
    owner_user_id: UUID
    title: Optional[str] = None
    original_filename: str
    storage_path: str
    mime_type: str
    source_type: str
    status: str
    page_count: Optional[int] = None
    checksum_sha256: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


# ---------------------------------------------------------------------
# Document permissions
# ---------------------------------------------------------------------
class DocumentPermissionCreate(BaseModel):
    document_id: UUID
    grantee_type: str
    grantee_id: UUID
    permission: str = "view"
    granted_by: UUID


class DocumentPermissionUpdate(BaseModel):
    permission: Optional[str] = None


class DocumentPermissionRead(ORMBase):
    id: UUID
    document_id: UUID
    grantee_type: str
    grantee_id: UUID
    permission: str
    granted_by: UUID
    created_at: datetime


# ---------------------------------------------------------------------
# Document nodes
# ---------------------------------------------------------------------
class DocumentNodeCreate(BaseModel):
    document_id: UUID
    parent_node_id: Optional[UUID] = None
    path: str
    node_type: str
    order_index: int = 0
    text_content: Optional[str] = None
    table_data: Optional[dict[str, Any]] = None
    bbox: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentNodeUpdate(BaseModel):
    text_content: Optional[str] = None
    table_data: Optional[dict[str, Any]] = None
    bbox: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    order_index: Optional[int] = None


class DocumentNodeRead(ORMBase):
    id: UUID
    document_id: UUID
    parent_node_id: Optional[UUID] = None
    path: str
    node_type: str
    order_index: int
    text_content: Optional[str] = None
    table_data: Optional[dict[str, Any]] = None
    bbox: Optional[dict[str, Any]] = None
    metadata: dict[str, Any] = Field(validation_alias="metadata_", serialization_alias="metadata")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------
# Node embeddings
# NOTE: `embedding` is a pgvector VECTOR(1536) column. For simplicity
# this API accepts/returns it as a plain list[float] and the model
# column is typed as Text — swap app/models.py's column to
# `from pgvector.sqlalchemy import Vector; Column(Vector(1536))` once
# you're actually generating embeddings, so Postgres can index/search
# them with cosine similarity instead of just storing them.
# ---------------------------------------------------------------------
class NodeEmbeddingCreate(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    node_id: UUID
    model_name: str
    embedding: list[float]


class NodeEmbeddingUpdate(BaseModel):
    embedding: Optional[list[float]] = None


class NodeEmbeddingRead(ORMBase):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    id: UUID
    node_id: UUID
    model_name: str
    created_at: datetime


# ---------------------------------------------------------------------
# Processing jobs
# ---------------------------------------------------------------------
class ProcessingJobCreate(BaseModel):
    document_id: UUID
    job_type: str
    status: str = "queued"


class ProcessingJobUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class ProcessingJobRead(ORMBase):
    id: UUID
    document_id: UUID
    job_type: str
    status: str
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


# ---------------------------------------------------------------------
# Audit logs — create + read only (append-only by design)
# ---------------------------------------------------------------------
class AuditLogCreate(BaseModel):
    organization_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditLogRead(ORMBase):
    id: UUID
    organization_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    action: str
    resource_type: str
    resource_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(validation_alias="metadata_", serialization_alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------
# Wallets — read-only via generic router; balance mutated only via
# the /credits/* endpoints that call the SQL functions.
# ---------------------------------------------------------------------
class WalletRead(ORMBase):
    id: UUID
    owner_type: str
    owner_id: UUID
    balance_credits: int
    held_credits: int
    low_balance_threshold: int
    created_at: datetime
    updated_at: datetime


class WalletCreate(BaseModel):
    """Only used to provision a new empty wallet for a new org/user."""
    owner_type: str
    owner_id: UUID
    low_balance_threshold: int = 0


# ---------------------------------------------------------------------
# Credit pricing — regular CRUD is fine, this is just config
# ---------------------------------------------------------------------
class CreditPricingCreate(BaseModel):
    action_type: str
    cost_credits: int
    unit: str = "per_action"
    description: Optional[str] = None
    is_active: bool = True


class CreditPricingUpdate(BaseModel):
    cost_credits: Optional[int] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CreditPricingRead(ORMBase):
    id: UUID
    action_type: str
    cost_credits: int
    unit: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------
# Credit holds / transactions — read-only, see app/routers/credits.py
# ---------------------------------------------------------------------
class CreditHoldRead(ORMBase):
    id: UUID
    wallet_id: UUID
    reserved_credits: int
    status: str
    reference_type: str
    reference_id: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None
    expires_at: datetime


class CreditTransactionRead(ORMBase):
    id: UUID
    wallet_id: UUID
    amount_credits: int
    balance_after: int
    txn_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    hold_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None
    metadata: dict[str, Any] = Field(validation_alias="metadata_", serialization_alias="metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


# ---------------------------------------------------------------------
# Request bodies for the dedicated /credits/* function-backed endpoints
# ---------------------------------------------------------------------
class TopUpRequest(BaseModel):
    wallet_id: UUID
    amount: int = Field(gt=0)
    txn_type: str = "topup"
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    actor_user_id: Optional[UUID] = None


class ReserveRequest(BaseModel):
    wallet_id: UUID
    amount: int = Field(gt=0)
    reference_type: str
    reference_id: Optional[UUID] = None
    created_by: Optional[UUID] = None


class CaptureRequest(BaseModel):
    actual_amount: int = Field(ge=0)
    actor_user_id: Optional[UUID] = None

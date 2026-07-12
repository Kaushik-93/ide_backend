from app import models, schemas
from app.routers.factory import build_crud_router

organizations_router = build_crud_router(
    model=models.Organization,
    create_schema=schemas.OrganizationCreate,
    update_schema=schemas.OrganizationUpdate,
    read_schema=schemas.OrganizationRead,
    prefix="/organizations",
    tags=["organizations"],
)

users_router = build_crud_router(
    model=models.User,
    create_schema=schemas.UserCreate,
    update_schema=schemas.UserUpdate,
    read_schema=schemas.UserRead,
    prefix="/users",
    tags=["users"],
)

org_memberships_router = build_crud_router(
    model=models.OrgMembership,
    create_schema=schemas.OrgMembershipCreate,
    update_schema=schemas.OrgMembershipUpdate,
    read_schema=schemas.OrgMembershipRead,
    prefix="/org-memberships",
    tags=["org-memberships"],
)

invitations_router = build_crud_router(
    model=models.Invitation,
    create_schema=schemas.InvitationCreate,
    update_schema=schemas.InvitationUpdate,
    read_schema=schemas.InvitationRead,
    prefix="/invitations",
    tags=["invitations"],
)

documents_router = build_crud_router(
    model=models.Document,
    create_schema=schemas.DocumentCreate,
    update_schema=schemas.DocumentUpdate,
    read_schema=schemas.DocumentRead,
    prefix="/documents",
    tags=["documents"],
)

document_permissions_router = build_crud_router(
    model=models.DocumentPermission,
    create_schema=schemas.DocumentPermissionCreate,
    update_schema=schemas.DocumentPermissionUpdate,
    read_schema=schemas.DocumentPermissionRead,
    prefix="/document-permissions",
    tags=["document-permissions"],
)

document_nodes_router = build_crud_router(
    model=models.DocumentNode,
    create_schema=schemas.DocumentNodeCreate,
    update_schema=schemas.DocumentNodeUpdate,
    read_schema=schemas.DocumentNodeRead,
    prefix="/document-nodes",
    tags=["document-nodes"],
)

node_embeddings_router = build_crud_router(
    model=models.NodeEmbedding,
    create_schema=schemas.NodeEmbeddingCreate,
    update_schema=schemas.NodeEmbeddingUpdate,
    read_schema=schemas.NodeEmbeddingRead,
    prefix="/node-embeddings",
    tags=["node-embeddings"],
)

processing_jobs_router = build_crud_router(
    model=models.ProcessingJob,
    create_schema=schemas.ProcessingJobCreate,
    update_schema=schemas.ProcessingJobUpdate,
    read_schema=schemas.ProcessingJobRead,
    prefix="/processing-jobs",
    tags=["processing-jobs"],
)

# Audit logs: append-only by design (see schema.sql section 12) — no
# update, no delete. Only create (for the app to log an action) and read.
audit_logs_router = build_crud_router(
    model=models.AuditLog,
    create_schema=schemas.AuditLogCreate,
    update_schema=schemas.AuditLogCreate,  # unused, update disabled below
    read_schema=schemas.AuditLogRead,
    prefix="/audit-logs",
    tags=["audit-logs"],
    allow_update=False,
    allow_delete=False,
)

credit_pricing_router = build_crud_router(
    model=models.CreditPricing,
    create_schema=schemas.CreditPricingCreate,
    update_schema=schemas.CreditPricingUpdate,
    read_schema=schemas.CreditPricingRead,
    prefix="/credit-pricing",
    tags=["credit-pricing"],
)

# Wallets: create is allowed (provisioning an empty wallet for a new org
# or standalone user), but balance must never be edited directly — only
# through fn_add_credits / fn_reserve_credits / fn_capture_hold, exposed
# via app/routers/credits.py. So update/delete are disabled here.
wallets_router = build_crud_router(
    model=models.Wallet,
    create_schema=schemas.WalletCreate,
    update_schema=schemas.WalletCreate,  # unused, update disabled below
    read_schema=schemas.WalletRead,
    prefix="/wallets",
    tags=["wallets"],
    allow_update=False,
    allow_delete=False,
)

# Credit holds & transactions: fully read-only via this router. They are
# only ever written by the SQL functions (see app/routers/credits.py) so
# the ledger can never drift from the wallet balance.
credit_holds_router = build_crud_router(
    model=models.CreditHold,
    create_schema=schemas.CreditHoldRead,   # unused, create disabled below
    update_schema=schemas.CreditHoldRead,   # unused, update disabled below
    read_schema=schemas.CreditHoldRead,
    prefix="/credit-holds",
    tags=["credit-holds"],
    allow_create=False,
    allow_update=False,
    allow_delete=False,
)

credit_transactions_router = build_crud_router(
    model=models.CreditTransaction,
    create_schema=schemas.CreditTransactionRead,  # unused, create disabled below
    update_schema=schemas.CreditTransactionRead,  # unused, update disabled below
    read_schema=schemas.CreditTransactionRead,
    prefix="/credit-transactions",
    tags=["credit-transactions"],
    allow_create=False,
    allow_update=False,
    allow_delete=False,
)

all_resource_routers = [
    organizations_router,
    users_router,
    org_memberships_router,
    invitations_router,
    documents_router,
    document_permissions_router,
    document_nodes_router,
    node_embeddings_router,
    processing_jobs_router,
    audit_logs_router,
    credit_pricing_router,
    wallets_router,
    credit_holds_router,
    credit_transactions_router,
]

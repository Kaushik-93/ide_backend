"""
Credit mutations MUST go through the Postgres functions defined in
schema.sql section 15 (fn_add_credits, fn_reserve_credits,
fn_capture_hold, fn_release_hold) — never via direct INSERT/UPDATE on
wallets/credit_transactions/credit_holds. This router is the only place
in the API that touches wallet balances, and it does so by calling those
functions, which keeps the ledger and the balance atomic and consistent
under concurrent requests (see the SELECT ... FOR UPDATE locking inside
those functions).
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    CaptureRequest, CreditTransactionRead, ReserveRequest, TopUpRequest,
)

router = APIRouter(prefix="/credits", tags=["credits"])


def _run_function(db: Session, sql: str, params: dict):
    try:
        row = db.execute(text(sql), params).mappings().first()
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        # fn_reserve_credits raises with ERRCODE insufficient_privilege
        # when the wallet doesn't have enough available balance.
        raise HTTPException(status_code=422, detail=str(exc.orig)) from exc
    if row is None:
        raise HTTPException(status_code=500, detail="Function returned no row")
    return dict(row)


@router.post("/topup", response_model=CreditTransactionRead)
def top_up(payload: TopUpRequest, db: Session = Depends(get_db)):
    """Add credits to a wallet (org admin action, or a billing webhook)."""
    row = _run_function(
        db,
        """
        SELECT * FROM fn_add_credits(
            :wallet_id, :amount, :txn_type, :reference_type, :reference_id, :actor_user_id
        )
        """,
        payload.model_dump(mode="json"),
    )
    return row


@router.post("/reserve")
def reserve(payload: ReserveRequest, db: Session = Depends(get_db)):
    """
    Reserve credits before starting a variable-cost job (e.g. document
    processing). Returns the created hold; call /credits/capture/{hold_id}
    or /credits/release/{hold_id} when the job finishes or fails.
    """
    row = _run_function(
        db,
        """
        SELECT * FROM fn_reserve_credits(
            :wallet_id, :amount, :reference_type, :reference_id, :created_by
        )
        """,
        payload.model_dump(mode="json"),
    )
    return row


@router.post("/capture/{hold_id}", response_model=CreditTransactionRead)
def capture(hold_id: UUID, payload: CaptureRequest, db: Session = Depends(get_db)):
    """Charge the actual cost of a completed job and release the unused hold amount."""
    row = _run_function(
        db,
        "SELECT * FROM fn_capture_hold(:hold_id, :actual_amount, :actor_user_id)",
        {"hold_id": str(hold_id), **payload.model_dump(mode="json")},
    )
    return row


@router.post("/release/{hold_id}", status_code=204)
def release(hold_id: UUID, db: Session = Depends(get_db)):
    """Release a hold with no charge (job failed or was cancelled)."""
    try:
        db.execute(text("SELECT fn_release_hold(:hold_id)"), {"hold_id": str(hold_id)})
        db.commit()
    except DBAPIError as exc:
        db.rollback()
        raise HTTPException(status_code=422, detail=str(exc.orig)) from exc
    return None

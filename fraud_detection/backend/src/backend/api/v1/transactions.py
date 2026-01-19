"""
Transaction endpoints for fraud detection.
"""
from datetime import datetime
from uuid import uuid4
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.core.database import get_db
from backend.models import Transaction, User
from backend.schemas.transaction import (
    TransactionCreate,
    TransactionScore,
    TransactionResponse,
    TransactionList
)
from backend.services.risk_scorer import RiskScorer
from backend.services.cache import get_cache
from backend.api.v1.websocket import get_websocket_manager

router = APIRouter()
risk_scorer = RiskScorer()
cache = get_cache()
ws_manager = get_websocket_manager()


@router.post("/transactions/score", response_model=TransactionScore)
async def score_transaction(
    transaction: TransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Score a transaction for fraud risk.

    Returns real-time fraud score (<100ms target latency).
    """
    # Ensure user exists (auto-create for testing)
    user_result = await db.execute(
        select(User).where(User.id == transaction.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        user = User(
            id=transaction.user_id,
            email=f"user_{str(transaction.user_id)[:8]}@test.com",
            first_name="Test",
            last_name="User"
        )
        db.add(user)
        await db.flush()

    # Try to get user history from cache first
    cached_history = await cache.get_user_history(str(transaction.user_id))

    if cached_history:
        # Use cached history (already in dict format)
        history_dicts = cached_history
    else:
        # Fetch from database
        user_history = await _get_user_history(db, transaction.user_id)

        # Convert to dicts
        history_dicts = [
            {
                "transaction_time": h.transaction_time,
                "amount": h.amount,
                "latitude": h.latitude,
                "longitude": h.longitude,
                "device_id": h.device_id,
                "country": h.country
            }
            for h in user_history
        ]

        # Cache for future requests
        await cache.set_user_history(str(transaction.user_id), history_dicts)

    # Convert transaction to dict for risk scorer
    txn_dict = transaction.model_dump()
    if txn_dict["transaction_time"] is None:
        txn_dict["transaction_time"] = datetime.utcnow()

    # Score the transaction
    risk_result = await risk_scorer.score_transaction(txn_dict, history_dicts)

    # Save transaction to database
    db_transaction = Transaction(
        id=uuid4(),
        user_id=transaction.user_id,
        amount=transaction.amount,
        currency=transaction.currency,
        merchant_name=transaction.merchant_name,
        merchant_category=transaction.merchant_category,
        transaction_type=transaction.transaction_type,
        latitude=transaction.latitude,
        longitude=transaction.longitude,
        country=transaction.country,
        city=transaction.city,
        device_id=transaction.device_id,
        ip_address=transaction.ip_address,
        user_agent=transaction.user_agent,
        fraud_score=risk_result["fraud_score"],
        risk_level=risk_result["risk_level"],
        is_fraud=risk_result["is_fraud"],
        is_blocked=risk_result["is_blocked"],
        model_version=risk_result["model_version"],
        transaction_time=txn_dict["transaction_time"],
        rule_triggers=risk_result["triggered_rules"]
    )

    db.add(db_transaction)
    await db.commit()
    await db.refresh(db_transaction)

    # Invalidate user history cache since we added a new transaction
    await cache.invalidate_user_history(str(transaction.user_id))

    # Prepare response
    response = TransactionScore(
        transaction_id=db_transaction.id,
        fraud_score=risk_result["fraud_score"],
        risk_level=risk_result["risk_level"],
        is_fraud=risk_result["is_fraud"],
        is_blocked=risk_result["is_blocked"],
        triggered_rules=risk_result["triggered_rules"],
        rule_scores=risk_result["rule_scores"],
        anomaly_score=risk_result["anomaly_score"],
        azure_score=risk_result.get("azure_score"),
        is_azure_anomaly=risk_result.get("is_azure_anomaly"),
        explanation=risk_result["explanation"],
        processing_time_ms=risk_result["processing_time_ms"]
    )

    # Broadcast to WebSocket subscribers
    await ws_manager.broadcast_transaction({
        "transaction_id": str(db_transaction.id),
        "user_id": str(transaction.user_id),
        "amount": transaction.amount,
        "merchant_name": transaction.merchant_name,
        "fraud_score": risk_result["fraud_score"],
        "risk_level": risk_result["risk_level"],
        "is_fraud": risk_result["is_fraud"],
        "is_blocked": risk_result["is_blocked"],
        "processing_time_ms": risk_result["processing_time_ms"]
    })

    # Broadcast alert for high-risk transactions
    if risk_result["is_fraud"]:
        await ws_manager.broadcast_alert({
            "transaction_id": str(db_transaction.id),
            "user_id": str(transaction.user_id),
            "amount": transaction.amount,
            "merchant_name": transaction.merchant_name,
            "fraud_score": risk_result["fraud_score"],
            "triggered_rules": risk_result["triggered_rules"],
            "explanation": risk_result["explanation"]
        })

    return response


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get transaction details with fraud analysis.
    """
    result = await db.execute(
        select(Transaction).where(Transaction.id == transaction_id)
    )
    transaction = result.scalar_one_or_none()

    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction


@router.get("/transactions", response_model=TransactionList)
async def list_transactions(
    skip: int = 0,
    limit: int = 100,
    risk_level: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List recent transactions.
    """
    query = select(Transaction).order_by(desc(Transaction.created_at))

    if risk_level:
        query = query.where(Transaction.risk_level == risk_level)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    transactions = result.scalars().all()

    # Count total
    count_query = select(Transaction)
    if risk_level:
        count_query = count_query.where(Transaction.risk_level == risk_level)

    total_result = await db.execute(count_query)
    total = len(total_result.scalars().all())

    return TransactionList(
        transactions=transactions,
        total=total,
        skip=skip,
        limit=limit
    )


async def _get_user_history(
    db: AsyncSession,
    user_id: str,
    limit: int = 100
) -> List[Transaction]:
    """Fetch user's recent transaction history."""
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(desc(Transaction.transaction_time))
        .limit(limit)
    )
    return result.scalars().all()

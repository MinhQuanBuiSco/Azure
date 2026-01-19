"""
Fraud detection rule management endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.database import get_db

router = APIRouter()


@router.get("/rules")
async def list_rules(
    db: AsyncSession = Depends(get_db)
):
    """
    Get all fraud detection rules.
    """
    # TODO: Implement rule listing
    return {
        "rules": [
            {
                "id": "rule_1",
                "name": "Velocity Check",
                "description": "Flag transactions if >5 in 10 minutes",
                "enabled": True,
            },
            {
                "id": "rule_2",
                "name": "Geolocation Anomaly",
                "description": "Flag if card used in 2 countries within 1 hour",
                "enabled": True,
            },
        ]
    }


@router.post("/rules")
async def create_rule(
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new fraud detection rule.
    """
    # TODO: Implement rule creation
    return {
        "id": "rule_new",
        "name": "New Rule",
        "status": "created",
    }


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a fraud detection rule.
    """
    # TODO: Implement rule update
    return {
        "id": rule_id,
        "status": "updated",
    }

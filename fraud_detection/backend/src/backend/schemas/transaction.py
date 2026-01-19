"""
Transaction schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID


class TransactionBase(BaseModel):
    """Base transaction schema."""
    amount: float = Field(..., gt=0, description="Transaction amount")
    currency: str = Field(default="USD", max_length=3)
    merchant_name: Optional[str] = Field(None, max_length=255)
    merchant_category: Optional[str] = Field(None, max_length=100)
    transaction_type: str = Field(..., max_length=50, description="purchase, transfer, withdrawal")

    # Location
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    country: Optional[str] = Field(None, max_length=2)
    city: Optional[str] = Field(None, max_length=100)

    # Device information
    device_id: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = Field(None, max_length=500)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    user_id: UUID
    transaction_time: Optional[datetime] = None


class TransactionScore(BaseModel):
    """Schema for fraud scoring response."""
    transaction_id: UUID
    fraud_score: float = Field(..., ge=0, le=100, description="Fraud probability score 0-100")
    risk_level: str = Field(..., description="low, medium, or high")
    is_fraud: bool
    is_blocked: bool

    # Rule triggers
    triggered_rules: list[str] = Field(default_factory=list)
    rule_scores: dict[str, float] = Field(default_factory=dict)

    # Anomaly detection
    anomaly_score: Optional[float] = None
    azure_score: Optional[float] = Field(None, description="Azure Anomaly Detector score 0-100")
    is_azure_anomaly: Optional[bool] = Field(None, description="Azure anomaly detection result")

    # Explanation
    explanation: Optional[str] = None

    # Processing metadata
    processing_time_ms: float


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: UUID
    user_id: UUID
    fraud_score: float
    risk_level: Optional[str]
    is_fraud: bool
    is_blocked: bool
    model_version: Optional[str]
    transaction_time: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    """Schema for paginated transaction list."""
    transactions: list[TransactionResponse]
    total: int
    skip: int
    limit: int

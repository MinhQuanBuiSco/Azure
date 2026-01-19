"""
Fraud rule schemas.
"""
from typing import Optional, Any
from pydantic import BaseModel, Field
from uuid import UUID


class RuleConfigBase(BaseModel):
    """Base configuration for a fraud rule."""
    max_transactions: Optional[int] = None
    time_window_minutes: Optional[int] = None
    max_amount: Optional[float] = None
    min_amount: Optional[float] = None
    distance_threshold_km: Optional[float] = None
    allowed_countries: Optional[list[str]] = None
    blocked_countries: Optional[list[str]] = None


class FraudRuleBase(BaseModel):
    """Base fraud rule schema."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., max_length=50, description="velocity, amount, geo, device, etc.")
    config: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    priority: int = Field(default=50, ge=0, le=100)
    weight: int = Field(default=10, ge=0, le=100, description="Contribution to fraud score")


class FraudRuleCreate(FraudRuleBase):
    """Schema for creating a fraud rule."""
    created_by: Optional[str] = None


class FraudRuleUpdate(BaseModel):
    """Schema for updating a fraud rule."""
    description: Optional[str] = None
    config: Optional[dict[str, Any]] = None
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    weight: Optional[int] = Field(None, ge=0, le=100)


class FraudRuleResponse(FraudRuleBase):
    """Schema for fraud rule response."""
    id: UUID
    total_triggers: int
    true_positives: int
    false_positives: int
    precision: float

    class Config:
        from_attributes = True


class RulePerformance(BaseModel):
    """Schema for rule performance metrics."""
    rule_id: UUID
    rule_name: str
    triggers: int
    true_positives: int
    false_positives: int
    precision: float
    recall: Optional[float] = None
    f1_score: Optional[float] = None

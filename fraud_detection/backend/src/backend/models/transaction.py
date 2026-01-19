"""
Transaction model for fraud detection system.
"""
from datetime import datetime
from sqlalchemy import Column, String, Float, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from backend.core.database import Base


class Transaction(Base):
    """Transaction model for storing transaction data."""

    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Transaction details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    merchant_name = Column(String(255), nullable=True)
    merchant_category = Column(String(100), nullable=True)
    transaction_type = Column(String(50), nullable=False)  # purchase, transfer, withdrawal

    # Location
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    country = Column(String(2), nullable=True)
    city = Column(String(100), nullable=True)

    # Device information
    device_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Fraud detection
    fraud_score = Column(Float, default=0.0, nullable=False, index=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    is_fraud = Column(Boolean, default=False, nullable=False, index=True)
    is_blocked = Column(Boolean, default=False, nullable=False)

    # ML Model outputs
    model_version = Column(String(100), nullable=True)
    feature_scores = Column(JSON, nullable=True)  # Individual feature contributions
    rule_triggers = Column(JSON, nullable=True)  # Which rules were triggered

    # Timestamps
    transaction_time = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    # user = relationship("User", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.id} - ${self.amount} - Score: {self.fraud_score}>"

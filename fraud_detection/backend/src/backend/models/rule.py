"""
Fraud detection rule model.
"""
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
import uuid

from backend.core.database import Base


class FraudRule(Base):
    """Fraud detection rule model."""

    __tablename__ = "fraud_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Rule details
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # velocity, amount, geo, device, etc.

    # Rule configuration (JSON)
    config = Column(JSON, nullable=False)
    # Example: {"max_transactions": 5, "time_window_minutes": 10}

    # Rule metadata
    enabled = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=50, nullable=False)  # Higher = more important
    weight = Column(Integer, default=10, nullable=False)  # Contribution to fraud score

    # Performance metrics
    total_triggers = Column(Integer, default=0, nullable=False)
    true_positives = Column(Integer, default=0, nullable=False)
    false_positives = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(255), nullable=True)

    def __repr__(self):
        return f"<FraudRule {self.name} - {'Enabled' if self.enabled else 'Disabled'}>"

    @property
    def precision(self) -> float:
        """Calculate precision of the rule."""
        if self.total_triggers == 0:
            return 0.0
        return self.true_positives / self.total_triggers

"""
Risk scoring service that combines rule engine and ML models.
"""
from typing import Dict, List, Tuple
from datetime import datetime

from backend.services.rule_engine import FraudRuleEngine, RuleResult
from backend.services.anomaly_detector import AnomalyDetector
from backend.services.azure_anomaly import AzureAnomalyDetector
from backend.services.claude_explainer import ClaudeExplainer
from backend.core.config import get_settings


class RiskScorer:
    """Combines multiple fraud detection methods into a single risk score."""

    def __init__(self):
        """Initialize the risk scorer."""
        self.settings = get_settings()
        self.rule_engine = FraudRuleEngine()
        self.anomaly_detector = AnomalyDetector(contamination=0.01)
        self.azure_detector = AzureAnomalyDetector()
        self.claude_explainer = ClaudeExplainer()

        # Weight distribution (rules have highest impact since ML models are secondary)
        self.rule_weight = 0.85   # 85% from rules
        self.ml_weight = 0.10     # 10% from Isolation Forest
        self.azure_weight = 0.05  # 5% from Azure Anomaly Detector

    async def score_transaction(
        self,
        transaction: Dict,
        user_history: List[Dict] = None
    ) -> Dict:
        """
        Calculate comprehensive fraud risk score for a transaction.

        Args:
            transaction: Transaction data
            user_history: User's previous transactions

        Returns:
            Dict with fraud score, risk level, and explanation
        """
        start_time = datetime.utcnow()

        if user_history is None:
            user_history = []

        # 1. Rule-based scoring (60%)
        rule_score, rule_results = await self.rule_engine.evaluate_transaction(
            transaction,
            user_history
        )

        # 2. Isolation Forest ML-based anomaly detection (25%)
        ml_score, is_anomaly = self._get_ml_anomaly_score(transaction, user_history)

        # 3. Azure Anomaly Detector (15%)
        azure_score, is_azure_anomaly, azure_explanation = await self.azure_detector.detect_anomaly(
            transaction,
            user_history
        )

        # 4. Combine scores
        final_score = (
            (rule_score * self.rule_weight) +
            (ml_score * self.ml_weight) +
            (azure_score * self.azure_weight)
        )

        # 5. Determine risk level
        risk_level = self._get_risk_level(final_score)

        # 6. Decide if transaction should be blocked
        is_fraud = final_score >= self.settings.high_risk_threshold
        is_blocked = is_fraud  # For now, block all high-risk transactions

        # 7. Build explanation with Claude (or fallback to basic)
        triggered_rules = [r for r in rule_results if r.triggered]
        triggered_rule_names = [r.rule_name for r in triggered_rules]
        rule_scores_dict = {r.rule_name: r.score for r in rule_results if r.triggered}

        explanation = await self.claude_explainer.generate_explanation(
            transaction=transaction,
            fraud_score=final_score,
            risk_level=risk_level,
            triggered_rules=triggered_rule_names,
            rule_scores=rule_scores_dict,
            ml_score=ml_score,
            azure_score=azure_score,
            is_fraud=is_fraud
        )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        return {
            "fraud_score": round(final_score, 2),
            "risk_level": risk_level,
            "is_fraud": is_fraud,
            "is_blocked": is_blocked,
            "triggered_rules": [r.rule_name for r in triggered_rules],
            "rule_scores": {r.rule_name: r.score for r in rule_results if r.triggered},
            "rule_score": round(rule_score, 2),
            "ml_score": round(ml_score, 2),
            "anomaly_score": ml_score,
            "is_anomaly": is_anomaly,
            "azure_score": round(azure_score, 2),
            "is_azure_anomaly": is_azure_anomaly,
            "explanation": explanation,
            "processing_time_ms": round(processing_time, 2),
            "model_version": "rule_engine_v1.0+isolation_forest+azure_anomaly+claude_haiku",
            "claude_enabled": self.claude_explainer.enabled
        }

    def _get_ml_anomaly_score(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> Tuple[float, bool]:
        """
        Get anomaly score from Isolation Forest ML model.

        Returns:
            Tuple of (anomaly_score, is_anomaly)
        """
        # Use Isolation Forest to detect anomalies
        anomaly_score, is_anomaly = self.anomaly_detector.predict_anomaly_score(
            transaction,
            user_history
        )

        return anomaly_score, is_anomaly

    def _get_risk_level(self, score: float) -> str:
        """Determine risk level based on score."""
        if score < self.settings.low_risk_threshold:
            return "low"
        elif score < self.settings.high_risk_threshold:
            return "medium"
        else:
            return "high"

    def _build_explanation(
        self,
        final_score: float,
        risk_level: str,
        triggered_rules: List[RuleResult],
        ml_score: float,
        azure_score: float = 0.0,
        azure_explanation: str = None
    ) -> str:
        """Build human-readable explanation of the fraud score."""
        if not triggered_rules and ml_score < 20 and azure_score < 20:
            return "Transaction appears normal. No suspicious patterns detected."

        explanation_parts = [f"Risk Level: {risk_level.upper()} (Score: {final_score:.1f}/100)"]

        if triggered_rules:
            explanation_parts.append("\nTriggered Rules:")
            for rule in triggered_rules:
                explanation_parts.append(f"  • {rule.reason}")

        if ml_score > 30:
            explanation_parts.append(f"\nIsolation Forest: Transaction pattern deviates from user's normal behavior (score: {ml_score:.1f})")

        if azure_score > 30 and azure_explanation:
            explanation_parts.append(f"\nAzure Anomaly Detector: {azure_explanation}")

        return "\n".join(explanation_parts)

    def get_risk_statistics(self, scores: List[float]) -> Dict:
        """Calculate statistics from a batch of risk scores."""
        if not scores:
            return {
                "mean": 0.0,
                "median": 0.0,
                "std_dev": 0.0,
                "min": 0.0,
                "max": 0.0,
                "high_risk_count": 0,
                "medium_risk_count": 0,
                "low_risk_count": 0
            }

        sorted_scores = sorted(scores)
        n = len(scores)

        mean = sum(scores) / n
        median = sorted_scores[n // 2] if n % 2 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2

        variance = sum((x - mean) ** 2 for x in scores) / n
        std_dev = variance ** 0.5

        return {
            "mean": round(mean, 2),
            "median": round(median, 2),
            "std_dev": round(std_dev, 2),
            "min": round(min(scores), 2),
            "max": round(max(scores), 2),
            "high_risk_count": sum(1 for s in scores if s >= self.settings.high_risk_threshold),
            "medium_risk_count": sum(1 for s in scores if self.settings.low_risk_threshold <= s < self.settings.high_risk_threshold),
            "low_risk_count": sum(1 for s in scores if s < self.settings.low_risk_threshold)
        }

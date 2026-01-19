"""
Fraud detection rule engine.

Implements configurable fraud detection rules for real-time transaction scoring.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
from math import radians, cos, sin, asin, sqrt


@dataclass
class RuleResult:
    """Result of a rule evaluation."""
    rule_name: str
    triggered: bool
    score: float
    reason: str


class FraudRuleEngine:
    """Rule-based fraud detection engine."""

    def __init__(self):
        """Initialize the rule engine with default rules."""
        self.rules = self._load_default_rules()

    def _load_default_rules(self) -> Dict:
        """Load default fraud detection rules."""
        return {
            "velocity_check": {
                "enabled": True,
                "weight": 25,
                "config": {
                    "max_transactions": 5,
                    "time_window_minutes": 10
                }
            },
            "high_amount": {
                "enabled": True,
                "weight": 20,
                "config": {
                    "threshold_multiplier": 3.0  # 3x average
                }
            },
            "geolocation_impossible": {
                "enabled": True,
                "weight": 30,
                "config": {
                    "max_distance_km": 500,
                    "time_window_minutes": 60
                }
            },
            "unusual_time": {
                "enabled": True,
                "weight": 10,
                "config": {
                    "unusual_hours": [0, 1, 2, 3, 4, 5]  # 12am - 5am
                }
            },
            "new_device": {
                "enabled": True,
                "weight": 15,
                "config": {
                    "min_amount": 500.0
                }
            },
            "blacklist_check": {
                "enabled": True,
                "weight": 85,  # Blacklisted countries immediately trigger fraud (85 * 0.85 rule_weight > 70 threshold)
                "config": {
                    "blocked_countries": ["KP", "IR", "SY"]  # Sanctioned countries
                }
            }
        }

    async def evaluate_transaction(
        self,
        transaction: Dict,
        user_history: List[Dict] = None
    ) -> Tuple[float, List[RuleResult]]:
        """
        Evaluate a transaction against all fraud rules.

        Args:
            transaction: Transaction data
            user_history: List of user's previous transactions

        Returns:
            Tuple of (total_score, list of rule results)
        """
        if user_history is None:
            user_history = []

        results = []
        total_score = 0.0

        # Evaluate each rule
        for rule_name, rule_config in self.rules.items():
            if not rule_config["enabled"]:
                continue

            result = None

            if rule_name == "velocity_check":
                result = self._check_velocity(transaction, user_history, rule_config)
            elif rule_name == "high_amount":
                result = self._check_high_amount(transaction, user_history, rule_config)
            elif rule_name == "geolocation_impossible":
                result = self._check_geolocation(transaction, user_history, rule_config)
            elif rule_name == "unusual_time":
                result = self._check_unusual_time(transaction, rule_config)
            elif rule_name == "new_device":
                result = self._check_new_device(transaction, user_history, rule_config)
            elif rule_name == "blacklist_check":
                result = self._check_blacklist(transaction, rule_config)

            if result:
                results.append(result)
                if result.triggered:
                    total_score += result.score

        # Cap score at 100
        total_score = min(total_score, 100.0)

        return total_score, results

    def _check_velocity(
        self,
        transaction: Dict,
        user_history: List[Dict],
        rule_config: Dict
    ) -> RuleResult:
        """Check if user is making too many transactions in a short time."""
        max_txns = rule_config["config"]["max_transactions"]
        window_minutes = rule_config["config"]["time_window_minutes"]
        weight = rule_config["weight"]

        current_time = transaction.get("transaction_time", datetime.utcnow())
        cutoff_time = current_time - timedelta(minutes=window_minutes)

        recent_txns = [
            txn for txn in user_history
            if txn.get("transaction_time", datetime.min) > cutoff_time
        ]

        triggered = len(recent_txns) >= max_txns

        return RuleResult(
            rule_name="velocity_check",
            triggered=triggered,
            score=weight if triggered else 0,
            reason=f"User made {len(recent_txns)} transactions in {window_minutes} minutes (max: {max_txns})"
        )

    def _check_high_amount(
        self,
        transaction: Dict,
        user_history: List[Dict],
        rule_config: Dict
    ) -> RuleResult:
        """Check if transaction amount is unusually high."""
        multiplier = rule_config["config"]["threshold_multiplier"]
        weight = rule_config["weight"]
        amount = transaction.get("amount", 0)

        if not user_history:
            # No history, can't determine if amount is high
            return RuleResult(
                rule_name="high_amount",
                triggered=False,
                score=0,
                reason="No transaction history available"
            )

        avg_amount = sum(txn.get("amount", 0) for txn in user_history) / len(user_history)
        threshold = avg_amount * multiplier
        triggered = amount > threshold

        return RuleResult(
            rule_name="high_amount",
            triggered=triggered,
            score=weight if triggered else 0,
            reason=f"Amount ${amount:.2f} is {amount/avg_amount:.1f}x user average ${avg_amount:.2f}"
        )

    def _check_geolocation(
        self,
        transaction: Dict,
        user_history: List[Dict],
        rule_config: Dict
    ) -> RuleResult:
        """Check for impossible travel (too far too fast)."""
        max_distance = rule_config["config"]["max_distance_km"]
        window_minutes = rule_config["config"]["time_window_minutes"]
        weight = rule_config["weight"]

        lat1 = transaction.get("latitude")
        lon1 = transaction.get("longitude")

        if not lat1 or not lon1 or not user_history:
            return RuleResult(
                rule_name="geolocation_impossible",
                triggered=False,
                score=0,
                reason="Insufficient location data"
            )

        current_time = transaction.get("transaction_time", datetime.utcnow())
        cutoff_time = current_time - timedelta(minutes=window_minutes)

        for prev_txn in reversed(user_history):
            prev_time = prev_txn.get("transaction_time")
            lat2 = prev_txn.get("latitude")
            lon2 = prev_txn.get("longitude")

            if not prev_time or not lat2 or not lon2:
                continue

            if prev_time < cutoff_time:
                break

            distance = self._haversine_distance(lat1, lon1, lat2, lon2)
            triggered = distance > max_distance

            if triggered:
                return RuleResult(
                    rule_name="geolocation_impossible",
                    triggered=True,
                    score=weight,
                    reason=f"Card used {distance:.0f}km away within {window_minutes} minutes"
                )

        return RuleResult(
            rule_name="geolocation_impossible",
            triggered=False,
            score=0,
            reason="No impossible travel detected"
        )

    def _check_unusual_time(
        self,
        transaction: Dict,
        rule_config: Dict
    ) -> RuleResult:
        """Check if transaction occurs at unusual hours."""
        unusual_hours = rule_config["config"]["unusual_hours"]
        weight = rule_config["weight"]

        txn_time = transaction.get("transaction_time", datetime.utcnow())
        hour = txn_time.hour

        triggered = hour in unusual_hours

        return RuleResult(
            rule_name="unusual_time",
            triggered=triggered,
            score=weight if triggered else 0,
            reason=f"Transaction at {hour}:00 (unusual hours: {unusual_hours})"
        )

    def _check_new_device(
        self,
        transaction: Dict,
        user_history: List[Dict],
        rule_config: Dict
    ) -> RuleResult:
        """Check for new device with high amount."""
        min_amount = rule_config["config"]["min_amount"]
        weight = rule_config["weight"]

        device_id = transaction.get("device_id")
        amount = transaction.get("amount", 0)

        if not device_id:
            return RuleResult(
                rule_name="new_device",
                triggered=False,
                score=0,
                reason="No device ID provided"
            )

        # Check if device was used before
        known_device = any(
            txn.get("device_id") == device_id
            for txn in user_history
        )

        triggered = not known_device and amount >= min_amount

        return RuleResult(
            rule_name="new_device",
            triggered=triggered,
            score=weight if triggered else 0,
            reason=f"New device with ${amount:.2f} transaction" if triggered
                   else "Known device or low amount"
        )

    def _check_blacklist(
        self,
        transaction: Dict,
        rule_config: Dict
    ) -> RuleResult:
        """Check if country is blacklisted."""
        blocked_countries = rule_config["config"]["blocked_countries"]
        weight = rule_config["weight"]

        country = transaction.get("country", "").upper()
        triggered = country in blocked_countries

        return RuleResult(
            rule_name="blacklist_check",
            triggered=triggered,
            score=weight if triggered else 0,
            reason=f"Country {country} is blocked" if triggered
                   else "Country is allowed"
        )

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on earth (km).
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Radius of earth in kilometers
        r = 6371

        return c * r

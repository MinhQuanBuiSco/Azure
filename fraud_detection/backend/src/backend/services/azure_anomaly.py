"""
Azure Anomaly Detector API integration for fraud detection.

Uses Azure AI Anomaly Detector to detect anomalies in transaction patterns.
This is a managed service that requires no model training.
"""
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import asyncio

from backend.core.config import get_settings


class AzureAnomalyDetector:
    """
    Azure Anomaly Detector service wrapper.

    Uses univariate anomaly detection to identify unusual transaction amounts.
    """

    def __init__(self):
        """Initialize Azure Anomaly Detector client."""
        self.settings = get_settings()
        self.client = None
        self.enabled = False

        # Initialize client if credentials are available
        if self.settings.anomaly_detector_endpoint and self.settings.anomaly_detector_key:
            try:
                self._init_client()
                self.enabled = True
            except Exception as e:
                print(f"⚠️  Azure Anomaly Detector not configured: {e}")
                print("   Continuing without Azure Anomaly Detector...")

    def _init_client(self):
        """Initialize the Azure Anomaly Detector client."""
        try:
            from azure.ai.anomalydetector import AnomalyDetectorClient
            from azure.core.credentials import AzureKeyCredential

            self.client = AnomalyDetectorClient(
                endpoint=self.settings.anomaly_detector_endpoint,
                credential=AzureKeyCredential(self.settings.anomaly_detector_key)
            )
            print(f"✅ Azure Anomaly Detector initialized")
        except ImportError:
            print("⚠️  azure-ai-anomalydetector package not installed")
            self.enabled = False
        except Exception as e:
            print(f"❌ Failed to initialize Azure Anomaly Detector: {e}")
            self.enabled = False

    async def detect_anomaly(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Detect anomaly using Azure Anomaly Detector API.

        Args:
            transaction: Current transaction
            user_history: User's previous transactions

        Returns:
            Tuple of (anomaly_score 0-100, is_anomaly, explanation)
        """
        if not self.enabled or not self.client:
            # Fallback to simple heuristic if Azure is not available
            return self._simple_anomaly_detection(transaction, user_history)

        try:
            # Prepare time series data (amounts over time)
            time_series = self._prepare_time_series(transaction, user_history)

            if len(time_series) < 12:
                # Azure requires at least 12 data points for univariate detection
                return self._simple_anomaly_detection(transaction, user_history)

            # Call Azure Anomaly Detector (async wrapper for sync client)
            result = await self._call_azure_api(time_series)

            if result:
                is_anomaly = result.get('is_anomaly', False)
                severity = result.get('severity', 0.0)  # 0.0 to 1.0

                # Convert severity to 0-100 score
                anomaly_score = severity * 100

                explanation = None
                if is_anomaly:
                    explanation = f"Azure detected anomalous transaction pattern (severity: {severity:.2f})"

                return anomaly_score, is_anomaly, explanation

        except Exception as e:
            print(f"Azure Anomaly Detector error: {e}")
            # Fallback to simple detection
            return self._simple_anomaly_detection(transaction, user_history)

        # Default fallback
        return self._simple_anomaly_detection(transaction, user_history)

    def _prepare_time_series(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> List[Dict]:
        """
        Prepare time series data for Azure API.

        Azure expects: [{"timestamp": "2021-01-01T00:00:00Z", "value": 100.0}, ...]
        """
        time_series = []

        # Add historical transactions
        for txn in reversed(user_history[:100]):  # Last 100 transactions
            timestamp = txn.get('transaction_time')
            amount = txn.get('amount', 0)

            if timestamp and amount:
                if hasattr(timestamp, 'isoformat'):
                    timestamp_str = timestamp.isoformat() + 'Z'
                elif isinstance(timestamp, str):
                    timestamp_str = timestamp
                else:
                    continue

                time_series.append({
                    "timestamp": timestamp_str,
                    "value": float(amount)
                })

        # Add current transaction
        current_time = transaction.get('transaction_time', datetime.utcnow())
        current_amount = transaction.get('amount', 0)

        if hasattr(current_time, 'isoformat'):
            timestamp_str = current_time.isoformat() + 'Z'
        else:
            timestamp_str = datetime.utcnow().isoformat() + 'Z'

        time_series.append({
            "timestamp": timestamp_str,
            "value": float(current_amount)
        })

        return time_series

    async def _call_azure_api(self, time_series: List[Dict]) -> Optional[Dict]:
        """
        Call Azure Anomaly Detector API asynchronously.

        Uses univariate anomaly detection (entire detect).
        """
        try:
            # Azure client is sync, so run in executor
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._detect_entire_series,
                time_series
            )
            return result
        except Exception as e:
            print(f"Azure API call failed: {e}")
            return None

    def _detect_entire_series(self, time_series: List[Dict]) -> Dict:
        """
        Detect anomalies in entire series (sync call).

        Returns the last point's anomaly status.
        """
        try:
            from azure.ai.anomalydetector.models import (
                DetectRequest,
                TimeSeriesPoint,
                TimeGranularity
            )

            # Convert to Azure format
            series = [
                TimeSeriesPoint(
                    timestamp=point['timestamp'],
                    value=point['value']
                )
                for point in time_series
            ]

            # Create request
            request = DetectRequest(
                series=series,
                granularity=TimeGranularity.HOURLY,  # Can be daily, hourly, per_minute, etc.
            )

            # Detect anomalies
            response = self.client.detect_entire_series(request)

            # Get the last point's result (current transaction)
            if response.is_anomaly and len(response.is_anomaly) > 0:
                last_idx = len(response.is_anomaly) - 1
                is_anomaly = response.is_anomaly[last_idx]

                # Get severity if available
                severity = 0.0
                if hasattr(response, 'severity') and response.severity:
                    severity = response.severity[last_idx]
                elif hasattr(response, 'expected_values') and response.expected_values:
                    # Calculate severity based on deviation from expected value
                    expected = response.expected_values[last_idx]
                    actual = time_series[last_idx]['value']
                    deviation = abs(actual - expected) / max(expected, 1)
                    severity = min(1.0, deviation)

                return {
                    'is_anomaly': is_anomaly,
                    'severity': severity
                }

        except Exception as e:
            print(f"Azure detection error: {e}")
            return None

        return {'is_anomaly': False, 'severity': 0.0}

    def _simple_anomaly_detection(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Simple z-score based anomaly detection (fallback).

        Used when Azure is unavailable.
        """
        amount = transaction.get('amount', 0)

        if not user_history or len(user_history) < 3:
            return 0.0, False, None

        amounts = [h.get('amount', 0) for h in user_history]
        if not amounts:
            return 0.0, False, None

        mean_amount = sum(amounts) / len(amounts)
        variance = sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)
        std_amount = variance ** 0.5

        if std_amount == 0:
            return 0.0, False, None

        # Calculate z-score
        z_score = abs(amount - mean_amount) / std_amount

        # Convert to 0-100 score (z-score > 3 is typically anomalous)
        anomaly_score = min(100, (z_score / 3) * 100)
        is_anomaly = z_score > 3

        explanation = None
        if is_anomaly:
            explanation = f"Amount ${amount:.2f} is {z_score:.1f} standard deviations from mean ${mean_amount:.2f}"

        return anomaly_score, is_anomaly, explanation

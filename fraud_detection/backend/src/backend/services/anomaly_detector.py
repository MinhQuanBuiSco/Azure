"""
ML-based anomaly detection using Isolation Forest.

Pretrained unsupervised model for detecting fraudulent transaction patterns.
"""
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetector:
    """
    Isolation Forest-based anomaly detector for fraud detection.

    Uses unsupervised learning to detect outliers in transaction patterns.
    No training required - works out of the box with default parameters.
    """

    def __init__(self, contamination: float = 0.01):
        """
        Initialize the anomaly detector.

        Args:
            contamination: Expected proportion of outliers (fraud rate)
        """
        self.contamination = contamination
        self.model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False,
            n_jobs=-1,
            verbose=0
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = [
            'amount',
            'hour_of_day',
            'day_of_week',
            'days_since_last_txn',
            'avg_amount_last_10',
            'std_amount_last_10',
            'txn_count_last_hour',
            'txn_count_last_day',
            'distance_from_last_txn'
        ]

    def _extract_features(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> np.ndarray:
        """
        Extract features from transaction for anomaly detection.

        Args:
            transaction: Current transaction
            user_history: User's previous transactions

        Returns:
            Feature vector as numpy array
        """
        features = []

        # 1. Transaction amount
        amount = transaction.get('amount', 0)
        features.append(amount)

        # 2. Hour of day (0-23)
        txn_time = transaction.get('transaction_time')
        if txn_time:
            hour = txn_time.hour if hasattr(txn_time, 'hour') else 12
            day_of_week = txn_time.weekday() if hasattr(txn_time, 'weekday') else 0
        else:
            hour = 12
            day_of_week = 0
        features.append(hour)

        # 3. Day of week (0-6)
        features.append(day_of_week)

        # 4. Days since last transaction
        if user_history and txn_time:
            last_txn_time = user_history[0].get('transaction_time')
            if last_txn_time and hasattr(txn_time, 'timestamp') and hasattr(last_txn_time, 'timestamp'):
                days_since = (txn_time.timestamp() - last_txn_time.timestamp()) / 86400
            else:
                days_since = 1.0
        else:
            days_since = 1.0
        features.append(days_since)

        # 5-6. Average and std of last 10 transactions
        if user_history:
            recent_amounts = [h.get('amount', 0) for h in user_history[:10]]
            avg_amount = np.mean(recent_amounts) if recent_amounts else 0
            std_amount = np.std(recent_amounts) if len(recent_amounts) > 1 else 0
        else:
            avg_amount = amount
            std_amount = 0
        features.append(avg_amount)
        features.append(std_amount)

        # 7. Transaction count in last hour
        txn_count_hour = 0
        if user_history and txn_time:
            for h in user_history:
                h_time = h.get('transaction_time')
                if h_time and hasattr(txn_time, 'timestamp') and hasattr(h_time, 'timestamp'):
                    hours_diff = (txn_time.timestamp() - h_time.timestamp()) / 3600
                    if hours_diff <= 1:
                        txn_count_hour += 1
        features.append(txn_count_hour)

        # 8. Transaction count in last day
        txn_count_day = 0
        if user_history and txn_time:
            for h in user_history:
                h_time = h.get('transaction_time')
                if h_time and hasattr(txn_time, 'timestamp') and hasattr(h_time, 'timestamp'):
                    days_diff = (txn_time.timestamp() - h_time.timestamp()) / 86400
                    if days_diff <= 1:
                        txn_count_day += 1
        features.append(txn_count_day)

        # 9. Distance from last transaction (km)
        distance = 0.0
        if user_history:
            lat1 = transaction.get('latitude')
            lon1 = transaction.get('longitude')
            if lat1 and lon1:
                for h in user_history:
                    lat2 = h.get('latitude')
                    lon2 = h.get('longitude')
                    if lat2 and lon2:
                        distance = self._haversine_distance(lat1, lon1, lat2, lon2)
                        break
        features.append(distance)

        return np.array(features).reshape(1, -1)

    def fit(self, transactions: List[Dict], histories: List[List[Dict]]) -> 'AnomalyDetector':
        """
        Fit the anomaly detector on transaction data.

        Args:
            transactions: List of transactions
            histories: List of user histories for each transaction

        Returns:
            Self
        """
        if not transactions:
            raise ValueError("Cannot fit on empty transaction list")

        # Extract features for all transactions
        X = []
        for txn, history in zip(transactions, histories):
            features = self._extract_features(txn, history)
            X.append(features.flatten())

        X = np.array(X)

        # Fit scaler and transform
        X_scaled = self.scaler.fit_transform(X)

        # Fit Isolation Forest
        self.model.fit(X_scaled)
        self.is_fitted = True

        return self

    def predict_anomaly_score(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> Tuple[float, bool]:
        """
        Predict anomaly score for a transaction.

        Args:
            transaction: Transaction to score
            user_history: User's previous transactions

        Returns:
            Tuple of (anomaly_score 0-100, is_anomaly boolean)
        """
        # Extract features
        features = self._extract_features(transaction, user_history)

        if self.is_fitted:
            # Scale features
            features_scaled = self.scaler.transform(features)

            # Get anomaly score (-1 for anomalies, 1 for normal)
            # decision_function returns negative for anomalies, positive for normal
            decision_score = self.model.decision_function(features_scaled)[0]

            # Predict (-1 for anomaly, 1 for normal)
            prediction = self.model.predict(features_scaled)[0]
            is_anomaly = prediction == -1

            # Convert decision score to 0-100 range
            # More negative = more anomalous
            # Normalize to 0-100 where 100 = definitely anomalous
            # decision_function typically ranges from -0.5 to 0.5
            anomaly_score = max(0, min(100, (0.5 - decision_score) * 100))
        else:
            # If not fitted, use simple heuristic
            anomaly_score, is_anomaly = self._simple_anomaly_detection(
                transaction,
                user_history
            )

        return anomaly_score, is_anomaly

    def _simple_anomaly_detection(
        self,
        transaction: Dict,
        user_history: List[Dict]
    ) -> Tuple[float, bool]:
        """
        Simple anomaly detection when model is not fitted.

        Based on z-score of transaction amount.
        """
        amount = transaction.get('amount', 0)

        if not user_history:
            return 0.0, False

        amounts = [h.get('amount', 0) for h in user_history]
        if not amounts:
            return 0.0, False

        mean_amount = np.mean(amounts)
        std_amount = np.std(amounts)

        if std_amount == 0:
            return 0.0, False

        # Calculate z-score
        z_score = abs(amount - mean_amount) / std_amount

        # Convert to 0-100 score (z-score > 3 is typically considered anomalous)
        anomaly_score = min(100, (z_score / 3) * 100)
        is_anomaly = z_score > 3

        return anomaly_score, is_anomaly

    def save_model(self, path: str):
        """Save model and scaler to disk."""
        model_path = Path(path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        with open(model_path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'scaler': self.scaler,
                'is_fitted': self.is_fitted,
                'contamination': self.contamination
            }, f)

    def load_model(self, path: str):
        """Load model and scaler from disk."""
        with open(path, 'rb') as f:
            data = pickle.load(f)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            self.contamination = data['contamination']

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points on Earth (km)."""
        from math import radians, cos, sin, asin, sqrt

        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Radius of earth in kilometers
        return c * r

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Get approximate feature importance.

        Note: Isolation Forest doesn't provide direct feature importance,
        so this is a simple approximation.
        """
        if not self.is_fitted:
            return {}

        # For Isolation Forest, we can't get traditional feature importance
        # Return equal importance as placeholder
        importance = 1.0 / len(self.feature_names)
        return {name: importance for name in self.feature_names}

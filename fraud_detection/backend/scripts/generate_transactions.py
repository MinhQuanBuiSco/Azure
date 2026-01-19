"""
Synthetic transaction data generator for fraud detection testing.

Generates realistic transaction data with configurable fraud rate.
Can be used for:
- Live demo (streaming transactions)
- Load testing
- Testing fraud detection models
"""
import asyncio
import argparse
import random
import httpx
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List, Dict

from faker import Faker

# Initialize Faker for realistic data
fake = Faker()

# Transaction patterns
MERCHANTS = [
    ("Amazon", "online_retail", 50, 500),
    ("Walmart", "retail", 20, 200),
    ("Shell Gas Station", "gas_station", 30, 100),
    ("Starbucks", "restaurant", 5, 25),
    ("Apple Store", "electronics", 200, 2000),
    ("Netflix", "subscription", 10, 20),
    ("Uber", "transportation", 10, 50),
    ("McDonald's", "restaurant", 5, 30),
    ("Target", "retail", 30, 300),
    ("CVS Pharmacy", "pharmacy", 10, 100),
    ("Best Buy", "electronics", 100, 1500),
    ("Whole Foods", "grocery", 50, 200),
    ("Delta Airlines", "travel", 200, 1500),
    ("Hilton Hotel", "travel", 150, 500),
    ("Steam Games", "online_retail", 20, 80),
]

COUNTRIES = [
    ("US", 40.7128, -74.0060, "New York"),
    ("US", 34.0522, -118.2437, "Los Angeles"),
    ("US", 41.8781, -87.6298, "Chicago"),
    ("GB", 51.5074, -0.1278, "London"),
    ("FR", 48.8566, 2.3522, "Paris"),
    ("DE", 52.5200, 13.4050, "Berlin"),
    ("JP", 35.6762, 139.6503, "Tokyo"),
    ("AU", -33.8688, 151.2093, "Sydney"),
    ("CA", 43.6532, -79.3832, "Toronto"),
    ("SG", 1.3521, 103.8198, "Singapore"),
]

# High-risk countries for fraud scenarios (includes blacklisted countries)
HIGH_RISK_COUNTRIES = [
    ("NG", 6.5244, 3.3792, "Lagos"),
    ("RU", 55.7558, 37.6173, "Moscow"),
    ("CN", 39.9042, 116.4074, "Beijing"),
    ("BR", -23.5505, -46.6333, "São Paulo"),
]

# Blacklisted countries (will definitely trigger fraud)
BLACKLISTED_COUNTRIES = [
    ("KP", 39.0392, 125.7625, "Pyongyang"),
    ("IR", 35.6892, 51.3890, "Tehran"),
    ("SY", 33.5138, 36.2765, "Damascus"),
]

DEVICE_IDS = [f"device_{i:04d}" for i in range(1, 201)]
IP_RANGES = ["192.168.1.", "10.0.0.", "172.16.0.", "203.0.113.", "198.51.100."]
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Mozilla/5.0 (Android 11; Mobile) AppleWebKit/537.36",
    "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36",
]


class TransactionGenerator:
    """Generate synthetic transaction data."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        fraud_rate: float = 0.05,
        users_count: int = 50
    ):
        """
        Initialize transaction generator.

        Args:
            api_url: Backend API URL
            fraud_rate: Percentage of fraudulent transactions (0.0 to 1.0)
            users_count: Number of unique users to simulate
        """
        self.api_url = api_url
        self.fraud_rate = fraud_rate
        self.users_count = users_count

        # Generate fake user IDs
        self.user_ids = [str(uuid4()) for _ in range(users_count)]

        # Track user patterns for realistic behavior
        self.user_patterns = {
            user_id: {
                "home_country": random.choice(COUNTRIES),
                "favorite_merchants": random.sample(MERCHANTS, 3),
                "device_id": random.choice(DEVICE_IDS),
                "avg_amount": random.uniform(50, 300),
                "last_transaction_time": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
                "last_location": None,
            }
            for user_id in self.user_ids
        }

    def generate_legitimate_transaction(self, user_id: str) -> Dict:
        """Generate a legitimate transaction based on user patterns."""
        pattern = self.user_patterns[user_id]

        # Use favorite merchant or random
        if random.random() < 0.7:  # 70% chance to use favorite
            merchant_name, category, min_amt, max_amt = random.choice(pattern["favorite_merchants"])
        else:
            merchant_name, category, min_amt, max_amt = random.choice(MERCHANTS)

        # Amount within reasonable range of user's average
        amount = random.gauss(pattern["avg_amount"], pattern["avg_amount"] * 0.3)
        amount = max(min_amt, min(amount, max_amt))  # Clamp to merchant range
        amount = round(amount, 2)

        # Use home country most of the time
        if random.random() < 0.9:  # 90% in home country
            country_code, lat, lon, city = pattern["home_country"]
        else:
            country_code, lat, lon, city = random.choice(COUNTRIES)

        # Add slight location variance
        lat += random.uniform(-0.1, 0.1)
        lon += random.uniform(-0.1, 0.1)

        # Normal business hours (mostly)
        now = datetime.utcnow()
        if random.random() < 0.9:  # 90% during business hours
            hour = random.randint(8, 22)
            now = now.replace(hour=hour)

        return {
            "user_id": user_id,
            "amount": amount,
            "currency": "USD",
            "merchant_name": merchant_name,
            "merchant_category": category,
            "transaction_type": "purchase",
            "latitude": lat,
            "longitude": lon,
            "country": country_code,
            "city": city,
            "device_id": pattern["device_id"],
            "ip_address": f"{random.choice(IP_RANGES)}{random.randint(1, 254)}",
            "user_agent": random.choice(USER_AGENTS),
            "transaction_time": now.isoformat(),
        }

    def generate_fraudulent_transaction(self, user_id: str) -> Dict:
        """Generate a fraudulent transaction with anomalous patterns."""
        pattern = self.user_patterns[user_id]

        # Choose fraud scenario (high_risk_country weighted higher for testing)
        fraud_scenario = random.choice([
            "high_amount",
            "unusual_location",
            "velocity_abuse",
            "new_device",
            "unusual_hours",
            "high_risk_country",
            "high_risk_country",  # Weighted higher
            "high_risk_country",  # Weighted higher
        ])

        # Start with a base transaction
        txn = self.generate_legitimate_transaction(user_id)

        # Apply fraud patterns
        if fraud_scenario == "high_amount":
            # Much higher than usual
            txn["amount"] = round(pattern["avg_amount"] * random.uniform(5, 10), 2)

        elif fraud_scenario == "unusual_location":
            # Far from home
            country_code, lat, lon, city = random.choice(COUNTRIES + HIGH_RISK_COUNTRIES)
            txn["country"] = country_code
            txn["latitude"] = lat
            txn["longitude"] = lon
            txn["city"] = city

        elif fraud_scenario == "velocity_abuse":
            # Multiple transactions in short time
            # (this script just generates one, but marks it as suspicious timing)
            txn["transaction_time"] = datetime.utcnow().isoformat()
            txn["amount"] = round(random.uniform(100, 500), 2)

        elif fraud_scenario == "new_device":
            # Different device with high amount
            txn["device_id"] = f"device_unknown_{random.randint(1000, 9999)}"
            txn["amount"] = round(random.uniform(500, 2000), 2)

        elif fraud_scenario == "unusual_hours":
            # Late night transaction
            now = datetime.utcnow().replace(hour=random.randint(2, 5))
            txn["transaction_time"] = now.isoformat()
            txn["amount"] = round(random.uniform(200, 1000), 2)

        elif fraud_scenario == "high_risk_country":
            # Transaction from blacklisted country (guaranteed to trigger fraud alert)
            country_code, lat, lon, city = random.choice(BLACKLISTED_COUNTRIES)
            txn["country"] = country_code
            txn["latitude"] = lat
            txn["longitude"] = lon
            txn["city"] = city
            txn["amount"] = round(random.uniform(100, 500), 2)

        return txn

    def generate_transaction(self) -> Dict:
        """Generate a single transaction (legitimate or fraudulent)."""
        user_id = random.choice(self.user_ids)

        # Decide if fraudulent
        if random.random() < self.fraud_rate:
            return self.generate_fraudulent_transaction(user_id)
        else:
            return self.generate_legitimate_transaction(user_id)

    async def send_transaction(self, client: httpx.AsyncClient, transaction: Dict) -> Dict:
        """Send transaction to API for scoring."""
        try:
            response = await client.post(
                f"{self.api_url}/api/v1/transactions/score",
                json=transaction,
                timeout=10.0
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error sending transaction: {e}")
            return None

    async def generate_stream(
        self,
        count: int = 100,
        interval: float = 1.0,
        verbose: bool = True
    ):
        """
        Generate a stream of transactions.

        Args:
            count: Number of transactions to generate
            interval: Seconds between transactions
            verbose: Print transaction details
        """
        print(f"🚀 Starting transaction generator")
        print(f"   API: {self.api_url}")
        print(f"   Count: {count}")
        print(f"   Interval: {interval}s")
        print(f"   Fraud Rate: {self.fraud_rate * 100:.1f}%")
        print(f"   Users: {self.users_count}")
        print()

        stats = {
            "total": 0,
            "fraud_detected": 0,
            "blocked": 0,
            "errors": 0,
        }

        async with httpx.AsyncClient() as client:
            for i in range(count):
                # Generate transaction
                txn = self.generate_transaction()

                # Send to API
                result = await self.send_transaction(client, txn)

                stats["total"] += 1

                if result:
                    if result.get("is_fraud"):
                        stats["fraud_detected"] += 1
                    if result.get("is_blocked"):
                        stats["blocked"] += 1

                    if verbose:
                        fraud_flag = "🚨 FRAUD" if result.get("is_fraud") else "✅ OK"
                        print(
                            f"[{i+1}/{count}] {fraud_flag} | "
                            f"${txn['amount']:.2f} @ {txn['merchant_name']} | "
                            f"Score: {result.get('fraud_score', 0):.1f} | "
                            f"Risk: {result.get('risk_level', 'unknown').upper()}"
                        )
                else:
                    stats["errors"] += 1

                # Wait before next transaction
                if i < count - 1:
                    await asyncio.sleep(interval)

        # Print summary
        print()
        print("=" * 60)
        print("📊 Generation Summary")
        print("=" * 60)
        print(f"Total Transactions:  {stats['total']}")
        print(f"Fraud Detected:      {stats['fraud_detected']} ({stats['fraud_detected']/stats['total']*100:.1f}%)")
        print(f"Blocked:             {stats['blocked']}")
        print(f"Errors:              {stats['errors']}")
        print("=" * 60)


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate synthetic transactions for fraud detection testing"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8000",
        help="Backend API URL"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=100,
        help="Number of transactions to generate"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between transactions"
    )
    parser.add_argument(
        "--fraud-rate",
        type=float,
        default=0.10,
        help="Fraud rate (0.0 to 1.0, default 0.10 = 10%%)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=50,
        help="Number of unique users"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode (no per-transaction output)"
    )

    args = parser.parse_args()

    generator = TransactionGenerator(
        api_url=args.api_url,
        fraud_rate=args.fraud_rate,
        users_count=args.users
    )

    await generator.generate_stream(
        count=args.count,
        interval=args.interval,
        verbose=not args.quiet
    )


if __name__ == "__main__":
    asyncio.run(main())

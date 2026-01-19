"""
ETL script to load Kaggle Credit Card Fraud Detection dataset into PostgreSQL.

Dataset: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
Contains 284,807 transactions with 492 frauds (0.172% fraud rate).

Usage:
    python scripts/load_kaggle_data.py --csv-path data/creditcard.csv --limit 10000
"""
import asyncio
import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4
from typing import List, Dict

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import select
from backend.core.database import get_async_sessionmaker
from backend.models import User, Transaction
from backend.core.config import get_settings


# Seed data for realistic transaction metadata
MERCHANTS = [
    ("Amazon", "online_retail"),
    ("Walmart", "retail"),
    ("Shell Gas Station", "gas_station"),
    ("Starbucks", "restaurant"),
    ("Apple Store", "electronics"),
    ("Netflix", "subscription"),
    ("Uber", "transportation"),
    ("McDonald's", "restaurant"),
    ("Target", "retail"),
    ("CVS Pharmacy", "pharmacy"),
    ("Best Buy", "electronics"),
    ("Whole Foods", "grocery"),
    ("Delta Airlines", "travel"),
    ("Hilton Hotel", "travel"),
    ("Steam Games", "online_retail"),
]

COUNTRIES = [
    ("US", 40.7128, -74.0060),  # New York
    ("US", 34.0522, -118.2437),  # Los Angeles
    ("US", 41.8781, -87.6298),  # Chicago
    ("GB", 51.5074, -0.1278),  # London
    ("FR", 48.8566, 2.3522),  # Paris
    ("DE", 52.5200, 13.4050),  # Berlin
    ("JP", 35.6762, 139.6503),  # Tokyo
    ("AU", -33.8688, 151.2093),  # Sydney
    ("CA", 43.6532, -79.3832),  # Toronto
    ("SG", 1.3521, 103.8198),  # Singapore
]

DEVICE_IDS = [f"device_{i:04d}" for i in range(1, 101)]
IP_RANGES = ["192.168.1.", "10.0.0.", "172.16.0."]
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (Android 11; Mobile)",
]


class KaggleDataLoader:
    """Load Kaggle credit card fraud dataset into PostgreSQL."""

    def __init__(self, csv_path: str, limit: int = None):
        """
        Initialize the data loader.

        Args:
            csv_path: Path to creditcard.csv file
            limit: Max number of transactions to load (for testing)
        """
        self.csv_path = Path(csv_path)
        self.limit = limit
        self.settings = get_settings()
        self.users: Dict[str, User] = {}

    async def load(self):
        """Main ETL process."""
        print(f"📊 Loading Kaggle Credit Card Fraud Detection dataset")
        print(f"   CSV: {self.csv_path}")
        print(f"   Limit: {self.limit or 'No limit'}")

        if not self.csv_path.exists():
            print(f"❌ CSV file not found: {self.csv_path}")
            print(f"\nDownload from: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
            return

        # Create async session
        async_session = get_async_sessionmaker()

        async with async_session() as session:
            # 1. Create seed users
            print("\n👥 Creating seed users...")
            await self._create_users(session)

            # 2. Load transactions
            print("\n💳 Loading transactions...")
            await self._load_transactions(session)

            print("\n✅ ETL complete!")

    async def _create_users(self, session):
        """Create seed users for transactions."""
        # Create 100 users
        user_count = 100

        for i in range(1, user_count + 1):
            user = User(
                id=uuid4(),
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                phone=f"+1555000{i:04d}",
                country="US",
                is_active=True,
            )
            session.add(user)
            self.users[f"user_{i}"] = user

        await session.commit()
        print(f"   Created {user_count} users")

    async def _load_transactions(self, session):
        """Load transactions from CSV."""
        user_list = list(self.users.values())
        base_time = datetime.utcnow() - timedelta(days=365)

        legitimate_count = 0
        fraud_count = 0
        batch = []
        batch_size = 1000

        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)

            for idx, row in enumerate(reader):
                if self.limit and idx >= self.limit:
                    break

                # Parse row
                time_seconds = float(row['Time'])
                amount = float(row['Amount'])
                is_fraud = int(row['Class']) == 1

                # Skip zero-amount transactions
                if amount < 0.01:
                    continue

                # Assign to random user
                user = random.choice(user_list)

                # Generate realistic metadata
                merchant_name, merchant_category = random.choice(MERCHANTS)
                country_code, latitude, longitude = random.choice(COUNTRIES)
                device_id = random.choice(DEVICE_IDS)
                ip_address = f"{random.choice(IP_RANGES)}{random.randint(1, 254)}"
                user_agent = random.choice(USER_AGENTS)

                # Calculate transaction time
                txn_time = base_time + timedelta(seconds=time_seconds)

                # For fraudulent transactions, add some fraud indicators
                if is_fraud:
                    # More likely to be:
                    # - High amounts
                    # - Unusual hours (2-5am)
                    # - Foreign countries
                    if random.random() > 0.5:
                        country_code = random.choice(["NG", "RU", "CN", "BR"])
                        latitude, longitude = random.uniform(-90, 90), random.uniform(-180, 180)

                    # Unusual hours
                    if random.random() > 0.5:
                        txn_time = txn_time.replace(hour=random.randint(2, 5))

                    fraud_count += 1
                else:
                    legitimate_count += 1

                # Create transaction
                transaction = Transaction(
                    id=uuid4(),
                    user_id=user.id,
                    amount=round(amount, 2),
                    currency="USD",
                    merchant_name=merchant_name,
                    merchant_category=merchant_category,
                    transaction_type="purchase",
                    latitude=latitude,
                    longitude=longitude,
                    country=country_code,
                    city="Unknown",
                    device_id=device_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    transaction_time=txn_time,
                    fraud_score=0.0,  # Will be scored by API later
                    risk_level="low",
                    is_fraud=is_fraud,
                    is_blocked=False,
                    model_version="kaggle_dataset",
                    rule_triggers=[],
                )

                batch.append(transaction)

                # Bulk insert in batches
                if len(batch) >= batch_size:
                    session.add_all(batch)
                    await session.commit()
                    print(f"   Loaded {idx + 1} transactions (Fraud: {fraud_count}, Legitimate: {legitimate_count})")
                    batch = []

            # Insert remaining
            if batch:
                session.add_all(batch)
                await session.commit()

        print(f"\n📈 Summary:")
        print(f"   Total transactions: {legitimate_count + fraud_count}")
        print(f"   Legitimate: {legitimate_count} ({legitimate_count / (legitimate_count + fraud_count) * 100:.2f}%)")
        print(f"   Fraudulent: {fraud_count} ({fraud_count / (legitimate_count + fraud_count) * 100:.2f}%)")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Load Kaggle Credit Card Fraud Detection dataset"
    )
    parser.add_argument(
        "--csv-path",
        type=str,
        default="data/creditcard.csv",
        help="Path to creditcard.csv file"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of transactions to load (for testing)"
    )

    args = parser.parse_args()

    loader = KaggleDataLoader(csv_path=args.csv_path, limit=args.limit)
    await loader.load()


if __name__ == "__main__":
    asyncio.run(main())

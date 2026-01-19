"""
Analytics and dashboard endpoints.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, cast, Date
from datetime import datetime, timedelta

from backend.core.database import get_db
from backend.services.cache import get_cache
from backend.services.claude_explainer import ClaudeExplainer
from backend.models import Transaction

router = APIRouter()
claude_explainer = ClaudeExplainer()


@router.get("/analytics/dashboard")
async def get_dashboard_metrics(
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard metrics for fraud detection.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Total transactions today
    total_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= today_start)
    )
    total_today = total_result.scalar() or 0

    # Fraud detected today
    fraud_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= today_start)
        .where(Transaction.is_fraud == True)
    )
    fraud_count = fraud_result.scalar() or 0

    # Fraud rate
    fraud_rate = round((fraud_count / total_today * 100), 2) if total_today > 0 else 0

    # Total amount blocked today
    blocked_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(Transaction.created_at >= today_start)
        .where(Transaction.is_blocked == True)
    )
    total_blocked = blocked_result.scalar() or 0.0

    # Blocked count (for alerts pending approximation)
    blocked_count_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= today_start)
        .where(Transaction.is_blocked == True)
    )
    blocked_count = blocked_count_result.scalar() or 0

    return {
        "total_transactions_today": total_today,
        "fraud_detected": fraud_count,
        "fraud_rate": fraud_rate,
        "total_amount_blocked": round(float(total_blocked), 2),
        "alerts_pending": blocked_count,
        "average_processing_time_ms": 45,
    }


@router.get("/analytics/trends")
async def get_fraud_trends(
    days: int = 7,
    db: AsyncSession = Depends(get_db)
):
    """
    Get fraud trends over time.
    """
    now = datetime.utcnow()
    start_date = now - timedelta(days=days)

    # Get daily aggregated data
    data_points = []
    for i in range(days):
        day_start = (start_date + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        # Total transactions for this day
        total_result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= day_start)
            .where(Transaction.created_at < day_end)
        )
        total_count = total_result.scalar() or 0

        # Fraud count for this day
        fraud_result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= day_start)
            .where(Transaction.created_at < day_end)
            .where(Transaction.is_fraud == True)
        )
        fraud_count = fraud_result.scalar() or 0

        # Blocked count for this day
        blocked_result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= day_start)
            .where(Transaction.created_at < day_end)
            .where(Transaction.is_blocked == True)
        )
        blocked_count = blocked_result.scalar() or 0

        data_points.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "day": day_start.strftime("%a"),
            "transactions": total_count,
            "fraud": fraud_count,
            "blocked": blocked_count,
        })

    return {
        "period_days": days,
        "data_points": data_points,
    }


@router.get("/analytics/hourly")
async def get_hourly_trends(
    db: AsyncSession = Depends(get_db)
):
    """
    Get hourly transaction volume and fraud rate for today.
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    hourly_data = []
    for hour in range(24):
        hour_start = today_start + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)

        # Total transactions for this hour
        total_result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= hour_start)
            .where(Transaction.created_at < hour_end)
        )
        total_count = total_result.scalar() or 0

        # Fraud count for this hour
        fraud_result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= hour_start)
            .where(Transaction.created_at < hour_end)
            .where(Transaction.is_fraud == True)
        )
        fraud_count = fraud_result.scalar() or 0

        fraud_rate = round((fraud_count / total_count * 100), 1) if total_count > 0 else 0

        hourly_data.append({
            "hour": f"{hour}:00",
            "transactions": total_count,
            "fraud": fraud_count,
            "fraudRate": fraud_rate,
        })

    return {
        "date": today_start.strftime("%Y-%m-%d"),
        "data_points": hourly_data,
    }


@router.get("/analytics/risk-distribution")
async def get_risk_distribution(
    db: AsyncSession = Depends(get_db)
):
    """
    Get distribution of transactions by risk level.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Count by risk level (case-insensitive comparison)
    low_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= week_ago)
        .where(func.lower(Transaction.risk_level) == "low")
    )
    low_count = low_result.scalar() or 0

    medium_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= week_ago)
        .where(func.lower(Transaction.risk_level) == "medium")
    )
    medium_count = medium_result.scalar() or 0

    high_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= week_ago)
        .where(func.lower(Transaction.risk_level) == "high")
    )
    high_count = high_result.scalar() or 0

    critical_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= week_ago)
        .where(func.lower(Transaction.risk_level) == "critical")
    )
    critical_count = critical_result.scalar() or 0

    return {
        "period_days": 7,
        "distribution": [
            {"name": "Low Risk", "value": low_count, "color": "#10b981"},
            {"name": "Medium Risk", "value": medium_count, "color": "#f59e0b"},
            {"name": "High Risk", "value": high_count, "color": "#ef4444"},
            {"name": "Critical", "value": critical_count, "color": "#dc2626"},
        ]
    }


@router.get("/analytics/merchant-fraud")
async def get_merchant_fraud(
    db: AsyncSession = Depends(get_db)
):
    """
    Get fraud statistics by merchant category.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Get merchant categories with fraud counts
    # Using raw merchant names as categories for now
    result = await db.execute(
        select(
            Transaction.merchant_name,
            func.count(Transaction.id).label("total"),
            func.sum(case((Transaction.is_fraud == True, 1), else_=0)).label("fraud")
        )
        .where(Transaction.created_at >= week_ago)
        .group_by(Transaction.merchant_name)
        .order_by(func.count(Transaction.id).desc())
        .limit(10)
    )
    rows = result.all()

    categories = []
    for row in rows:
        categories.append({
            "category": row.merchant_name or "Unknown",
            "total": row.total,
            "fraud": int(row.fraud or 0),
        })

    return {
        "period_days": 7,
        "categories": categories,
    }


@router.get("/analytics/score-distribution")
async def get_score_distribution(
    db: AsyncSession = Depends(get_db)
):
    """
    Get distribution of fraud scores.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    ranges = [
        (0, 20, "0-20"),
        (20, 40, "20-40"),
        (40, 60, "40-60"),
        (60, 80, "60-80"),
        (80, 100, "80-100"),
    ]

    distribution = []
    for low, high, label in ranges:
        result = await db.execute(
            select(func.count(Transaction.id))
            .where(Transaction.created_at >= week_ago)
            .where(Transaction.fraud_score >= low)
            .where(Transaction.fraud_score < high)
        )
        count = result.scalar() or 0
        distribution.append({
            "range": label,
            "count": count,
        })

    return {
        "period_days": 7,
        "distribution": distribution,
    }


@router.get("/analytics/rules-performance")
async def get_rules_performance(
    db: AsyncSession = Depends(get_db)
):
    """
    Get performance metrics for each fraud detection rule.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    # Get all transactions with triggered rules
    result = await db.execute(
        select(Transaction.triggered_rules, Transaction.is_fraud)
        .where(Transaction.created_at >= week_ago)
        .where(Transaction.triggered_rules.isnot(None))
    )
    rows = result.all()

    # Aggregate rule statistics
    rule_stats = {}
    for row in rows:
        triggered_rules = row.triggered_rules or []
        is_fraud = row.is_fraud

        for rule in triggered_rules:
            if rule not in rule_stats:
                rule_stats[rule] = {"triggers": 0, "true_positives": 0}
            rule_stats[rule]["triggers"] += 1
            if is_fraud:
                rule_stats[rule]["true_positives"] += 1

    rules = []
    for rule_id, stats in rule_stats.items():
        triggers = stats["triggers"]
        true_positives = stats["true_positives"]
        false_positives = triggers - true_positives
        precision = round(true_positives / triggers, 2) if triggers > 0 else 0

        rules.append({
            "rule_id": rule_id,
            "name": rule_id.replace("_", " ").title(),
            "triggers": triggers,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "precision": precision,
        })

    # Sort by triggers descending
    rules.sort(key=lambda x: x["triggers"], reverse=True)

    return {
        "period_days": 7,
        "rules": rules,
    }


@router.get("/analytics/cache-stats")
async def get_cache_statistics():
    """
    Get Redis cache performance statistics.
    """
    cache = get_cache()
    stats = await cache.get_stats()

    # Calculate hit rate
    hits = stats.get("keyspace_hits", 0)
    misses = stats.get("keyspace_misses", 0)
    total_requests = hits + misses
    hit_rate = (hits / total_requests * 100) if total_requests > 0 else 0

    return {
        "cache_enabled": await cache.ping(),
        "connected_clients": stats.get("connected_clients", 0),
        "memory_usage": stats.get("used_memory_human", "0B"),
        "total_commands": stats.get("total_commands_processed", 0),
        "keyspace_hits": hits,
        "keyspace_misses": misses,
        "hit_rate_percent": round(hit_rate, 2)
    }


@router.get("/analytics/summary")
async def get_ai_summary(
    hours: int = 24,
    db: AsyncSession = Depends(get_db)
):
    """
    Get AI-generated summary of fraud detection activity.

    Uses Claude Haiku to generate natural language summary.
    """
    # Get transactions from last N hours
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    # Count total transactions
    total_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= cutoff_time)
    )
    total_count = total_result.scalar() or 0

    # Count fraud transactions
    fraud_result = await db.execute(
        select(func.count(Transaction.id))
        .where(Transaction.created_at >= cutoff_time)
        .where(Transaction.is_fraud == True)
    )
    fraud_count = fraud_result.scalar() or 0

    # Sum blocked amounts
    amount_result = await db.execute(
        select(func.sum(Transaction.amount))
        .where(Transaction.created_at >= cutoff_time)
        .where(Transaction.is_blocked == True)
    )
    total_blocked = amount_result.scalar() or 0.0

    # Get most triggered rules (from JSON field)
    # This is a simplified version - in production you'd want better aggregation
    top_rules = ["velocity_check", "high_amount", "geolocation_impossible"]

    # Generate AI summary
    summary = await claude_explainer.generate_batch_summary(
        transaction_count=total_count,
        fraud_count=fraud_count,
        total_amount_blocked=float(total_blocked),
        top_rules=top_rules
    )

    return {
        "period_hours": hours,
        "total_transactions": total_count,
        "fraud_detected": fraud_count,
        "fraud_rate_percent": round((fraud_count / total_count * 100), 2) if total_count > 0 else 0,
        "total_amount_blocked": round(float(total_blocked), 2),
        "summary": summary,
        "claude_enabled": claude_explainer.enabled
    }

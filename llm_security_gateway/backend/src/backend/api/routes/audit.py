"""Audit log API endpoints."""

from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status

from backend.api.dependencies import CosmosDep, APIKeyDep
from backend.models.audit import AuditLog, AuditLogQuery, AuditLogSummary

router = APIRouter()


@router.get("/audit")
async def list_audit_logs(
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    start_date: datetime | None = Query(None, description="Filter by start date"),
    end_date: datetime | None = Query(None, description="Filter by end date"),
    status_filter: Literal["allowed", "blocked", "filtered", "error"] | None = Query(
        None, alias="status", description="Filter by status"
    ),
    user_id: str | None = Query(None, description="Filter by user ID"),
    has_threats: bool | None = Query(None, description="Filter by threat detection"),
    has_pii: bool | None = Query(None, description="Filter by PII detection"),
    model: str | None = Query(None, description="Filter by model"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results to return"),
    offset: int = Query(0, ge=0, description="Results offset"),
    sort_by: str = Query("timestamp", description="Sort field"),
    sort_order: Literal["asc", "desc"] = Query("desc", description="Sort order"),
) -> dict:
    """
    List audit logs with optional filtering.

    Returns paginated audit log entries.
    """
    query = AuditLogQuery(
        start_date=start_date,
        end_date=end_date,
        status=status_filter,
        user_id=user_id,
        has_threats=has_threats,
        has_pii=has_pii,
        model=model,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    logs = await cosmos.query_audit_logs(query)

    return {
        "logs": [log.model_dump() for log in logs],
        "count": len(logs),
        "offset": offset,
        "limit": limit,
    }


@router.get("/audit/summary")
async def get_audit_summary(
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    start_date: datetime | None = Query(None, description="Start of time range"),
    end_date: datetime | None = Query(None, description="End of time range"),
    period: Literal["1h", "24h", "7d", "30d"] | None = Query(
        None, description="Predefined time period"
    ),
) -> AuditLogSummary:
    """
    Get summary statistics for audit logs.

    Returns aggregated metrics for the specified time range.
    """
    # Handle predefined periods
    if period and not start_date:
        now = datetime.utcnow()
        period_deltas = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_date = now - period_deltas.get(period, timedelta(hours=24))
        end_date = now

    return await cosmos.get_summary(start_date, end_date)


@router.get("/audit/{log_id}")
async def get_audit_log(
    log_id: str,
    request_id: str,
    cosmos: CosmosDep,
    api_key: APIKeyDep,
) -> AuditLog:
    """
    Get a specific audit log by ID.

    Requires the request_id as it's used as the partition key.
    """
    log = await cosmos.get_audit_log(log_id, request_id)

    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log {log_id} not found",
        )

    return log


@router.get("/analytics/threats")
async def get_threat_analytics(
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    period: Literal["1h", "24h", "7d", "30d"] | None = Query("24h"),
) -> dict:
    """
    Get threat detection analytics.

    Returns breakdown of detected threats by type.
    """
    # Handle predefined periods
    if period and not start_date:
        now = datetime.utcnow()
        period_deltas = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_date = now - period_deltas.get(period, timedelta(hours=24))
        end_date = now

    # Get logs with threats
    query = AuditLogQuery(
        start_date=start_date,
        end_date=end_date,
        has_threats=True,
        limit=1000,
    )

    logs = await cosmos.query_audit_logs(query)

    # Aggregate threat types
    threat_counts = {}
    severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

    for log in logs:
        for threat in log.threats_detected:
            threat_type = threat.get("type", "unknown")
            threat_counts[threat_type] = threat_counts.get(threat_type, 0) + 1

            severity = threat.get("severity", "medium")
            if severity in severity_counts:
                severity_counts[severity] += 1

    return {
        "period": {"start": start_date, "end": end_date},
        "total_threats": sum(threat_counts.values()),
        "by_type": threat_counts,
        "by_severity": severity_counts,
        "affected_requests": len(logs),
    }


@router.get("/analytics/usage")
async def get_usage_analytics(
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    start_date: datetime | None = Query(None),
    end_date: datetime | None = Query(None),
    period: Literal["1h", "24h", "7d", "30d"] | None = Query("24h"),
) -> dict:
    """
    Get usage analytics.

    Returns token usage and request statistics.
    """
    # Handle predefined periods
    if period and not start_date:
        now = datetime.utcnow()
        period_deltas = {
            "1h": timedelta(hours=1),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        start_date = now - period_deltas.get(period, timedelta(hours=24))
        end_date = now

    summary = await cosmos.get_summary(start_date, end_date)

    return {
        "period": {"start": start_date, "end": end_date},
        "requests": {
            "total": summary.total_requests,
            "allowed": summary.allowed_requests,
            "blocked": summary.blocked_requests,
            "filtered": summary.filtered_requests,
            "errors": summary.error_requests,
        },
        "tokens": {
            "total": summary.total_tokens,
            "prompt": summary.prompt_tokens,
            "completion": summary.completion_tokens,
        },
        "performance": {
            "avg_response_time_ms": summary.avg_response_time_ms,
        },
    }

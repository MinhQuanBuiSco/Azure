"""Request and response schemas for research API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResearchType(str, Enum):
    """Type of research to perform."""

    COMPREHENSIVE = "comprehensive"
    QUICK_ANALYSIS = "quick_analysis"
    NEWS_FOCUSED = "news_focused"
    FINANCIAL_ONLY = "financial_only"


class ResearchStatus(str, Enum):
    """Status of a research session."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResearchRequest(BaseModel):
    """Request to start a new research session."""

    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the company to research",
    )
    ticker_symbol: str | None = Field(
        None,
        max_length=10,
        description="Stock ticker symbol (optional, will be auto-detected)",
    )
    research_type: ResearchType = Field(
        default=ResearchType.COMPREHENSIVE,
        description="Type of research to perform",
    )
    additional_context: str | None = Field(
        None,
        max_length=1000,
        description="Additional context or specific questions",
    )
    include_competitors: bool = Field(
        default=True,
        description="Include competitor analysis",
    )
    time_period_days: int = Field(
        default=30,
        ge=7,
        le=365,
        description="Number of days of historical data to analyze",
    )


class ResearchResponse(BaseModel):
    """Response containing research session info."""

    research_id: str = Field(..., description="Unique research session ID")
    status: ResearchStatus = Field(..., description="Current status")
    company_name: str = Field(..., description="Company being researched")
    ticker_symbol: str | None = Field(None, description="Detected ticker symbol")
    research_type: ResearchType = Field(..., description="Type of research")
    created_at: datetime = Field(..., description="Session creation time")
    updated_at: datetime = Field(..., description="Last update time")
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Overall progress percentage",
    )
    current_agent: str | None = Field(None, description="Currently active agent")
    error_message: str | None = Field(None, description="Error message if failed")


class ResearchResult(BaseModel):
    """Complete research result."""

    research_id: str
    status: ResearchStatus
    company_name: str
    ticker_symbol: str | None
    research_type: ResearchType
    created_at: datetime
    completed_at: datetime | None

    # Research outputs
    executive_summary: str | None = None
    market_analysis: str | dict[str, Any] | None = None
    financial_data: dict[str, Any] | None = None
    news_analysis: dict[str, Any] | None = None
    competitor_analysis: dict[str, Any] | None = None
    risk_assessment: str | dict[str, Any] | None = None
    recommendations: list[str] | None = None

    # Full report
    full_report: str | None = None


class ReportListItem(BaseModel):
    """Summary item for report listing."""

    research_id: str
    company_name: str
    ticker_symbol: str | None
    research_type: ResearchType
    status: ResearchStatus
    created_at: datetime
    completed_at: datetime | None


class ReportListResponse(BaseModel):
    """Response containing list of reports."""

    reports: list[ReportListItem]
    total: int
    page: int
    page_size: int

"""Agent state and progress schemas."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentType(str, Enum):
    """Types of agents in the pipeline."""

    SUPERVISOR = "supervisor"
    WEB_RESEARCH = "web_research"
    FINANCIAL_DATA = "financial_data"
    NEWS_ANALYSIS = "news_analysis"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"


class AgentStatus(str, Enum):
    """Status of an individual agent."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"
    SKIPPED = "skipped"


class AgentProgress(BaseModel):
    """Progress update for a single agent."""

    agent_type: AgentType
    status: AgentStatus
    message: str | None = None
    progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Agent progress percentage",
    )
    started_at: datetime | None = None
    completed_at: datetime | None = None
    output_preview: str | None = Field(
        None,
        max_length=500,
        description="Preview of agent output",
    )
    error: str | None = None


class PipelineProgress(BaseModel):
    """Overall pipeline progress including all agents."""

    research_id: str
    overall_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
    )
    current_agent: AgentType | None = None
    agents: dict[str, AgentProgress] = Field(default_factory=dict)
    started_at: datetime
    estimated_completion: datetime | None = None


class StreamToken(BaseModel):
    """Single token from LLM streaming."""

    research_id: str
    agent_type: AgentType
    token: str
    is_final: bool = False


class WebSocketMessage(BaseModel):
    """WebSocket message format."""

    type: str = Field(..., description="Message type: progress, error, complete")
    research_id: str
    payload: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

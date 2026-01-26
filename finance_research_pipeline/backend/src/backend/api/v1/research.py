"""REST API endpoints for research operations."""

import asyncio
from datetime import datetime, UTC
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Response, status

from backend.core.dependencies import (
    CacheServiceDep,
    CosmosServiceDep,
    LLMFactoryDep,
    SettingsDep,
    WebSocketManagerDep,
)
from backend.core.logging import get_logger
from backend.graph.research_graph import run_research_pipeline
from backend.schemas.research import (
    ReportListItem,
    ReportListResponse,
    ResearchRequest,
    ResearchResponse,
    ResearchResult,
    ResearchStatus,
)
from backend.services.report_generator import ReportGenerator

logger = get_logger(__name__)

router = APIRouter(prefix="/research", tags=["research"])

# In-memory storage for research sessions (for demo/dev without Cosmos DB)
_research_sessions: dict[str, dict[str, Any]] = {}


@router.post(
    "/start",
    response_model=ResearchResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_research(
    request: ResearchRequest,
    background_tasks: BackgroundTasks,
    settings: SettingsDep,
    llm_factory: LLMFactoryDep,
    ws_manager: WebSocketManagerDep,
    cache_service: CacheServiceDep,
    cosmos_service: CosmosServiceDep,
) -> ResearchResponse:
    """
    Start a new research session.

    This endpoint initiates the research pipeline in the background
    and returns immediately with a research ID for tracking.
    """
    research_id = str(uuid4())
    now = datetime.now(UTC)

    logger.info(f"Starting research session {research_id} for {request.company_name}")

    # Create session record
    session = {
        "research_id": research_id,
        "company_name": request.company_name,
        "ticker_symbol": request.ticker_symbol,
        "research_type": request.research_type,
        "additional_context": request.additional_context,
        "include_competitors": request.include_competitors,
        "time_period_days": request.time_period_days,
        "status": ResearchStatus.PENDING,
        "progress": 0.0,
        "current_agent": None,
        "created_at": now,
        "updated_at": now,
        "error_message": None,
    }

    # Store in Cosmos DB if available
    if cosmos_service:
        await cosmos_service.create_session(
            research_id=research_id,
            company_name=request.company_name,
            research_type=request.research_type,
            ticker_symbol=request.ticker_symbol,
            additional_context=request.additional_context,
        )

    # Store in memory as fallback
    _research_sessions[research_id] = session

    # Cache the session
    await cache_service.set_research_state(research_id, session)

    # Get LLM for the pipeline
    llm = llm_factory.get_llm()

    # Run pipeline in background
    background_tasks.add_task(
        _run_research_background,
        research_id=research_id,
        request=request,
        llm=llm,
        ws_manager=ws_manager,
        cache_service=cache_service,
        cosmos_service=cosmos_service,
    )

    return ResearchResponse(
        research_id=research_id,
        status=ResearchStatus.PENDING,
        company_name=request.company_name,
        ticker_symbol=request.ticker_symbol,
        research_type=request.research_type,
        created_at=now,
        updated_at=now,
        progress=0.0,
    )


async def _run_research_background(
    research_id: str,
    request: ResearchRequest,
    llm: Any,
    ws_manager: Any,
    cache_service: Any,
    cosmos_service: Any,
) -> None:
    """Background task to run the research pipeline."""
    try:
        # Update status to in progress
        _research_sessions[research_id]["status"] = ResearchStatus.IN_PROGRESS
        _research_sessions[research_id]["updated_at"] = datetime.now(UTC)

        # Persist to cache immediately
        await cache_service.set_research_state(research_id, _research_sessions[research_id])

        # Run the pipeline
        final_state = await run_research_pipeline(
            research_id=research_id,
            company_name=request.company_name,
            research_type=request.research_type.value,
            llm=llm,
            ws_manager=ws_manager,
            ticker_symbol=request.ticker_symbol,
            additional_context=request.additional_context,
            include_competitors=request.include_competitors,
            time_period_days=request.time_period_days,
        )

        # Update session with results
        _research_sessions[research_id].update({
            "status": final_state.get("status", ResearchStatus.COMPLETED),
            "ticker_symbol": final_state.get("ticker_symbol"),
            "progress": 100.0,
            "completed_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
            "result": {
                "executive_summary": final_state.get("executive_summary"),
                "full_report": final_state.get("full_report"),
                "recommendations": final_state.get("recommendations", []),
                "market_analysis": final_state.get("market_analysis"),
                "risk_assessment": final_state.get("risk_assessment"),
                "financial_data": final_state.get("financial_data"),
                "news_data": final_state.get("news_data"),
            },
        })

        # Cache the final state
        await cache_service.set_research_state(research_id, _research_sessions[research_id])

        # Update Cosmos DB if available
        if cosmos_service:
            await cosmos_service.update_session(
                research_id,
                {
                    "status": ResearchStatus.COMPLETED.value,
                    "progress": 100.0,
                    "completed_at": datetime.now(UTC).isoformat(),
                },
            )
            await cosmos_service.save_report(
                research_id,
                final_state.get("full_report", ""),
                _research_sessions[research_id]["result"],
            )

        logger.info(f"Research session {research_id} completed successfully")

    except Exception as e:
        logger.error(f"Research session {research_id} failed: {e}")
        _research_sessions[research_id]["status"] = ResearchStatus.FAILED
        _research_sessions[research_id]["error_message"] = str(e)
        _research_sessions[research_id]["updated_at"] = datetime.now(UTC)

        # Persist failure to cache
        await cache_service.set_research_state(research_id, _research_sessions[research_id])

        await ws_manager.send_error(research_id, str(e))


@router.get("/{research_id}", response_model=ResearchResponse)
async def get_research_status(
    research_id: str,
    cache_service: CacheServiceDep,
    cosmos_service: CosmosServiceDep,
) -> ResearchResponse:
    """Get the status of a research session."""
    # Try cache first
    cached = await cache_service.get_research_state(research_id)
    if cached:
        return ResearchResponse(**cached)

    # Try Cosmos DB
    if cosmos_service:
        session = await cosmos_service.get_session(research_id)
        if session:
            return ResearchResponse(
                research_id=session["research_id"],
                status=ResearchStatus(session["status"]),
                company_name=session["company_name"],
                ticker_symbol=session.get("ticker_symbol"),
                research_type=session["research_type"],
                created_at=session["created_at"],
                updated_at=session["updated_at"],
                progress=session.get("progress", 0.0),
                current_agent=session.get("current_agent"),
                error_message=session.get("error_message"),
            )

    # Try in-memory
    if research_id in _research_sessions:
        session = _research_sessions[research_id]
        return ResearchResponse(
            research_id=research_id,
            status=session["status"],
            company_name=session["company_name"],
            ticker_symbol=session.get("ticker_symbol"),
            research_type=session["research_type"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            progress=session.get("progress", 0.0),
            current_agent=session.get("current_agent"),
            error_message=session.get("error_message"),
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Research session {research_id} not found",
    )


@router.get("/{research_id}/result", response_model=ResearchResult)
async def get_research_result(
    research_id: str,
    cache_service: CacheServiceDep,
    cosmos_service: CosmosServiceDep,
) -> ResearchResult:
    """Get the complete result of a research session."""
    session = None

    # Try in-memory first
    if research_id in _research_sessions:
        session = _research_sessions[research_id]

    # Try Cosmos DB if not in memory
    if not session and cosmos_service:
        session = await cosmos_service.get_session(research_id)
        if session:
            report = await cosmos_service.get_report(research_id)
            if report:
                session["result"] = report.get("data", {})

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {research_id} not found",
        )

    # Normalize status (could be enum or string depending on source)
    session_status = session["status"]
    if isinstance(session_status, str):
        session_status = ResearchStatus(session_status)

    if session_status != ResearchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Research session is not complete. Status: {session_status}",
        )

    result = session.get("result", {})

    return ResearchResult(
        research_id=research_id,
        status=session["status"],
        company_name=session["company_name"],
        ticker_symbol=session.get("ticker_symbol"),
        research_type=session["research_type"],
        created_at=session["created_at"],
        completed_at=session.get("completed_at"),
        executive_summary=result.get("executive_summary"),
        market_analysis=result.get("market_analysis"),
        financial_data=result.get("financial_data"),
        news_analysis=result.get("news_data"),
        risk_assessment=result.get("risk_assessment"),
        recommendations=result.get("recommendations", []),
        full_report=result.get("full_report"),
    )


@router.get("/{research_id}/report/pdf")
async def download_pdf_report(
    research_id: str,
    cache_service: CacheServiceDep,
    cosmos_service: CosmosServiceDep,
) -> Response:
    """Download the research report as a PDF."""
    session = None

    if research_id in _research_sessions:
        session = _research_sessions[research_id]

    if not session and cosmos_service:
        session = await cosmos_service.get_session(research_id)
        if session:
            report = await cosmos_service.get_report(research_id)
            if report:
                session["result"] = report.get("data", {})

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research session {research_id} not found",
        )

    # Normalize status (could be enum or string depending on source)
    session_status = session["status"]
    if isinstance(session_status, str):
        session_status = ResearchStatus(session_status)

    if session_status != ResearchStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Research is not complete",
        )

    result = session.get("result", {})

    # Generate PDF
    generator = ReportGenerator()
    pdf_bytes = generator.generate_pdf(
        research_id=research_id,
        company_name=session["company_name"],
        ticker_symbol=session.get("ticker_symbol"),
        report_data=result,
    )

    filename = f"research_report_{session['company_name'].replace(' ', '_')}_{research_id[:8]}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


@router.get("/", response_model=ReportListResponse)
async def list_reports(
    page: int = 1,
    page_size: int = 20,
    cosmos_service: CosmosServiceDep = None,
) -> ReportListResponse:
    """List all research reports."""
    reports = []

    # Get from Cosmos DB if available
    if cosmos_service:
        sessions, total = await cosmos_service.list_sessions(page, page_size)
        for session in sessions:
            reports.append(
                ReportListItem(
                    research_id=session["research_id"],
                    company_name=session["company_name"],
                    ticker_symbol=session.get("ticker_symbol"),
                    research_type=session["research_type"],
                    status=ResearchStatus(session["status"]),
                    created_at=session["created_at"],
                    completed_at=session.get("completed_at"),
                )
            )
    else:
        # Fall back to in-memory
        all_sessions = list(_research_sessions.values())
        total = len(all_sessions)
        start = (page - 1) * page_size
        end = start + page_size

        for session in all_sessions[start:end]:
            reports.append(
                ReportListItem(
                    research_id=session["research_id"],
                    company_name=session["company_name"],
                    ticker_symbol=session.get("ticker_symbol"),
                    research_type=session["research_type"],
                    status=session["status"],
                    created_at=session["created_at"],
                    completed_at=session.get("completed_at"),
                )
            )

    return ReportListResponse(
        reports=reports,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{research_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    research_id: str,
    cache_service: CacheServiceDep,
    cosmos_service: CosmosServiceDep,
) -> None:
    """Delete a research session."""
    # Remove from memory
    if research_id in _research_sessions:
        del _research_sessions[research_id]

    # Invalidate cache
    await cache_service.invalidate_research(research_id)

    # Delete from Cosmos DB
    if cosmos_service:
        await cosmos_service.delete_session(research_id)

    logger.info(f"Deleted research session: {research_id}")

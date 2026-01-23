"""Chat completions proxy endpoint."""

import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse, StreamingResponse

from backend.api.dependencies import (
    AIClientDep,
    ScannerDep,
    CosmosDep,
    APIKeyDep,
    SettingsDep,
)
from backend.models.requests import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    SecurityBlockedResponse,
)
from backend.models.audit import AuditLogCreate
from backend.models.security import SecurityScanResult, SecurityScanRequest

router = APIRouter()


@router.post("/chat/completions")
async def chat_completions(
    request: Request,
    body: ChatCompletionRequest,
    ai_client: AIClientDep,
    scanner: ScannerDep,
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    settings: SettingsDep,
) -> ChatCompletionResponse | SecurityBlockedResponse:
    """
    OpenAI-compatible chat completions endpoint with security scanning.

    This endpoint:
    1. Scans input messages for security threats
    2. Masks PII and secrets if detected
    3. Forwards safe requests to Azure AI Foundry
    4. Scans the response for safety
    5. Logs the request to audit trail
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()

    # Convert messages to dict format for scanning
    messages_dict = [msg.model_dump() for msg in body.messages]

    # Scan input messages
    scan_result, processed_messages = await scanner.scan_messages(messages_dict)

    # Check if request should be blocked
    if scan_result.should_block():
        # Log blocked request
        await _log_request(
            cosmos=cosmos,
            request_id=request_id,
            request=request,
            body=body,
            scan_result=scan_result,
            status="blocked",
            response_time_ms=(time.time() - start_time) * 1000,
        )

        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "message": scan_result.action_reason or "Request blocked by security policy",
                    "type": "security_violation",
                    "code": "content_filter",
                },
                "blocked": True,
                "security_scan": {
                    "scan_id": scan_result.scan_id,
                    "action": scan_result.action,
                    "prompt_injection_score": scan_result.prompt_injection_score,
                    "jailbreak_score": scan_result.jailbreak_score,
                    "threats_detected": len(scan_result.threats),
                },
            },
        )

    try:
        # Update request with processed messages if any transformations were applied
        if scan_result.input_transformed:
            # Create new request with processed messages
            body_dict = body.model_dump()
            body_dict["messages"] = processed_messages
            body = ChatCompletionRequest(**body_dict)

        # Forward to Azure AI Foundry
        response = await ai_client.chat_completion(body)

        # Optionally scan the response
        if settings.enable_content_filtering and response.choices:
            response_text = response.choices[0].message.content or ""
            response_scan, _ = await scanner.scan(
                response_text,
                scan_types=["content_safety"],
                mask_pii=False,
                mask_secrets=False,
            )

            # Log response safety issues but don't block (just warn)
            if response_scan.threats:
                print(f"[{request_id}] Response contains flagged content")

        # Log successful request
        await _log_request(
            cosmos=cosmos,
            request_id=request_id,
            request=request,
            body=body,
            scan_result=scan_result,
            status="filtered" if scan_result.input_transformed else "allowed",
            response=response,
            response_time_ms=(time.time() - start_time) * 1000,
        )

        return response

    except ValueError as e:
        # Configuration error
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        # Log error
        await _log_request(
            cosmos=cosmos,
            request_id=request_id,
            request=request,
            body=body,
            scan_result=scan_result,
            status="error",
            response_time_ms=(time.time() - start_time) * 1000,
            error=str(e),
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}",
        )


@router.post("/security/scan")
async def security_scan(
    body: SecurityScanRequest,
    scanner: ScannerDep,
) -> SecurityScanResult:
    """
    Scan text for security threats without forwarding to LLM.

    Useful for testing and the security playground.
    """
    result, processed_text = await scanner.scan(
        body.text,
        scan_types=body.scan_types,
        mask_pii=True,
        mask_secrets=True,
    )

    if body.include_details:
        return result

    # Return simplified result
    return SecurityScanResult(
        scan_id=result.scan_id,
        passed=result.passed,
        action=result.action,
        action_reason=result.action_reason,
        prompt_injection_score=result.prompt_injection_score,
        jailbreak_score=result.jailbreak_score,
        overall_risk_score=result.overall_risk_score,
    )


async def _log_request(
    cosmos: CosmosDep,
    request_id: str,
    request: Request,
    body: ChatCompletionRequest,
    scan_result: SecurityScanResult,
    status: str,
    response: ChatCompletionResponse | None = None,
    response_time_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Log request to audit trail."""
    try:
        log = AuditLogCreate(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            client_ip=request.client.host if request.client else None,
            endpoint="/v1/chat/completions",
            method="POST",
            model=body.model,
            prompt_tokens=response.usage.prompt_tokens if response and response.usage else None,
            completion_tokens=response.usage.completion_tokens if response and response.usage else None,
            total_tokens=response.usage.total_tokens if response and response.usage else None,
            security_scan_performed=True,
            threats_detected=[t.model_dump() for t in scan_result.threats],
            pii_detected=[p.model_dump() for p in scan_result.pii_detections],
            secrets_detected=[s.model_dump() for s in scan_result.secret_detections],
            content_filtered=scan_result.input_transformed,
            status=status,
            block_reason=scan_result.action_reason if status == "blocked" else error,
            response_time_ms=response_time_ms,
        )

        await cosmos.create_audit_log(log)

    except Exception as e:
        print(f"[{request_id}] Failed to log request: {e}")

"""Text completions proxy endpoint."""

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from backend.api.dependencies import (
    AIClientDep,
    ScannerDep,
    CosmosDep,
    APIKeyDep,
    SettingsDep,
)
from backend.models.requests import (
    CompletionRequest,
    CompletionResponse,
    ChatCompletionRequest,
    ChatMessage,
)
from backend.models.audit import AuditLogCreate

router = APIRouter()


@router.post("/completions")
async def completions(
    request: Request,
    body: CompletionRequest,
    ai_client: AIClientDep,
    scanner: ScannerDep,
    cosmos: CosmosDep,
    api_key: APIKeyDep,
    settings: SettingsDep,
) -> CompletionResponse:
    """
    OpenAI-compatible completions endpoint with security scanning.

    Note: This endpoint converts completion requests to chat format
    since Azure AI Foundry primarily uses chat completions.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    start_time = time.time()

    # Get prompt text
    prompt = body.prompt if isinstance(body.prompt, str) else body.prompt[0]

    # Scan input
    scan_result, processed_text = await scanner.scan(prompt)

    # Check if request should be blocked
    if scan_result.should_block():
        # Log blocked request
        await _log_completion_request(
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
                },
            },
        )

    try:
        # Convert to chat format
        chat_request = ChatCompletionRequest(
            model=body.model,
            messages=[ChatMessage(role="user", content=processed_text)],
            temperature=body.temperature,
            top_p=body.top_p,
            max_tokens=body.max_tokens,
            stop=body.stop,
            presence_penalty=body.presence_penalty,
            frequency_penalty=body.frequency_penalty,
        )

        # Forward to Azure AI Foundry
        chat_response = await ai_client.chat_completion(chat_request)

        # Convert response back to completion format
        response = CompletionResponse(
            id=chat_response.id,
            object="text_completion",
            created=chat_response.created,
            model=chat_response.model,
            choices=[
                {
                    "text": choice.message.content or "",
                    "index": choice.index,
                    "logprobs": None,
                    "finish_reason": choice.finish_reason,
                }
                for choice in chat_response.choices
            ],
            usage=chat_response.usage,
        )

        # Log successful request
        await _log_completion_request(
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
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )
    except Exception as e:
        await _log_completion_request(
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


async def _log_completion_request(
    cosmos: CosmosDep,
    request_id: str,
    request: Request,
    body: CompletionRequest,
    scan_result,
    status: str,
    response: CompletionResponse | None = None,
    response_time_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Log completion request to audit trail."""
    try:
        log = AuditLogCreate(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            client_ip=request.client.host if request.client else None,
            endpoint="/v1/completions",
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

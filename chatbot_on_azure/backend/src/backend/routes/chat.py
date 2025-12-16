from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from backend.services.openai_service import openai_service
import json
import asyncio


router = APIRouter(prefix="/api", tags=["chat"])


class Message(BaseModel):
    """Message model for chat requests."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: list[Message]


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes messages and returns AI response.

    Args:
        request: ChatRequest containing conversation history

    Returns:
        ChatResponse with AI-generated reply
    """
    try:
        # Convert Pydantic models to dict for OpenAI API
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        # Generate response using Azure OpenAI
        response = await openai_service.generate_response(messages)

        return ChatResponse(response=response)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint that returns AI response in real-time.

    Args:
        request: ChatRequest containing conversation history

    Returns:
        StreamingResponse with Server-Sent Events
    """
    try:
        # Convert Pydantic models to dict for OpenAI API
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]

        async def event_generator():
            try:
                print("[STREAM] Starting streaming response", flush=True)
                chunk_count = 0
                async for chunk in openai_service.generate_streaming_response(messages):
                    chunk_count += 1
                    print(f"[STREAM] Chunk {chunk_count}: {repr(chunk[:50] if len(chunk) > 50 else chunk)}", flush=True)
                    # Send as Server-Sent Events format
                    data = f"data: {json.dumps({'content': chunk})}\n\n"
                    yield data
                    # Force immediate flush by yielding control to event loop
                    await asyncio.sleep(0)

                print(f"[STREAM] Completed with {chunk_count} chunks", flush=True)
                # Send completion signal
                yield f"data: {json.dumps({'done': True})}\n\n"
            except Exception as e:
                print(f"[STREAM] Error: {str(e)}", flush=True)
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in nginx
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "chatbot-api"}

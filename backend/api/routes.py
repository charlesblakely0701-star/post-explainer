"""API route definitions."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import logging

from models.schemas import ExplainRequest, ExplainResponse, HealthResponse, CompareResponse
from services.explainer import PostExplainer

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton explainer instance
_explainer: PostExplainer | None = None


def get_explainer() -> PostExplainer:
    """Get or create the PostExplainer instance."""
    global _explainer
    if _explainer is None:
        _explainer = PostExplainer()
    return _explainer


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(status="ok", version="1.0.0")


@router.post("/explain", response_model=ExplainResponse)
async def explain_post(request: ExplainRequest):
    """
    Explain a social media post.
    
    Takes a post text and returns 3-5 bullet point explanations
    with source citations. Optionally accepts an image URL for
    visual context analysis.
    """
    try:
        explainer = get_explainer()
        response = await explainer.explain(
            request.text,
            image_url=request.image_url
        )
        return response
    except Exception as e:
        logger.exception(f"Error explaining post: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain/compare")
async def compare_providers(request: ExplainRequest):
    """
    Compare explanations from multiple LLM providers.
    
    Returns side-by-side results from available providers
    (OpenAI GPT-4, Anthropic Claude, etc.)
    """
    try:
        explainer = get_explainer()
        response = await explainer.compare_providers(
            request.text,
            image_url=request.image_url
        )
        return response
    except Exception as e:
        logger.exception(f"Error comparing providers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers():
    """List available LLM providers."""
    explainer = get_explainer()
    return {
        "providers": explainer.llm_service.get_available_providers()
    }


@router.post("/explain/stream")
async def explain_post_stream(request: ExplainRequest):
    """
    Stream an explanation for a social media post.
    
    Returns Server-Sent Events with the explanation as it's generated.
    """
    explainer = get_explainer()
    
    async def event_generator():
        try:
            async for item in explainer.explain_stream(request.text):
                if item["type"] == "sources":
                    yield {
                        "event": "sources",
                        "data": json.dumps(item["data"])
                    }
                elif item["type"] == "chunk":
                    yield {
                        "event": "chunk",
                        "data": json.dumps({"text": item["data"]})
                    }
            
            # Send completion event
            yield {
                "event": "done",
                "data": json.dumps({"status": "complete"})
            }
            
        except Exception as e:
            logger.exception(f"Streaming error: {str(e)}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
    
    return EventSourceResponse(event_generator())


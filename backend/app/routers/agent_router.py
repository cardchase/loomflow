from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from fastapi.responses import StreamingResponse
from agent.orchestrator import SynthesizerAgent

router = APIRouter(prefix="/api/agent", tags=["agent"])

class SynthesizeRequest(BaseModel):
    prompt: str
    session_id: str
    file_path: Optional[str] = None
    provider: Optional[str] = None

@router.post("/synthesize/stream")
def synthesize_stream(request: SynthesizeRequest):
    agent = SynthesizerAgent(
        session_id=request.session_id,
        file_path=request.file_path,
        provider_override=request.provider
    )
    return StreamingResponse(
        agent.synthesize_stream(request.prompt),
        media_type="text/event-stream"
    )

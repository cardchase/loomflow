import json
from typing import Optional, Any, List, Dict
from fastapi import APIRouter
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel

from agent.orchestrator import AgentOrchestrator
from agent.providers.factory import get_llm_client

router = APIRouter(prefix="/api/agent", tags=["agent"])

class SynthesizeRequest(BaseModel):
    prompt: str
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    provider: Optional[str] = None
    custom_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    provider: Optional[str] = None
    custom_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: Optional[str] = None

class PingRequest(BaseModel):
    provider: Optional[str] = None
    custom_base_url: Optional[str] = None
    custom_api_key: Optional[str] = None
    custom_model: Optional[str] = None

@router.post("/ping")
async def ping_llm(request: PingRequest):
    try:
        client = get_llm_client(
            provider_override=request.provider,
            custom_base_url=request.custom_base_url,
            custom_api_key=request.custom_api_key,
            custom_model=request.custom_model
        )
        messages = [{"role": "user", "content": "ping"}]
        await client.complete(messages=messages, tools=None)
        return {"status": "ok", "message": "Connected successfully"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})

@router.post("/chat")
async def chat_assistant(request: ChatRequest):
    try:
        client = get_llm_client(
            provider_override=request.provider,
            custom_base_url=request.custom_base_url,
            custom_api_key=request.custom_api_key,
            custom_model=request.custom_model
        )
        
        context = f"The user is asking about their ETL pipeline. Here is the current graph:\nNodes: {len(request.nodes)}\nEdges: {len(request.edges)}\n"
        if len(request.nodes) > 0:
            node_summaries = []
            for n in request.nodes:
                data = n.get("data", {})
                name = data.get("label", n.get("type", "Node"))
                node_type = n.get("type", "Unknown")
                params = data.get("parameters", {})
                
                # Format node summary
                summary = f"- {name} (ID: {n.get('id')}, Type: {node_type})"
                if params:
                    # Clean up params to not be too huge
                    summary += f"\n  Parameters: {params}"
                    
                node_summaries.append(summary)
            context += "Node List:\n" + "\n".join(node_summaries) + "\n"

        prompt = f"{context}\n\nUser Message: {request.message}"
        messages = [{"role": "user", "content": prompt}]
        
        response = await client.complete(messages=messages, tools=None)
        return {"response": response.content, "context_used": prompt}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(status_code=500, content={"response": f"AI Error: {str(e)}"})

@router.post("/synthesize/stream")
async def synthesize_stream(request: SynthesizeRequest):
    orchestrator = AgentOrchestrator(
        provider=request.provider,
        custom_base_url=request.custom_base_url,
        custom_api_key=request.custom_api_key,
        custom_model=request.custom_model
    )
    
    async def event_generator():
        async for event in orchestrator.run(
            user_prompt=request.prompt,
            initial_nodes=request.nodes,
            initial_edges=request.edges
        ):
            # Format as standard Server-Sent Event
            yield f"data: {json.dumps(event)}\n\n"
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

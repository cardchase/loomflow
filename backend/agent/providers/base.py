from abc import ABC, abstractmethod
from typing import Optional, Any, AsyncGenerator
from pydantic import BaseModel

class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict

class LLMResponse(BaseModel):
    content: Optional[str]
    tool_calls: list[ToolCall]
    raw_response: Any

class LLMStreamChunk(BaseModel):
    delta_content: Optional[str]
    tool_call_delta: Optional[dict]
    is_finished: bool

class BaseLLMClient(ABC):
    @abstractmethod
    async def complete(self, messages: list[dict], tools: Optional[list[dict]] = None, response_schema: Optional[dict] = None, **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    async def stream_complete(self, messages: list[dict], tools: Optional[list[dict]] = None, **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        pass

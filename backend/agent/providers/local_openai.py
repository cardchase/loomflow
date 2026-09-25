import json
from typing import Optional, AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings
from .base import BaseLLMClient, LLMResponse, ToolCall, LLMStreamChunk

class LocalOpenAIClient(BaseLLMClient):
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = AsyncOpenAI(
            base_url=base_url or settings.LOCAL_LLM_BASE_URL,
            api_key=api_key or settings.LOCAL_LLM_API_KEY
        )
        self.model = model or settings.LOCAL_LLM_MODEL

    async def complete(self, messages: list[dict], tools: Optional[list[dict]] = None, response_schema: Optional[dict] = None, **kwargs) -> LLMResponse:
        api_kwargs = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        if tools:
            # Format to OpenAI format
            formatted_tools = [
                {"type": "function", "function": t} for t in tools
            ]
            api_kwargs["tools"] = formatted_tools
            
        if response_schema:
            api_kwargs["response_format"] = {
                "type": "json_schema", 
                "json_schema": {"name": "response", "schema": response_schema, "strict": True}
            }

        response = await self.client.chat.completions.create(**api_kwargs)
        message = response.choices[0].message
        
        tool_calls = []
        if message.tool_calls:
            for tc in message.tool_calls:
                # Safely parse JSON arguments per instruction #3
                try:
                    arguments = json.loads(tc.function.arguments) if isinstance(tc.function.arguments, str) else tc.function.arguments
                except json.JSONDecodeError:
                    arguments = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=arguments))

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
            raw_response=response
        )

    async def stream_complete(self, messages: list[dict], tools: Optional[list[dict]] = None) -> AsyncGenerator[LLMStreamChunk, None]:
        yield LLMStreamChunk(delta_content="", tool_call_delta=None, is_finished=True)

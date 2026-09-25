import uuid
from typing import Optional, AsyncGenerator
from google import genai
from google.genai import types
from app.config import settings
from .base import BaseLLMClient, LLMResponse, ToolCall, LLMStreamChunk

class GeminiClient(BaseLLMClient):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.client = genai.Client(api_key=api_key or settings.GEMINI_API_KEY)
        self.model = model or "gemini-2.5-flash"

    def _convert_schema_to_gemini(self, schema: dict) -> types.Tool:
        fd = types.FunctionDeclaration(
            name=schema["name"],
            description=schema.get("description", ""),
            parameters=schema.get("parameters", {})
        )
        return types.Tool(function_declarations=[fd])

    async def complete(self, messages: list[dict], tools: Optional[list[dict]] = None, response_schema: Optional[dict] = None, **kwargs) -> LLMResponse:
        gemini_messages = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            if role == "system":
                system_instruction = msg["content"]
                continue
                
            if role == "tool":
                # Convert standard tool response to Gemini function response format
                part = types.Part.from_function_response(
                    name=msg.get("name", "tool"),
                    response={"result": msg.get("content", {})}
                )
                gemini_messages.append(types.Content(role="user", parts=[part]))
            elif role == "assistant" and msg.get("tool_calls"):
                parts = []
                if msg.get("content"):
                    parts.append(types.Part.from_text(text=msg["content"]))
                for tc in msg["tool_calls"]:
                    parts.append(types.Part.from_function_call(
                        name=tc["function"]["name"], 
                        args=tc["function"]["arguments"]
                    ))
                gemini_messages.append(types.Content(role="model", parts=parts))
            else:
                gemini_role = "user" if role == "user" else "model"
                content_val = msg.get("content", "") or ""
                gemini_messages.append(types.Content(role=gemini_role, parts=[types.Part.from_text(text=content_val)]))
                
        config = types.GenerateContentConfig()
        if system_instruction:
            config.system_instruction = system_instruction
            
        if tools:
            config.tools = [self._convert_schema_to_gemini(t) for t in tools]
            
        if response_schema:
            config.response_mime_type = "application/json"
            config.response_schema = response_schema
            
        if "temperature" in kwargs:
            config.temperature = kwargs["temperature"]

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=gemini_messages,
            config=config
        )

        tool_calls = []
        if response.function_calls:
            for fc in response.function_calls:
                args = fc.args if hasattr(fc, 'args') else {}
                tc_id = f"call_{uuid.uuid4().hex[:8]}"
                tool_calls.append(ToolCall(id=tc_id, name=fc.name, arguments=args))

        return LLMResponse(
            content=response.text,
            tool_calls=tool_calls,
            raw_response=response
        )

    async def stream_complete(self, messages: list[dict], tools: Optional[list[dict]] = None, **kwargs) -> AsyncGenerator[LLMStreamChunk, None]:
        yield LLMStreamChunk(delta_content="", tool_call_delta=None, is_finished=True)

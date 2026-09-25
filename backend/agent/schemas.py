import functools
import inspect
from typing import Any, Callable, Dict, Type
from pydantic import BaseModel, create_model

class CanvasNode(BaseModel):
    id: str
    type: str
    position: dict[str, float]
    data: dict[str, Any]

class CanvasEdge(BaseModel):
    id: str
    source: str
    target: str

class CanvasGraph(BaseModel):
    nodes: list[CanvasNode]
    edges: list[CanvasEdge]
    summary: str

# Registry for agent tools
AGENT_TOOLS: Dict[str, Dict[str, Any]] = {}

def agent_tool(func: Callable) -> Callable:
    """
    Decorator to register a function as an agent tool.
    Uses Pydantic's create_model and model_json_schema() to generate the schema.
    """
    sig = inspect.signature(func)
    
    # Create Pydantic fields from signature
    fields = {}
    for name, param in sig.parameters.items():
        if param.annotation == inspect.Parameter.empty:
            anno = Any
        else:
            anno = param.annotation
            
        if param.default == inspect.Parameter.empty:
            fields[name] = (anno, ...)
        else:
            fields[name] = (anno, param.default)
            
    # Create a dynamic Pydantic model for the arguments
    Model: Type[BaseModel] = create_model(f"{func.__name__}_args", **fields)
    
    # Generate schema
    schema = Model.model_json_schema()
    
    # Remove title to keep it clean
    schema.pop("title", None)

    # Recursively scrub additionalProperties to prevent Gemini API ClientErrors
    def scrub_additional_properties(d: dict):
        if not isinstance(d, dict):
            return
        d.pop("additionalProperties", None)
        d.pop("additional_properties", None)
        for k, v in d.items():
            if isinstance(v, dict):
                scrub_additional_properties(v)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        scrub_additional_properties(item)

    scrub_additional_properties(schema)
    
    tool_def = {
        "name": func.__name__,
        "description": func.__doc__.strip() if func.__doc__ else f"Call {func.__name__}",
        "parameters": schema
    }
    
    AGENT_TOOLS[func.__name__] = {
        "callable": func,
        "schema": tool_def
    }
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
        
    return wrapper

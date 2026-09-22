import os
import json
import traceback
import logging
from typing import List, Dict, Any, Optional, Generator
from pydantic import BaseModel, Field

# We import the sandbox session manager
from agent.sandbox.session_manager import SandboxSession

# Pydantic schemas for the final DAG structure
class CanvasNode(BaseModel):
    id: str = Field(..., description="Unique identifier for the node (e.g., node_1_fileInput)")
    type: str = Field(..., description="The registered LoomFlow node type (e.g., fileInput, MLPredictorNode)")
    position: Dict[str, float] = Field(..., description="X and Y coordinates, e.g., {'x': 100, 'y': 100}")
    data: Dict[str, Any] = Field(..., description="Data object containing label and parameters")

class CanvasEdge(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")

class CanvasGraph(BaseModel):
    nodes: List[CanvasNode] = Field(..., description="List of nodes in the workflow")
    edges: List[CanvasEdge] = Field(..., description="List of edges connecting the nodes")

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "inspect_source_metadata",
            "description": "Returns column names, inferred Polars dtypes, null ratios, and 5 preview rows.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "profile_column_semantics",
            "description": "Returns distribution shape for a given column.",
            "parameters": {
                "type": "object",
                "properties": {
                    "column_name": {"type": "string"}
                },
                "required": ["column_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_polars_transformation",
            "description": "Safely evaluates a transformation on the micro-sample.",
            "parameters": {
                "type": "object",
                "properties": {
                    "node_type": {"type": "string"},
                    "config": {"type": "object"}
                },
                "required": ["node_type", "config"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "test_symbolic_expression",
            "description": "Validates SymPy syntax.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "compile_and_layout_dag",
            "description": "Converts verified sequence into React Flow schema.",
            "parameters": {
                "type": "object",
                "properties": {
                    "sequence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "node_type": {"type": "string"},
                                "config": {"type": "object"}
                            },
                            "required": ["node_type", "config"]
                        }
                    }
                },
                "required": ["sequence"]
            }
        }
    }
]

class SynthesizerAgent:
    def __init__(self, session_id: str, file_path: Optional[str] = None, provider_override: Optional[str] = None):
        self.session = SandboxSession(session_id, file_path)
        self.provider = provider_override or os.getenv("DEFAULT_LLM_PROVIDER", "local")
        self.local_base_url = os.getenv("LOCAL_LLM_BASE_URL", "http://localhost:1234/v1")
        self.max_turns = 12
        
        self.system_prompt = f"""You are the LoomFlow Autonomous Workflow Synthesizer.
Your goal is to build a valid ETL DAG based on the user's request.
You MUST use the provided Sandbox tools to inspect the dataset and iteratively test your Polars/SymPy transformations before emitting the final DAG.
If a tool returns an error or traceback, analyze the error, self-correct, and try again.

FINAL OUTPUT SCHEMA REQUIREMENT:
When you are completely done and have tested your nodes, your final response MUST be a raw JSON object adhering to this schema:
{CanvasGraph.schema_json(indent=2)}
"""

    def _execute_tool(self, tool_name: str, args: dict) -> Any:
        if tool_name == "inspect_source_metadata":
            return self.session.inspect_source_metadata()
        elif tool_name == "profile_column_semantics":
            return self.session.profile_column_semantics(args.get("column_name", ""))
        elif tool_name == "test_polars_transformation":
            return self.session.test_polars_transformation(args.get("node_type", ""), args.get("config", {}))
        elif tool_name == "test_symbolic_expression":
            return self.session.test_symbolic_expression(args.get("expression", ""))
        elif tool_name == "compile_and_layout_dag":
            return self.session.compile_and_layout_dag(args.get("sequence", []))
        else:
            return {"error": f"Unknown tool {tool_name}"}

    def synthesize_stream(self, prompt: str) -> Generator[str, None, None]:
        if "gemini" in self.provider.lower():
            yield from self._run_gemini(prompt)
        else:
            yield from self._run_openai(prompt)

    def _run_openai(self, prompt: str) -> Generator[str, None, None]:
        try:
            from openai import OpenAI
            client = OpenAI(base_url=self.local_base_url, api_key="local-no-key")
        except ImportError:
            yield json.dumps({"event": "ERROR_CORRECTION", "error": "openai package not installed"}) + "\n"
            yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"
            return
            
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        for turn in range(self.max_turns):
            try:
                response = client.chat.completions.create(
                    model="local-model",
                    messages=messages,
                    tools=TOOLS,
                    response_format={
                        "type": "json_schema", 
                        "json_schema": {
                            "name": "CanvasGraph", 
                            "schema": CanvasGraph.schema(),
                            "strict": True
                        }
                    }
                )
            except Exception as e:
                # If strict true is not supported by LM studio, fallback
                try:
                    response = client.chat.completions.create(
                        model="local-model",
                        messages=messages,
                        tools=TOOLS
                    )
                except Exception as e2:
                    yield json.dumps({"event": "ERROR_CORRECTION", "error": str(e2)}) + "\n"
                    break
            
            message = response.choices[0].message
            # Append message to history
            messages.append(message.model_dump(exclude_none=True))
            
            if getattr(message, "tool_calls", None):
                for tool_call in message.tool_calls:
                    yield json.dumps({"event": "TOOL_START", "tool": tool_call.function.name}) + "\n"
                    
                    try:
                        args = json.loads(tool_call.function.arguments)
                        result = self._execute_tool(tool_call.function.name, args)
                        
                        if isinstance(result, dict) and result.get("status") == "error":
                            yield json.dumps({"event": "ERROR_CORRECTION", "error": result}) + "\n"
                        else:
                            yield json.dumps({"event": "TOOL_RESULT", "result": result}) + "\n"
                            
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps(result)
                        })
                    except Exception as e:
                        err_str = str(e) + "\n" + traceback.format_exc()
                        yield json.dumps({"event": "ERROR_CORRECTION", "error": err_str}) + "\n"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_call.function.name,
                            "content": json.dumps({"error": err_str})
                        })
            else:
                try:
                    dag = json.loads(message.content)
                    yield json.dumps({"event": "DONE", "dag": dag}) + "\n"
                except Exception as e:
                    yield json.dumps({"event": "ERROR_CORRECTION", "error": f"Failed to parse DAG: {e}"}) + "\n"
                    yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"
                break
        else:
            yield json.dumps({"event": "ERROR_CORRECTION", "error": "Max turns reached"}) + "\n"
            yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"

    def _run_gemini(self, prompt: str) -> Generator[str, None, None]:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client() # Will pick up from environment
        except ImportError:
            yield json.dumps({"event": "ERROR_CORRECTION", "error": "google-genai package not installed"}) + "\n"
            yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"
            return
            
        def inspect_source_metadata():
            return self.session.inspect_source_metadata()
            
        def profile_column_semantics(column_name: str):
            return self.session.profile_column_semantics(column_name)
            
        def test_polars_transformation(node_type: str, config: dict):
            return self.session.test_polars_transformation(node_type, config)
            
        def test_symbolic_expression(expression: str):
            return self.session.test_symbolic_expression(expression)
            
        def compile_and_layout_dag(sequence: list):
            return self.session.compile_and_layout_dag(sequence)
            
        tool_funcs = [
            inspect_source_metadata,
            profile_column_semantics,
            test_polars_transformation,
            test_symbolic_expression,
            compile_and_layout_dag
        ]
        
        # We need to manage conversation history
        # Due to complexity of manually unrolling history with tools in genai SDK, 
        # using client.chats.create might be easier.
        try:
            chat = client.chats.create(
                model="gemini-2.5-pro",
                config=types.GenerateContentConfig(
                    system_instruction=self.system_prompt,
                    temperature=0.0,
                    tools=tool_funcs,
                    response_schema=CanvasGraph,
                    response_mime_type="application/json"
                )
            )
            
            # Initiate the chat
            response = chat.send_message(prompt)
            
            for turn in range(self.max_turns):
                # Check if there are tool calls in the response
                if response.function_calls:
                    for fc in response.function_calls:
                        yield json.dumps({"event": "TOOL_START", "tool": fc.name}) + "\n"
                        try:
                            # Use mapping since function_calls are processed by SDK usually,
                            # but we might be in manual loop
                            # Actually, google-genai handles tool execution if we pass tools to chat? No, wait.
                            # The google-genai SDK doesn't auto-execute tools by default unless using specific wrappers,
                            # but we want to intercept to yield SSE streams.
                            args = fc.args
                            if isinstance(args, dict):
                                result = self._execute_tool(fc.name, args)
                            else:
                                result = {"error": "Invalid arguments format"}
                            
                            if isinstance(result, dict) and result.get("status") == "error":
                                yield json.dumps({"event": "ERROR_CORRECTION", "error": result}) + "\n"
                            else:
                                yield json.dumps({"event": "TOOL_RESULT", "result": result}) + "\n"
                            
                            # Send tool result back to Gemini
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response=result
                                )
                            )
                        except Exception as e:
                            err_str = str(e) + "\n" + traceback.format_exc()
                            yield json.dumps({"event": "ERROR_CORRECTION", "error": err_str}) + "\n"
                            response = chat.send_message(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"error": err_str}
                                )
                            )
                else:
                    # No tool calls, must be final output
                    try:
                        dag = json.loads(response.text)
                        yield json.dumps({"event": "DONE", "dag": dag}) + "\n"
                    except:
                        yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"
                    break
        except Exception as e:
            yield json.dumps({"event": "ERROR_CORRECTION", "error": str(e)}) + "\n"
            yield json.dumps({"event": "DONE", "dag": {"nodes": [], "edges": []}}) + "\n"

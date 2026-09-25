import json
import re
import traceback
import uuid
from typing import AsyncGenerator, Optional
from pydantic import ValidationError

from agent.providers.factory import get_llm_client
from agent.schemas import AGENT_TOOLS, CanvasGraph, CanvasNode, CanvasEdge, agent_tool

TOOL_METADATA = {
    "fileinput": {"type": "fileInput", "category": "inout", "icon": "FileText", "label": "File Input"},
    "folderinput": {"type": "folderInput", "category": "inout", "icon": "FolderOpen", "label": "Folder Input"},
    "dynamicinput": {"type": "dynamicInput", "category": "inout", "icon": "FileStack", "label": "Dynamic Input"},
    "fileoutput": {"type": "fileOutput", "category": "inout", "icon": "Save", "label": "File Output"},
    "browse": {"type": "browse", "category": "inout", "icon": "Search", "label": "Browse"},
    "select": {"type": "select", "category": "prep", "icon": "Columns", "label": "Select"},
    "filter": {"type": "filter", "category": "prep", "icon": "Filter", "label": "Filter"},
    "unique": {"type": "unique", "category": "prep", "icon": "Layers", "label": "Unique"},
    "formula": {"type": "formula", "category": "prep", "icon": "Calculator", "label": "Formula"},
    "union": {"type": "union", "category": "join", "icon": "Layers", "label": "Union"},
    "join": {"type": "join", "category": "join", "icon": "GitMerge", "label": "Join"},
}

MULTI_INPUT_TOOLS = {"union", "join"}

def resolve_tool_meta(raw_type: str) -> dict:
    """Case-insensitive and alias-safe tool metadata lookup."""
    clean = re.sub(r"[_\-\s]", "", (raw_type or "").lower()).replace("tool", "")
    return TOOL_METADATA.get(clean, {
        "type": raw_type or "browse",
        "category": "prep",
        "icon": "Search",
        "label": (raw_type or "Node").capitalize()
    })

def sanitize_regex_expression(expr: str) -> str:
    """Auto-correct swapped Regex_Extract arguments: Regex_Extract("pattern", [Col]) -> Regex_Extract([Col], "pattern")"""
    if not expr:
        return expr
    # Detect swapped order where quoted pattern is first and [Column] is second
    swapped_match = re.search(r'Regex_Extract\s*\(\s*(["\'].*?["\'])\s*,\s*(\[[^\]]+\])\s*\)', expr, re.IGNORECASE)
    if swapped_match:
        pattern, col = swapped_match.group(1), swapped_match.group(2)
        expr = expr[:swapped_match.start()] + f'Regex_Extract({col}, {pattern})' + expr[swapped_match.end():]
    return expr

def normalize_formula_params(params: dict) -> dict:
    if not isinstance(params, dict):
        params = {}
    
    formulas = params.get("formulas", [])
    if isinstance(formulas, list) and len(formulas) > 0:
        cleaned = []
        for f in formulas:
            col = f.get("column") or f.get("newColumn") or f.get("outputColumn") or f.get("newColumnName") or f.get("targetColumn") or "stripped"
            col = re.sub(r"_[a-f0-9]{4}_AI$", "", col)
            
            raw_expr = f.get("expression") or f.get("formula") or 'Regex_Extract([URL], "([^/]+)/?$")'
            expr = sanitize_regex_expression(raw_expr)
            
            # If the column name accidentally equals the source column being extracted, rename it
            if col == "URL" and "Regex_Extract" in expr:
                col = "stripped"

            cleaned.append({
                "column": col,
                "newColumn": col,
                "outputColumn": col,
                "output_column": col,
                "newColumnName": col,
                "targetColumn": col,
                "isNew": True,
                "isNewColumn": True,
                "expression": expr,
                "type": f.get("type", "String"),
                "dataType": f.get("type", "String"),
                "size": f.get("size", "")
            })
        return {"formulas": cleaned, "isCached": False}

    raw_expr = params.get("expression") or params.get("formula") or 'Regex_Extract([URL], "([^/]+)/?$")'
    expr = sanitize_regex_expression(raw_expr)
    
    col = params.get("column") or params.get("new_column") or params.get("newColumn") or params.get("outputColumn") or "stripped"
    col = re.sub(r"_[a-f0-9]{4}_AI$", "", col)
    
    if col == "URL" and "Regex_Extract" in expr:
        col = "stripped"

    return {
        "formulas": [
            {
                "column": col,
                "newColumn": col,
                "outputColumn": col,
                "output_column": col,
                "newColumnName": col,
                "targetColumn": col,
                "isNew": True,
                "isNewColumn": True,
                "expression": expr,
                "type": "String",
                "dataType": "String",
                "size": ""
            }
        ],
        "isCached": False
    }

# Fallback extraction helper
def extract_delta_json(content: str) -> Optional[dict]:
    if not content:
        return None
    # 1. Look for any code block containing a JSON object
    code_blocks = re.findall(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", content)
    for block in code_blocks:
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # 2. Look for any top-level JSON object in the raw string
    raw_match = re.search(r"(\{[\s\S]*\})", content)
    if raw_match:
        try:
            parsed = json.loads(raw_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    return None

class OrchestratorComplete(Exception):
    def __init__(self, delta: dict):
        self.delta = delta

@agent_tool
def submit_pipeline_graph(
    new_nodes: list[dict] = [],
    new_edges: list[dict] = [],
    modified_nodes: list[dict] = [],
    deleted_node_ids: list[str] = [],
    summary: str = ""
) -> dict:
    """
    Submits changes to the pipeline graph. 
    You do NOT need to return existing unchanged nodes.
    Only supply new nodes to add, new edges to connect, or nodes to modify/delete.
    """
    raise OrchestratorComplete(delta={
        "new_nodes": new_nodes or [],
        "new_edges": new_edges or [],
        "modified_nodes": modified_nodes or [],
        "deleted_node_ids": deleted_node_ids or [],
        "summary": summary
    })

class AgentOrchestrator:
    def __init__(self, provider: Optional[str] = None, **kwargs):
        self.client = get_llm_client(provider, **kwargs)
        self.tools = list(AGENT_TOOLS.values())
        self.tool_schemas = [t["schema"] for t in self.tools]

    async def run(self, user_prompt: str, initial_nodes: list = None, initial_edges: list = None, max_turns: int = 10) -> AsyncGenerator[dict, None]:
        initial_nodes = initial_nodes or []
        initial_edges = initial_edges or []
        
        # 1. ALWAYS RESET MESSAGES AT THE START OF A RUN
        base_system_prompt = (
            "You are the LoomFlow Autonomous Pipeline Synthesizer. You use tools to inspect data, "
            "test Polars transformations, and compile execution DAGs. When an operation throws an error, "
            "reflect on the traceback, correct the parameter or transformation, and retry. "
            "When finished, you MUST call submit_pipeline_graph to finalize your response."
        )

        # Identify in/out degrees to find terminal nodes
        in_degree = {n["id"]: 0 for n in initial_nodes}
        out_degree = {n["id"]: 0 for n in initial_nodes}
        for e in initial_edges:
            in_degree[e["target"]] = in_degree.get(e["target"], 0) + 1
            out_degree[e["source"]] = out_degree.get(e["source"], 0) + 1
            
        terminal_nodes = []
        for n in initial_nodes:
            if n.get("selected") or (in_degree.get(n["id"], 0) > 0 and out_degree.get(n["id"], 0) == 0):
                terminal_nodes.append(n)
        
        terminal_previews = []
        for n in terminal_nodes:
            data = n.get("data", {})
            output = data.get("output") or data.get("preview")
            if output is not None:
                records = []
                columns = []
                if hasattr(output, "to_dicts"): # Polars
                    records = output.head(5).to_dicts()
                    columns = list(output.columns)
                elif hasattr(output, "to_dict"): # Pandas
                    records = output.head(5).to_dict(orient="records")
                    columns = list(output.columns)
                elif isinstance(output, list) and len(output) > 0 and isinstance(output[0], dict):
                    records = output[:5]
                    columns = list(output[0].keys())
                    
                if records:
                    preview_str = f"Terminal Node Preview (`{n['id']}` - {data.get('label', 'Unknown')}):\n"
                    preview_str += f"Columns: {columns[:20]}\n"
                    preview_str += f"Sample Rows (First 5):\n"
                    
                    rows_str = json.dumps(records, default=str)
                    if len(rows_str) > 1500:
                        rows_str = rows_str[:1500] + "... (truncated)"
                        
                    preview_str += rows_str + "\n"
                    terminal_previews.append(preview_str)

        context = "Here is the CURRENT state of the user's pipeline graph:\n"
        context += f"Nodes: {len(initial_nodes)}\nEdges: {len(initial_edges)}\n"
        
        if len(initial_nodes) > 0:
            context += "Node List:\n"
            for n in initial_nodes:
                params = n.get("data", {}).get("parameters", {})
                params_str = json.dumps(params)
                # Cap excessive rule parameters (e.g. 52 filter rules) to avoid token spikes
                if len(params_str) > 300:
                    whitelisted_keys = ["filePath", "folderPath", "columns", "filterType"]
                    retained_params = {k: params[k] for k in whitelisted_keys if k in params}
                    retained_params["summary"] = "parameters truncated to save context"
                    params = retained_params

                clean_node = {
                    "id": n["id"],
                    "type": n["type"],
                    "position": {
                        "x": round(n.get("position", {}).get("x", 0)),
                        "y": round(n.get("position", {}).get("y", 0))
                    },
                    "data": {
                        "label": n.get("data", {}).get("label", ""),
                        "parameters": params
                    }
                }
                context += f"- {json.dumps(clean_node)}\n"
        
        if len(initial_edges) > 0:
            context += "Edge List:\n"
            for e in initial_edges:
                clean_edge = {
                    "id": e["id"],
                    "source": e["source"],
                    "target": e["target"]
                }
                context += f"- {json.dumps(clean_edge)}\n"

        if terminal_previews:
            context += "\n--- TERMINAL NODE PREVIEWS ---\n"
            context += "\n".join(terminal_previews)
            context += "\n------------------------------\n"

        context += "\nIMPORTANT INSTRUCTIONS FOR YOUR TASK:\n"
        context += "1. To modify the workflow, call `submit_pipeline_graph` with ONLY the delta changes:\n"
        context += "   - `new_nodes`: Array of newly created nodes with unique IDs (e.g., 'node_27'), valid tool `type`, `label`, and computed (x, y) `position`.\n"
        context += "   - `new_edges`: Array of new connection edges with `source` and `target`.\n"
        context += "   - `modified_nodes`: Array of changes to existing nodes (if any).\n"
        context += "   - `deleted_node_ids`: Array of node IDs to remove (if any).\n"
        context += "   - `summary`: A concise explanation of the change.\n"
        context += "2. DO NOT re-emit unchanged existing nodes or edges in `new_nodes`. The system automatically preserves all existing canvas elements.\n"
        context += "3. Compute the layout position for new nodes using:\n"
        context += "   - Target X = upstream_node.x + 260\n"
        context += "   - Target Y = upstream_node.y\n"
        
        context += "\nEDGE CONNECTION CONSTRAINTS:\n"
        context += "1. When asked to add a new tool downstream of Node X, create ONLY the edge from Node X to the new tool: {\"source\": \"Node_X\", \"target\": \"New_Node\"}.\n"
        context += "2. DO NOT connect the new tool to other pre-existing canvas nodes (such as existing Browse tools) unless the user explicitly told you to \"insert\" or \"splice\" between them.\n"
        context += "3. Tools such as Browse, Formula, Select, and Filter can ONLY have ONE incoming connection. Never send multiple wires into the same input handle.\n"
        
        context += "\nCRITICAL FORMATTING RULES:\n"
        context += "1. Output ONLY the `submit_pipeline_graph` tool call or raw JSON delta.\n"
        context += "2. DO NOT write explanations, tables, or markdown conversation.\n"
        context += "3. Stop generation immediately after the closing bracket.\n"
        
        context += "\nFORMULA SYNTAX RULES (STRICT):\n"
        context += "1. Regex Extraction Signature:\n"
        context += "   Regex_Extract([Column], \"regex_pattern\")\n"
        context += "   - Arg 1 MUST be the bracketed column name, e.g., [URL]\n"
        context += "   - Arg 2 MUST be the string pattern, e.g., \"([^/]+)/?$\"\n"
        context += "   NEVER swap the arguments. Example: Regex_Extract([URL], \"([^/]+)/?$\")\n"
        context += "2. Target Column Naming:\n"
        context += "   - When extracting or deriving a new field, DO NOT set \"column\" to the source column name (e.g., do not set column=\"URL\").\n"
        context += "   - Set \"column\" to the requested target name (e.g., column=\"stripped\").\n"
        context += "   - Always include \"isNew\": true.\n"
        
        context += "\nREQUIRED OUTPUT FORMAT FOR FORMULA NODES:\n"
        context += "```json\n"
        context += "{\n"
        context += "  \"new_nodes\": [\n"
        context += "    {\n"
        context += "      \"id\": \"node_formula_1\",\n"
        context += "      \"type\": \"formula\",\n"
        context += "      \"position\": {\"x\": 1700, \"y\": 608},\n"
        context += "      \"data\": {\n"
        context += "        \"label\": \"Formula\",\n"
        context += "        \"parameters\": {\n"
        context += "          \"formulas\": [\n"
        context += "            {\n"
        context += "              \"column\": \"stripped\",\n"
        context += "              \"expression\": \"Regex_Extract([URL], \\\"([^/]+)/?$\\\")\",\n"
        context += "              \"type\": \"String\"\n"
        context += "            }\n"
        context += "          ]\n"
        context += "        }\n"
        context += "      }\n"
        context += "    }\n"
        context += "  ],\n"
        context += "  \"new_edges\": [\n"
        context += "    {\"source\": \"node_20\", \"target\": \"node_formula_1\", \"sourceHandle\": \"true\"}\n"
        context += "  ],\n"
        context += "  \"summary\": \"Added formula node to extract stripped URL slug\"\n"
        context += "}\n"
        context += "```\n"
        context += "RULES:\n"
        context += "- ONLY forward edges from upstream to downstream (never add edges going backward).\n"
        context += "- For filter source nodes, always specify \"sourceHandle\": \"true\".\n"
        
        # Fresh message list for this run
        self.messages = [
            {"role": "system", "content": base_system_prompt + "\n\n" + context},
            {"role": "user", "content": user_prompt}
        ]
        
        turn = 0
        while turn < max_turns:
            turn += 1
            
            response = await self.client.complete(
                messages=self.messages,
                tools=self.tool_schemas,
                temperature=0.0,
                max_tokens=1024
            )
            
            # The LLMResponse might contain content (Thought)
            if response.content:
                yield {"event": "THOUGHT", "data": response.content}
                
            assistant_msg = {"role": "assistant", "content": response.content or ""}
            
            if response.tool_calls:
                # Format tool calls for message history
                formatted_calls = []
                for tc in response.tool_calls:
                    formatted_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments) if not isinstance(tc.arguments, str) else tc.arguments
                        }
                    })
                assistant_msg["tool_calls"] = formatted_calls
                self.messages.append(assistant_msg)
                
                # Execute tools
                for tc in response.tool_calls:
                    yield {"event": "TOOL_CALL", "data": {"tool": tc.name, "args": tc.arguments}}
                    
                    tool_func = AGENT_TOOLS.get(tc.name, {}).get("callable")
                    if not tool_func:
                        result = {"status": "error", "error": f"Tool {tc.name} not found"}
                        yield {"event": "SELF_HEAL", "data": {"error": result["error"], "attempt": turn}}
                        self.messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name, "content": json.dumps(result)})
                        continue
                        
                    try:
                        # tc.arguments is already a dict, parsed safely in the providers
                        result = tool_func(**tc.arguments)
                        yield {"event": "TOOL_RESULT", "data": {"tool": tc.name, "result": result}}
                        self.messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name, "content": json.dumps(result)})
                    except OrchestratorComplete as e:
                        # Successfully completed
                        delta = e.delta
                        deleted_ids = set(delta.get("deleted_node_ids", []))
                        
                        # 1. Start with initial nodes, filtering out deletions
                        merged_nodes_by_id = {
                            n["id"]: dict(n) for n in initial_nodes if n["id"] not in deleted_ids
                        }
                        
                        # 2. Apply modifications to existing nodes
                        for mod in delta.get("modified_nodes", []):
                            node_id = mod.get("id")
                            if node_id in merged_nodes_by_id:
                                target = merged_nodes_by_id[node_id]
                                if "position" in mod:
                                    target["position"] = mod["position"]
                                if "label" in mod:
                                    target.setdefault("data", {})["label"] = mod["label"]
                                if "parameters" in mod:
                                    target.setdefault("data", {}).setdefault("parameters", {}).update(mod["parameters"])
                                    
                        # 3. Add new nodes
                        for new_n in delta.get("new_nodes", []):
                            raw_type = new_n.get("type") or new_n.get("data", {}).get("type", "browse")
                            meta = resolve_tool_meta(raw_type)
                            canonical_type = meta["type"]
                        
                            # Safely extract parameters
                            raw_params = new_n.get("parameters") or new_n.get("data", {}).get("parameters") or {}
                            if canonical_type == "formula":
                                raw_params = normalize_formula_params(raw_params)
                            elif canonical_type == "browse" and not raw_params:
                                raw_params = {"info": "View Data in Results Panel", "isCached": False}
                        
                            # Anti-collision positioning
                            pos = dict(new_n.get("position", {"x": 0, "y": 0}))
                            edges_list = delta.get("new_edges") or []
                            source_node_id = new_n.get("source") or (edges_list[0].get("source") if edges_list else None)
                            source_node = merged_nodes_by_id.get(source_node_id)
                            
                            if source_node:
                                src_pos = source_node.get("position", {"x": 0, "y": 0})
                                
                                # Best of both worlds: if the model returned a small X, treat it as a relative delta
                                if pos.get("x", 0) < src_pos.get("x", 0) - 100:
                                    pos["x"] = src_pos.get("x", 0) + max(150, pos.get("x", 260))
                                    pos["y"] = src_pos.get("y", 0) + pos.get("y", 0)
                                    
                                # If position is too close to source, push it downstream
                                if pos.get("x", 0) <= src_pos.get("x", 0) + 150:
                                    pos["x"] = src_pos.get("x", 0) + 260
                                    pos["y"] = src_pos.get("y", 0)
                                    
                                # Check if another node already occupies this (x, y) slot (e.g. node_28)
                                occupied = any(
                                    n["id"] != new_n["id"] and 
                                    abs(n.get("position", {}).get("x", 0) - pos["x"]) < 100 and 
                                    abs(n.get("position", {}).get("y", 0) - pos["y"]) < 60
                                    for n in merged_nodes_by_id.values()
                                )
                                if occupied:
                                    pos["y"] = src_pos.get("y", 0) + 140
                        
                            merged_nodes_by_id[new_n["id"]] = {
                                "id": new_n["id"],
                                "type": canonical_type,
                                "position": pos,
                                "data": {
                                    "label": new_n.get("label") or new_n.get("data", {}).get("label") or meta["label"],
                                    "icon": meta["icon"],
                                    "category": meta["category"],
                                    "parameters": raw_params,
                                    "status": "idle",
                                    "output": None,
                                    "resultSummary": {"row_count": 0}
                                }
                            }
                            
                        # 4. Merge edges
                        merged_edges_by_id = {
                            e["id"]: dict(e) for e in initial_edges 
                            if e["source"] not in deleted_ids and e["target"] not in deleted_ids
                        }
                        
                        node_types = {n_id: (n.get("type") or "").lower() for n_id, n in merged_nodes_by_id.items()}
                        for new_e in delta.get("new_edges", []):
                            src = new_e.get("source")
                            tgt = new_e.get("target")
                            if not src or not tgt or src == tgt:
                                continue
                                
                            # Check against merged_edges_by_id, NOT just initial_edges
                            backward_exists = any(
                                e.get("source") == tgt and e.get("target") == src 
                                for e in merged_edges_by_id.values()
                            )
                            if backward_exists:
                                continue

                            tgt_type = node_types.get(tgt, "")
                            # Single-input invariant: non-union tools cannot have > 1 incoming edge
                            if tgt_type not in MULTI_INPUT_TOOLS:
                                existing_incoming = [
                                    e_id for e_id, e in merged_edges_by_id.items() 
                                    if e.get("target") == tgt and e.get("targetHandle", "input") == "input"
                                ]
                                if existing_incoming:
                                    # If target already has an incoming wire from an existing canvas node,
                                    # ignore this hallucinated extra edge to prevent dual-input corruption
                                    continue

                            edge_id = new_e.get("id", f"edge_{src}_{tgt}")
                            edge_obj = {
                                "id": edge_id,
                                "source": src,
                                "target": new_e["target"],
                                "type": "default"
                            }
                            # Assign handles based on source type
                            src_type = node_types.get(new_e["source"])
                            if src_type == "filter":
                                edge_obj["sourceHandle"] = new_e.get("sourceHandle", "true")
                            elif src_type == "unique":
                                edge_obj["sourceHandle"] = new_e.get("sourceHandle", "unique")
                                
                            edge_obj["targetHandle"] = new_e.get("targetHandle", "input")
                            merged_edges_by_id[edge_id] = edge_obj

                        final_graph = {
                            "nodes": list(merged_nodes_by_id.values()),
                            "edges": list(merged_edges_by_id.values()),
                            "summary": delta.get("summary", "Pipeline graph updated.")
                        }
                        yield {"event": "DONE", "data": final_graph}
                        return
                    except Exception as e:
                        # Tool failed, SELF HEAL
                        tb = traceback.format_exc()
                        result = {"status": "error", "traceback": tb}
                        yield {"event": "SELF_HEAL", "data": {"error": str(e), "attempt": turn}}
                        self.messages.append({"role": "tool", "tool_call_id": tc.id, "name": tc.name, "content": json.dumps(result)})
            else:
                # Check if the model printed valid delta JSON in text rather than calling the tool
                fallback_delta = extract_delta_json(response.content)
                
                # Handle both delta format and full pipeline wrapper format
                if fallback_delta:
                    if "pipeline" in fallback_delta and isinstance(fallback_delta["pipeline"], dict):
                        fallback_delta = fallback_delta["pipeline"]

                    # If model outputted full "nodes" instead of "new_nodes", convert to delta
                    if "nodes" in fallback_delta and "new_nodes" not in fallback_delta:
                        initial_ids = {n["id"] for n in initial_nodes}
                        fallback_delta["new_nodes"] = [n for n in fallback_delta["nodes"] if n["id"] not in initial_ids]
                        
                    if "edges" in fallback_delta and "new_edges" not in fallback_delta:
                        initial_edge_ids = {e.get("id") for e in initial_edges}
                        fallback_delta["new_edges"] = [e for e in fallback_delta["edges"] if e.get("id") not in initial_edge_ids]

                    # Trigger tool rehydration if valid nodes or edges exist
                    if fallback_delta.get("new_nodes") or fallback_delta.get("new_edges") or fallback_delta.get("modified_nodes"):
                        try:
                            # Directly execute the completion logic
                            raise OrchestratorComplete(delta=fallback_delta)
                        except OrchestratorComplete as e:
                            delta = e.delta
                            deleted_ids = set(delta.get("deleted_node_ids", []))
                            
                            # 1. Start with initial nodes, filtering out deletions
                            merged_nodes_by_id = {
                                n["id"]: dict(n) for n in initial_nodes if n["id"] not in deleted_ids
                            }
                            
                            # 2. Apply modifications to existing nodes
                            for mod in delta.get("modified_nodes", []):
                                node_id = mod.get("id")
                                if node_id in merged_nodes_by_id:
                                    target = merged_nodes_by_id[node_id]
                                    if "position" in mod:
                                        target["position"] = mod["position"]
                                    if "label" in mod:
                                        target.setdefault("data", {})["label"] = mod["label"]
                                    if "parameters" in mod:
                                        target.setdefault("data", {}).setdefault("parameters", {}).update(mod["parameters"])
                                        
                            # 3. Add new nodes
                            for new_n in delta.get("new_nodes", []):
                                raw_type = new_n.get("type") or new_n.get("data", {}).get("type", "browse")
                                meta = resolve_tool_meta(raw_type)
                                canonical_type = meta["type"]
                            
                                # Safely extract parameters
                                raw_params = new_n.get("parameters") or new_n.get("data", {}).get("parameters") or {}
                                if canonical_type == "formula":
                                    raw_params = normalize_formula_params(raw_params)
                                elif canonical_type == "browse" and not raw_params:
                                    raw_params = {"info": "View Data in Results Panel", "isCached": False}
                            
                                # Anti-collision positioning
                                pos = dict(new_n.get("position", {"x": 0, "y": 0}))
                                edges_list = delta.get("new_edges") or []
                                source_node_id = new_n.get("source") or (edges_list[0].get("source") if edges_list else None)
                                source_node = merged_nodes_by_id.get(source_node_id)
                                
                                if source_node:
                                    src_pos = source_node.get("position", {"x": 0, "y": 0})
                                    
                                    # Best of both worlds: if the model returned a small X, treat it as a relative delta
                                    if pos.get("x", 0) < src_pos.get("x", 0) - 100:
                                        pos["x"] = src_pos.get("x", 0) + max(150, pos.get("x", 260))
                                        pos["y"] = src_pos.get("y", 0) + pos.get("y", 0)
                                        
                                    # If position is too close to source, push it downstream
                                    if pos.get("x", 0) <= src_pos.get("x", 0) + 150:
                                        pos["x"] = src_pos.get("x", 0) + 260
                                        pos["y"] = src_pos.get("y", 0)
                                        
                                    # Check if another node already occupies this (x, y) slot (e.g. node_28)
                                    occupied = any(
                                        n["id"] != new_n["id"] and 
                                        abs(n.get("position", {}).get("x", 0) - pos["x"]) < 100 and 
                                        abs(n.get("position", {}).get("y", 0) - pos["y"]) < 60
                                        for n in merged_nodes_by_id.values()
                                    )
                                    if occupied:
                                        pos["y"] = src_pos.get("y", 0) + 140
                            
                                merged_nodes_by_id[new_n["id"]] = {
                                    "id": new_n["id"],
                                    "type": canonical_type,
                                    "position": pos,
                                    "data": {
                                        "label": new_n.get("label") or new_n.get("data", {}).get("label") or meta["label"],
                                        "icon": meta["icon"],
                                        "category": meta["category"],
                                        "parameters": raw_params,
                                        "status": "idle",
                                        "output": None,
                                        "resultSummary": {"row_count": 0}
                                    }
                                }
                                
                            # 4. Merge edges
                            merged_edges_by_id = {
                                e["id"]: dict(e) for e in initial_edges 
                                if e["source"] not in deleted_ids and e["target"] not in deleted_ids
                            }
                            
                            node_types = {n_id: (n.get("type") or "").lower() for n_id, n in merged_nodes_by_id.items()}
                            for new_e in delta.get("new_edges", []):
                                src = new_e.get("source")
                                tgt = new_e.get("target")
                                if not src or not tgt or src == tgt:
                                    continue
                                    
                                # Check against merged_edges_by_id, NOT just initial_edges
                                backward_exists = any(
                                    e.get("source") == tgt and e.get("target") == src 
                                    for e in merged_edges_by_id.values()
                                )
                                if backward_exists:
                                    continue

                                tgt_type = node_types.get(tgt, "")
                                # Single-input invariant: non-union tools cannot have > 1 incoming edge
                                if tgt_type not in MULTI_INPUT_TOOLS:
                                    existing_incoming = [
                                        e_id for e_id, e in merged_edges_by_id.items() 
                                        if e.get("target") == tgt and e.get("targetHandle", "input") == "input"
                                    ]
                                    if existing_incoming:
                                        # If target already has an incoming wire from an existing canvas node,
                                        # ignore this hallucinated extra edge to prevent dual-input corruption
                                        continue
    
                                edge_id = new_e.get("id", f"edge_{src}_{tgt}")
                                edge_obj = {
                                    "id": edge_id,
                                    "source": src,
                                    "target": new_e["target"],
                                    "type": "default"
                                }
                                # Assign handles based on source type
                                src_type = node_types.get(new_e["source"])
                                if src_type == "filter":
                                    edge_obj["sourceHandle"] = new_e.get("sourceHandle", "true")
                                elif src_type == "unique":
                                    edge_obj["sourceHandle"] = new_e.get("sourceHandle", "unique")
                                    
                                edge_obj["targetHandle"] = new_e.get("targetHandle", "input")
                                merged_edges_by_id[edge_id] = edge_obj

                            final_graph = {
                                "nodes": list(merged_nodes_by_id.values()),
                                "edges": list(merged_edges_by_id.values()),
                                "summary": delta.get("summary", "Pipeline graph updated via fallback parsing.")
                            }
                            yield {"event": "DONE", "data": final_graph}
                            return

                yield {"event": "SELF_HEAL", "data": {"error": "No tools called. You must call submit_pipeline_graph with new_nodes.", "attempt": turn}}
                
                # Prevent turn accumulation by resetting messages to the initial state with a strong correction hint
                self.messages = [
                    {"role": "system", "content": base_system_prompt + "\n\n" + context},
                    {"role": "user", "content": user_prompt},
                    {"role": "user", "content": "Correction: Output ONLY valid JSON containing new_nodes and new_edges. Example: {\"new_nodes\": [{\"id\": \"node_29\", \"type\": \"formula\", \"position\": {\"x\": 1700, \"y\": 608}}], \"new_edges\": [{\"source\": \"node_20\", \"target\": \"node_29\"}]}"}
                ]

        # Max turns exceeded
        yield {"event": "ERROR", "data": "Max turns (10) exceeded without completing the workflow."}

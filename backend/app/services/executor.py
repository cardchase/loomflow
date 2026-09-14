import json
import os
from typing import Dict, Any
from app.engine import execute_pipeline

def run_pipeline_by_id(workflow_id: str):
    """Loads a saved workflow JSON and runs it headlessly."""
    workflows_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workflows")
    filepath = os.path.join(workflows_dir, f"{workflow_id}.json")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Workflow {workflow_id} not found at {filepath}")
        
    with open(filepath, "r", encoding="utf-8") as f:
        workflow_data = json.load(f)
        
    # The pipeline executor expects a dict with 'nodes' and 'edges'
    execute_pipeline(workflow_data)

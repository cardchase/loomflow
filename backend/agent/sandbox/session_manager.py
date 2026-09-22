import os
import polars as pl
from typing import Dict, Any, Optional

class SandboxSession:
    def __init__(self, session_id: str, file_path: Optional[str] = None):
        self.session_id = session_id
        self.micro_sample: Optional[pl.DataFrame] = None
        
        if file_path:
            self._load_sample(file_path)
            
    def _load_sample(self, file_path: str):
        # Resolve to uploads dir if it's not an absolute path
        if not os.path.isabs(file_path):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads"))
            resolved_path = os.path.join(base_dir, file_path)
        else:
            resolved_path = file_path
            
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"Dataset not found at {resolved_path}")
            
        # Load exactly 200 rows to keep agent latency low and sandbox safe
        # using lazy execution when possible
        ext = os.path.splitext(resolved_path)[1].lower()
        if ext == ".csv":
            self.micro_sample = pl.read_csv(resolved_path, n_rows=200, infer_schema_length=200)
        elif ext == ".parquet":
            self.micro_sample = pl.scan_parquet(resolved_path).head(200).collect()
        elif ext in [".xls", ".xlsx"]:
            self.micro_sample = pl.read_excel(resolved_path).head(200)
        else:
            raise ValueError(f"Unsupported file format for sandbox sampling: {ext}")
            
    def inspect_source_metadata(self) -> dict:
        if self.micro_sample is None:
            return {"error": "No data loaded into SandboxSession."}
            
        df = self.micro_sample
        null_counts = {col: df[col].null_count() for col in df.columns}
        
        return {
            "columns": df.columns,
            "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
            "null_counts": null_counts,
            "preview_rows": df.head(5).to_dicts()
        }
        
    def profile_column_semantics(self, column_name: str) -> dict:
        if self.micro_sample is None:
            return {"error": "No data loaded into SandboxSession."}
            
        if column_name not in self.micro_sample.columns:
            return {"error": f"Column '{column_name}' not found."}
            
        series = self.micro_sample[column_name]
        is_numeric = series.dtype in [pl.Int32, pl.Int64, pl.Float32, pl.Float64]
        
        profile = {
            "name": column_name,
            "dtype": str(series.dtype),
            "null_count": series.null_count(),
            "unique_count": series.n_unique(),
        }
        
        if is_numeric:
            profile.update({
                "mean": series.mean(),
                "min": series.min(),
                "max": series.max(),
                "std": series.std()
            })
        else:
            # Top categorical values
            val_counts = series.value_counts().sort("count", descending=True).head(5)
            # Polars value_counts returns a struct, so we convert it cleanly
            top_vals = [
                {str(column_name): row[column_name], "count": row["count"]} 
                for row in val_counts.to_dicts()
            ]
            profile["top_values"] = top_vals
            
        return profile
        
    def test_polars_transformation(self, node_type: str, config: dict) -> dict:
        if self.micro_sample is None:
            return {"error": "No data loaded into SandboxSession."}
            
        # Dynamically instantiate the node from tools based on node_type
        from app.tools import NODE_CLASSES
        if node_type not in NODE_CLASSES:
            return {"error": f"Node type '{node_type}' is not registered in LoomFlow."}
            
        try:
            node_instance = NODE_CLASSES[node_type](node_id="sandbox_test", parameters=config)
            result_df = node_instance.execute({"input": self.micro_sample.clone()})
            return {
                "status": "success",
                "new_schema": {col: str(dtype) for col, dtype in zip(result_df.columns, result_df.dtypes)},
                "preview_rows": result_df.head(5).to_dicts()
            }
        except Exception as e:
            import traceback
            return {
                "status": "error",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
            
    def test_symbolic_expression(self, expression: str) -> dict:
        try:
            import sympy
            expr = sympy.sympify(expression)
            
            # Simple singularity checks (e.g. division by zero at x=0 if x is a symbol)
            # In sandbox we just ensure it parses and we can get free symbols
            symbols = [str(s) for s in expr.free_symbols]
            
            return {
                "status": "success",
                "parsed_expression": str(expr),
                "required_variables": symbols
            }
        except Exception as e:
            return {
                "status": "error",
                "error_message": str(e)
            }
            
    def compile_and_layout_dag(self, sequence: list) -> dict:
        """
        Translates a sequential array of tools into a React Flow JSON graph.
        Assigns basic sequential X coordinates, relying on frontend for auto-layout if needed.
        sequence: list of dicts {"node_type": str, "config": dict}
        """
        nodes = []
        edges = []
        
        # We start X at 100 and add 300 for each node in the sequence
        x_pos = 100
        y_pos = 100
        
        prev_node_id = None
        for i, step in enumerate(sequence):
            node_id = f"node_{i}_{step['node_type']}"
            
            node = {
                "id": node_id,
                "type": step['node_type'],
                "position": {"x": x_pos, "y": y_pos},
                "data": {
                    "label": step['node_type'],
                    "parameters": step.get('config', {})
                }
            }
            nodes.append(node)
            
            if prev_node_id:
                edge = {
                    "id": f"e_{prev_node_id}-{node_id}",
                    "source": prev_node_id,
                    "target": node_id
                }
                edges.append(edge)
                
            prev_node_id = node_id
            x_pos += 300
            
        return {
            "nodes": nodes,
            "edges": edges
        }

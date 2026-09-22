import polars as pl
from typing import Dict, Any
from app.tools.base import BaseNode

class SymbolicFormulaNode(BaseNode):
    MANIFEST = {
        "id": "symbolicFormula",
        "name": "Symbolic Math",
        "category": "stem",
        "icon": "Sigma",
        "description": "Apply natural math expressions to generate features (derivatives, integrals).",
        "ui_schema": [
            {"field": "expression", "type": "string", "label": "Math Expression", "default": ""},
            {"field": "output_col", "type": "string", "label": "Output Column Name", "default": "math_out"},
            {"field": "latex_preview", "type": "string", "label": "Expression Preview", "default": "", "ui_type": "latex_preview"}
        ]
    }

    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        expr_str = self.parameters.get("expression", "")
        out_col = self.parameters.get("output_col", "math_out")
        
        if not expr_str:
            return df
            
        try:
            import sympy
            import numpy as np
            expr = sympy.sympify(expr_str)
            symbols = list(expr.free_symbols)
            
            # Map sympy symbols to Polars column arrays
            # We lambdify the expression using numpy backend
            func = sympy.lambdify(symbols, expr, modules=['numpy'])
            
            # Evaluate using Polars map_batches or simple column arithmetic
            # Since polars expressions are better, we could convert, but lambdify+numpy is flexible
            # We'll extract numpy arrays from df for the required symbols
            kwargs = {}
            for s in symbols:
                col_name = str(s)
                if col_name in df.columns:
                    kwargs[col_name] = df[col_name].to_numpy()
                else:
                    self.log(f"Warning: Symbol {col_name} not found in columns. Setting to 0.")
                    kwargs[col_name] = np.zeros(len(df))
                    
            if not kwargs:
                # Constant expression
                res = float(expr.evalf())
                return df.with_columns(pl.lit(res).alias(out_col))
                
            result_array = func(**kwargs)
            return df.with_columns(pl.Series(out_col, result_array))
            
        except Exception as e:
            self.log(f"Error evaluating symbolic expression: {e}")
            return df

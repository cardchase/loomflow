import pytest
import polars as pl
from app.tools.symbolic_math import SymbolicFormulaNode

def test_symbolic_math_execution():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0], "y": [4.0, 5.0, 6.0]})
    node = SymbolicFormulaNode("test_node", {"expression": "x**2 + y", "output_col": "result"})
    
    out_df = node.execute({"input": df})
    
    assert "result" in out_df.columns
    # 1**2 + 4 = 5
    # 2**2 + 5 = 9
    # 3**2 + 6 = 15
    res = out_df["result"].to_list()
    assert res == [5.0, 9.0, 15.0]

def test_symbolic_math_missing_col():
    df = pl.DataFrame({"x": [1.0, 2.0, 3.0]})
    node = SymbolicFormulaNode("test_node", {"expression": "x + z", "output_col": "result"})
    
    out_df = node.execute({"input": df})
    
    assert "result" in out_df.columns
    # z is missing, should default to 0. 1+0 = 1.0
    res = out_df["result"].to_list()
    assert res == [1.0, 2.0, 3.0]

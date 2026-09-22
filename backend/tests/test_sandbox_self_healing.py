import pytest
import polars as pl
from app.agent.sandbox.session_manager import SandboxSession

def test_sandbox_catches_bad_transformation():
    # Provide dummy data
    df = pl.DataFrame({"revenue": ["$1,000", "$2,000", "invalid", None]})
    session = SandboxSession(session_id="test_heal")
    session._sample_df = df
    
    # Intentionally bad polars cast (trying to cast string with '$' to float without replace)
    bad_expr = 'df.with_columns(pl.col("revenue").cast(pl.Float64))'
    
    result = session.test_polars_transformation(bad_expr)
    
    # Ensure it returns an error string, not throwing an unhandled exception
    assert result.startswith("Error executing transformation:"), "Sandbox should catch and format the error"
    assert "revenue" in result or "cast" in result or "ComputeError" in result, "Trace should contain useful details for LLM"

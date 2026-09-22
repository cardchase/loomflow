import pytest
import polars as pl
from app.tools.crm import SLATimerNode, RuleRouterNode

def test_sla_timer_node():
    df = pl.DataFrame({"ticket_id": [1, 2]})
    node = SLATimerNode("test_sla", {"start_col": "created", "end_col": "resolved", "sla_hours": 24})
    
    out_df = node.execute({"input": df})
    
    assert "sla_breached" in out_df.columns
    # Mock implementation sets everything to False
    assert out_df["sla_breached"].to_list() == [False, False]

def test_rule_router_node():
    df = pl.DataFrame({"ticket_id": [1, 2]})
    node = RuleRouterNode("test_router", {"rules": "[{\"condition\": \"A\", \"route\": \"vip\"}]"})
    
    out_df = node.execute({"input": df})
    
    assert "matched_route" in out_df.columns
    assert out_df["matched_route"].to_list() == ["default", "default"]

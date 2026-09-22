import polars as pl
from typing import Dict, Any
from app.tools.base import BaseNode

class CRMConnectorNode(BaseNode):
    MANIFEST = {
        "id": "crmConnector",
        "name": "CRM Connector",
        "category": "crm",
        "icon": "Users",
        "description": "Parse and ingest data from Zendesk, HubSpot, or Salesforce ticket/lead structures.",
        "ui_schema": [
            {"field": "crm_source", "type": "select", "label": "CRM Source", "options": ["Zendesk", "HubSpot", "Salesforce"], "default": "Zendesk"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        return df

class TextClassificationNode(BaseNode):
    MANIFEST = {
        "id": "textClassification",
        "name": "Text Classification",
        "category": "crm",
        "icon": "MessageSquare",
        "description": "Apply intent extraction and sentiment scoring on text columns.",
        "ui_schema": [
            {"field": "text_column", "type": "string", "label": "Text Column", "default": ""},
            {"field": "task", "type": "select", "label": "Task", "options": ["Sentiment", "Intent"], "default": "Sentiment"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        col = self.parameters.get("text_column")
        if col and col in df.columns:
            # Mock sentiment logic for prototype
            df = df.with_columns(pl.lit(0.8).alias(f"{col}_sentiment_score"))
        return df

class SLATimerNode(BaseNode):
    MANIFEST = {
        "id": "slaTimer",
        "name": "SLA Timer",
        "category": "crm",
        "icon": "Clock",
        "description": "Calculate business-hours elapsed time and output sla_breached flags.",
        "ui_schema": [
            {"field": "start_col", "type": "string", "label": "Start Time Column", "default": ""},
            {"field": "end_col", "type": "string", "label": "End Time Column", "default": ""},
            {"field": "sla_hours", "type": "number", "label": "SLA Hours", "default": 24}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        # Mock SLA flag for prototype
        df = df.with_columns(pl.lit(False).alias("sla_breached"))
        return df

class RuleRouterNode(BaseNode):
    MANIFEST = {
        "id": "ruleRouter",
        "name": "Rule Router",
        "category": "crm",
        "icon": "GitMerge",
        "description": "Evaluate multiple rules and assign a routing path column.",
        "ui_schema": [
            {"field": "rules", "type": "string", "label": "Routing Rules (JSON)", "default": "[]"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        # Assign a mock route
        df = df.with_columns(pl.lit("default").alias("matched_route"))
        return df

class ActionWebhookNode(BaseNode):
    MANIFEST = {
        "id": "actionWebhook",
        "name": "Action Webhook",
        "category": "crm",
        "icon": "Send",
        "description": "Dispatch external HTTP POST payloads.",
        "ui_schema": [
            {"field": "url", "type": "string", "label": "Webhook URL", "default": ""}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        self.log("Action webhook triggered.")
        return df

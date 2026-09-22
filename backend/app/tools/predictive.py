import polars as pl
from typing import Dict, Any
from app.tools.base import BaseNode

class WindowFeaturesNode(BaseNode):
    MANIFEST = {
        "id": "windowFeatures",
        "name": "Window Features",
        "category": "predictive",
        "icon": "Activity",
        "description": "Polars rolling averages, EWMA, lag/lead, and Bollinger bands.",
        "ui_schema": [
            {"field": "column", "type": "string", "label": "Target Column", "default": ""},
            {"field": "window_size", "type": "number", "label": "Window Size", "default": 5},
            {"field": "feature_type", "type": "select", "label": "Feature Type", "options": ["Rolling Mean", "EWMA", "Lag"], "default": "Rolling Mean"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        col = self.parameters.get("column")
        ws = int(self.parameters.get("window_size", 5))
        ft = self.parameters.get("feature_type", "Rolling Mean")
        
        if col and col in df.columns:
            if ft == "Rolling Mean":
                df = df.with_columns(pl.col(col).rolling_mean(window_size=ws).alias(f"{col}_rolling_{ws}"))
            elif ft == "Lag":
                df = df.with_columns(pl.col(col).shift(ws).alias(f"{col}_lag_{ws}"))
        return df

class OutlierTreatmentNode(BaseNode):
    MANIFEST = {
        "id": "outlierTreatment",
        "name": "Outlier Treatment",
        "category": "predictive",
        "icon": "Scissors",
        "description": "Z-score and IQR winsorization/clipping.",
        "ui_schema": [
            {"field": "column", "type": "string", "label": "Target Column", "default": ""},
            {"field": "method", "type": "select", "label": "Method", "options": ["IQR", "Z-Score"], "default": "IQR"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        col = self.parameters.get("column")
        if col and col in df.columns:
            # Simple mock for winsorization
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            df = df.with_columns(
                pl.col(col).clip(lower_bound=lower, upper_bound=upper).alias(f"{col}_winsorized")
            )
        return df

class MLPredictorNode(BaseNode):
    MANIFEST = {
        "id": "mlPredictor",
        "name": "ML Predictor",
        "category": "predictive",
        "icon": "Cpu",
        "description": "In-pipeline training/evaluation for XGBoost and Regression models.",
        "ui_schema": [
            {"field": "target", "type": "string", "label": "Target Column", "default": ""},
            {"field": "features", "type": "string", "label": "Feature Columns (comma separated)", "default": ""},
            {"field": "model_type", "type": "select", "label": "Model Type", "options": ["XGBoost", "Poisson Regression"], "default": "XGBoost"}
        ]
    }
    def execute(self, inputs: Dict[str, pl.DataFrame]) -> pl.DataFrame:
        df = inputs.get("input", pl.DataFrame())
        target = self.parameters.get("target")
        if target and target in df.columns:
            # Mock prediction logic for prototype
            df = df.with_columns(pl.col(target).alias(f"{target}_prediction"))
        return df

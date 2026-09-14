from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field

class WorkflowSchedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workflow_id: str
    workflow_name: str
    cron_expr: str            # e.g., "0 9 * * 1-5"
    timezone: str = "UTC"
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

class WorkflowJobRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    schedule_id: Optional[int] = Field(default=None, foreign_key="workflowschedule.id")
    workflow_id: str
    status: str = "Queued"     # Queued, Running, Success, Failed, Cancelled
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    log_output: Optional[str] = None

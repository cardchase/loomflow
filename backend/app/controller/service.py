import asyncio
import time
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select
from app.database import engine, init_db
from app.models.controller import WorkflowSchedule, WorkflowJobRun
from app.services.executor import run_pipeline_by_id

class VibeController:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        init_db()
        self.scheduler.start()
        self.sync_jobs_from_db()

    def shutdown(self):
        self.scheduler.shutdown(wait=False)

    def sync_jobs_from_db(self):
        with Session(engine) as session:
            schedules = session.exec(select(WorkflowSchedule).where(WorkflowSchedule.enabled == True)).all()
            for sched in schedules:
                self.register_schedule_job(sched)

    def register_schedule_job(self, sched: WorkflowSchedule):
        job_id = f"sched_{sched.id}"
        trigger = CronTrigger.from_crontab(sched.cron_expr, timezone=sched.timezone)
        
        self.scheduler.add_job(
            func=self.dispatch_job,
            trigger=trigger,
            args=[sched.id, sched.workflow_id],
            id=job_id,
            replace_existing=True
        )

    def remove_schedule_job(self, schedule_id: int):
        job_id = f"sched_{schedule_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    async def dispatch_job(self, schedule_id: Optional[int], workflow_id: str):
        start_time = time.time()
        job_run = WorkflowJobRun(
            schedule_id=schedule_id,
            workflow_id=workflow_id,
            status="Running",
            started_at=datetime.utcnow()
        )
        with Session(engine) as session:
            session.add(job_run)
            session.commit()
            session.refresh(job_run)

        status = "Success"
        log = "Execution complete."
        try:
            # We run it in a thread so APScheduler isn't completely blocked
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, run_pipeline_by_id, workflow_id)
        except Exception as exc:
            status = "Failed"
            log = str(exc)

        elapsed = int((time.time() - start_time) * 1000)
        with Session(engine) as session:
            job_run.status = status
            job_run.finished_at = datetime.utcnow()
            job_run.duration_ms = elapsed
            job_run.log_output = log
            session.add(job_run)

            if schedule_id:
                sched = session.get(WorkflowSchedule, schedule_id)
                if sched:
                    sched.last_run_at = datetime.utcnow()
                    # Calculate next run time
                    job = self.scheduler.get_job(f"sched_{sched.id}")
                    if job and job.next_run_time:
                        sched.next_run_at = job.next_run_time
                    session.add(sched)
            session.commit()

controller = VibeController()

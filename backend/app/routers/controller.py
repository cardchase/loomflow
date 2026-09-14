import asyncio
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select
from app.database import engine
from app.models.controller import WorkflowSchedule, WorkflowJobRun
from app.controller.service import controller

router = APIRouter(prefix="/api/controller", tags=["Controller"])

@router.get("/schedules")
def get_schedules():
    with Session(engine) as session:
        return session.exec(select(WorkflowSchedule)).all()

@router.post("/schedules")
def create_schedule(sched: WorkflowSchedule):
    with Session(engine) as session:
        session.add(sched)
        session.commit()
        session.refresh(sched)
        if sched.enabled:
            controller.register_schedule_job(sched)
            job = controller.scheduler.get_job(f"sched_{sched.id}")
            if job and job.next_run_time:
                sched.next_run_at = job.next_run_time
            session.add(sched)
            session.commit()
        return sched

@router.delete("/schedules/{schedule_id}")
def delete_schedule(schedule_id: int):
    with Session(engine) as session:
        sched = session.get(WorkflowSchedule, schedule_id)
        if not sched:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        session.delete(sched)
        session.commit()
        
        # Remove from running APScheduler
        controller.remove_schedule_job(schedule_id)
        
        return {"message": "Deleted successfully"}

@router.post("/jobs/trigger/{workflow_id}")
async def run_now(workflow_id: str):
    asyncio.create_task(controller.dispatch_job(schedule_id=None, workflow_id=workflow_id))
    return {"message": "Job dispatched to worker queue"}

@router.get("/queue")
def get_job_history(limit: int = 50):
    with Session(engine) as session:
        stmt = select(WorkflowJobRun).order_by(WorkflowJobRun.started_at.desc()).limit(limit)
        return session.exec(stmt).all()

@router.delete("/jobs/{job_id}")
def delete_job_history(job_id: int):
    with Session(engine) as session:
        job = session.get(WorkflowJobRun, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        session.delete(job)
        session.commit()
        
        return {"message": "Job history deleted"}


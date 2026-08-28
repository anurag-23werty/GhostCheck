from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Company, Job, JobSnapshot
from app.schemas import (
    JobCreate,
    JobHistoryResponse,
    JobResponse,
    JobSnapshotResponse,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
):
    # 1. Find existing company
    company = db.scalar(
        select(Company).where(
            Company.domain == payload.company_domain
        )
    )

    # 2. Create company if it doesn't exist
    if company is None:
        company = Company(
            name=payload.company_name,
            domain=payload.company_domain,
        )

        db.add(company)
        db.flush()

    now = datetime.utcnow()

    # 3. Create canonical job
    job = Job(
        company_id=company.id,
        canonical_title=payload.title,
        canonical_location=payload.location,
        employment_type=payload.employment_type,
        first_seen_at=now,
        last_seen_at=now,
        is_active=True,
    )

    db.add(job)
    db.flush()

    # 4. Store the original observation
    snapshot = JobSnapshot(
        job_id=job.id,
        source=payload.source,
        source_url=payload.source_url,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        salary=payload.salary,
        captured_at=now,
    )

    db.add(snapshot)

    db.commit()
    db.refresh(job)

    return job


@router.get(
    "",
    response_model=list[JobResponse],
)
def list_jobs(
    db: Session = Depends(get_db),
):
    jobs = db.scalars(
        select(Job)
        .order_by(Job.last_seen_at.desc())
    ).all()

    return jobs


@router.get(
    "/{job_id}",
    response_model=JobResponse,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job


@router.get(
    "/{job_id}/history",
    response_model=JobHistoryResponse,
)
def get_job_history(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    snapshots = db.scalars(
        select(JobSnapshot)
        .where(JobSnapshot.job_id == job_id)
        .order_by(JobSnapshot.captured_at.asc())
    ).all()

    return {
        "job": job,
        "snapshots": snapshots,
    }
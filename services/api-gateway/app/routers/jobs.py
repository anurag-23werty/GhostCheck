import json
import os
from datetime import datetime

import redis
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import (
    Company,
    Job,
    JobSnapshot,
    SourceObservation,
)
from app.schemas import (
    CollectionRequest,
    JobCreate,
    JobHistoryResponse,
    JobResponse,
    SourceObservationResponse,
)


router = APIRouter(
    prefix="/api/v1/jobs",
    tags=["Jobs"],
)


# ============================================================
# Redis
# ============================================================

REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379",
)

redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

QUEUE_NAME = "ghostcheck:collection"


# ============================================================
# Collection endpoint
# ============================================================

@router.post(
    "/collect",
    status_code=202,
)
def collect_job(
    payload: CollectionRequest,
):
    redis_client.lpush(
        QUEUE_NAME,
        json.dumps(
            {
                "url": str(payload.url),
            }
        ),
    )

    return {
        "status": "queued",
        "url": str(payload.url),
    }


# ============================================================
# Create / Update Job
# ============================================================

@router.post(
    "",
    response_model=JobResponse,
    status_code=201,
)
def create_job(
    payload: JobCreate,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()

    # --------------------------------------------------------
    # 1. Find existing company
    # --------------------------------------------------------

    company = db.scalar(
        select(Company).where(
            Company.domain == payload.company_domain
        )
    )

    # --------------------------------------------------------
    # 2. Create company if it doesn't exist
    # --------------------------------------------------------

    if company is None:
        company = Company(
            name=payload.company_name,
            domain=payload.company_domain,
        )

        db.add(company)
        db.flush()

    # --------------------------------------------------------
    # 3. Find existing job using source identity
    # --------------------------------------------------------

    job = db.scalar(
        select(Job).where(
            Job.source == payload.source,
            Job.external_id == payload.external_id,
        )
    )

    # --------------------------------------------------------
    # 4. Existing job → update it
    # --------------------------------------------------------

    if job is not None:
        job.last_seen_at = now
        job.canonical_title = payload.title
        job.canonical_location = payload.location
        job.employment_type = payload.employment_type
        job.is_active = True

    # --------------------------------------------------------
    # 5. New job → create it
    # --------------------------------------------------------

    else:
        job = Job(
            company_id=company.id,
            external_id=payload.external_id,
            source=payload.source,
            canonical_title=payload.title,
            canonical_location=payload.location,
            employment_type=payload.employment_type,
            first_seen_at=now,
            last_seen_at=now,
            is_active=True,
        )

        db.add(job)
        db.flush()

    # --------------------------------------------------------
    # 6. ALWAYS create a snapshot
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 7. ALWAYS create a source observation
    #
    # This records:
    # "At this point in time, this job was present on LinkedIn."
    # --------------------------------------------------------

    observation = SourceObservation(
        job_id=job.id,
        source=payload.source,
        observed_at=now,
        is_present=True,
        source_url=payload.source_url,
    )

    db.add(observation)

    # --------------------------------------------------------
    # 8. Commit everything
    # --------------------------------------------------------

    db.commit()
    db.refresh(job)

    return job


# ============================================================
# List Jobs
# ============================================================

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


# ============================================================
# Get Single Job
# ============================================================

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


# ============================================================
# Get Job History
# ============================================================

@router.get(
    "/{job_id}/history",
    response_model=JobHistoryResponse,
)
def get_job_history(
    job_id: int,
    db: Session = Depends(get_db),
):
    # --------------------------------------------------------
    # 1. Find job
    # --------------------------------------------------------

    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # --------------------------------------------------------
    # 2. Get snapshots
    # --------------------------------------------------------

    snapshots = db.scalars(
        select(JobSnapshot)
        .where(JobSnapshot.job_id == job_id)
        .order_by(JobSnapshot.captured_at.asc())
    ).all()

    # --------------------------------------------------------
    # 3. Get source observations
    # --------------------------------------------------------

    observations = db.scalars(
        select(SourceObservation)
        .where(SourceObservation.job_id == job_id)
        .order_by(SourceObservation.observed_at.asc())
    ).all()

    # --------------------------------------------------------
    # 4. Return complete history
    # --------------------------------------------------------

    return {
        "job": job,
        "snapshots": snapshots,
        "observations": observations,
    }
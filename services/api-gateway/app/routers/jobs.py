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

COLLECTION_QUEUE = "ghostcheck:collection"
DETECTION_QUEUE = "ghostcheck:detection"


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
    """
    Accept a job URL and place it on the collection queue.

    API Gateway
        ↓
    Redis collection queue
        ↓
    Collector worker
    """

    message = {
        "url": str(payload.url),
    }

    redis_client.rpush(
        COLLECTION_QUEUE,
        json.dumps(message),
    )

    return {
        "status": "queued",
        "queue": COLLECTION_QUEUE,
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
    """
    Persist a normalized collected job.

    This endpoint performs four important operations:

    1. Resolve/create company
    2. Resolve/create job
    3. Store immutable snapshot
    4. Store source observation

    After the transaction is committed, the job is sent to
    the detection queue.
    """

    now = datetime.utcnow()

    # ========================================================
    # 1. Find company
    # ========================================================

    company = None

    # Prefer domain because it is more stable than company name.
    if payload.company_domain:
        company = db.scalar(
            select(Company).where(
                Company.domain == payload.company_domain
            )
        )

    # Fall back to company name.
    if company is None:
        company = db.scalar(
            select(Company).where(
                Company.name == payload.company_name
            )
        )

    # ========================================================
    # 2. Create company if necessary
    # ========================================================

    if company is None:
        company = Company(
            name=payload.company_name,
            domain=payload.company_domain,
        )

        db.add(company)
        db.flush()

    # ========================================================
    # 3. Find existing job by source identity
    # ========================================================

    job = None

    if payload.external_id:
        job = db.scalar(
            select(Job).where(
                Job.source == payload.source,
                Job.external_id == payload.external_id,
            )
        )

    # ========================================================
    # 4. Existing job → update
    # ========================================================

    if job is not None:

        job.last_seen_at = now
        job.canonical_title = payload.title
        job.canonical_location = payload.location
        job.employment_type = payload.employment_type
        job.is_active = True

    # ========================================================
    # 5. New job → create
    # ========================================================

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

    # ========================================================
    # 6. ALWAYS create snapshot
    # ========================================================

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

    # ========================================================
    # 7. ALWAYS create source observation
    # ========================================================

    observation = SourceObservation(
        job_id=job.id,
        source=payload.source,
        observed_at=now,
        is_present=True,
        source_url=payload.source_url,
    )

    db.add(observation)

    # ========================================================
    # 8. Commit database transaction
    # ========================================================

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    # ========================================================
    # 9. Refresh job
    # ========================================================

    db.refresh(job)

    # ========================================================
    # 10. Queue detection
    # ========================================================

    detection_message = {
        "job_id": job.id,
        "source": payload.source,
        "trigger": "job_collected",
    }

    try:
        redis_client.rpush(
            DETECTION_QUEUE,
            json.dumps(detection_message),
        )

    except Exception as exc:
        # IMPORTANT:
        #
        # The database transaction has already succeeded.
        # Therefore we do NOT rollback the job.
        #
        # In a production system, this should eventually be
        # replaced by an outbox pattern for guaranteed delivery.

        print(
            f"WARNING: failed to enqueue detection "
            f"for job {job.id}: {exc}"
        )

    # ========================================================
    # 11. Return
    # ========================================================

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
    """
    Return jobs ordered by most recently observed.
    """

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
    """
    Return a single job.
    """

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
    """
    Return the complete historical record for a job.

    Includes:

    - canonical job
    - all snapshots
    - all source observations
    """

    # ========================================================
    # 1. Find job
    # ========================================================

    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    # ========================================================
    # 2. Get snapshots
    # ========================================================

    snapshots = db.scalars(
        select(JobSnapshot)
        .where(JobSnapshot.job_id == job_id)
        .order_by(JobSnapshot.captured_at.asc())
    ).all()

    # ========================================================
    # 3. Get source observations
    # ========================================================

    observations = db.scalars(
        select(SourceObservation)
        .where(SourceObservation.job_id == job_id)
        .order_by(SourceObservation.observed_at.asc())
    ).all()

    # ========================================================
    # 4. Return complete history
    # ========================================================

    return {
        "job": job,
        "snapshots": snapshots,
        "observations": observations,
    }
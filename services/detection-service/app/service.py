from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.engine import GhostDetectionEngine
from app.features import build_features
from app.models import (
    DetectionFeature,
    GhostScore,
    Job,
    JobSnapshot,
    SourceObservation,
)


detector = GhostDetectionEngine()


def detect_job(
    db: Session,
    job_id: int,
):
    job = db.get(Job, job_id)

    if job is None:
        raise ValueError(
            f"Job {job_id} not found"
        )

    snapshots = db.scalars(
        select(JobSnapshot)
        .where(JobSnapshot.job_id == job.id)
        .order_by(JobSnapshot.captured_at.asc())
    ).all()

    observations = db.scalars(
        select(SourceObservation)
        .where(SourceObservation.job_id == job.id)
        .order_by(SourceObservation.observed_at.asc())
    ).all()

    descriptions = [
        snapshot.description
        for snapshot in snapshots
    ]

    sources = [
        observation.source
        for observation in observations
        if observation.is_present
    ]

    latest_snapshot = (
        snapshots[-1]
        if snapshots
        else None
    )

    features = build_features(
        first_seen_at=job.first_seen_at,
        last_seen_at=job.last_seen_at,
        descriptions=descriptions,
        sources=sources,
        latest_description=(
            latest_snapshot.description
            if latest_snapshot
            else None
        ),
        latest_salary=(
            latest_snapshot.salary
            if latest_snapshot
            else None
        ),
        latest_source_url=(
            latest_snapshot.source_url
            if latest_snapshot
            else None
        ),
    )

    result = detector.predict(features)

    now = datetime.utcnow()

    detection_features = DetectionFeature(
        job_id=job.id,
        staleness_score=features.staleness_score,
        repost_score=features.repost_score,
        cross_source_score=features.cross_source_score,
        description_duplication_score=(
            features.description_duplication_score
        ),
        headcount_drift_score=(
            features.headcount_drift_score
        ),
        detail_omission_score=(
            features.detail_omission_score
        ),
        calculated_at=now,
    )

    ghost_score = GhostScore(
        job_id=job.id,
        score=result.score,
        model_version=result.model_version,
        explanation=result.explanation,
        calculated_at=now,
    )

    db.add(detection_features)
    db.add(ghost_score)

    db.commit()

    return result
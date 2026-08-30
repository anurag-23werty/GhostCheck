import os
from datetime import datetime

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.engine import GhostDetectionEngine
from app.features import build_features
from app.models import (
    DetectionFeature,
    GhostScore,
    Job,
    JobSnapshot,
    SourceObservation,
)
from app.schemas import (
    DetectionRequest,
    DetectionResponse,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://ghostcheck:ghostcheck@localhost:5432/ghostcheck",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)

app = FastAPI(
    title="GhostCheck Detection Service",
    description="ML-powered ghost job detection service",
    version="0.1.0",
)

detector = GhostDetectionEngine()


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "detection-service",
        "model_version": detector.MODEL_VERSION,
    }


@app.get("/")
def root():
    return {
        "message": "GhostCheck Detection Service",
        "model_version": detector.MODEL_VERSION,
    }


@app.post(
    "/api/v1/detect",
    response_model=DetectionResponse,
)
def detect_job(
    payload: DetectionRequest,
):
    db: Session = SessionLocal()

    try:
        job = db.get(Job, payload.job_id)

        if job is None:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        snapshots = db.scalars(
            select(JobSnapshot)
            .where(
                JobSnapshot.job_id == job.id
            )
            .order_by(
                JobSnapshot.captured_at.asc()
            )
        ).all()

        observations = db.scalars(
            select(SourceObservation)
            .where(
                SourceObservation.job_id == job.id
            )
            .order_by(
                SourceObservation.observed_at.asc()
            )
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

        return DetectionResponse(
            job_id=job.id,
            score=result.score,
            model_version=result.model_version,
            explanation=result.explanation,
            features=features,
            calculated_at=now,
        )

    finally:
        db.close()
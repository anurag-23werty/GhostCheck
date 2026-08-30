import asyncio

from sqlalchemy import select

from app.database import SessionLocal
from app.features import build_features
from app.models import (
    DetectionFeature,
    Job,
    JobSnapshot,
    SourceObservation,
)
from app.queue import dequeue_detection


async def process_detection(message: dict) -> None:
    job_id = message["job_id"]

    print(f"[Detection] Processing job {job_id}")

    db = SessionLocal()

    try:
        # ====================================================
        # 1. Load job
        # ====================================================

        job = db.get(Job, job_id)

        if job is None:
            raise ValueError(
                f"Job {job_id} not found"
            )

        # ====================================================
        # 2. Load snapshots
        # ====================================================

        snapshots = db.scalars(
            select(JobSnapshot)
            .where(JobSnapshot.job_id == job_id)
            .order_by(JobSnapshot.captured_at.asc())
        ).all()

        # ====================================================
        # 3. Load source observations
        # ====================================================

        observations = db.scalars(
            select(SourceObservation)
            .where(SourceObservation.job_id == job_id)
            .order_by(SourceObservation.observed_at.asc())
        ).all()

        # ====================================================
        # 4. Build detection features
        # ====================================================

        features = build_features(
            job=job,
            snapshots=snapshots,
            observations=observations,
        )

        print(
            f"[Detection] Features for job {job_id}: "
            f"{features}"
        )

        # ====================================================
        # 5. Persist detection features
        # ====================================================

        detection_feature = DetectionFeature(
            job_id=job_id,
            staleness_score=features["staleness_score"],
            repost_score=features["repost_score"],
            cross_source_score=features["cross_source_score"],
            description_duplication_score=features[
                "description_duplication_score"
            ],
            headcount_drift_score=features[
                "headcount_drift_score"
            ],
            detail_omission_score=features[
                "detail_omission_score"
            ],
        )

        db.add(detection_feature)

        # ====================================================
        # 6. Commit feature vector
        # ====================================================

        db.commit()

        db.refresh(detection_feature)

        print(
            f"[Detection] Features persisted for job {job_id} "
            f"(feature_id={detection_feature.id})"
        )

        # ====================================================
        # 7. ML scoring comes next
        # ====================================================

        print(
            f"[Detection] ML scoring not implemented yet "
            f"for job {job_id}"
        )

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


async def worker() -> None:
    print("GhostCheck detection worker started")

    while True:
        message = await dequeue_detection()

        if message is None:
            continue

        try:
            await process_detection(message)

        except Exception as exc:
            print(
                f"[Detection] Failed: {exc}"
            )


if __name__ == "__main__":
    asyncio.run(worker())
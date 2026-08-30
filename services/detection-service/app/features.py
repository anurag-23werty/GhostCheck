from datetime import datetime

from app.models import Job, JobSnapshot, SourceObservation


def calculate_staleness_score(
    job: Job,
    now: datetime | None = None,
) -> float:
    """
    Higher score means the job has existed for a longer period.

    0.0 -> fresh
    1.0 -> very stale

    Saturates at 90 days.
    """

    now = now or datetime.utcnow()

    age_days = max(
        0.0,
        (now - job.first_seen_at).total_seconds() / 86400,
    )

    return min(age_days / 90.0, 1.0)


def calculate_repost_score(
    snapshots: list[JobSnapshot],
) -> float:
    """
    Measures repeated captures with essentially
    unchanged descriptions.
    """

    if len(snapshots) <= 1:
        return 0.0

    descriptions = [
        snapshot.description.strip().lower()
        for snapshot in snapshots
        if snapshot.description
    ]

    if len(descriptions) <= 1:
        return 0.0

    latest = descriptions[-1]

    identical_count = sum(
        description == latest
        for description in descriptions[:-1]
    )

    return min(
        identical_count / max(len(descriptions) - 1, 1),
        1.0,
    )


def calculate_cross_source_score(
    observations: list[SourceObservation],
) -> float:
    """
    Measures whether the job is observed across
    multiple recruiting sources.

    Currently GhostCheck actively collects LinkedIn.
    This feature remains ready for future sources.
    """

    sources = {
        observation.source
        for observation in observations
        if observation.is_present
    }

    if len(sources) <= 1:
        return 0.0

    return min(
        (len(sources) - 1) / 2.0,
        1.0,
    )


def calculate_description_duplication_score(
    snapshots: list[JobSnapshot],
) -> float:
    """
    Measures how much historical descriptions
    are duplicated.
    """

    descriptions = [
        snapshot.description.strip().lower()
        for snapshot in snapshots
        if snapshot.description
    ]

    if len(descriptions) <= 1:
        return 0.0

    unique_descriptions = set(descriptions)

    duplication_ratio = 1.0 - (
        len(unique_descriptions) / len(descriptions)
    )

    return max(
        0.0,
        min(duplication_ratio, 1.0),
    )


def calculate_headcount_drift_score(
    snapshots: list[JobSnapshot],
) -> float:
    """
    Placeholder for future company-headcount intelligence.

    LinkedIn job collection currently does not provide
    reliable historical company headcount information.
    """

    return 0.0


def calculate_detail_omission_score(
    snapshots: list[JobSnapshot],
) -> float:
    """
    Measures missing job information.

    Missing details are treated as a weak signal,
    not proof of a ghost job.
    """

    if not snapshots:
        return 0.0

    latest = snapshots[-1]

    missing = 0
    total = 3

    if not latest.description:
        missing += 1

    if not latest.salary:
        missing += 1

    if not latest.source_url:
        missing += 1

    return missing / total


# ============================================================
# Feature vector
# ============================================================

def build_features(
    job: Job,
    snapshots: list[JobSnapshot],
    observations: list[SourceObservation],
    now: datetime | None = None,
) -> dict[str, float]:
    """
    Build the numerical feature vector used by the
    GhostCheck detection model.

    Every feature is normalized to approximately [0, 1].
    """

    return {
        "staleness_score": calculate_staleness_score(
            job,
            now=now,
        ),

        "repost_score": calculate_repost_score(
            snapshots,
        ),

        "cross_source_score": calculate_cross_source_score(
            observations,
        ),

        "description_duplication_score": (
            calculate_description_duplication_score(
                snapshots,
            )
        ),

        "headcount_drift_score": (
            calculate_headcount_drift_score(
                snapshots,
            )
        ),

        "detail_omission_score": (
            calculate_detail_omission_score(
                snapshots,
            )
        ),
    }
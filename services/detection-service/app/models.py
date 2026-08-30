from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
    )

    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    canonical_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    canonical_location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class JobSnapshot(Base):
    __tablename__ = "job_snapshots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    salary: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )


class SourceObservation(Base):
    __tablename__ = "source_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    observed_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    is_present: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class DetectionFeature(Base):
    __tablename__ = "detection_features"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    staleness_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    repost_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    cross_source_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    description_duplication_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    headcount_drift_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    detail_omission_score: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class GhostScore(Base):
    __tablename__ = "ghost_scores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    explanation: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    calculated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
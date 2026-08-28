from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    domain: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    jobs: Mapped[list["Job"]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id"),
        nullable=False,
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

    company: Mapped["Company"] = relationship(
        back_populates="jobs",
    )

    snapshots: Mapped[list["JobSnapshot"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )

    observations: Mapped[list["SourceObservation"]] = relationship(
        back_populates="job",
        cascade="all, delete-orphan",
    )


class JobSnapshot(Base):
    __tablename__ = "job_snapshots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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
        default=datetime.utcnow,
        nullable=False,
    )

    raw_data: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    job: Mapped["Job"] = relationship(
        back_populates="snapshots",
    )


class SourceObservation(Base):
    __tablename__ = "source_observations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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
        default=datetime.utcnow,
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

    job: Mapped["Job"] = relationship(
        back_populates="observations",
    )


class DetectionFeature(Base):
    __tablename__ = "detection_features"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
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
        autoincrement=True,
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


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    final_report: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class InvestigationEvidence(Base):
    __tablename__ = "investigation_evidence"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id"),
        nullable=False,
    )

    evidence_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    scraper_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    jobs_found: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )


class ScraperHealEvent(Base):
    __tablename__ = "scraper_heal_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    scraper_run_id: Mapped[int] = mapped_column(
        ForeignKey("scraper_runs.id"),
        nullable=False,
    )

    failure_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    proposed_fix: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
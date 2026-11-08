from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class JobPosting(Base):
    """A discovered job posting."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False, default="jobspy")
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    reasons: Mapped[str | None] = mapped_column(Text, nullable=True)


class ContactRecord(Base):
    """A recruiter or hiring contact discovered for a job."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id"), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(100), default="manual", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class StartupRecord(Base):
    """A startup discovered for outreach or analysis."""

    __tablename__ = "startups"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    funding_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class DatabaseManager:
    """Thin wrapper around the SQLAlchemy engine and session factory."""

    def __init__(self, database_url: str | None = None):
        configured_url = database_url or os.getenv("JOBPILOT_DB_URL", "sqlite:///jobpilot.db")
        self.database_url = configured_url
        self.engine = create_engine(configured_url, future=True)
        self.session_factory = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.init_db()

    def init_db(self) -> None:
        """Create all tables in the configured database."""

        Base.metadata.create_all(self.engine)

    def session(self) -> Session:
        """Get a database session."""

        return self.session_factory()


def init_database(database_url: str | None = None) -> DatabaseManager:
    """Convenience function for database initialization from application code."""

    manager = DatabaseManager(database_url=database_url)
    manager.init_db()
    return manager

from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

from pydantic import BaseModel, field_validator

from jobpilot.db import DatabaseManager, JobPosting

logger = logging.getLogger(__name__)


class JobListing(BaseModel):
    """A normalized job listing discovered from a public source."""

    title: str
    company: str
    location: str
    source: str = "jobspy"
    url: str = ""
    description: str = ""
    published_at: datetime | None = None

    @field_validator("title", "company", "location")
    @classmethod
    def strip_whitespace(cls, value: str) -> str:
        if value is None:
            return ""
        return value.strip()

    @property
    def dedupe_key(self) -> str:
        base = self.url.strip() or f"{self.title}|{self.company}|{self.location}"
        return base.lower()


class JobDiscoveryService:
    """Gateway for pulling public jobs and saving them into the DB."""

    def __init__(self, database_manager: DatabaseManager | None = None):
        self.database_manager = database_manager or DatabaseManager()

    def search(
        self,
        roles: Iterable[str],
        locations: Iterable[str],
        results_wanted: int = 25,
    ) -> list[JobListing]:
        """Search for jobs across the configured roles and locations."""

        jobs: list[JobListing] = []
        for role in roles:
            for location in locations:
                jobs.extend(self._fetch_live_jobs(role=role, location=location, results_wanted=results_wanted))

        deduped_jobs = dedupe_jobs(jobs)
        self.save(deduped_jobs)
        return deduped_jobs

    def save(self, jobs: Iterable[JobListing]) -> list[JobPosting]:
        """Persist deduplicated jobs to the database."""

        stored_jobs: list[JobPosting] = []
        with self.database_manager.session() as session:
            for job in jobs:
                existing = session.query(JobPosting).filter_by(url=job.url).first() if job.url else None
                if existing is not None:
                    continue

                record = JobPosting(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    source=job.source,
                    url=job.url or job.dedupe_key,
                    description=job.description,
                    published_at=job.published_at,
                    status="new",
                )
                session.add(record)
                stored_jobs.append(record)
            session.commit()

        return stored_jobs

    def _fetch_live_jobs(
        self,
        *,
        role: str,
        location: str,
        results_wanted: int,
    ) -> list[JobListing]:
        """Pull job postings from a public listing source when available."""

        try:
            from python_jobspy import scrape_jobs  # type: ignore
        except ImportError:
            logger.warning("python-jobspy is not installed; discovery skipped for %s in %s", role, location)
            return []

        try:
            results = scrape_jobs(
                site_name=["indeed", "linkedin", "glassdoor", "google"],
                search_term=role,
                location=location,
                results_wanted=min(results_wanted, 25),
                hours_old=24,
            )
        except Exception as exc:  # pragma: no cover - depends on upstream job source behavior
            logger.warning("Job discovery failed for %s in %s: %s", role, location, exc)
            return []

        items: list[JobListing] = []
        for raw in results:
            if raw is None:
                continue

            title = str(getattr(raw, "title", "") or raw.get("title", "") or "").strip()
            company = str(getattr(raw, "company", "") or raw.get("company", "") or "").strip()
            loc = str(getattr(raw, "location", "") or raw.get("location", "") or location).strip()
            url = str(getattr(raw, "url", "") or raw.get("url", "") or raw.get("job_url", "") or "").strip()
            description = str(getattr(raw, "description", "") or raw.get("description", "") or raw.get("snippet", "") or "").strip()
            published_at = getattr(raw, "date_posted", None) or raw.get("date_posted") if hasattr(raw, "keys") else None

            if not title or not company:
                continue

            items.append(
                JobListing(
                    title=title,
                    company=company,
                    location=loc,
                    source="jobspy",
                    url=url,
                    description=description,
                    published_at=published_at,
                )
            )

        return items


def dedupe_jobs(jobs: Iterable[JobListing]) -> list[JobListing]:
    """Remove duplicates based on URL or a normalized title/company/location key."""

    seen: set[str] = set()
    unique_jobs: list[JobListing] = []

    for job in jobs:
        key = job.dedupe_key
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(job)

    return unique_jobs


def discover_jobs(
    roles: Iterable[str],
    locations: Iterable[str],
    database_manager: DatabaseManager | None = None,
    results_wanted: int = 25,
) -> list[JobListing]:
    """Convenience wrapper for the discovery stage."""

    service = JobDiscoveryService(database_manager=database_manager)
    return service.search(roles=roles, locations=locations, results_wanted=results_wanted)

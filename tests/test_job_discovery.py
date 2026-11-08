from __future__ import annotations

from datetime import datetime, timezone

from jobpilot.db import DatabaseManager, JobPosting
from jobpilot.discovery.jobs import JobDiscoveryService, JobListing, dedupe_jobs


def test_dedupe_filters_duplicate_jobs() -> None:
    jobs = [
        JobListing(
            title="SOC Analyst",
            company="Acme Corp",
            location="Bengaluru, India",
            url="https://example.com/a",
            description="Detect threats.",
            published_at=datetime.now(timezone.utc),
        ),
        JobListing(
            title="SOC Analyst",
            company="Acme Corp",
            location="Bengaluru, India",
            url="https://example.com/a",
            description="Duplicate listing.",
            published_at=datetime.now(timezone.utc),
        ),
        JobListing(
            title="Security Analyst",
            company="Beta Labs",
            location="Bengaluru, India",
            url="https://example.com/b",
            description="Analyze security incidents.",
            published_at=datetime.now(timezone.utc),
        ),
    ]

    unique_jobs = dedupe_jobs(jobs)

    assert len(unique_jobs) == 2
    assert {job.url for job in unique_jobs} == {"https://example.com/a", "https://example.com/b"}


def test_discovery_service_persists_new_jobs(tmp_path, monkeypatch) -> None:
    database_url = f"sqlite:///{tmp_path / 'jobpilot.db'}"
    manager = DatabaseManager(database_url=database_url)
    service = JobDiscoveryService(database_manager=manager)

    def fake_fetch_live_jobs(*, role: str, location: str, results_wanted: int):
        return [
            JobListing(
                title="SOC Analyst",
                company="Acme Corp",
                location="Bengaluru",
                url="https://example.com/job-1",
                description="Monitor and investigate incidents.",
                published_at=datetime.now(timezone.utc),
            ),
            JobListing(
                title="SOC Analyst",
                company="Acme Corp",
                location="Bengaluru",
                url="https://example.com/job-1",
                description="Duplicate listing.",
                published_at=datetime.now(timezone.utc),
            ),
            JobListing(
                title="Pentest Intern",
                company="ThreatForge",
                location="Bengaluru",
                url="https://example.com/job-2",
                description="Assist with web app assessments.",
                published_at=datetime.now(timezone.utc),
            ),
        ]

    monkeypatch.setattr(service, "_fetch_live_jobs", fake_fetch_live_jobs)

    discovered = service.search(["SOC Analyst", "Pentest Intern"], ["Bengaluru"], results_wanted=10)

    assert len(discovered) == 2
    with manager.session() as session:
        count = session.query(JobPosting).count()
        assert count == 2

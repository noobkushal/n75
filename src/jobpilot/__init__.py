"""JobPilot package."""

from .config import Settings, load_master_profile, load_settings
from .db import Base, DatabaseManager, JobPosting
from .discovery.jobs import JobDiscoveryService, JobListing, dedupe_jobs, discover_jobs
from .llm import LLMClient
from .scoring import JobScore, JobScorer, parse_score_response

__all__ = [
    "Base",
    "DatabaseManager",
    "JobListing",
    "JobDiscoveryService",
    "JobPosting",
    "JobScore",
    "JobScorer",
    "LLMClient",
    "Settings",
    "dedupe_jobs",
    "discover_jobs",
    "load_master_profile",
    "load_settings",
    "parse_score_response",
]

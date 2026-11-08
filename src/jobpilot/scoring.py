from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .llm import LLMClient


class JobScore(BaseModel):
    """Structured scoring result for a job match against a profile."""

    score: int = Field(..., ge=0, le=100)
    reasons: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    summary: str = ""


def parse_score_response(raw: dict[str, Any]) -> JobScore:
    """Validate and normalize a raw LLM scoring payload."""

    return JobScore.model_validate(raw)


class JobScorer:
    """LLM-based job match scorer."""

    def __init__(self, llm_client: LLMClient | None = None, master_profile: dict[str, Any] | None = None):
        self.llm_client = llm_client or LLMClient()
        self.master_profile = master_profile or {}

    def score_job(self, job: dict[str, Any] | str, *, role: str | None = None) -> JobScore:
        """Score a job using the configured master profile and LLM."""

        if isinstance(job, str):
            job_payload = {"title": role or "Target Role", "description": job}
        else:
            job_payload = dict(job)

        prompt = self._build_prompt(job_payload)
        return self.llm_client.generate_json(prompt, JobScore, system_prompt=self._system_prompt())

    def _system_prompt(self) -> str:
        return (
            "You are evaluating a job against a candidate profile. Return a JSON object with "
            "keys: score, reasons, missing_skills, summary. score must be an integer from 0 to 100. "
            "reasons is a list of strings. missing_skills is a list of strings. summary is one sentence. "
            "Keep the response valid JSON with no trailing comments or Markdown fences."
        )

    def _build_prompt(self, job: dict[str, Any]) -> str:
        profile = self.master_profile.get("candidate", self.master_profile)
        skills = profile.get("skills", [])
        projects = profile.get("projects", [])
        summary = profile.get("summary", "")

        project_descriptions = ", ".join(project.get("name", "") for project in projects if isinstance(project, dict))

        title = job.get("title", "Unknown role")
        company = job.get("company", "Unknown company")
        location = job.get("location", "Unknown location")
        description = job.get("description", "")

        return (
            "Compare the following job with the candidate profile and estimate how well it matches.\n\n"
            f"Job title: {title}\n"
            f"Company: {company}\n"
            f"Location: {location}\n"
            f"Description: {description}\n\n"
            f"Candidate summary: {summary}\n"
            f"Candidate skills: {', '.join(skills)}\n"
            f"Candidate projects: {project_descriptions}\n\n"
            "Return a JSON object with these exact keys: score, reasons, missing_skills, summary. "
            "The score should reflect fit from 0 to 100; reasons should explain the best matches; missing_skills should list the relevant skills or experience not covered by the profile; summary should summarize the overall fit in one sentence."
        )

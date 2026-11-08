from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .guardrail import GuardrailViolation, validate_claims


class TailoredResume(BaseModel):
    """A resume payload tailored to a specific job while staying within the profile facts."""

    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[dict[str, str]] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return self.model_dump()


class TailorService:
    """Build a job-specific resume from the master profile without inventing facts."""

    def __init__(self, master_profile: dict[str, Any] | None = None):
        self.master_profile = master_profile or {}

    def tailor(self, job: dict[str, Any] | str, *, role: str | None = None) -> TailoredResume:
        profile = self.master_profile.get("candidate", self.master_profile)
        skills = profile.get("skills", []) or []
        projects = profile.get("projects", []) or []
        summary = str(profile.get("summary", "")).strip()

        job_text = job if isinstance(job, str) else " ".join(
            str(value)
            for value in [
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                job.get("description", ""),
            ]
            if value
        )
        job_text = job_text.lower()

        matched_skills = [skill for skill in skills if skill.lower() in job_text]
        if not matched_skills:
            matched_skills = skills[: min(4, len(skills))]

        ordered_projects = []
        for project in projects:
            if not isinstance(project, dict):
                continue
            match_score = 0
            project_text = " ".join(str(value).lower() for value in project.values())
            for skill in matched_skills:
                if skill.lower() in project_text:
                    match_score += 1
            ordered_projects.append({"project": project, "score": match_score})

        ordered_projects.sort(key=lambda item: item["score"], reverse=True)
        selected_projects = [entry["project"] for entry in ordered_projects]

        resume = TailoredResume(
            summary=summary,
            skills=matched_skills,
            projects=[
                {
                    "name": str(project.get("name", "")),
                    "description": str(project.get("description", "")),
                }
                for project in selected_projects
                if isinstance(project, dict)
            ],
            certifications=list(profile.get("certifications", []) or []),
        )

        invalid_claims = validate_claims(self._flatten_resume(resume), self.master_profile)
        if invalid_claims:
            raise GuardrailViolation(f"Generated resume contains claims outside the profile: {invalid_claims}")

        return resume

    def _flatten_resume(self, resume: TailoredResume) -> list[str]:
        values: list[str] = [resume.summary]
        values.extend(resume.skills)
        for project in resume.projects:
            values.append(project.get("name", ""))
            values.append(project.get("description", ""))
        values.extend(resume.certifications)
        return [value for value in values if value]

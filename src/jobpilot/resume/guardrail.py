from __future__ import annotations

from collections.abc import Iterable


class GuardrailViolation(ValueError):
    """Raised when a generated artifact includes claims not grounded in the master profile."""


def _normalize(value: str) -> str:
    return value.casefold().strip()


def validate_claims(claims: Iterable[str], master_profile: dict) -> list[str]:
    """Check candidate claims against the source-of-truth profile and return invalid claims."""

    profile = master_profile.get("candidate", master_profile)
    profile_values: set[str] = set()

    for key in ["skills", "certifications", "summary"]:
        section = profile.get(key, [])
        if isinstance(section, list):
            profile_values.update(_normalize(item) for item in section)
        elif isinstance(section, str):
            profile_values.add(_normalize(section))

    for project in profile.get("projects", []):
        if isinstance(project, dict):
            profile_values.add(_normalize(str(project.get("name", ""))))
            profile_values.add(_normalize(str(project.get("description", ""))))

    invalid: list[str] = []
    for claim in claims:
        normalized = _normalize(str(claim))
        if not normalized:
            continue
        if normalized not in profile_values and not any(token in profile_values for token in normalized.split() if len(token) > 3):
            invalid.append(claim)

    return invalid

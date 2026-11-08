from __future__ import annotations

from pathlib import Path

from .tailor import TailoredResume


def render_resume(resume: TailoredResume, output_path: str | Path) -> Path:
    """Render a tailored resume to a plain-text fallback file if a PDF renderer is unavailable."""

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "Tailored resume",
        "==============",
        "",
        "Summary:",
        resume.summary,
        "",
        "Skills:",
        *[f"- {skill}" for skill in resume.skills],
        "",
        "Projects:",
    ]

    for project in resume.projects:
        lines.append(f"- {project.get('name', '')}: {project.get('description', '')}")

    lines.extend(["", "Certifications:"])
    if resume.certifications:
        lines.extend(f"- {item}" for item in resume.certifications)
    else:
        lines.append("- None listed")

    destination.write_text("\n".join(lines), encoding="utf-8")
    return destination

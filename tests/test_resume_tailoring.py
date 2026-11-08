from __future__ import annotations

from jobpilot.resume.guardrail import validate_claims
from jobpilot.resume.tailor import TailorService


PROFILE = {
    "candidate": {
        "summary": "Security-focused engineering graduate with hands-on experience in networking, Linux, Python, and cybersecurity tooling.",
        "skills": ["Python", "Linux", "Wireshark", "Nmap", "Burp Suite", "SQL", "CI/CD", "Git"],
        "projects": [
            {
                "name": "Home Lab Hardening",
                "description": "Set up a homelab with pfSense, IDS monitoring, and log analysis to learn incident response workflows.",
            },
            {
                "name": "Network Enumeration Toolkit",
                "description": "Built a Python-based toolkit to scan hosts and summarize open ports and services.",
            },
        ],
        "certifications": [],
    }
}


def test_tailor_service_uses_profile_facts_only() -> None:
    service = TailorService(master_profile=PROFILE)
    job = {
        "title": "SOC Analyst",
        "company": "Acme Security",
        "location": "Bengaluru",
        "description": "Monitor SIEM, investigate incidents, and use Python and Linux for automation.",
    }

    resume = service.tailor(job)

    assert resume.summary == PROFILE["candidate"]["summary"]
    assert "Python" in resume.skills
    assert "Linux" in resume.skills
    assert any(project["name"] == "Home Lab Hardening" for project in resume.projects)


def test_guardrail_flags_claims_not_in_profile() -> None:
    invalid = validate_claims(["Python", "Rust"], PROFILE)

    assert invalid == ["Rust"]

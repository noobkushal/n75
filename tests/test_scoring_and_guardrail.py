from __future__ import annotations

from jobpilot.scoring import JobScore, parse_score_response
from jobpilot.resume.guardrail import validate_claims


def test_parse_score_response_validates_json_payload() -> None:
    payload = {
        "score": 88,
        "reasons": ["Strong Python and Linux fit", "Good security project match"],
        "missing_skills": ["Burp Suite"],
        "summary": "Strong match for a security-focused role.",
    }

    result = parse_score_response(payload)

    assert isinstance(result, JobScore)
    assert result.score == 88
    assert result.reasons[0].startswith("Strong")


def test_guardrail_rejects_out_of_profile_claims() -> None:
    profile = {
        "candidate": {
            "skills": ["Python", "Linux", "Wireshark"],
            "projects": [{"name": "Home Lab Hardening", "description": "Set up a homelab for incident response."}],
            "certifications": [],
        }
    }

    claims = ["Python", "Linux", "Rust", "Home Lab Hardening"]

    invalid = validate_claims(claims, profile)

    assert invalid == ["Rust"]

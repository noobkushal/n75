from __future__ import annotations

from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from pydantic import BaseModel, ConfigDict, Field

_yaml = YAML(typ="safe")


class LLMSettings(BaseModel):
    """Configuration for the selected LLM provider."""

    provider: str = "gemini"
    model: str = "gemini-2.0-flash"
    temperature: float = 0.2
    max_retries: int = 3


class DatabaseSettings(BaseModel):
    """Database configuration."""

    url: str = "sqlite:///jobpilot.db"


class JobSearchSettings(BaseModel):
    """Settings used during daily job discovery and scoring."""

    roles: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    location: str = "Bengaluru, India"
    min_score: int = 75
    max_jobs_per_run: int = 25


class Settings(BaseModel):
    """Top-level application configuration."""

    model_config = ConfigDict(extra="allow")

    jobs: JobSearchSettings = Field(default_factory=JobSearchSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)


def load_settings(config_path: str | Path = "config/settings.yaml") -> Settings:
    """Load the YAML configuration file into a validated Settings model."""

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = _yaml.load(handle) or {}

    return Settings.model_validate(data)


def load_master_profile(path: str | Path = "config/master_profile.yaml") -> dict[str, Any]:
    """Load the master profile used for scoring and resume tailoring."""

    profile_path = Path(path)
    if not profile_path.exists():
        raise FileNotFoundError(f"Master profile not found: {profile_path}")

    with profile_path.open("r", encoding="utf-8") as handle:
        data = _yaml.load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError("Master profile YAML must decode to a dictionary.")

    return data

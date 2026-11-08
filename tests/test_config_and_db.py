from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect
from typer.testing import CliRunner

from jobpilot.cli import app
from jobpilot.config import load_settings
from jobpilot.db import DatabaseManager


def test_settings_file_loads() -> None:
    config_path = Path(__file__).resolve().parents[1] / "config" / "settings.yaml"
    settings = load_settings(config_path)

    assert settings.jobs.roles == ["SOC Analyst", "Security Intern", "Pentest Intern"]
    assert settings.llm.provider == "gemini"
    assert settings.database.url == "sqlite:///jobpilot.db"


def test_database_manager_creates_tables(tmp_path) -> None:
    database_path = tmp_path / "jobpilot.db"
    manager = DatabaseManager(database_url=f"sqlite:///{database_path}")

    manager.init_db()

    tables = inspect(manager.engine).get_table_names()
    assert "jobs" in tables
    assert "contacts" in tables
    assert "startups" in tables


def test_cli_init_db() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["init-db"])

    assert result.exit_code == 0
    assert "Initialized database" in result.output

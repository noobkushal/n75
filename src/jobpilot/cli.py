from __future__ import annotations

from pathlib import Path

import typer

from .config import load_settings
from .db import DatabaseManager

app = typer.Typer(help="JobPilot job-search automation pipeline")


@app.command("init-db")
def init_db() -> None:
    """Initialize the local SQLite database schema."""

    manager = DatabaseManager()
    manager.init_db()
    typer.echo(f"Initialized database at {manager.database_url}")


@app.command("show-settings")
def show_settings(config_path: str = "config/settings.yaml") -> None:
    """Print the validated configuration from the YAML file."""

    settings = load_settings(config_path)
    typer.echo(settings.model_dump_json(indent=2))


@app.callback()
def main() -> None:
    """Command group entry point."""

    return None


if __name__ == "__main__":
    app()

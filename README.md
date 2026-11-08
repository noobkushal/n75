# JobPilot

JobPilot is a human-in-the-loop job hunting automation pipeline for Bengaluru roles. It is designed to discover jobs, score them against a master profile, generate tailored resume content, and draft outreach emails without auto-sending.

## Stage 1 and Stage 2 delivered

This repository now includes the project skeleton, configuration loader, database layer, and the public-job discovery flow with dedupe and SQLite persistence for the second build stage.

## Quick start

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
2. Install the package in editable mode:
   ```bash
   pip install -e .
   ```
3. Initialize the SQLite database:
   ```bash
   jobpilot init-db
   ```
4. Run the test suite:
   ```bash
   pytest
   ```

## Project layout

```text
jobpilot/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
├── config/
│   ├── master_profile.yaml
│   ├── settings.yaml
│   └── prompts/
├── src/jobpilot/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   └── db.py
└── tests/
    └── test_config_and_db.py
```

## Notes

- The default database is SQLite and is configured via `JOBPILOT_DB_URL` or the YAML settings file.
- The CLI intentionally focuses on initialization and configuration validation at this stage.
- More job discovery and scoring logic will be added in later stages.

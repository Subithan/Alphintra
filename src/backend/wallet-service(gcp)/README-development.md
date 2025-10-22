# Wallet Service Development Guide

## Prerequisites
- Python 3.11+
- Local PostgreSQL instance or Docker container
- Virtual environment tooling (`venv`, `pipenv`, or `poetry`)

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Locally
```bash
uvicorn main:app --reload --port 8000
```

## Testing
- Add test cases under `tests/` (create the directory if it does not exist).
- Use `pytest` for unit tests and `httpx` for API integration tests.
- Example command: `pytest --maxfail=1 --disable-warnings -q`

## Coding Standards
- Follow PEP 8 style guidelines.
- Run `ruff` or `flake8` before opening a pull request.
- Keep functions small and focused; add docstrings for public functions.

For database configuration specifics, see `README-database.md`.

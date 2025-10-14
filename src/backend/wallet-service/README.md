# Wallet Service

This service exposes wallet-related APIs for the Alphintra platform. It handles wallet creation, balance retrieval, and transaction processing using FastAPI.

## Highlights
- FastAPI application defined in `main.py`
- SQLAlchemy models for wallets and transactions in `models.py`
- Database initialization helpers in `init_database.py`
- Dependency versions tracked in `requirements.txt`

## Getting Started
1. Create a virtual environment and install dependencies with `pip install -r requirements.txt`.
2. Set the required database environment variables (see `README-database.md`).
3. Run the service locally with `uvicorn main:app --reload`.
4. Explore the interactive docs at `http://localhost:8000/docs`.

For development workflows and testing guidance, refer to `README-development.md`.

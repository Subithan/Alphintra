# Wallet Service Database Notes

## Schema Overview
- `wallets`: stores user wallet metadata and balances.
- `transactions`: records credits, debits, and references to source systems.
- All timestamps are stored in UTC.

## Environment Variables
Set these variables before starting the service:
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`

Example `.env` snippet:
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=alphintra_wallet
DB_USER=wallet_user
DB_PASSWORD=change_me
```

## Database Migrations
- Use Alembic for migrations; initialize with `alembic init migrations`.
- Generate new migrations via `alembic revision --autogenerate -m "Describe change"`.
- Apply migrations using `alembic upgrade head`.

## Local Development Tips
- Run PostgreSQL via Docker: `docker run --name wallet-db -e POSTGRES_PASSWORD=change_me -p 5432:5432 -d postgres:15`.
- Use `init_database.py` to seed essential data for manual testing.

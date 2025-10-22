# Wallet Service

This service exposes wallet-related APIs for the Alphintra platform. It handles wallet creation, balance retrieval, and transaction processing using FastAPI.

## Highlights
- FastAPI application defined in `main.py`
- SQLAlchemy models for wallets and transactions in `models.py`
- Database initialization helpers in `init_database.py`
- Dependency versions tracked in `requirements.txt`

## Coinbase Trading Endpoints

Authenticated Coinbase requests reuse the shared SQLAlchemy session helpers so the
service automatically fetches stored API credentials, tracks `last_used_at`, and
records error details on failures. The following routes are now available:

| Method | Route | Description |
| ------ | ----- | ----------- |
| `POST` | `/coinbase/buy` | Submit a market buy (long) order. Body accepts `symbol`, `size`, optional `type`, price overrides, `clientOrderId`, and optional `takeProfit`/`stopLoss` trigger metadata. |
| `POST` | `/coinbase/sell` | Submit a market sell (short) order with the same payload schema as `/coinbase/buy`. |
| `POST` | `/coinbase/open-order` | Place limit/stop orders with take-profit and stop-loss metadata. Requires a `side` (`buy`/`sell`) and a price. |
| `GET` | `/coinbase/positions` | Return normalized open positions (or open orders when positions are unavailable) including order IDs, filled quantity, average price, and any persisted TP/SL metadata. |
| `GET` | `/coinbase/history` | Retrieve normalized trade history with order IDs, fills, pricing, and TP/SL metadata for persistence. |

Every response includes `orderId`, `filledQuantity`, `averagePrice`, and
take-profit/stop-loss fields so downstream trading components can persist the
orders without additional normalization.

## Getting Started
1. Create a virtual environment and install dependencies with `pip install -r requirements.txt`.
2. Set the required database environment variables (see `README-database.md`).
3. Run the service locally with `uvicorn main:app --reload`.
4. Explore the interactive docs at `http://localhost:8000/docs`.

For development workflows and testing guidance, refer to `README-development.md`.

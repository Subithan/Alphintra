"""Trading engine proxy used for live execution environments."""

import json
import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional

import aiohttp

from app.core.config import get_settings


@dataclass
class BrokerPosition:
    """Standardized position representation returned by the trading engine."""

    symbol: str
    quantity: Decimal
    side: str
    avg_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal


@dataclass
class BrokerAccount:
    """Standardized account representation returned by the trading engine."""

    account_id: str
    account_type: str
    buying_power: Decimal
    cash_balance: Decimal
    equity: Decimal
    day_trade_buying_power: Optional[Decimal] = None
    maintenance_margin: Optional[Decimal] = None


class TradingEngineServiceClient:
    """Thin async client that proxies requests to the trading engine service."""

    def __init__(self) -> None:
        self._logger = logging.getLogger(__name__)
        self._base_url = get_settings().TRADING_ENGINE_URL.rstrip("/")
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        session = await self._get_session()
        url = f"{self._base_url}{path}"
        self._logger.debug("Trading engine request", extra={"method": method, "url": url})
        async with session.request(method, url, **kwargs) as response:
            text = await response.text()
            if response.status >= 400:
                self._logger.error(
                    "Trading engine request failed",
                    extra={"method": method, "url": url, "status": response.status, "body": text},
                )
                raise RuntimeError(f"Trading engine request failed ({response.status}): {text}")

            if not text:
                return None

            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text

    @staticmethod
    def _to_decimal(value: Any) -> Decimal:
        if value is None:
            return Decimal("0")
        return Decimal(str(value))

    async def initialize_environment(self, environment_id: int) -> bool:
        """Ensure that the trading engine has an active session for the environment."""

        data = await self._request("POST", f"/api/trading/environments/{environment_id}/connect")
        if isinstance(data, dict):
            return bool(data.get("success", data.get("connected", True)))
        return True

    async def disconnect_environment(self, environment_id: int) -> bool:
        """Tear down any active session for the environment in the trading engine."""

        data = await self._request("POST", f"/api/trading/environments/{environment_id}/disconnect")
        if isinstance(data, dict):
            return bool(data.get("success", data.get("disconnected", True)))
        return True

    async def test_connection(self, environment_id: int) -> Dict[str, Any]:
        """Fetch connection status for the environment."""

        data = await self._request("GET", f"/api/trading/environments/{environment_id}/status")
        if isinstance(data, dict):
            return data
        return {"environment_id": environment_id, "status": data}

    async def get_positions(self, environment_id: int) -> List[BrokerPosition]:
        """Retrieve open positions from the trading engine."""

        data = await self._request("GET", f"/api/trading/environments/{environment_id}/positions") or {}
        items = data.get("positions", data if isinstance(data, list) else [])
        positions: List[BrokerPosition] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            positions.append(
                BrokerPosition(
                    symbol=item.get("symbol", ""),
                    quantity=self._to_decimal(item.get("quantity", 0)),
                    side=item.get("side", "flat"),
                    avg_price=self._to_decimal(item.get("avg_price", 0)),
                    market_value=self._to_decimal(item.get("market_value", 0)),
                    unrealized_pnl=self._to_decimal(item.get("unrealized_pnl", 0)),
                    unrealized_pnl_pct=self._to_decimal(item.get("unrealized_pnl_pct", 0)),
                )
            )
        return positions

    async def get_account_info(self, environment_id: int) -> Optional[BrokerAccount]:
        """Retrieve account balances and limits from the trading engine."""

        data = await self._request("GET", f"/api/trading/environments/{environment_id}/account")
        if not isinstance(data, dict):
            return None

        return BrokerAccount(
            account_id=str(data.get("account_id", "")),
            account_type=data.get("account_type", "unknown"),
            buying_power=self._to_decimal(data.get("buying_power", 0)),
            cash_balance=self._to_decimal(data.get("cash_balance", 0)),
            equity=self._to_decimal(data.get("equity", 0)),
            day_trade_buying_power=
                self._to_decimal(data.get("day_trade_buying_power")) if data.get("day_trade_buying_power") is not None else None,
            maintenance_margin=
                self._to_decimal(data.get("maintenance_margin")) if data.get("maintenance_margin") is not None else None,
        )

    async def cleanup(self) -> None:
        """Close the underlying HTTP session."""

        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None


# Global client instance used by the application
trading_engine_client = TradingEngineServiceClient()

# Backwards compatibility export
broker_integration_service = trading_engine_client


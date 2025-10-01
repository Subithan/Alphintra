"""Tests for live execution endpoints interacting with the trading engine boundary."""

from decimal import Decimal
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from main import app
from app.services.broker_integration import BrokerAccount, BrokerPosition

client = TestClient(app)


@patch("app.api.endpoints.live_execution.trading_engine_client")
def test_get_broker_status(mock_client):
    mock_client.test_connection = AsyncMock(return_value={"connected": True})

    response = client.get("/api/live-execution/environments/1/broker/status")

    assert response.status_code == 200
    assert response.json()["connected"] is True
    mock_client.test_connection.assert_awaited_once_with(1)


@patch("app.api.endpoints.live_execution.trading_engine_client")
def test_connect_broker(mock_client):
    mock_client.initialize_environment = AsyncMock(return_value=True)

    response = client.post("/api/live-execution/environments/1/broker/connect")

    assert response.status_code == 200
    assert "Connected to broker" in response.json()["message"]
    mock_client.initialize_environment.assert_awaited_once_with(1)


@patch("app.api.endpoints.live_execution.trading_engine_client")
def test_disconnect_broker(mock_client):
    mock_client.disconnect_environment = AsyncMock(return_value=True)

    response = client.post("/api/live-execution/environments/1/broker/disconnect")

    assert response.status_code == 200
    assert "Disconnected from broker" in response.json()["message"]
    mock_client.disconnect_environment.assert_awaited_once_with(1)


@patch("app.api.endpoints.live_execution.trading_engine_client")
def test_get_broker_positions(mock_client):
    mock_client.get_positions = AsyncMock(
        return_value=[
            BrokerPosition(
                symbol="AAPL",
                quantity=Decimal("10"),
                side="long",
                avg_price=Decimal("150"),
                market_value=Decimal("1500"),
                unrealized_pnl=Decimal("100"),
                unrealized_pnl_pct=Decimal("0.07"),
            )
        ]
    )

    response = client.get("/api/live-execution/environments/1/broker/positions")

    assert response.status_code == 200
    body = response.json()
    assert body["environment_id"] == 1
    assert len(body["positions"]) == 1
    assert body["positions"][0]["symbol"] == "AAPL"
    mock_client.get_positions.assert_awaited_once_with(1)


@patch("app.api.endpoints.live_execution.trading_engine_client")
def test_get_broker_account(mock_client):
    mock_client.get_account_info = AsyncMock(
        return_value=BrokerAccount(
            account_id="acct-123",
            account_type="margin",
            buying_power=Decimal("100000"),
            cash_balance=Decimal("50000"),
            equity=Decimal("120000"),
            day_trade_buying_power=Decimal("80000"),
            maintenance_margin=Decimal("20000"),
        )
    )

    response = client.get("/api/live-execution/environments/1/broker/account")

    assert response.status_code == 200
    body = response.json()
    assert body["environment_id"] == 1
    assert body["account_id"] == "acct-123"
    assert body["buying_power"] == 100000.0
    mock_client.get_account_info.assert_awaited_once_with(1)


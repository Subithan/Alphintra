"""
Broker integration service for live trading.
"""

import asyncio
import logging
import json
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

import aiohttp
import websockets
from sqlalchemy.orm import Session

from app.models.execution import ExecutionEnvironment, ExecutionOrder
from app.database.connection import get_db_session


class BrokerType(Enum):
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "interactive_brokers"
    TD_AMERITRADE = "td_ameritrade"
    SCHWAB = "schwab"
    ROBINHOOD = "robinhood"
    BINANCE = "binance"
    COINBASE = "coinbase"


@dataclass
class BrokerOrder:
    """Standardized broker order representation."""
    broker_order_id: str
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    status: str = "pending"
    filled_quantity: Decimal = Decimal("0")
    avg_fill_price: Optional[Decimal] = None
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    commission: Decimal = Decimal("0")
    error_message: Optional[str] = None


@dataclass
class BrokerPosition:
    """Standardized broker position representation."""
    symbol: str
    quantity: Decimal
    side: str
    avg_price: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_pct: Decimal


@dataclass
class BrokerAccount:
    """Standardized broker account representation."""
    account_id: str
    account_type: str
    buying_power: Decimal
    cash_balance: Decimal
    equity: Decimal
    day_trade_buying_power: Optional[Decimal] = None
    maintenance_margin: Optional[Decimal] = None


class BaseBrokerConnector(ABC):
    """Abstract base class for broker connectors."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_connected = False
        self.session: Optional[aiohttp.ClientSession] = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to broker API."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from broker API."""
        pass
    
    @abstractmethod
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        """Submit an order to the broker."""
        pass
    
    @abstractmethod
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrder]:
        """Get order status."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[BrokerPosition]:
        """Get current positions."""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> BrokerAccount:
        """Get account information."""
        pass
    
    @abstractmethod
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current market price for symbol."""
        pass


class AlpacaBrokerConnector(BaseBrokerConnector):
    """Alpaca broker connector."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.secret_key = config.get("secret_key")
        self.base_url = config.get("base_url", "https://paper-api.alpaca.markets")
        self.data_url = config.get("data_url", "https://data.alpaca.markets")
        
    async def connect(self) -> bool:
        """Connect to Alpaca API."""
        
        try:
            if not self.api_key or not self.secret_key:
                raise ValueError("API key and secret key required")
            
            # Create HTTP session
            headers = {
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Content-Type": "application/json"
            }
            
            self.session = aiohttp.ClientSession(headers=headers)
            
            # Test connection by getting account info
            async with self.session.get(f"{self.base_url}/v2/account") as response:
                if response.status == 200:
                    self.is_connected = True
                    self.logger.info("Connected to Alpaca API")
                    return True
                else:
                    raise Exception(f"Failed to connect: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error connecting to Alpaca: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Disconnect from Alpaca API."""
        
        if self.session:
            await self.session.close()
            self.session = None
        
        self.is_connected = False
        self.logger.info("Disconnected from Alpaca API")
        return True
    
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        """Submit order to Alpaca."""
        
        if not self.is_connected or not self.session:
            raise Exception("Not connected to broker")
        
        try:
            # Prepare order data
            order_data = {
                "symbol": order.symbol,
                "qty": str(order.quantity),
                "side": order.side,
                "type": order.order_type,
                "time_in_force": "day"
            }
            
            if order.price:
                order_data["limit_price"] = str(order.price)
            if order.stop_price:
                order_data["stop_price"] = str(order.stop_price)
            
            # Submit order
            async with self.session.post(
                f"{self.base_url}/v2/orders",
                json=order_data
            ) as response:
                
                if response.status == 201:
                    result = await response.json()
                    
                    # Update order with broker response
                    order.broker_order_id = result["id"]
                    order.status = result["status"]
                    order.submitted_at = datetime.fromisoformat(result["created_at"].replace('Z', '+00:00'))
                    
                    return order
                else:
                    error_text = await response.text()
                    raise Exception(f"Order submission failed: {response.status} - {error_text}")
                    
        except Exception as e:
            order.status = "rejected"
            order.error_message = str(e)
            self.logger.error(f"Error submitting Alpaca order: {e}")
            return order
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        """Cancel Alpaca order."""
        
        if not self.is_connected or not self.session:
            return False
        
        try:
            async with self.session.delete(
                f"{self.base_url}/v2/orders/{broker_order_id}"
            ) as response:
                return response.status == 204
                
        except Exception as e:
            self.logger.error(f"Error cancelling Alpaca order: {e}")
            return False
    
    async def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrder]:
        """Get Alpaca order status."""
        
        if not self.is_connected or not self.session:
            return None
        
        try:
            async with self.session.get(
                f"{self.base_url}/v2/orders/{broker_order_id}"
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    return BrokerOrder(
                        broker_order_id=result["id"],
                        symbol=result["symbol"],
                        side=result["side"],
                        order_type=result["type"],
                        quantity=Decimal(result["qty"]),
                        price=Decimal(result["limit_price"]) if result.get("limit_price") else None,
                        stop_price=Decimal(result["stop_price"]) if result.get("stop_price") else None,
                        status=result["status"],
                        filled_quantity=Decimal(result["filled_qty"]),
                        avg_fill_price=Decimal(result["filled_avg_price"]) if result.get("filled_avg_price") else None,
                        submitted_at=datetime.fromisoformat(result["created_at"].replace('Z', '+00:00')),
                        filled_at=datetime.fromisoformat(result["filled_at"].replace('Z', '+00:00')) if result.get("filled_at") else None
                    )
                    
        except Exception as e:
            self.logger.error(f"Error getting Alpaca order status: {e}")
            return None
    
    async def get_positions(self) -> List[BrokerPosition]:
        """Get Alpaca positions."""
        
        if not self.is_connected or not self.session:
            return []
        
        try:
            async with self.session.get(f"{self.base_url}/v2/positions") as response:
                if response.status == 200:
                    results = await response.json()
                    
                    positions = []
                    for pos in results:
                        positions.append(BrokerPosition(
                            symbol=pos["symbol"],
                            quantity=Decimal(pos["qty"]),
                            side="long" if Decimal(pos["qty"]) > 0 else "short",
                            avg_price=Decimal(pos["avg_cost"]),
                            market_value=Decimal(pos["market_value"]),
                            unrealized_pnl=Decimal(pos["unrealized_pl"]),
                            unrealized_pnl_pct=Decimal(pos["unrealized_plpc"]) * 100
                        ))
                    
                    return positions
                    
        except Exception as e:
            self.logger.error(f"Error getting Alpaca positions: {e}")
            return []
    
    async def get_account_info(self) -> BrokerAccount:
        """Get Alpaca account information."""
        
        if not self.is_connected or not self.session:
            raise Exception("Not connected to broker")
        
        try:
            async with self.session.get(f"{self.base_url}/v2/account") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    return BrokerAccount(
                        account_id=result["id"],
                        account_type=result["status"],
                        buying_power=Decimal(result["buying_power"]),
                        cash_balance=Decimal(result["cash"]),
                        equity=Decimal(result["equity"]),
                        day_trade_buying_power=Decimal(result["daytrading_buying_power"]),
                        maintenance_margin=Decimal(result["maintenance_margin"])
                    )
                else:
                    raise Exception(f"Failed to get account info: {response.status}")
                    
        except Exception as e:
            self.logger.error(f"Error getting Alpaca account info: {e}")
            raise
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        """Get current price from Alpaca."""
        
        if not self.is_connected or not self.session:
            return None
        
        try:
            async with self.session.get(
                f"{self.data_url}/v2/stocks/{symbol}/quotes/latest"
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    quote = result["quote"]
                    # Use mid-point of bid-ask spread
                    bid = Decimal(quote["bp"])
                    ask = Decimal(quote["ap"])
                    return (bid + ask) / 2
                    
        except Exception as e:
            self.logger.error(f"Error getting Alpaca price for {symbol}: {e}")
            return None


class InteractiveBrokerConnector(BaseBrokerConnector):
    """Interactive Brokers connector (placeholder)."""
    
    async def connect(self) -> bool:
        """Connect to IB API."""
        # TODO: Implement IB API integration
        self.logger.warning("Interactive Brokers integration not yet implemented")
        return False
    
    async def disconnect(self) -> bool:
        return True
    
    async def submit_order(self, order: BrokerOrder) -> BrokerOrder:
        order.status = "rejected"
        order.error_message = "Interactive Brokers not implemented"
        return order
    
    async def cancel_order(self, broker_order_id: str) -> bool:
        return False
    
    async def get_order_status(self, broker_order_id: str) -> Optional[BrokerOrder]:
        return None
    
    async def get_positions(self) -> List[BrokerPosition]:
        return []
    
    async def get_account_info(self) -> BrokerAccount:
        raise Exception("Interactive Brokers not implemented")
    
    async def get_current_price(self, symbol: str) -> Optional[Decimal]:
        return None


class BrokerIntegrationService:
    """Service to manage broker integrations."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connectors: Dict[int, BaseBrokerConnector] = {}
        
        # Broker connector classes
        self.connector_classes = {
            BrokerType.ALPACA: AlpacaBrokerConnector,
            BrokerType.INTERACTIVE_BROKERS: InteractiveBrokerConnector,
            # Add more brokers as they are implemented
        }
    
    async def initialize_environment(self, environment_id: int) -> bool:
        """Initialize broker connection for an execution environment."""
        
        try:
            with get_db_session() as db:
                environment = db.query(ExecutionEnvironment).filter(
                    ExecutionEnvironment.id == environment_id
                ).first()
                
                if not environment:
                    raise ValueError(f"Environment {environment_id} not found")
                
                # Get broker type
                broker_name = environment.broker_name.lower()
                
                # Find matching broker type
                broker_type = None
                for bt in BrokerType:
                    if bt.value == broker_name:
                        broker_type = bt
                        break
                
                if not broker_type:
                    raise ValueError(f"Unsupported broker: {broker_name}")
                
                # Get connector class
                connector_class = self.connector_classes.get(broker_type)
                if not connector_class:
                    raise ValueError(f"No connector available for {broker_name}")
                
                # Create and configure connector
                connector = connector_class(environment.broker_config)
                
                # Connect to broker
                success = await connector.connect()
                if success:
                    self.connectors[environment_id] = connector
                    self.logger.info(f"Initialized broker connection for environment {environment_id}")
                    return True
                else:
                    raise Exception("Failed to connect to broker")
                    
        except Exception as e:
            self.logger.error(f"Error initializing broker for environment {environment_id}: {e}")
            return False
    
    async def disconnect_environment(self, environment_id: int) -> bool:
        """Disconnect broker for an execution environment."""
        
        try:
            if environment_id in self.connectors:
                connector = self.connectors[environment_id]
                await connector.disconnect()
                del self.connectors[environment_id]
                self.logger.info(f"Disconnected broker for environment {environment_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error disconnecting broker for environment {environment_id}: {e}")
            return False
    
    async def submit_order(self, environment_id: int, order: BrokerOrder) -> BrokerOrder:
        """Submit order through broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            order.status = "rejected"
            order.error_message = "Broker not connected"
            return order
        
        return await connector.submit_order(order)
    
    async def cancel_order(self, environment_id: int, broker_order_id: str) -> bool:
        """Cancel order through broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return False
        
        return await connector.cancel_order(broker_order_id)
    
    async def get_order_status(self, environment_id: int, broker_order_id: str) -> Optional[BrokerOrder]:
        """Get order status from broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return None
        
        return await connector.get_order_status(broker_order_id)
    
    async def get_positions(self, environment_id: int) -> List[BrokerPosition]:
        """Get positions from broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return []
        
        return await connector.get_positions()
    
    async def get_account_info(self, environment_id: int) -> Optional[BrokerAccount]:
        """Get account information from broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return None
        
        try:
            return await connector.get_account_info()
        except Exception as e:
            self.logger.error(f"Error getting account info: {e}")
            return None
    
    async def get_current_price(self, environment_id: int, symbol: str) -> Optional[Decimal]:
        """Get current price from broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return None
        
        return await connector.get_current_price(symbol)
    
    async def sync_orders(self, environment_id: int) -> List[BrokerOrder]:
        """Sync orders with broker to get latest status."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return []
        
        try:
            # Get all pending orders from database
            with get_db_session() as db:
                # Find execution using this environment
                from app.models.execution import StrategyExecution
                executions = db.query(StrategyExecution).filter(
                    StrategyExecution.environment_id == environment_id
                ).all()
                
                updated_orders = []
                
                for execution in executions:
                    pending_orders = db.query(ExecutionOrder).filter(
                        and_(
                            ExecutionOrder.strategy_execution_id == execution.id,
                            ExecutionOrder.status.in_(["pending", "partially_filled"])
                        )
                    ).all()
                    
                    for order in pending_orders:
                        if order.broker_order_id:
                            # Get updated status from broker
                            broker_order = await connector.get_order_status(order.broker_order_id)
                            if broker_order:
                                updated_orders.append(broker_order)
                
                return updated_orders
                
        except Exception as e:
            self.logger.error(f"Error syncing orders: {e}")
            return []
    
    async def sync_positions(self, environment_id: int) -> List[BrokerPosition]:
        """Sync positions with broker."""
        
        connector = self.connectors.get(environment_id)
        if not connector:
            return []
        
        return await connector.get_positions()
    
    def is_connected(self, environment_id: int) -> bool:
        """Check if broker is connected for environment."""
        
        connector = self.connectors.get(environment_id)
        return connector is not None and connector.is_connected
    
    async def test_connection(self, environment_id: int) -> Dict[str, Any]:
        """Test broker connection and return status."""
        
        try:
            connector = self.connectors.get(environment_id)
            if not connector:
                return {
                    "connected": False,
                    "error": "No connector found"
                }
            
            # Test by getting account info
            account = await connector.get_account_info()
            
            return {
                "connected": True,
                "account_id": account.account_id,
                "account_type": account.account_type,
                "buying_power": float(account.buying_power),
                "cash_balance": float(account.cash_balance),
                "equity": float(account.equity)
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e)
            }
    
    async def cleanup(self) -> None:
        """Cleanup all broker connections."""
        
        for environment_id in list(self.connectors.keys()):
            await self.disconnect_environment(environment_id)
        
        self.logger.info("Broker integration service cleaned up")


# Global broker integration service instance
broker_integration_service = BrokerIntegrationService()
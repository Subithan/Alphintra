from __future__ import annotations

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import ccxt.async_support as ccxt
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from database import get_db, create_tables, engine
from models import User, WalletConnection
from ccxt.base.errors import AuthenticationError, RequestTimeout, ExchangeNotAvailable, NetworkError, DDoSProtection, RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(title="Alphintra Wallet Service", version="1.0.0")

#
# Lightweight diagnostic helpers used as dummy placeholders to keep room for future flags.
#
DUMMY_FEATURE_FLAGS: Dict[str, bool] = {
    "wallet_service_experimental_mode": False,
    "wallet_service_metrics_probe": False,
}


def noop_feature_probe(feature_name: str) -> bool:
    """Return the state of a dummy feature flag for future experiments."""
    logger.debug("noop_feature_probe called for feature=%s", feature_name)
    return DUMMY_FEATURE_FLAGS.get(feature_name, False)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _safe_float(value: Any) -> Optional[float]:
    """Convert a value to float if possible, otherwise return None."""
    try:
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _read_key(value: Any) -> str:
    """Normalize stored credential values from the database."""
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode()
        except Exception:
            return str(value)
    return str(value)


def _normalize_coinbase_symbol(symbol: str) -> str:
    """Normalize Coinbase symbols to the CCXT expected format (e.g. BTC/USD)."""
    if not symbol:
        return symbol
    symbol = symbol.upper()
    if "-" in symbol:
        symbol = symbol.replace("-", "/")
    return symbol


def _stringify_amount(value: Optional[float]) -> str:
    """Return a compact string representation for numeric balance fields."""
    if value is None:
        return "0"
    # ``.15g`` avoids scientific notation for typical crypto balances.
    formatted = format(value, ".15g")
    # Guard against formatting edge-cases that yield an empty string.
    return formatted if formatted else "0"


def _extract_available_value(payload: Any) -> Optional[float]:
    """Handle the different shapes Coinbase may use for balance payloads."""
    if isinstance(payload, dict):
        return _safe_float(payload.get("value"))
    return _safe_float(payload)


def _normalize_balances(balance_data: Any) -> List[Dict[str, str]]:
    """Normalize CCXT balance payloads into a consistent API response."""
    if not isinstance(balance_data, dict):
        return []

    totals = balance_data.get("total") or {}
    free = balance_data.get("free") or {}
    used = balance_data.get("used") or {}

    normalized: List[Dict[str, str]] = []
    for asset, total_amount in totals.items():
        total_value = _safe_float(total_amount)
        if total_value is None or total_value <= 0:
            continue
        normalized.append(
            {
                "asset": str(asset),
                "free": _stringify_amount(_safe_float(free.get(asset))),
                "locked": _stringify_amount(_safe_float(used.get(asset))),
            }
        )

    if normalized:
        return normalized

    # Fallback: inspect the raw payload returned by Coinbase Advanced Trade.
    raw_info = balance_data.get("info")
    accounts: List[Any] = []
    if isinstance(raw_info, dict):
        accounts = raw_info.get("accounts") or raw_info.get("data") or raw_info.get("balances") or []
    elif isinstance(raw_info, list):
        accounts = raw_info

    if not accounts and isinstance(balance_data.get("data"), list):
        accounts = balance_data["data"]

    for account in accounts:
        if not isinstance(account, dict):
            continue

        asset = (
            account.get("currency")
            or account.get("currency_code")
            or account.get("asset")
        )
        if not asset:
            continue

        free_value = _extract_available_value(
            account.get("available_balance")
            or account.get("available")
        )

        total_value = _extract_available_value(account.get("balance"))
        if total_value is None:
            total_value = _safe_float(account.get("value") or account.get("total"))

        locked_value = _extract_available_value(account.get("hold"))

        if total_value is None and free_value is not None and locked_value is not None:
            total_value = free_value + locked_value

        if locked_value is None and total_value is not None and free_value is not None:
            locked_value = max(total_value - free_value, 0.0)

        if total_value is None:
            total_value = free_value

        has_balance = any(
            (val is not None and val > 0)
            for val in (total_value, free_value, locked_value)
        )
        if not has_balance:
            continue

        normalized.append(
            {
                "asset": str(asset),
                "free": _stringify_amount(free_value),
                "locked": _stringify_amount(locked_value),
            }
        )

    return normalized


def _format_trigger(trigger: Optional[TriggerMetadata]) -> Optional[Dict[str, Any]]:
    if not trigger:
        return None
    data: Dict[str, Any] = {"price": _safe_float(trigger.price)}
    size = _safe_float(trigger.size)
    if size is not None:
        data["size"] = size
    return data


def _ensure_trigger(trigger: Optional[Any]) -> Optional[TriggerMetadata]:
    if trigger is None:
        return None
    if isinstance(trigger, TriggerMetadata):
        return trigger
    if isinstance(trigger, dict):
        price = _safe_float(trigger.get("price") or trigger.get("triggerPrice") or trigger.get("stopPrice"))
        if price is None:
            return None
        size = _safe_float(trigger.get("size") or trigger.get("amount"))
        return TriggerMetadata(price=price, size=size)
    price = _safe_float(trigger)
    if price is None:
        return None
    return TriggerMetadata(price=price)


def _extract_trigger(order: Dict[str, Any], key: str) -> Optional[Any]:
    value = order.get(key)
    if value is not None:
        return value
    info = order.get("info")
    if isinstance(info, dict):
        return (
            info.get(key)
            or info.get(key.lower())
            or info.get(key.upper())
            or info.get(f"{key}_params")
        )
    return None


def _normalize_order_response(
    order: Dict[str, Any],
    *,
    take_profit: Optional[TriggerMetadata] = None,
    stop_loss: Optional[TriggerMetadata] = None,
) -> CoinbaseOrderResponse:
    response_payload = {
        "orderId": order.get("id")
        or order.get("orderId")
        or order.get("clientOrderId"),
        "clientOrderId": order.get("clientOrderId"),
        "status": order.get("status"),
        "symbol": order.get("symbol"),
        "side": order.get("side"),
        "type": order.get("type"),
        "filledQuantity": _safe_float(
            order.get("filled")
            or order.get("filledSize")
            or order.get("amount")
            or order.get("contracts")
        ),
        "remainingQuantity": _safe_float(order.get("remaining")),
        "averagePrice": _safe_float(order.get("average") or order.get("price")),
        "cost": _safe_float(order.get("cost")),
        "takeProfit": _ensure_trigger(take_profit),
        "stopLoss": _ensure_trigger(stop_loss),
        "timestamp": order.get("timestamp"),
        "datetime": order.get("datetime"),
        "raw": order,
    }
    return CoinbaseOrderResponse(**response_payload)


def _normalize_history_response(
    trade: Dict[str, Any],
    *,
    take_profit: Optional[TriggerMetadata] = None,
    stop_loss: Optional[TriggerMetadata] = None,
) -> CoinbaseHistoryResponse:
    response_payload = {
        "orderId": trade.get("order"),
        "tradeId": trade.get("id"),
        "symbol": trade.get("symbol"),
        "side": trade.get("side"),
        "filledQuantity": _safe_float(trade.get("amount")),
        "averagePrice": _safe_float(trade.get("price")),
        "fee": trade.get("fee"),
        "timestamp": trade.get("timestamp"),
        "datetime": trade.get("datetime"),
        "takeProfit": _ensure_trigger(take_profit),
        "stopLoss": _ensure_trigger(stop_loss),
        "raw": trade,
    }
    return CoinbaseHistoryResponse(**response_payload)


def _get_coinbase_connection(db: Session, user: User) -> WalletConnection:
    connection = (
        db.query(WalletConnection)
        .filter(
            WalletConnection.user_id == user.id,
            WalletConnection.exchange_name == "coinbase",
            WalletConnection.is_active == True,
            WalletConnection.connection_status == "connected",
        )
        .first()
    )
    if not connection:
        raise HTTPException(status_code=401, detail="Not connected to Coinbase")
    return connection


async def _create_coinbase_exchange(connection: WalletConnection):
    api_key = _read_key(connection.encrypted_api_key)
    private_key = _read_key(connection.encrypted_secret_key)
    exchange = ccxt.coinbase(
        {
            "apiKey": api_key,
            "secret": private_key,
            "enableRateLimit": True,
            "timeout": 60000,
            "options": {"fetchTime": True},
        }
    )
    await exchange.load_markets()
    return exchange


def _handle_coinbase_error(
    db: Session, connection: WalletConnection, error: Exception
) -> None:
    connection.connection_status = "error"
    connection.last_error = f"{type(error).__name__}: {error}"
    connection.last_used_at = func.now()
    db.commit()


def _coinbase_success(db: Session, connection: WalletConnection) -> None:
    connection.connection_status = "connected"
    connection.last_error = None
    connection.last_used_at = func.now()
    db.commit()


async def _submit_coinbase_order(
    db: Session,
    user: User,
    request: CoinbaseOrderBase,
    side: str,
    *,
    require_price: bool = False,
) -> CoinbaseOrderResponse:
    connection = _get_coinbase_connection(db, user)
    exchange = await _create_coinbase_exchange(connection)
    symbol = _normalize_coinbase_symbol(request.symbol)
    order_type = (request.type or ("limit" if require_price else "market")).lower()
    side = side.lower()

    if order_type in {"limit", "stop", "stop_limit", "stoploss", "takeprofit"} and request.price is None:
        await exchange.close()
        raise HTTPException(status_code=400, detail="Price is required for limit or stop orders")

    params = dict(request.extraParams or {})
    if request.clientOrderId:
        params.setdefault("clientOrderId", request.clientOrderId)

    amount = _safe_float(request.size)
    if amount is None or amount <= 0:
        await exchange.close()
        raise HTTPException(status_code=400, detail="Order size must be greater than zero")

    price = _safe_float(request.price) if request.price is not None else None

    try:
        order = await exchange.create_order(
            symbol,
            order_type,
            side,
            amount,
            price,
            params,
        )
        order_payload = dict(order)
        metadata = order_payload.setdefault("metadata", {})
        if request.takeProfit:
            metadata["takeProfit"] = _format_trigger(request.takeProfit)
        if request.stopLoss:
            metadata["stopLoss"] = _format_trigger(request.stopLoss)
        _coinbase_success(db, connection)
        return _normalize_order_response(
            order_payload,
            take_profit=request.takeProfit,
            stop_loss=request.stopLoss,
        )
    except AuthenticationError as auth_err:
        _handle_coinbase_error(db, connection, auth_err)
        raise HTTPException(
            status_code=401,
            detail="Authentication failed: check Coinbase API key/secret",
        ) from auth_err
    except (ExchangeNotAvailable, NetworkError) as net_err:
        _handle_coinbase_error(db, connection, net_err)
        raise HTTPException(
            status_code=503, detail="Coinbase exchange is not reachable right now"
        ) from net_err
    except RequestTimeout as timeout_err:
        _handle_coinbase_error(db, connection, timeout_err)
        raise HTTPException(status_code=504, detail="Timeout contacting Coinbase") from timeout_err
    except (DDoSProtection, RateLimitExceeded) as rl_err:
        _handle_coinbase_error(db, connection, rl_err)
        raise HTTPException(
            status_code=429,
            detail="Coinbase rate limit or DDoS protection triggered",
        ) from rl_err
    except Exception as error:
        _handle_coinbase_error(db, connection, error)
        raise HTTPException(
            status_code=500, detail=f"Failed to submit order to Coinbase: {error}"
        ) from error
    finally:
        try:
            await exchange.close()
        except Exception:
            pass
# Enable CORS for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database on service startup"""
    create_tables()
    print("✅ Database tables initialized")

# Add request logging middleware
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"DEBUG: Incoming request: {request.method} {request.url}")
    print(f"DEBUG: Request headers: {dict(request.headers)}")
    
    try:
        body = await request.body()
        body_text = body.decode(errors='ignore')
        if 'apiKey' in body_text or 'secretKey' in body_text:
            print("DEBUG: Request body: <masked>")
        else:
            print(f"DEBUG: Request body: {body_text}")
        # Make the body available to downstream handlers by overriding receive
        async def receive():
            return {"type": "http.request", "body": body}
        # attach overridden receive so FastAPI can read body again
        request._receive = receive
    except Exception as e:
        print(f"DEBUG: Could not read request body: {e}")
    
    response = await call_next(request)
    print(f"DEBUG: Response status: {response.status_code}")
    return response

# Pydantic models for request/response
class CredentialsResponse(BaseModel):
    apiKey: str
    secretKey: str

class ConnectRequest(BaseModel):
    apiKey: str
    privateKey: str

class Balance(BaseModel):
    asset: str
    free: str
    locked: str

class ConnectionResponse(BaseModel):
    connected: bool
    message: str = ""


class TriggerMetadata(BaseModel):
    price: float
    size: Optional[float] = None


class CoinbaseOrderBase(BaseModel):
    symbol: str = Field(..., description="Coinbase symbol such as BTC-USD or BTC/USD")
    size: float = Field(..., gt=0, description="Order quantity in base currency")
    type: str = Field("market", description="Order type: market, limit, stop, etc.")
    price: Optional[float] = Field(None, description="Limit/stop price when applicable")
    clientOrderId: Optional[str] = Field(
        None, description="Optional client order identifier for idempotency"
    )
    takeProfit: Optional[TriggerMetadata] = Field(
        None, description="Optional take profit configuration"
    )
    stopLoss: Optional[TriggerMetadata] = Field(
        None, description="Optional stop loss configuration"
    )
    extraParams: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional exchange-specific parameters to forward to Coinbase",
    )


class CoinbaseOrderRequest(CoinbaseOrderBase):
    """Request body for Coinbase market buy/sell endpoints."""


class CoinbaseOpenOrderRequest(CoinbaseOrderBase):
    side: str = Field(
        ..., pattern="^(?i)(buy|sell)$", description="Order side: buy for long, sell for short"
    )


class CoinbaseOrderResponse(BaseModel):
    orderId: Optional[str]
    clientOrderId: Optional[str] = None
    status: Optional[str] = None
    symbol: Optional[str] = None
    side: Optional[str] = None
    type: Optional[str] = None
    filledQuantity: Optional[float] = None
    remainingQuantity: Optional[float] = None
    averagePrice: Optional[float] = None
    cost: Optional[float] = None
    takeProfit: Optional[TriggerMetadata] = None
    stopLoss: Optional[TriggerMetadata] = None
    timestamp: Optional[int] = None
    datetime: Optional[str] = None
    raw: Dict[str, Any]


class CoinbaseHistoryResponse(BaseModel):
    orderId: Optional[str]
    tradeId: Optional[str]
    symbol: Optional[str]
    side: Optional[str]
    filledQuantity: Optional[float]
    averagePrice: Optional[float]
    fee: Optional[Dict[str, Any]] = None
    timestamp: Optional[int] = None
    datetime: Optional[str] = None
    takeProfit: Optional[TriggerMetadata] = None
    stopLoss: Optional[TriggerMetadata] = None
    raw: Dict[str, Any]

# Helper function to get or create test user
def get_current_user_from_db(db: Session) -> User:
    """Get current user (for now, returns test user - in production, get from JWT token)"""
    test_user = db.query(User).filter(User.email == "wallet_test@alphintra.com").first()
    
    if not test_user:
        # Create test user if doesn't exist
        test_user = User(
            email="wallet_test@alphintra.com",
            password_hash="test_hash",
            first_name="Wallet",
            last_name="Test",
            is_verified=True,
            is_active=True
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
    
    return test_user

@app.get("/")
async def root():
    print("DEBUG: Root endpoint called")
    return {"message": "Alphintra Wallet Service is running"}

@app.get("/health")
async def health_check():
    print("DEBUG: Health check called")
    return {"status": "healthy", "service": "wallet-service"}

@app.post("/binance/connect")
async def connect_to_binance(request: ConnectRequest, db: Session = Depends(get_db)):
    print("DEBUG: connect_to_binance function called successfully")
    print(f"DEBUG: Received request type: {type(request)}")
    
    try:
        print(f"DEBUG: API Key received: {request.apiKey[:10] if request.apiKey else 'None'}...")
        print(f"DEBUG: Secret Key length: {len(request.secretKey) if request.secretKey else 'No secret'}")
        
        # Validate inputs
        if not request.apiKey or not request.secretKey:
            print("DEBUG: Missing API key or secret key")
            raise HTTPException(status_code=400, detail="API Key and Secret Key are required")
        
        if len(request.apiKey) < 10 or len(request.secretKey) < 10:
            print("DEBUG: Keys too short")
            raise HTTPException(status_code=400, detail="API Key and Secret Key seem too short")
        
        # print("DEBUG: Getting current user...")
        # current_user = get_current_user_from_db(db)
        # print(f"DEBUG: Current user: {current_user.email}")

        current_user = get_current_user_from_db(db)
        
        # Check if connection already exists for this user
        existing_connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'binance',
            WalletConnection.is_active == True
        ).first()
        
        if existing_connection:
            print("DEBUG: Updating existing connection...")
            # Update existing connection
            # Store API/Secret as plain text (INSECURE — tokens will be stored unencrypted)
            existing_connection.encrypted_api_key = request.apiKey
            existing_connection.encrypted_secret_key = request.secretKey
            existing_connection.last_used_at = func.now()
            existing_connection.connection_status = 'connected'
            existing_connection.last_error = None
            connection = existing_connection
        else:
             print("DEBUG: Creating new connection...")
             # Create new connection
             connection = WalletConnection(
                 user_id=current_user.id,
                 exchange_name='binance',
                 exchange_environment='testnet',
                 # store plain text keys
                 encrypted_api_key=request.apiKey,
                 encrypted_secret_key=request.secretKey,
                 connection_name=f"Binance Connection ({datetime.now().strftime('%Y-%m-%d')})",
                 is_active=True,
                 connection_status='connected'
             )
       
        # Only add if it's a new connection
        if not existing_connection:
            db.add(connection)
        
        db.commit()
        db.refresh(connection)
        print(f"DEBUG: Connection stored successfully with ID: {connection.uuid}")
        
        return ConnectionResponse(
            connected=True,
            message="Successfully connected to Binance"
        )
        
    except HTTPException as he:
        print(f"DEBUG: HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/binance/connection-status")
async def get_connection_status(db: Session = Depends(get_db)):
    print("DEBUG: get_connection_status called")
    
    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Checking connection for user: {current_user.email}")
        
        # Look for active Binance connection
        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'binance',
            WalletConnection.is_active == True,
            WalletConnection.connection_status == 'connected'
        ).first()
        
        connected = connection is not None
        print(f"DEBUG: Connection status: {connected}")
        
        if connection:
            # Update last used timestamp
            connection.last_used_at = func.now()
            db.commit()
        
        return ConnectionResponse(connected=connected)
        
    except Exception as e:
        print(f"DEBUG: Error checking connection status: {str(e)}")
        return ConnectionResponse(connected=False)

@app.get("/binance/balances")
async def get_balances(db: Session = Depends(get_db)):
    print("DEBUG: get_balances called")
    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Getting balances for user: {current_user.email}")

        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'binance',
            WalletConnection.is_active == True,
            WalletConnection.connection_status == 'connected'
        ).first()

        if not connection:
            print("DEBUG: No active connection found")
            raise HTTPException(status_code=401, detail="Not connected to Binance")

        print("DEBUG: Active connection found, fetching balances...")
        connection.last_used_at = func.now()
        db.commit()

        # Read stored credentials (handles plain str or bytes)
        def _read_key(k):
            if isinstance(k, (bytes, bytearray)):
                try:
                    return k.decode()
                except Exception:
                    return str(k)
            return str(k)

        api_key = _read_key(connection.encrypted_api_key)
        secret_key = _read_key(connection.encrypted_secret_key)
        

        exchange = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'timeout': 60000,
        })

        try:
            # ============================================================
            # PRODUCTION MODE (COMMENTED OUT - US GCP blocked by Binance)
            # ============================================================
            # print("DEBUG: Using production Binance API")
            # balance_data = await exchange.fetch_balance()

            # ============================================================
            # TESTNET MODE (ACTIVE)
            # ============================================================
            # Enable sandbox mode for Binance testnet
            exchange.set_sandbox_mode(True)
            print("DEBUG: Using Binance TESTNET API (testnet.binance.vision)")
            print(f"DEBUG: Testnet enabled for connection: {connection.uuid}")

            balance_data = await exchange.fetch_balance()

            balances = _normalize_balances(balance_data)
            print(
                f"DEBUG: Returning real balances for connection {connection.uuid} (assets={len(balances)})"
            )
            return {"balances": balances}

        except AuthenticationError as auth_err:
            connection.connection_status = 'error'
            connection.last_error = f"AuthenticationError: {auth_err}"
            db.commit()
            raise HTTPException(status_code=401, detail="Authentication failed: check API key/secret (testnet keys required)")
        except (ExchangeNotAvailable, NetworkError) as net_err:
            connection.connection_status = 'error'
            connection.last_error = f"Network/Exchange error: {net_err}"
            db.commit()
            raise HTTPException(status_code=503, detail="Binance testnet not reachable right now")
        except (RequestTimeout,) as rt:
            connection.connection_status = 'error'
            connection.last_error = f"RequestTimeout: {rt}"
            db.commit()
            raise HTTPException(status_code=504, detail="Timeout contacting Binance testnet")
        except (DDoSProtection, RateLimitExceeded) as rl:
            connection.connection_status = 'error'
            connection.last_error = f"RateLimit: {rl}"
            db.commit()
            raise HTTPException(status_code=429, detail="Rate limit / DDoS protection triggered")
        except Exception as api_error:
            connection.connection_status = 'error'
            connection.last_error = str(api_error)
            db.commit()
            import traceback
            print(f"DEBUG: Traceback fetching balances: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {api_error}")
        finally:
            try:
                await exchange.close()
            except Exception:
                pass
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"DEBUG: Error fetching balances: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")

        
        
        
    # except HTTPException:
    #     raise
    # except Exception as e:
    #     print(f"DEBUG: Error fetching balances: {str(e)}")
    #     import traceback
    #     print(f"DEBUG: Traceback: {traceback.format_exc()}")
    #     raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")

@app.post("/binance/disconnect")
async def disconnect_from_binance(db: Session = Depends(get_db)):
    print("DEBUG: disconnect_from_binance called")
    
    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Disconnecting user: {current_user.email}")
        
        # Find active Binance connections
        connections = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'binance',
            WalletConnection.is_active == True
        ).all()
        
        if connections:
            print(f"DEBUG: Found {len(connections)} connections to disconnect")
            # Deactivate all active connections
            for connection in connections:
                connection.is_active = False
                connection.connection_status = 'disconnected'
                print(f"DEBUG: Disconnected connection: {connection.uuid}")
            
            db.commit()
        else:
            print("DEBUG: No active connections found")
        
        return ConnectionResponse(
            connected=False,
            message="Successfully disconnected from Binance"
        )
        
    except Exception as e:
        print(f"DEBUG: Error disconnecting: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

# The "userId: int" parameter tells FastAPI to expect a URL like "...?userId=1"
@app.get("/binance/credentials", response_model=CredentialsResponse)
async def get_binance_credentials(userId: int, db: Session = Depends(get_db)):
    """
    Retrieves the active Binance API key and secret for a SPECIFIC user.
    """
    print(f"DEBUG: /binance/credentials endpoint called for userId: {userId}")
    
    try:
        # We no longer use the hardcoded get_current_user_from_db function here.
        # We use the userId passed directly in the URL.
        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == userId, # <-- Use the userId from the request
            # WalletConnection.exchange_name == 'binance',
            # WalletConnection.is_active == True,
            # WalletConnection.connection_status == 'connected'
        ).first()

        if not connection:
            print(f"DEBUG: No active Binance connection found for userId: {userId}.")
            raise HTTPException(status_code=404, detail=f"Active Binance connection not found for userId: {userId}.")

        api_key = connection.encrypted_api_key
        secret_key = connection.encrypted_secret_key

        print(f"DEBUG: Found credentials for userId: {userId}. Sending API Key starting with: {api_key[:5]}...")
        return CredentialsResponse(apiKey=api_key, secretKey=secret_key)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Error fetching credentials for userId {userId}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching credentials.")

# ============================================================================
# COINBASE ENDPOINTS
# ============================================================================

@app.post("/coinbase/connect")
async def connect_to_coinbase(request: ConnectRequest, db: Session = Depends(get_db)):
    """Connect to Coinbase exchange and store credentials"""
    print("DEBUG: connect_to_coinbase function called")

    try:
        print(f"DEBUG: API Key Name received: {request.apiKey.split('/')[-1] if request.apiKey else 'None'}")
        print(f"DEBUG: Private Key received: {'Yes' if request.privateKey else 'No'}")

        # Validate inputs
        if not request.apiKey or not request.privateKey:
            print("DEBUG: Missing API key or secret key")
            raise HTTPException(status_code=400, detail="API Key Name (apiKey) and Private Key (privateKey) are required")

        if len(request.apiKey) < 10 or len(request.privateKey) < 10:
            print("DEBUG: Keys too short")
            raise HTTPException(status_code=400, detail="API Key and Secret Key seem too short")

        current_user = get_current_user_from_db(db)

        # Check if connection already exists for this user
        existing_connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'coinbase',
            WalletConnection.is_active == True
        ).first()

        if existing_connection:
            print("DEBUG: Updating existing Coinbase connection...")
            existing_connection.encrypted_api_key = request.apiKey # This is the API Key 'name'
            existing_connection.encrypted_secret_key = request.privateKey # This is the PEM private key
            existing_connection.last_used_at = func.now()
            existing_connection.connection_status = 'connected'
            existing_connection.last_error = None
            connection = existing_connection
        else:
            print("DEBUG: Creating new Coinbase connection...")
            connection = WalletConnection(
                user_id=current_user.id,
                exchange_name='coinbase',
                exchange_environment='production', # Advanced Trade API is production
                encrypted_api_key=request.apiKey, # Store the API Key 'name'
                encrypted_secret_key=request.privateKey, # Store the PEM private key
                connection_name=f"Coinbase Connection ({datetime.now().strftime('%Y-%m-%d')})",
                is_active=True,
                connection_status='connected'
            )

        if not existing_connection:
            db.add(connection)

        db.commit()
        db.refresh(connection)
        print(f"DEBUG: Coinbase connection stored successfully with ID: {connection.uuid}")

        return ConnectionResponse(
            connected=True,
            message="Successfully connected to Coinbase"
        )

    except HTTPException as he:
        print(f"DEBUG: HTTP Exception: {he.detail}")
        raise he
    except Exception as e:
        print(f"DEBUG: Unexpected error: {str(e)}")
        print(f"DEBUG: Error type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/coinbase/connection-status")
async def get_coinbase_connection_status(db: Session = Depends(get_db)):
    """Check if user has active Coinbase connection"""
    print("DEBUG: get_coinbase_connection_status called")

    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Checking Coinbase connection for user: {current_user.email}")

        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'coinbase',
            WalletConnection.is_active == True,
            WalletConnection.connection_status == 'connected'
        ).first()

        connected = connection is not None
        print(f"DEBUG: Coinbase connection status: {connected}")

        if connection:
            connection.last_used_at = func.now()
            db.commit()

        return ConnectionResponse(connected=connected)

    except Exception as e:
        print(f"DEBUG: Error checking Coinbase connection status: {str(e)}")
        return ConnectionResponse(connected=False)

@app.get("/coinbase/balances")
async def get_coinbase_balances(db: Session = Depends(get_db)):
    """Fetch balances from Coinbase"""
    print("DEBUG: get_coinbase_balances called")
    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Getting Coinbase balances for user: {current_user.email}")

        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'coinbase',
            WalletConnection.is_active == True,
            WalletConnection.connection_status == 'connected'
        ).first()

        if not connection:
            print("DEBUG: No active Coinbase connection found")
            raise HTTPException(status_code=401, detail="Not connected to Coinbase")

        print("DEBUG: Active Coinbase connection found, fetching balances...")
        connection.last_used_at = func.now()
        db.commit()

        # Read stored credentials
        def _read_key(k):
            if isinstance(k, (bytes, bytearray)):
                try:
                    return k.decode()
                except Exception:
                    return str(k)
            return str(k)

        api_key = _read_key(connection.encrypted_api_key)
        private_key = _read_key(connection.encrypted_secret_key)

        # Initialize Coinbase exchange with CCXT
        exchange_config = {
            'apiKey': api_key, # The API Key 'name'
            'secret': private_key, # The PEM private key
            'enableRateLimit': True,
            'timeout': 60000,
            # IMPORTANT: This synchronizes the local clock with the server's clock
            # to prevent 401 Unauthorized errors due to timestamp mismatches.
            'options': { 'fetchTime': True },
        }

        exchange = ccxt.coinbase(exchange_config)

        try:
            print("DEBUG: Using Coinbase API via CCXT")

            balance_data = await exchange.fetch_balance()

            balances = _normalize_balances(balance_data)
            print(
                f"DEBUG: Returning Coinbase balances for connection {connection.uuid} (assets={len(balances)})"
            )
            return {"balances": balances}

        except AuthenticationError as auth_err:
            connection.connection_status = 'error'
            connection.last_error = f"AuthenticationError: {auth_err}"
            db.commit()
            raise HTTPException(status_code=401, detail="Authentication failed: check Coinbase API key/secret")
        except (ExchangeNotAvailable, NetworkError) as net_err:
            connection.connection_status = 'error'
            connection.last_error = f"Network/Exchange error: {net_err}"
            db.commit()
            raise HTTPException(status_code=503, detail="Coinbase not reachable right now")
        except (RequestTimeout,) as rt:
            connection.connection_status = 'error'
            connection.last_error = f"RequestTimeout: {rt}"
            db.commit()
            raise HTTPException(status_code=504, detail="Timeout contacting Coinbase")
        except (DDoSProtection, RateLimitExceeded) as rl:
            connection.connection_status = 'error'
            connection.last_error = f"RateLimit: {rl}"
            db.commit()
            raise HTTPException(status_code=429, detail="Rate limit / DDoS protection triggered")
        except Exception as api_error:
            connection.connection_status = 'error'
            connection.last_error = str(api_error)
            db.commit()
            import traceback
            print(f"DEBUG: Traceback fetching Coinbase balances: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {api_error}")
        finally:
            # Always close the exchange connection
            try:
                await exchange.close()
            except Exception:
                pass

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"DEBUG: Error fetching Coinbase balances: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to fetch balances: {str(e)}")


@app.post("/coinbase/buy", response_model=CoinbaseOrderResponse)
async def coinbase_buy_order(
    order: CoinbaseOrderRequest, db: Session = Depends(get_db)
):
    """Place a Coinbase buy (long) order using stored credentials."""
    current_user = get_current_user_from_db(db)
    logger.debug("coinbase_buy_order called for symbol=%s", order.symbol)
    return await _submit_coinbase_order(db, current_user, order, "buy")


@app.post("/coinbase/sell", response_model=CoinbaseOrderResponse)
async def coinbase_sell_order(
    order: CoinbaseOrderRequest, db: Session = Depends(get_db)
):
    """Place a Coinbase sell (short) order using stored credentials."""
    current_user = get_current_user_from_db(db)
    logger.debug("coinbase_sell_order called for symbol=%s", order.symbol)
    return await _submit_coinbase_order(db, current_user, order, "sell")


@app.post("/coinbase/open-order", response_model=CoinbaseOrderResponse)
async def coinbase_open_order(
    order: CoinbaseOpenOrderRequest, db: Session = Depends(get_db)
):
    """Place a Coinbase limit/stop order with optional TP/SL metadata."""
    current_user = get_current_user_from_db(db)
    logger.debug(
        "coinbase_open_order called for symbol=%s side=%s", order.symbol, order.side
    )
    return await _submit_coinbase_order(
        db,
        current_user,
        order,
        order.side,
        require_price=True,
    )


@app.get("/coinbase/positions", response_model=List[CoinbaseOrderResponse])
async def coinbase_positions(db: Session = Depends(get_db)):
    """Retrieve normalized Coinbase positions for the authenticated user."""
    current_user = get_current_user_from_db(db)
    connection = _get_coinbase_connection(db, current_user)
    exchange = await _create_coinbase_exchange(connection)

    try:
        positions: List[CoinbaseOrderResponse] = []
        if getattr(exchange, "has", {}).get("fetchPositions"):
            raw_positions = await exchange.fetch_positions()
            for position in raw_positions or []:
                tp_raw = _extract_trigger(position, "takeProfit")
                sl_raw = _extract_trigger(position, "stopLoss")
                order_payload = {
                    "id": position.get("id")
                    or f"{position.get('symbol')}-{position.get('side', 'position')}",
                    "symbol": position.get("symbol"),
                    "side": position.get("side"),
                    "type": "position",
                    "filled": position.get("contracts") or position.get("amount"),
                    "remaining": position.get("remaining"),
                    "average": position.get("entryPrice")
                    or position.get("avgPrice"),
                    "cost": position.get("notional")
                    or position.get("initialMargin"),
                    "timestamp": position.get("timestamp"),
                    "datetime": position.get("datetime"),
                    "info": position,
                }
                metadata = order_payload.setdefault("metadata", {})
                tp_obj = _ensure_trigger(tp_raw)
                sl_obj = _ensure_trigger(sl_raw)
                if tp_obj:
                    metadata["takeProfit"] = _format_trigger(tp_obj)
                if sl_obj:
                    metadata["stopLoss"] = _format_trigger(sl_obj)
                positions.append(
                    _normalize_order_response(
                        order_payload,
                        take_profit=tp_obj,
                        stop_loss=sl_obj,
                    )
                )
        else:
            open_orders = await exchange.fetch_open_orders()
            for order in open_orders or []:
                order_payload = dict(order)
                tp_raw = _extract_trigger(order_payload, "takeProfit")
                sl_raw = _extract_trigger(order_payload, "stopLoss")
                tp_obj = _ensure_trigger(tp_raw)
                sl_obj = _ensure_trigger(sl_raw)
                metadata = order_payload.setdefault("metadata", {})
                if tp_obj:
                    metadata["takeProfit"] = _format_trigger(tp_obj)
                if sl_obj:
                    metadata["stopLoss"] = _format_trigger(sl_obj)
                positions.append(
                    _normalize_order_response(
                        order_payload,
                        take_profit=tp_obj,
                        stop_loss=sl_obj,
                    )
                )

        _coinbase_success(db, connection)
        return positions
    except AuthenticationError as auth_err:
        _handle_coinbase_error(db, connection, auth_err)
        raise HTTPException(
            status_code=401,
            detail="Authentication failed: check Coinbase API key/secret",
        ) from auth_err
    except (ExchangeNotAvailable, NetworkError) as net_err:
        _handle_coinbase_error(db, connection, net_err)
        raise HTTPException(
            status_code=503, detail="Coinbase exchange is not reachable right now"
        ) from net_err
    except RequestTimeout as timeout_err:
        _handle_coinbase_error(db, connection, timeout_err)
        raise HTTPException(status_code=504, detail="Timeout contacting Coinbase") from timeout_err
    except (DDoSProtection, RateLimitExceeded) as rl_err:
        _handle_coinbase_error(db, connection, rl_err)
        raise HTTPException(
            status_code=429,
            detail="Coinbase rate limit or DDoS protection triggered",
        ) from rl_err
    except Exception as error:
        _handle_coinbase_error(db, connection, error)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch Coinbase positions: {error}"
        ) from error
    finally:
        try:
            await exchange.close()
        except Exception:
            pass


@app.get("/coinbase/history", response_model=List[CoinbaseHistoryResponse])
async def coinbase_trade_history(
    symbol: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """Retrieve recent Coinbase trade history for the authenticated user."""
    current_user = get_current_user_from_db(db)
    connection = _get_coinbase_connection(db, current_user)
    exchange = await _create_coinbase_exchange(connection)

    normalized_symbol = (
        _normalize_coinbase_symbol(symbol) if symbol else None
    )

    try:
        trades = await exchange.fetch_my_trades(
            symbol=normalized_symbol, limit=limit if limit > 0 else None
        )
        _coinbase_success(db, connection)
        history: List[CoinbaseHistoryResponse] = []
        for trade in trades or []:
            trade_payload = dict(trade)
            tp_raw = _extract_trigger(trade_payload, "takeProfit")
            sl_raw = _extract_trigger(trade_payload, "stopLoss")
            tp_obj = _ensure_trigger(tp_raw)
            sl_obj = _ensure_trigger(sl_raw)
            metadata = trade_payload.setdefault("metadata", {})
            if tp_obj:
                metadata["takeProfit"] = _format_trigger(tp_obj)
            if sl_obj:
                metadata["stopLoss"] = _format_trigger(sl_obj)
            history.append(
                _normalize_history_response(
                    trade_payload,
                    take_profit=tp_obj,
                    stop_loss=sl_obj,
                )
            )
        return history
    except AuthenticationError as auth_err:
        _handle_coinbase_error(db, connection, auth_err)
        raise HTTPException(
            status_code=401,
            detail="Authentication failed: check Coinbase API key/secret",
        ) from auth_err
    except (ExchangeNotAvailable, NetworkError) as net_err:
        _handle_coinbase_error(db, connection, net_err)
        raise HTTPException(
            status_code=503, detail="Coinbase exchange is not reachable right now"
        ) from net_err
    except RequestTimeout as timeout_err:
        _handle_coinbase_error(db, connection, timeout_err)
        raise HTTPException(status_code=504, detail="Timeout contacting Coinbase") from timeout_err
    except (DDoSProtection, RateLimitExceeded) as rl_err:
        _handle_coinbase_error(db, connection, rl_err)
        raise HTTPException(
            status_code=429,
            detail="Coinbase rate limit or DDoS protection triggered",
        ) from rl_err
    except Exception as error:
        _handle_coinbase_error(db, connection, error)
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch Coinbase trade history: {error}"
        ) from error
    finally:
        try:
            await exchange.close()
        except Exception:
            pass

@app.post("/coinbase/disconnect")
async def disconnect_from_coinbase(db: Session = Depends(get_db)):
    """Disconnect from Coinbase"""
    print("DEBUG: disconnect_from_coinbase called")

    try:
        current_user = get_current_user_from_db(db)
        print(f"DEBUG: Disconnecting Coinbase user: {current_user.email}")

        connections = db.query(WalletConnection).filter(
            WalletConnection.user_id == current_user.id,
            WalletConnection.exchange_name == 'coinbase',
            WalletConnection.is_active == True
        ).all()

        if connections:
            print(f"DEBUG: Found {len(connections)} Coinbase connections to disconnect")
            for connection in connections:
                connection.is_active = False
                connection.connection_status = 'disconnected'
                print(f"DEBUG: Disconnected Coinbase connection: {connection.uuid}")

            db.commit()
        else:
            print("DEBUG: No active Coinbase connections found")

        return ConnectionResponse(
            connected=False,
            message="Successfully disconnected from Coinbase"
        )

    except Exception as e:
        print(f"DEBUG: Error disconnecting from Coinbase: {str(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")

@app.get("/coinbase/credentials", response_model=CredentialsResponse)
async def get_coinbase_credentials(userId: int, db: Session = Depends(get_db)):
    """Retrieves the active Coinbase API key and secret for a SPECIFIC user"""
    print(f"DEBUG: /coinbase/credentials endpoint called for userId: {userId}")

    try:
        connection = db.query(WalletConnection).filter(
            WalletConnection.user_id == userId,
            WalletConnection.exchange_name == 'coinbase',
            WalletConnection.is_active == True,
            WalletConnection.connection_status == 'connected'
        ).first()

        if not connection:
            print(f"DEBUG: No active Coinbase connection found for userId: {userId}.")
            raise HTTPException(status_code=404, detail=f"Active Coinbase connection not found for userId: {userId}.")

        api_key = connection.encrypted_api_key
        secret_key = connection.encrypted_secret_key

        print(f"DEBUG: Found Coinbase credentials for userId: {userId}. Sending API Key starting with: {api_key[:5]}...")
        return CredentialsResponse(apiKey=api_key, secretKey=secret_key)

    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"DEBUG: Error fetching Coinbase credentials for userId {userId}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error while fetching credentials.")

# ...existing code...

if __name__ == "__main__":
    import uvicorn
    print("DEBUG: Starting server on port 8011")
    uvicorn.run(app, host="0.0.0.0", port=8011)

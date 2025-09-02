from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ccxt.async_support as ccxt
from typing import List, Dict, Any
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
class ConnectRequest(BaseModel):
    apiKey: str
    secretKey: str

class Balance(BaseModel):
    asset: str
    free: str
    locked: str

class ConnectionResponse(BaseModel):
    connected: bool
    message: str = ""

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

            # Always enable sandbox mode for testnet
            # exchange.set_sandbox_mode(True)
            print("DEBUG: Using production Binance API") 
            # use sandbox/testnet if stored
            # if getattr(connection, "exchange_environment", "").lower() == "testnet":
            #     exchange.set_sandbox_mode(True)

            balance_data = await exchange.fetch_balance()

            totals = balance_data.get('total', {}) if isinstance(balance_data, dict) else {}
            free = balance_data.get('free', {}) if isinstance(balance_data, dict) else {}
            used = balance_data.get('used', {}) if isinstance(balance_data, dict) else {}

            balances = []
            for asset, total_amount in totals.items():
                try:
                    total_f = float(total_amount or 0)
                except Exception:
                    total_f = 0.0
                if total_f > 0:
                    balances.append({
                        'asset': asset,
                        'free': str(free.get(asset, 0)),
                        'locked': str(used.get(asset, 0))
                    })

            print(f"DEBUG: Returning real balances for connection: {connection.uuid}")
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

# ...existing code...

if __name__ == "__main__":
    import uvicorn
    print("DEBUG: Starting server on port 8011")
    uvicorn.run(app, host="0.0.0.0", port=8011)
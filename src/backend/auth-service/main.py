from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
import asyncio
import asyncpg
import redis.asyncio as redis
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import logging
import os
import uuid
import hashlib
import secrets
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from contextlib import asynccontextmanager
import json
from kafka import KafkaProducer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://alphintra:alphintra@localhost:5432/alphintra")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Email Configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@alphintra.com")

# Global connections
db_pool = None
redis_client = None
kafka_producer = None

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
security = HTTPBearer()

# Pydantic models
class UserRegistration(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    phone_number: Optional[str] = Field(None, regex=r'^\+?[1-9]\d{1,14}$')
    country: Optional[str] = Field(None, max_length=2, description="ISO 3166-1 alpha-2 country code")
    date_of_birth: Optional[str] = Field(None, regex=r'^\d{4}-\d{2}-\d{2}$')
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False

class UserResponse(BaseModel):
    id: int
    uuid: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    profile: Optional[Dict[str, Any]] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @validator('new_password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class EmailVerification(BaseModel):
    token: str

class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    permissions: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: int
    name: str
    key: str
    permissions: List[str]
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]

# Database connection management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, redis_client, kafka_producer
    
    try:
        # Initialize database connection
        db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
        
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        
        # Initialize Kafka producer
        kafka_producer = KafkaProducer(
            bootstrap_servers=[KAFKA_BOOTSTRAP_SERVERS],
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        
        logger.info("Auth service connections initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize connections: {e}")
        raise
    
    yield
    
    # Shutdown
    try:
        if db_pool:
            await db_pool.close()
        if redis_client:
            await redis_client.close()
        if kafka_producer:
            kafka_producer.close()
        logger.info("All connections closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Initialize FastAPI app
app = FastAPI(
    title="alphintra Auth Service",
    description="Authentication and authorization service for alphintra platform",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utility functions
def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Check if token is blacklisted
    is_blacklisted = await redis_client.get(f"blacklist:{token}")
    if is_blacklisted:
        raise credentials_exception
    
    # Get user from database
    async with db_pool.acquire() as conn:
        user = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1 AND is_active = true",
            user_id
        )
        
        if user is None:
            raise credentials_exception
        
        # Update last activity
        await conn.execute(
            "UPDATE users SET last_activity = NOW() WHERE id = $1",
            user_id
        )
        
        return dict(user)

async def get_current_active_user(current_user: dict = Depends(get_current_user)):
    """Get current active user"""
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """Send email notification"""
    try:
        if not SMTP_USERNAME or not SMTP_PASSWORD:
            logger.warning("SMTP credentials not configured, skipping email")
            return
        
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(FROM_EMAIL, to_email, text)
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")

# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connectivity
        async with db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        
        # Check Redis connectivity
        await redis_client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "services": {
                "database": "connected",
                "redis": "connected",
                "kafka": "connected" if kafka_producer else "disconnected"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=UserResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        async with db_pool.acquire() as conn:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                user_data.email.lower()
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="User with this email already exists"
                )
            
            # Hash password
            hashed_password = hash_password(user_data.password)
            
            # Create user
            user_uuid = str(uuid.uuid4())
            user_id = await conn.fetchval(
                """
                INSERT INTO users (uuid, email, password_hash, first_name, last_name, is_active, is_verified)
                VALUES ($1, $2, $3, $4, $5, true, false)
                RETURNING id
                """,
                user_uuid, user_data.email.lower(), hashed_password,
                user_data.first_name, user_data.last_name
            )
            
            # Create user profile
            await conn.execute(
                """
                INSERT INTO user_profiles (user_id, phone_number, country, date_of_birth)
                VALUES ($1, $2, $3, $4)
                """,
                user_id, user_data.phone_number, user_data.country, user_data.date_of_birth
            )
            
            # Create default trading account
            await conn.execute(
                """
                INSERT INTO user_accounts (user_id, account_type, currency, is_active)
                VALUES ($1, 'spot', 'USDT', true)
                """,
                user_id
            )
            
            # Generate email verification token
            verification_token = secrets.token_urlsafe(32)
            await redis_client.setex(
                f"email_verification:{verification_token}",
                3600,  # 1 hour expiry
                user_id
            )
            
            # Send verification email
            verification_link = f"https://alphintra.com/verify-email?token={verification_token}"
            email_body = f"""
            <html>
            <body>
                <h2>Welcome to alphintra!</h2>
                <p>Hi {user_data.first_name},</p>
                <p>Thank you for registering with alphintra. Please click the link below to verify your email address:</p>
                <p><a href="{verification_link}">Verify Email Address</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't create this account, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The alphintra Team</p>
            </body>
            </html>
            """
            
            await send_email(
                user_data.email,
                "Welcome to alphintra - Verify Your Email",
                email_body,
                is_html=True
            )
            
            # Publish user registration event
            user_event = {
                "event_type": "user_registered",
                "user_id": user_id,
                "email": user_data.email,
                "timestamp": datetime.utcnow().isoformat()
            }
            kafka_producer.send('user-events', user_event)
            
            # Get created user
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            
            return UserResponse(
                id=user['id'],
                uuid=str(user['uuid']),
                email=user['email'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                is_active=user['is_active'],
                is_verified=user['is_verified'],
                created_at=user['created_at'],
                last_login=user['last_login']
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/login", response_model=TokenResponse)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return JWT tokens"""
    try:
        async with db_pool.acquire() as conn:
            # Get user by email
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = true",
                form_data.username.lower()
            )
            
            if not user or not verify_password(form_data.password, user['password_hash']):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Update last login
            await conn.execute(
                "UPDATE users SET last_login = NOW() WHERE id = $1",
                user['id']
            )
            
            # Create tokens
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user['id'], "email": user['email']},
                expires_delta=access_token_expires
            )
            
            refresh_token = create_refresh_token(
                data={"sub": user['id'], "email": user['email']}
            )
            
            # Store refresh token in Redis
            await redis_client.setex(
                f"refresh_token:{user['id']}",
                REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
                refresh_token
            )
            
            # Get user profile
            profile = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                user['id']
            )
            
            # Publish login event
            login_event = {
                "event_type": "user_login",
                "user_id": user['id'],
                "email": user['email'],
                "timestamp": datetime.utcnow().isoformat()
            }
            kafka_producer.send('user-events', login_event)
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserResponse(
                    id=user['id'],
                    uuid=str(user['uuid']),
                    email=user['email'],
                    first_name=user['first_name'],
                    last_name=user['last_name'],
                    is_active=user['is_active'],
                    is_verified=user['is_verified'],
                    created_at=user['created_at'],
                    last_login=user['last_login'],
                    profile=dict(profile) if profile else None
                )
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        token_type: str = payload.get("type")
        
        if user_id is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Check if refresh token exists in Redis
        stored_token = await redis_client.get(f"refresh_token:{user_id}")
        if not stored_token or stored_token != refresh_token:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1 AND is_active = true",
                user_id
            )
            
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
        
        # Create new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": user['id'], "email": user['email']},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/logout")
async def logout_user(current_user: dict = Depends(get_current_active_user), token: str = Depends(oauth2_scheme)):
    """Logout user and blacklist token"""
    try:
        # Blacklist the access token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp = payload.get("exp")
        
        if exp:
            # Calculate TTL for blacklist (until token expires)
            ttl = exp - int(datetime.utcnow().timestamp())
            if ttl > 0:
                await redis_client.setex(f"blacklist:{token}", ttl, "true")
        
        # Remove refresh token
        await redis_client.delete(f"refresh_token:{current_user['id']}")
        
        # Publish logout event
        logout_event = {
            "event_type": "user_logout",
            "user_id": current_user['id'],
            "email": current_user['email'],
            "timestamp": datetime.utcnow().isoformat()
        }
        kafka_producer.send('user-events', logout_event)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/verify-email")
async def verify_email(verification: EmailVerification):
    """Verify user email address"""
    try:
        # Get user ID from verification token
        user_id = await redis_client.get(f"email_verification:{verification.token}")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")
        
        # Update user verification status
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET is_verified = true WHERE id = $1",
                int(user_id)
            )
        
        # Delete verification token
        await redis_client.delete(f"email_verification:{verification.token}")
        
        # Publish email verification event
        verification_event = {
            "event_type": "email_verified",
            "user_id": int(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        kafka_producer.send('user-events', verification_event)
        
        return {"message": "Email verified successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying email: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/forgot-password")
async def forgot_password(password_reset: PasswordReset):
    """Send password reset email"""
    try:
        async with db_pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1 AND is_active = true",
                password_reset.email.lower()
            )
            
            if not user:
                # Don't reveal if email exists or not
                return {"message": "If the email exists, a password reset link has been sent"}
            
            # Generate password reset token
            reset_token = secrets.token_urlsafe(32)
            await redis_client.setex(
                f"password_reset:{reset_token}",
                3600,  # 1 hour expiry
                user['id']
            )
            
            # Send password reset email
            reset_link = f"https://alphintra.com/reset-password?token={reset_token}"
            email_body = f"""
            <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hi {user['first_name']},</p>
                <p>You requested a password reset for your alphintra account. Click the link below to reset your password:</p>
                <p><a href="{reset_link}">Reset Password</a></p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request this reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>The alphintra Team</p>
            </body>
            </html>
            """
            
            await send_email(
                user['email'],
                "alphintra - Password Reset Request",
                email_body,
                is_html=True
            )
            
            return {"message": "If the email exists, a password reset link has been sent"}
            
    except Exception as e:
        logger.error(f"Error in forgot password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/reset-password")
async def reset_password(password_reset: PasswordResetConfirm):
    """Reset user password using reset token"""
    try:
        # Get user ID from reset token
        user_id = await redis_client.get(f"password_reset:{password_reset.token}")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        # Hash new password
        hashed_password = hash_password(password_reset.new_password)
        
        # Update user password
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                hashed_password, int(user_id)
            )
        
        # Delete reset token
        await redis_client.delete(f"password_reset:{password_reset.token}")
        
        # Invalidate all existing refresh tokens for this user
        await redis_client.delete(f"refresh_token:{user_id}")
        
        # Publish password reset event
        reset_event = {
            "event_type": "password_reset",
            "user_id": int(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        kafka_producer.send('user-events', reset_event)
        
        return {"message": "Password reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/v1/auth/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: dict = Depends(get_current_active_user)
):
    """Change user password"""
    try:
        # Verify current password
        if not verify_password(password_change.current_password, current_user['password_hash']):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Hash new password
        hashed_password = hash_password(password_change.new_password)
        
        # Update password
        async with db_pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET password_hash = $1 WHERE id = $2",
                hashed_password, current_user['id']
            )
        
        # Invalidate all existing refresh tokens
        await redis_client.delete(f"refresh_token:{current_user['id']}")
        
        # Publish password change event
        change_event = {
            "event_type": "password_changed",
            "user_id": current_user['id'],
            "timestamp": datetime.utcnow().isoformat()
        }
        kafka_producer.send('user-events', change_event)
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# User profile endpoints
@app.get("/api/v1/auth/me", response_model=UserResponse)
async def get_current_user_profile(current_user: dict = Depends(get_current_active_user)):
    """Get current user profile"""
    try:
        async with db_pool.acquire() as conn:
            profile = await conn.fetchrow(
                "SELECT * FROM user_profiles WHERE user_id = $1",
                current_user['id']
            )
            
            return UserResponse(
                id=current_user['id'],
                uuid=str(current_user['uuid']),
                email=current_user['email'],
                first_name=current_user['first_name'],
                last_name=current_user['last_name'],
                is_active=current_user['is_active'],
                is_verified=current_user['is_verified'],
                created_at=current_user['created_at'],
                last_login=current_user['last_login'],
                profile=dict(profile) if profile else None
            )
            
    except Exception as e:
        logger.error(f"Error fetching user profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# API Key management
@app.post("/api/v1/auth/api-keys", response_model=APIKeyResponse)
async def create_api_key(
    api_key_data: APIKeyCreate,
    current_user: dict = Depends(get_current_active_user)
):
    """Create a new API key"""
    try:
        # Generate API key
        api_key = f"ak_{secrets.token_urlsafe(32)}"
        api_secret = secrets.token_urlsafe(64)
        
        # Hash the secret for storage
        hashed_secret = hashlib.sha256(api_secret.encode()).hexdigest()
        
        async with db_pool.acquire() as conn:
            api_key_id = await conn.fetchval(
                """
                INSERT INTO api_keys (user_id, name, key_hash, permissions, expires_at, is_active)
                VALUES ($1, $2, $3, $4, $5, true)
                RETURNING id
                """,
                current_user['id'], api_key_data.name, hashed_secret,
                json.dumps(api_key_data.permissions), api_key_data.expires_at
            )
            
            # Get created API key
            created_key = await conn.fetchrow(
                "SELECT * FROM api_keys WHERE id = $1",
                api_key_id
            )
            
            return APIKeyResponse(
                id=created_key['id'],
                name=created_key['name'],
                key=f"{api_key}:{api_secret}",  # Return full key only once
                permissions=json.loads(created_key['permissions']),
                is_active=created_key['is_active'],
                created_at=created_key['created_at'],
                expires_at=created_key['expires_at'],
                last_used=created_key['last_used']
            )
            
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/auth/api-keys")
async def get_api_keys(current_user: dict = Depends(get_current_active_user)):
    """Get user's API keys"""
    try:
        async with db_pool.acquire() as conn:
            api_keys = await conn.fetch(
                "SELECT * FROM api_keys WHERE user_id = $1 ORDER BY created_at DESC",
                current_user['id']
            )
            
            return {
                "api_keys": [
                    {
                        "id": key['id'],
                        "name": key['name'],
                        "key": f"ak_{'*' * 32}",  # Masked key
                        "permissions": json.loads(key['permissions']),
                        "is_active": key['is_active'],
                        "created_at": key['created_at'],
                        "expires_at": key['expires_at'],
                        "last_used": key['last_used']
                    }
                    for key in api_keys
                ]
            }
            
    except Exception as e:
        logger.error(f"Error fetching API keys: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.delete("/api/v1/auth/api-keys/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: dict = Depends(get_current_active_user)
):
    """Delete an API key"""
    try:
        async with db_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM api_keys WHERE id = $1 AND user_id = $2",
                key_id, current_user['id']
            )
            
            if result == "DELETE 0":
                raise HTTPException(status_code=404, detail="API key not found")
            
            return {"message": "API key deleted successfully"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    """User table - matches the user structure from other services"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime)
    
    # Relationships
    wallet_connections = relationship("WalletConnection", back_populates="user")

class WalletConnection(Base):
    """Store encrypted exchange API credentials"""
    __tablename__ = "wallet_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Exchange information
    exchange_name = Column(String(50), nullable=False)  # 'binance', 'coinbase', etc.
    exchange_environment = Column(String(20), default='testnet')  # 'testnet', 'mainnet'
    
    # Encrypted credentials (using Fernet encryption)
    encrypted_api_key = Column(Text, nullable=False)
    encrypted_secret_key = Column(Text, nullable=False)
    
    # Connection metadata
    connection_name = Column(String(255))  # User-friendly name
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    
    # Status tracking
    connection_status = Column(String(20), default='connected')  # 'connected', 'error', 'disabled'
    last_error = Column(Text)
    
    # Security
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="wallet_connections")
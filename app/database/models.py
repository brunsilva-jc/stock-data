"""
SQLAlchemy database models for cryptocurrency data.

This module defines the database schema using SQLAlchemy ORM.
Models represent tables in the PostgreSQL database with TimescaleDB extensions.
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    Text,
    Boolean,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from app.database.session import Base


class CryptoCurrency(Base):
    """
    Model representing a cryptocurrency.

    This table stores metadata about cryptocurrencies we're tracking.
    Each cryptocurrency has a unique symbol-market pair (e.g., BTC-USD).

    Attributes:
        id: Primary key
        symbol: Crypto symbol (BTC, ETH, etc.)
        name: Full name (Bitcoin, Ethereum, etc.)
        market: Market currency (USD, EUR, etc.)
        is_active: Whether we're actively tracking this crypto
        created_at: When the record was created
        updated_at: When the record was last updated
        prices: Relationship to CryptoPrice records
    """

    __tablename__ = "crypto_currencies"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    symbol = Column(String(10), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    market = Column(String(10), nullable=False, default="USD")
    is_active = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    prices = relationship(
        "CryptoPrice",
        back_populates="currency",
        cascade="all, delete-orphan"
    )

    # Ensure unique symbol-market pairs
    __table_args__ = (
        UniqueConstraint("symbol", "market", name="uq_symbol_market"),
        Index("idx_symbol_market", "symbol", "market"),
    )

    def __repr__(self):
        return f"<CryptoCurrency(id={self.id}, symbol={self.symbol}, market={self.market})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "name": self.name,
            "market": self.market,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class CryptoPrice(Base):
    """
    Model representing OHLCV (Open, High, Low, Close, Volume) price data.

    This is a TimescaleDB hypertable for efficient time-series queries.
    Each record represents one day of price data for a cryptocurrency.

    Attributes:
        id: Primary key
        currency_id: Foreign key to CryptoCurrency
        timestamp: Date and time of the price data
        open: Opening price
        high: Highest price during the period
        low: Lowest price during the period
        close: Closing price (most important for analysis)
        volume: Trading volume
        created_at: When the record was created
        currency: Relationship to CryptoCurrency
    """

    __tablename__ = "crypto_prices"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    currency_id = Column(
        Integer,
        ForeignKey("crypto_currencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Time-series data
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Record creation timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    currency = relationship("CryptoCurrency", back_populates="prices")

    # Indexes for efficient time-series queries
    __table_args__ = (
        # Composite index for common query patterns
        Index("idx_currency_timestamp", "currency_id", "timestamp"),
        # Unique constraint to prevent duplicate data
        UniqueConstraint("currency_id", "timestamp", name="uq_currency_timestamp"),
    )

    def __repr__(self):
        return f"<CryptoPrice(id={self.id}, currency_id={self.currency_id}, timestamp={self.timestamp}, close={self.close})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "currency_id": self.currency_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ComputedIndicator(Base):
    """
    Model for storing pre-computed technical indicators.

    This table stores calculated technical indicators (RSI, MACD, SMA, etc.)
    to avoid recalculating them on every request. This improves performance
    and is a common pattern in financial applications.

    Attributes:
        id: Primary key
        currency_id: Foreign key to CryptoCurrency
        timestamp: Date for which the indicator was calculated
        indicator_type: Type of indicator (RSI, MACD, SMA, etc.)
        indicator_name: Full name of the indicator
        value: Calculated value
        parameters: JSON string with calculation parameters
        created_at: When the record was created
        currency: Relationship to CryptoCurrency
    """

    __tablename__ = "computed_indicators"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    currency_id = Column(
        Integer,
        ForeignKey("crypto_currencies.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False, index=True)  # RSI, MACD, SMA, etc.
    indicator_name = Column(String(100), nullable=False)  # Full name
    value = Column(Float, nullable=False)
    parameters = Column(Text, nullable=True)  # JSON string with parameters

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    currency = relationship("CryptoCurrency")

    # Indexes for efficient queries
    __table_args__ = (
        Index("idx_currency_indicator_timestamp", "currency_id", "indicator_type", "timestamp"),
        # Allow multiple indicators for the same timestamp (RSI, MACD, etc.)
        UniqueConstraint(
            "currency_id",
            "timestamp",
            "indicator_type",
            "parameters",
            name="uq_currency_indicator"
        ),
    )

    def __repr__(self):
        return f"<ComputedIndicator(id={self.id}, type={self.indicator_type}, value={self.value})>"

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "currency_id": self.currency_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "indicator_type": self.indicator_type,
            "indicator_name": self.indicator_name,
            "value": self.value,
            "parameters": self.parameters,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# Note: After creating these models, we need to convert crypto_prices to a TimescaleDB hypertable.
# This is done via SQL migration in Alembic:
#
# SELECT create_hypertable('crypto_prices', 'timestamp', if_not_exists => TRUE);
#
# Hypertables provide:
# - Automatic partitioning by time
# - Improved query performance for time-series data
# - Data retention policies
# - Continuous aggregates

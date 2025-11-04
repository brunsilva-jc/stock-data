"""
Repository pattern for database operations.
Provides CRUD operations for CryptoCurrency, CryptoPrice, and ComputedIndicator models.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.database.models import CryptoCurrency, CryptoPrice, ComputedIndicator


class CryptoCurrencyRepository:
    """Repository for CryptoCurrency model operations."""

    @staticmethod
    def get_by_id(db: Session, currency_id: int) -> Optional[CryptoCurrency]:
        """Get cryptocurrency by ID."""
        return db.query(CryptoCurrency).filter(CryptoCurrency.id == currency_id).first()

    @staticmethod
    def get_by_symbol_and_market(
        db: Session, symbol: str, market: str
    ) -> Optional[CryptoCurrency]:
        """Get cryptocurrency by symbol and market."""
        return (
            db.query(CryptoCurrency)
            .filter(
                and_(
                    CryptoCurrency.symbol == symbol.upper(),
                    CryptoCurrency.market == market.upper(),
                )
            )
            .first()
        )

    @staticmethod
    def get_all(
        db: Session, active_only: bool = True, skip: int = 0, limit: int = 100
    ) -> List[CryptoCurrency]:
        """Get all cryptocurrencies with pagination."""
        query = db.query(CryptoCurrency)
        if active_only:
            query = query.filter(CryptoCurrency.is_active == True)
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def create(
        db: Session, symbol: str, name: str, market: str, is_active: bool = True
    ) -> CryptoCurrency:
        """Create a new cryptocurrency."""
        currency = CryptoCurrency(
            symbol=symbol.upper(),
            name=name,
            market=market.upper(),
            is_active=is_active,
        )
        db.add(currency)
        db.commit()
        db.refresh(currency)
        return currency

    @staticmethod
    def get_or_create(
        db: Session, symbol: str, name: str, market: str
    ) -> CryptoCurrency:
        """Get existing cryptocurrency or create if it doesn't exist."""
        currency = CryptoCurrencyRepository.get_by_symbol_and_market(
            db, symbol, market
        )
        if not currency:
            currency = CryptoCurrencyRepository.create(db, symbol, name, market)
        return currency

    @staticmethod
    def update(
        db: Session,
        currency_id: int,
        name: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional[CryptoCurrency]:
        """Update cryptocurrency information."""
        currency = CryptoCurrencyRepository.get_by_id(db, currency_id)
        if not currency:
            return None

        if name is not None:
            currency.name = name
        if is_active is not None:
            currency.is_active = is_active

        currency.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(currency)
        return currency

    @staticmethod
    def delete(db: Session, currency_id: int) -> bool:
        """Delete a cryptocurrency (soft delete by marking as inactive)."""
        currency = CryptoCurrencyRepository.get_by_id(db, currency_id)
        if not currency:
            return False

        currency.is_active = False
        currency.updated_at = datetime.utcnow()
        db.commit()
        return True


class CryptoPriceRepository:
    """Repository for CryptoPrice model operations."""

    @staticmethod
    def get_by_id(db: Session, price_id: int) -> Optional[CryptoPrice]:
        """Get price record by ID."""
        return db.query(CryptoPrice).filter(CryptoPrice.id == price_id).first()

    @staticmethod
    def get_latest(
        db: Session, currency_id: int, limit: int = 1
    ) -> List[CryptoPrice]:
        """Get latest price(s) for a cryptocurrency."""
        return (
            db.query(CryptoPrice)
            .filter(CryptoPrice.currency_id == currency_id)
            .order_by(desc(CryptoPrice.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_by_date_range(
        db: Session,
        currency_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[CryptoPrice]:
        """Get price data for a specific date range."""
        return (
            db.query(CryptoPrice)
            .filter(
                and_(
                    CryptoPrice.currency_id == currency_id,
                    CryptoPrice.timestamp >= start_date,
                    CryptoPrice.timestamp <= end_date,
                )
            )
            .order_by(CryptoPrice.timestamp)
            .all()
        )

    @staticmethod
    def get_recent(
        db: Session, currency_id: int, days: int = 30
    ) -> List[CryptoPrice]:
        """Get recent price data for the last N days."""
        from datetime import timedelta

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        return CryptoPriceRepository.get_by_date_range(
            db, currency_id, start_date, end_date
        )

    @staticmethod
    def create(
        db: Session,
        currency_id: int,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
    ) -> CryptoPrice:
        """Create a new price record."""
        price = CryptoPrice(
            currency_id=currency_id,
            timestamp=timestamp,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
        )
        db.add(price)
        db.commit()
        db.refresh(price)
        return price

    @staticmethod
    def bulk_create(
        db: Session, price_records: List[dict]
    ) -> int:
        """Bulk insert price records. Returns count of inserted records."""
        if not price_records:
            return 0

        price_objects = [CryptoPrice(**record) for record in price_records]
        db.bulk_save_objects(price_objects)
        db.commit()
        return len(price_objects)

    @staticmethod
    def get_price_at_timestamp(
        db: Session, currency_id: int, timestamp: datetime
    ) -> Optional[CryptoPrice]:
        """Get price at a specific timestamp."""
        return (
            db.query(CryptoPrice)
            .filter(
                and_(
                    CryptoPrice.currency_id == currency_id,
                    CryptoPrice.timestamp == timestamp,
                )
            )
            .first()
        )

    @staticmethod
    def get_stats(
        db: Session,
        currency_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> dict:
        """Get statistics for a currency in a date range."""
        from sqlalchemy import func

        result = (
            db.query(
                func.avg(CryptoPrice.close).label("avg_price"),
                func.max(CryptoPrice.high).label("max_price"),
                func.min(CryptoPrice.low).label("min_price"),
                func.avg(CryptoPrice.volume).label("avg_volume"),
                func.count().label("count"),
            )
            .filter(
                and_(
                    CryptoPrice.currency_id == currency_id,
                    CryptoPrice.timestamp >= start_date,
                    CryptoPrice.timestamp <= end_date,
                )
            )
            .first()
        )

        return {
            "avg_price": float(result.avg_price) if result.avg_price else None,
            "max_price": float(result.max_price) if result.max_price else None,
            "min_price": float(result.min_price) if result.min_price else None,
            "avg_volume": float(result.avg_volume) if result.avg_volume else None,
            "count": result.count,
        }


class ComputedIndicatorRepository:
    """Repository for ComputedIndicator model operations."""

    @staticmethod
    def get_by_id(db: Session, indicator_id: int) -> Optional[ComputedIndicator]:
        """Get computed indicator by ID."""
        return (
            db.query(ComputedIndicator)
            .filter(ComputedIndicator.id == indicator_id)
            .first()
        )

    @staticmethod
    def get_by_currency_and_type(
        db: Session,
        currency_id: int,
        indicator_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[ComputedIndicator]:
        """Get computed indicators by currency and type."""
        query = db.query(ComputedIndicator).filter(
            and_(
                ComputedIndicator.currency_id == currency_id,
                ComputedIndicator.indicator_type == indicator_type,
            )
        )

        if start_date:
            query = query.filter(ComputedIndicator.timestamp >= start_date)
        if end_date:
            query = query.filter(ComputedIndicator.timestamp <= end_date)

        return query.order_by(desc(ComputedIndicator.timestamp)).limit(limit).all()

    @staticmethod
    def get_latest(
        db: Session,
        currency_id: int,
        indicator_type: str,
        limit: int = 1,
    ) -> List[ComputedIndicator]:
        """Get latest computed indicator(s)."""
        return (
            db.query(ComputedIndicator)
            .filter(
                and_(
                    ComputedIndicator.currency_id == currency_id,
                    ComputedIndicator.indicator_type == indicator_type,
                )
            )
            .order_by(desc(ComputedIndicator.timestamp))
            .limit(limit)
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        currency_id: int,
        timestamp: datetime,
        indicator_type: str,
        indicator_name: str,
        value: float,
        parameters: Optional[str] = None,
    ) -> ComputedIndicator:
        """Create a new computed indicator."""
        indicator = ComputedIndicator(
            currency_id=currency_id,
            timestamp=timestamp,
            indicator_type=indicator_type,
            indicator_name=indicator_name,
            value=value,
            parameters=parameters,
        )
        db.add(indicator)
        db.commit()
        db.refresh(indicator)
        return indicator

    @staticmethod
    def bulk_create(
        db: Session, indicator_records: List[dict]
    ) -> int:
        """Bulk insert indicator records. Returns count of inserted records."""
        if not indicator_records:
            return 0

        indicator_objects = [
            ComputedIndicator(**record) for record in indicator_records
        ]
        db.bulk_save_objects(indicator_objects)
        db.commit()
        return len(indicator_objects)

    @staticmethod
    def delete_by_currency_and_date_range(
        db: Session,
        currency_id: int,
        start_date: datetime,
        end_date: datetime,
        indicator_type: Optional[str] = None,
    ) -> int:
        """Delete computed indicators for a currency in a date range."""
        query = db.query(ComputedIndicator).filter(
            and_(
                ComputedIndicator.currency_id == currency_id,
                ComputedIndicator.timestamp >= start_date,
                ComputedIndicator.timestamp <= end_date,
            )
        )

        if indicator_type:
            query = query.filter(ComputedIndicator.indicator_type == indicator_type)

        count = query.delete(synchronize_session=False)
        db.commit()
        return count


# Convenience function to get all repositories
def get_repositories(db: Session) -> dict:
    """Get all repository instances."""
    return {
        "currency": CryptoCurrencyRepository,
        "price": CryptoPriceRepository,
        "indicator": ComputedIndicatorRepository,
    }

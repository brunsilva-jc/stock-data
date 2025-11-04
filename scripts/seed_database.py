"""
Seed script to populate the database with initial cryptocurrency data.
Fetches data from AlphaVantage API and stores in PostgreSQL/TimescaleDB.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.database.session import SessionLocal
from app.database.repository import (
    CryptoCurrencyRepository,
    CryptoPriceRepository,
)
from app.services.alphavantage import alphavantage_service
from app.models.currency import CurrencyDataProcessor


# Cryptocurrencies to seed
CRYPTOCURRENCIES = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "LTC": "Litecoin",
    "XRP": "Ripple",
    "BCH": "Bitcoin Cash",
    "ADA": "Cardano",
    "DOT": "Polkadot",
    "LINK": "Chainlink",
}

DEFAULT_MARKET = "USD"


async def fetch_and_store_crypto_data(
    db, symbol: str, name: str, market: str = DEFAULT_MARKET
) -> bool:
    """Fetch data from API and store in database."""
    try:
        print(f"Fetching data for {name} ({symbol})...")

        # Get or create cryptocurrency record
        currency = CryptoCurrencyRepository.get_or_create(
            db, symbol=symbol, name=name, market=market
        )
        print(f"  ✓ Currency record: {currency.name} (ID: {currency.id})")

        # Fetch data from AlphaVantage
        raw_data = await alphavantage_service.get_digital_currency_daily(
            symbol, market
        )
        processed_data = CurrencyDataProcessor.process_response(raw_data)

        # Prepare price records for bulk insert
        price_records = []
        for data_point in processed_data.recent_data:
            price_records.append(
                {
                    "currency_id": currency.id,
                    "timestamp": datetime.fromisoformat(data_point.date),
                    "open": data_point.open,
                    "high": data_point.high,
                    "low": data_point.low,
                    "close": data_point.close,
                    "volume": data_point.volume,
                }
            )

        # Bulk insert price data
        if price_records:
            count = CryptoPriceRepository.bulk_create(db, price_records)
            print(f"  ✓ Inserted {count} price records")
            return True
        else:
            print(f"  ⚠ No price data to insert")
            return False

    except Exception as e:
        print(f"  ✗ Error processing {symbol}: {str(e)}")
        return False


async def seed_database():
    """Main seeding function."""
    print("=" * 60)
    print("CRYPTOCURRENCY DATA SEEDING SCRIPT")
    print("=" * 60)
    print(f"Database: {settings.postgres_db}")
    print(f"Market: {DEFAULT_MARKET}")
    print(f"Cryptocurrencies to seed: {len(CRYPTOCURRENCIES)}")
    print("=" * 60)
    print()

    # Create database session
    db = SessionLocal()

    try:
        success_count = 0
        fail_count = 0

        for symbol, name in CRYPTOCURRENCIES.items():
            success = await fetch_and_store_crypto_data(
                db, symbol, name, DEFAULT_MARKET
            )

            if success:
                success_count += 1
            else:
                fail_count += 1

            # Add delay to respect API rate limits (5 requests/minute)
            if symbol != list(CRYPTOCURRENCIES.keys())[-1]:  # Not the last one
                print(f"  ⏳ Waiting 15 seconds (API rate limit)...")
                await asyncio.sleep(15)

            print()

        print("=" * 60)
        print("SEEDING COMPLETE")
        print(f"✓ Success: {success_count}/{len(CRYPTOCURRENCIES)}")
        print(f"✗ Failed: {fail_count}/{len(CRYPTOCURRENCIES)}")
        print("=" * 60)

    except Exception as e:
        print(f"Fatal error during seeding: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Starting database seeding...")
    print()

    # Run the async seeding function
    asyncio.run(seed_database())

    print()
    print("Database seeding script finished!")

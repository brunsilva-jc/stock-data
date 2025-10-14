"""
FastAPI main application with routes for cryptocurrency data.
"""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from app.services.alphavantage import alphavantage_service
from app.models.currency import CurrencyDataProcessor, CurrencyResponse
from app.config import settings

app = FastAPI(
    title="Stock Data API",
    description="FastAPI application for fetching and displaying cryptocurrency data from AlphaVantage",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Stock Data API",
        "version": "1.0.0"
    }


@app.get("/home", response_model=CurrencyResponse)
async def home():
    """
    Home route that displays cryptocurrency data.
    Uses default cryptocurrency (Bitcoin) and market (USD) from configuration.

    Returns:
        CurrencyResponse: Processed cryptocurrency data with metadata, metrics, and recent time series

    Raises:
        HTTPException: If there's an error fetching or processing the data
    """
    try:
        # Fetch data using default settings
        raw_data = await alphavantage_service.get_digital_currency_daily(
            symbol=settings.default_symbol,
            market=settings.default_market
        )

        # Process the data
        processed_data = CurrencyDataProcessor.process_response(raw_data)

        return processed_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching currency data: {str(e)}"
        )


@app.get("/currency/{symbol}", response_model=CurrencyResponse)
async def get_currency(symbol: str, market: str = "USD"):
    """
    Get cryptocurrency data for a specific symbol.

    Args:
        symbol: Cryptocurrency symbol (e.g., BTC, ETH, LTC)
        market: Market currency (default: USD)

    Returns:
        CurrencyResponse: Processed cryptocurrency data with metadata, metrics, and recent time series

    Raises:
        HTTPException: If there's an error fetching or processing the data
    """
    try:
        # Fetch data for specified currency
        raw_data = await alphavantage_service.get_digital_currency_daily(
            symbol=symbol.upper(),
            market=market.upper()
        )

        # Process the data
        processed_data = CurrencyDataProcessor.process_response(raw_data)

        return processed_data

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching currency data: {str(e)}"
        )


@app.get("/")
async def root():
    """
    Root endpoint with API information.

    Returns:
        dict: Welcome message and available endpoints
    """
    return {
        "message": "Welcome to Stock Data API",
        "endpoints": {
            "/health": "Check API health status",
            "/home": "Get default cryptocurrency data (Bitcoin)",
            "/currency/{symbol}": "Get specific cryptocurrency data",
            "/docs": "Interactive API documentation"
        }
    }

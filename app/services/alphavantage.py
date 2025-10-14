"""
AlphaVantage API service for fetching cryptocurrency data.
"""
import httpx
from typing import Dict, Optional
from app.config import settings


class AlphaVantageService:
    """Service to interact with AlphaVantage API."""

    def __init__(self):
        self.base_url = settings.alphavantage_base_url
        self.api_key = settings.alphavantage_api_key

    async def get_digital_currency_daily(
        self, symbol: str, market: str = "USD"
    ) -> Dict:
        """
        Fetch daily digital currency data from AlphaVantage.

        Args:
            symbol: Cryptocurrency symbol (e.g., 'BTC', 'ETH')
            market: Market currency (default: 'USD')

        Returns:
            Dict containing the API response

        Raises:
            httpx.HTTPError: If the API request fails
            ValueError: If the API returns an error message
        """
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
            "apikey": self.api_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.base_url, params=params)
            response.raise_for_status()

            data = response.json()

            # Check for API error messages
            if "Error Message" in data:
                raise ValueError(f"API Error: {data['Error Message']}")

            if "Note" in data:
                raise ValueError(f"API Rate Limit: {data['Note']}")

            return data


# Global service instance
alphavantage_service = AlphaVantageService()

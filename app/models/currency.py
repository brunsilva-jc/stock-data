"""
Data models and processors for cryptocurrency information.
"""
from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel


class TimeSeriesData(BaseModel):
    """Individual time series data point."""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class CurrencyMetadata(BaseModel):
    """Metadata about the cryptocurrency."""
    information: str
    digital_currency_code: str
    digital_currency_name: str
    market_code: str
    market_name: str
    last_refreshed: str
    time_zone: str


class CalculatedMetrics(BaseModel):
    """Calculated metrics from the time series data."""
    latest_price: float
    latest_volume: float
    latest_date: str
    daily_change: Optional[float] = None
    daily_change_percent: Optional[float] = None
    weekly_avg: Optional[float] = None
    weekly_high: Optional[float] = None
    weekly_low: Optional[float] = None
    monthly_avg: Optional[float] = None
    monthly_high: Optional[float] = None
    monthly_low: Optional[float] = None


class CurrencyResponse(BaseModel):
    """Formatted response for currency data."""
    metadata: CurrencyMetadata
    metrics: CalculatedMetrics
    recent_data: List[TimeSeriesData]


class CurrencyDataProcessor:
    """Process and calculate metrics from raw AlphaVantage data."""

    @staticmethod
    def parse_metadata(raw_metadata: Dict) -> CurrencyMetadata:
        """Parse metadata from API response."""
        return CurrencyMetadata(
            information=raw_metadata.get("1. Information", ""),
            digital_currency_code=raw_metadata.get("2. Digital Currency Code", ""),
            digital_currency_name=raw_metadata.get("3. Digital Currency Name", ""),
            market_code=raw_metadata.get("4. Market Code", ""),
            market_name=raw_metadata.get("5. Market Name", ""),
            last_refreshed=raw_metadata.get("6. Last Refreshed", ""),
            time_zone=raw_metadata.get("7. Time Zone", "")
        )

    @staticmethod
    def parse_time_series(raw_time_series: Dict, market_code: str = "USD") -> List[TimeSeriesData]:
        """
        Parse time series data from API response.

        AlphaVantage returns data with simple numbered keys:
        - "1. open": Opening price in market currency (USD)
        - "2. high": Highest price of the day
        - "3. low": Lowest price of the day
        - "4. close": Closing price (most important for calculations)
        - "5. volume": Trading volume in cryptocurrency units
        """
        series_data = []
        for date_str, values in raw_time_series.items():
            series_data.append(TimeSeriesData(
                date=date_str,
                open=float(values.get("1. open", 0)),
                high=float(values.get("2. high", 0)),
                low=float(values.get("3. low", 0)),
                close=float(values.get("4. close", 0)),
                volume=float(values.get("5. volume", 0))
            ))
        # Sort by date descending (most recent first)
        series_data.sort(key=lambda x: x.date, reverse=True)
        return series_data

    @staticmethod
    def calculate_metrics(time_series: List[TimeSeriesData]) -> CalculatedMetrics:
        """Calculate relevant metrics from time series data."""
        if not time_series:
            raise ValueError("No time series data available")

        latest = time_series[0]

        # Daily change (if we have at least 2 days)
        daily_change = None
        daily_change_percent = None
        if len(time_series) > 1:
            previous = time_series[1]
            daily_change = latest.close - previous.close
            daily_change_percent = (daily_change / previous.close) * 100 if previous.close else None

        # Weekly metrics (last 7 days)
        weekly_data = time_series[:7]
        weekly_avg = sum(d.close for d in weekly_data) / len(weekly_data) if weekly_data else None
        weekly_high = max(d.high for d in weekly_data) if weekly_data else None
        weekly_low = min(d.low for d in weekly_data) if weekly_data else None

        # Monthly metrics (last 30 days)
        monthly_data = time_series[:30]
        monthly_avg = sum(d.close for d in monthly_data) / len(monthly_data) if monthly_data else None
        monthly_high = max(d.high for d in monthly_data) if monthly_data else None
        monthly_low = min(d.low for d in monthly_data) if monthly_data else None

        return CalculatedMetrics(
            latest_price=latest.close,
            latest_volume=latest.volume,
            latest_date=latest.date,
            daily_change=round(daily_change, 2) if daily_change else None,
            daily_change_percent=round(daily_change_percent, 2) if daily_change_percent else None,
            weekly_avg=round(weekly_avg, 2) if weekly_avg else None,
            weekly_high=round(weekly_high, 2) if weekly_high else None,
            weekly_low=round(weekly_low, 2) if weekly_low else None,
            monthly_avg=round(monthly_avg, 2) if monthly_avg else None,
            monthly_high=round(monthly_high, 2) if monthly_high else None,
            monthly_low=round(monthly_low, 2) if monthly_low else None
        )

    @classmethod
    def process_response(cls, raw_data: Dict) -> CurrencyResponse:
        """
        Process raw API response into structured format.

        Args:
            raw_data: Raw response from AlphaVantage API

        Returns:
            CurrencyResponse with metadata, metrics, and recent data
        """
        metadata = cls.parse_metadata(raw_data.get("Meta Data", {}))

        time_series_key = "Time Series (Digital Currency Daily)"
        raw_time_series = raw_data.get(time_series_key, {})

        time_series = cls.parse_time_series(raw_time_series, metadata.market_code)
        metrics = cls.calculate_metrics(time_series)

        # Return only last 10 days of data for brevity
        recent_data = time_series[:10]

        return CurrencyResponse(
            metadata=metadata,
            metrics=metrics,
            recent_data=recent_data
        )

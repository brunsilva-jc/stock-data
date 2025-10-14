# Stock Data API

A FastAPI application that fetches and displays cryptocurrency data from the AlphaVantage API. The project provides structured endpoints to retrieve digital currency information with calculated metrics for future dashboard integration.

## Features

- **Health Check Endpoint**: Monitor application status
- **Cryptocurrency Data**: Fetch daily time series data for cryptocurrencies
- **Calculated Metrics**: Automatic calculation of:
  - Latest price and volume
  - Daily price changes (absolute and percentage)
  - Weekly averages, highs, and lows
  - Monthly averages, highs, and lows
- **Structured Data Processing**: Clean JSON responses ready for dashboard consumption
- **Test-First Approach**: Comprehensive pytest test suite included
- **Environment Configuration**: Secure API key management via .env file

## Project Structure

```
stock-data-project/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app with routes
│   ├── config.py            # Environment configuration
│   ├── services/
│   │   ├── __init__.py
│   │   └── alphavantage.py  # AlphaVantage API client
│   └── models/
│       ├── __init__.py
│       └── currency.py      # Data models and processors
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Test suite
├── .env                     # Environment variables (not in git)
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /home/bruno/learning/stock-data/stock-data-project
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   The `.env` file is already created with your AlphaVantage API key. You can modify it if needed:
   ```env
   ALPHAVANTAGE_API_KEY=F6YFCLQZ340BZ9ND
   DEFAULT_SYMBOL=BTC
   DEFAULT_MARKET=USD
   ```

## Running the Application

Start the FastAPI server using uvicorn:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Root Endpoint
- **GET /** - Welcome message with available endpoints

### Health Check
- **GET /health** - Check application health status
  ```json
  {
    "status": "healthy",
    "service": "Stock Data API",
    "version": "1.0.0"
  }
  ```

### Home (Default Cryptocurrency)
- **GET /home** - Get Bitcoin data (default)
- Returns processed cryptocurrency data with metadata, calculated metrics, and recent time series

### Specific Cryptocurrency
- **GET /currency/{symbol}** - Get data for a specific cryptocurrency
- **Parameters**:
  - `symbol` (path): Cryptocurrency symbol (e.g., BTC, ETH, LTC)
  - `market` (query, optional): Market currency (default: USD)
- **Example**: `/currency/ETH?market=USD`

### Interactive Documentation
- **GET /docs** - Swagger UI interactive documentation
- **GET /redoc** - ReDoc documentation

## Response Structure

The API returns cryptocurrency data in the following structure:

```json
{
  "metadata": {
    "information": "Daily Prices and Volumes for Digital Currency",
    "digital_currency_code": "BTC",
    "digital_currency_name": "Bitcoin",
    "market_code": "USD",
    "market_name": "United States Dollar",
    "last_refreshed": "2024-01-15",
    "time_zone": "UTC"
  },
  "metrics": {
    "latest_price": 42500.00,
    "latest_volume": 1000000.00,
    "latest_date": "2024-01-15",
    "daily_change": 700.00,
    "daily_change_percent": 1.67,
    "weekly_avg": 42000.00,
    "weekly_high": 43500.00,
    "weekly_low": 40500.00,
    "monthly_avg": 41800.00,
    "monthly_high": 44000.00,
    "monthly_low": 39000.00
  },
  "recent_data": [
    {
      "date": "2024-01-15",
      "open": 42000.00,
      "high": 43000.00,
      "low": 41500.00,
      "close": 42500.00,
      "volume": 1000000.00
    }
    // ... up to 10 most recent days
  ]
}
```

## Running Tests

The project includes a comprehensive test suite demonstrating Test-First development practices.

Run all tests:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run with coverage report:
```bash
pytest --cov=app tests/
```

## Development

### Adding New Cryptocurrency Symbols

To fetch data for different cryptocurrencies, use the `/currency/{symbol}` endpoint with any valid cryptocurrency symbol supported by AlphaVantage:

- Bitcoin: `BTC`
- Ethereum: `ETH`
- Litecoin: `LTC`
- And many more...

### Extending the Data Processing

The `CurrencyDataProcessor` class in `app/models/currency.py` provides methods for processing raw API data. You can extend it to add more calculated metrics or custom data transformations.

### Future Dashboard Integration

The structured response format is designed to be easily consumed by frontend dashboards. The calculated metrics provide ready-to-use data points for:
- Price trend charts
- Volume analysis
- Volatility indicators
- Performance comparisons

## API Rate Limits

AlphaVantage free tier has the following limits:
- 5 API requests per minute
- 100 API requests per day

The application includes error handling for rate limit responses.

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **HTTPX**: Async HTTP client for API requests
- **Pydantic**: Data validation and settings management
- **Pytest**: Testing framework with async support

## License

This project is for educational and personal use.

## Support

For AlphaVantage API documentation, visit: https://www.alphavantage.co/documentation/

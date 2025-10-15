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
├── assets/
│   └── crypto.png           # Dashboard logo
├── tests/
│   ├── __init__.py
│   └── test_main.py         # Test suite
├── streamlit_app.py         # Streamlit dashboard application
├── Dockerfile               # Docker container configuration
├── docker-compose.yml       # Docker Compose orchestration
├── .dockerignore            # Docker build exclusions
├── Makefile                 # Convenience commands for Docker
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template (safe for git)
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation

1. **Clone or navigate to the project directory**:
   ```bash
   cd /your-repository/
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

## Docker Deployment

The application is fully containerized and ready for Docker deployment. This is the **recommended method** for production environments and cloud deployments.

### Prerequisites

- Docker Engine 20.10+ installed
- Docker Compose V2 installed
- (Optional) Make utility for convenience commands

### Quick Start with Docker

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd stock-data-project
   ```

2. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your AlphaVantage API key
   ```

3. **Build and run with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

   The dashboard will be available at `http://localhost:8501`

4. **View logs**:
   ```bash
   docker-compose logs -f streamlit
   ```

5. **Stop the application**:
   ```bash
   docker-compose down
   ```

### Using Makefile (Convenience Commands)

If you have `make` installed, you can use these convenient commands:

```bash
make build      # Build Docker image
make up         # Start containers in detached mode
make dev        # Start in foreground (see logs)
make down       # Stop containers
make restart    # Restart containers
make logs       # View logs
make shell      # Open shell in container
make clean      # Remove all containers, images, and volumes
make help       # Show all available commands
```

### Docker Configuration Files

- **Dockerfile**: Production-ready multi-stage build with non-root user
- **docker-compose.yml**: Orchestration configuration with health checks
- **.dockerignore**: Optimizes build by excluding unnecessary files
- **.env.example**: Template for environment variables

### Production Deployment

#### Security Best Practices

1. **Never commit .env file** - It contains your API key
2. **Use secrets management** in production:
   - AWS Secrets Manager (AWS ECS/Fargate)
   - Google Secret Manager (Google Cloud Run)
   - Azure Key Vault (Azure Container Instances)
   - Kubernetes Secrets (K8s deployments)

3. **Environment Variables in Production**:
   ```bash
   # Pass directly in docker-compose or cloud platform
   ALPHAVANTAGE_API_KEY=your_production_key
   DEFAULT_SYMBOL=BTC
   DEFAULT_MARKET=USD
   ```

#### Cloud Deployment Options

**1. AWS (Amazon Web Services)**
- **ECS Fargate**: Serverless container deployment
  ```bash
  # Push image to ECR
  aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
  docker tag crypto-dashboard:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-dashboard:latest
  docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/crypto-dashboard:latest
  ```
- Use AWS Secrets Manager for API key
- Configure health checks using the built-in endpoint

**2. Google Cloud Platform**
- **Cloud Run**: Fully managed serverless platform
  ```bash
  # Build and deploy
  gcloud builds submit --tag gcr.io/PROJECT_ID/crypto-dashboard
  gcloud run deploy crypto-dashboard --image gcr.io/PROJECT_ID/crypto-dashboard --platform managed
  ```
- Auto-scaling based on traffic
- Pay only for actual usage

**3. Azure**
- **Azure Container Instances**: Simple container deployment
  ```bash
  az container create \
    --resource-group myResourceGroup \
    --name crypto-dashboard \
    --image crypto-dashboard:latest \
    --dns-name-label crypto-dashboard \
    --ports 8501
  ```

**4. DigitalOcean**
- **App Platform**: Easy deployment with git integration
- Automatic HTTPS and built-in CDN

**5. Heroku**
- **Container Registry**:
  ```bash
  heroku container:push web -a your-app-name
  heroku container:release web -a your-app-name
  ```

#### Health Checks

The Docker container includes built-in health checks:
- Endpoint: `http://localhost:8501/_stcore/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3

This allows container orchestrators (ECS, K8s, etc.) to automatically monitor and restart unhealthy containers.

#### Resource Limits

For production, consider setting resource limits in `docker-compose.yml`:

```yaml
services:
  streamlit:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

## Running the Application

### Option 1: Streamlit Dashboard (Recommended for Visualization)

Start the Streamlit dashboard for interactive data visualization:

```bash
streamlit run streamlit_app.py
```

The dashboard will be available at `http://localhost:8501`

**Features:**
- Interactive cryptocurrency selection (BTC, ETH, LTC, XRP, BCH, ADA, DOT, LINK)
- Market currency selection (USD, EUR, GBP, JPY, CNY)
- Real-time price and volume charts
- Key metrics dashboard with daily changes
- Weekly and monthly statistical analysis
- Recent OHLCV data table
- Data caching to respect API rate limits

### Option 2: FastAPI Server (For API Access)

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

## Streamlit Dashboard

The project includes a comprehensive Streamlit dashboard for visualizing cryptocurrency data:

### Dashboard Components

1. **Sidebar Configuration**
   - Cryptocurrency selector (8 popular cryptocurrencies)
   - Market currency selector (USD, EUR, GBP, JPY, CNY)
   - Refresh button to clear cache and fetch new data

2. **Key Metrics Cards**
   - Latest price with daily change indicator
   - Daily change percentage
   - Trading volume
   - Last update timestamp

3. **Interactive Charts**
   - Price trend line chart with high/low ranges
   - Trading volume bar chart
   - Plotly-powered interactive visualizations

4. **Statistical Analysis**
   - Weekly statistics (7-day averages, highs, lows)
   - Monthly statistics (30-day averages, highs, lows)

5. **Data Tables**
   - Recent OHLCV (Open, High, Low, Close, Volume) data table
   - Last 10 days of detailed price information

### Features

- **Data Caching**: 5-minute cache to minimize API calls and respect rate limits
- **Error Handling**: Graceful handling of API errors and rate limit messages
- **Responsive Design**: Clean, professional interface with wide layout
- **Real-time Updates**: Manual refresh option to fetch latest data

## Technologies Used

- **FastAPI**: Modern, fast web framework for building APIs
- **Streamlit**: Framework for creating interactive data dashboards
- **Plotly**: Interactive visualization library for charts
- **Pandas**: Data manipulation and analysis
- **Uvicorn**: ASGI server for running FastAPI applications
- **HTTPX**: Async HTTP client for API requests
- **Pydantic**: Data validation and settings management
- **Pytest**: Testing framework with async support

## License

This project is for educational and personal use.

## Support

For AlphaVantage API documentation, visit: https://www.alphavantage.co/documentation/

"""
Test suite for the FastAPI application.
Demonstrates Test-First mentality with basic test examples.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.currency import CurrencyResponse, CurrencyMetadata, CalculatedMetrics, TimeSeriesData


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_200(self):
        """Test that health check endpoint returns 200 status code."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_returns_correct_structure(self):
        """Test that health check returns expected JSON structure."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "service" in data
        assert "version" in data
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for the root / endpoint."""

    def test_root_returns_200(self):
        """Test that root endpoint returns 200 status code."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_welcome_message(self):
        """Test that root endpoint returns welcome message and endpoints info."""
        response = client.get("/")
        data = response.json()

        assert "message" in data
        assert "endpoints" in data
        assert "/health" in data["endpoints"]
        assert "/home" in data["endpoints"]


class TestHomeEndpoint:
    """Tests for the /home endpoint."""

    @pytest.fixture
    def mock_api_response(self):
        """Fixture providing a mock API response."""
        return {
            "Meta Data": {
                "1. Information": "Daily Prices and Volumes for Digital Currency",
                "2. Digital Currency Code": "BTC",
                "3. Digital Currency Name": "Bitcoin",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar",
                "6. Last Refreshed": "2024-01-15",
                "7. Time Zone": "UTC"
            },
            "Time Series (Digital Currency Daily)": {
                "2024-01-15": {
                    "1a. open (USD)": "42000.00",
                    "2a. high (USD)": "43000.00",
                    "3a. low (USD)": "41500.00",
                    "4a. close (USD)": "42500.00",
                    "5. volume": "1000000.00"
                },
                "2024-01-14": {
                    "1a. open (USD)": "41000.00",
                    "2a. high (USD)": "42000.00",
                    "3a. low (USD)": "40500.00",
                    "4a. close (USD)": "41800.00",
                    "5. volume": "950000.00"
                }
            }
        }

    @patch('app.services.alphavantage.alphavantage_service.get_digital_currency_daily')
    def test_home_endpoint_returns_200_with_valid_data(self, mock_get_data, mock_api_response):
        """Test that /home endpoint returns 200 with processed data."""
        # Mock the async method
        mock_get_data.return_value = mock_api_response

        response = client.get("/home")
        assert response.status_code == 200

    @patch('app.services.alphavantage.alphavantage_service.get_digital_currency_daily')
    def test_home_endpoint_returns_currency_response_structure(self, mock_get_data, mock_api_response):
        """Test that /home endpoint returns correct response structure."""
        mock_get_data.return_value = mock_api_response

        response = client.get("/home")
        data = response.json()

        # Check main keys exist
        assert "metadata" in data
        assert "metrics" in data
        assert "recent_data" in data

        # Check metadata structure
        assert "digital_currency_code" in data["metadata"]
        assert "digital_currency_name" in data["metadata"]

        # Check metrics structure
        assert "latest_price" in data["metrics"]
        assert "latest_volume" in data["metrics"]

    @patch('app.services.alphavantage.alphavantage_service.get_digital_currency_daily')
    def test_home_endpoint_handles_api_errors(self, mock_get_data):
        """Test that /home endpoint handles API errors gracefully."""
        mock_get_data.side_effect = ValueError("API Error: Invalid symbol")

        response = client.get("/home")
        assert response.status_code == 400
        assert "API Error" in response.json()["detail"]


class TestCurrencyEndpoint:
    """Tests for the /currency/{symbol} endpoint."""

    @patch('app.services.alphavantage.alphavantage_service.get_digital_currency_daily')
    def test_currency_endpoint_accepts_symbol_parameter(self, mock_get_data):
        """Test that /currency endpoint accepts symbol parameter."""
        mock_get_data.return_value = {
            "Meta Data": {
                "1. Information": "Daily Prices",
                "2. Digital Currency Code": "ETH",
                "3. Digital Currency Name": "Ethereum",
                "4. Market Code": "USD",
                "5. Market Name": "United States Dollar",
                "6. Last Refreshed": "2024-01-15",
                "7. Time Zone": "UTC"
            },
            "Time Series (Digital Currency Daily)": {
                "2024-01-15": {
                    "1a. open (USD)": "2500.00",
                    "2a. high (USD)": "2600.00",
                    "3a. low (USD)": "2450.00",
                    "4a. close (USD)": "2550.00",
                    "5. volume": "500000.00"
                }
            }
        }

        response = client.get("/currency/ETH")
        assert response.status_code == 200

        # Verify the service was called with uppercase symbol
        mock_get_data.assert_called_once()
        args = mock_get_data.call_args[1]
        assert args["symbol"] == "ETH"


class TestDataProcessing:
    """Tests for data processing logic."""

    def test_calculate_metrics_with_valid_data(self):
        """Test that metrics are calculated correctly from time series data."""
        from app.models.currency import CurrencyDataProcessor

        time_series = [
            TimeSeriesData(date="2024-01-15", open=42000, high=43000, low=41500, close=42500, volume=1000000),
            TimeSeriesData(date="2024-01-14", open=41000, high=42000, low=40500, close=41800, volume=950000)
        ]

        metrics = CurrencyDataProcessor.calculate_metrics(time_series)

        assert metrics.latest_price == 42500
        assert metrics.latest_volume == 1000000
        assert metrics.daily_change == 700  # 42500 - 41800
        assert metrics.daily_change_percent > 0

    def test_calculate_metrics_raises_error_with_empty_data(self):
        """Test that calculate_metrics raises error with empty time series."""
        from app.models.currency import CurrencyDataProcessor

        with pytest.raises(ValueError, match="No time series data available"):
            CurrencyDataProcessor.calculate_metrics([])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

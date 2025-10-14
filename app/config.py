"""
Configuration module for the FastAPI application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    alphavantage_api_key: str = Field(..., alias="ALPHAVANTAGE_API_KEY")
    default_symbol: str = Field(default="BTC", alias="DEFAULT_SYMBOL")
    default_market: str = Field(default="USD", alias="DEFAULT_MARKET")

    # AlphaVantage API configuration
    alphavantage_base_url: str = "https://www.alphavantage.co/query"

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

"""
Configuration module for the FastAPI application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AlphaVantage API configuration
    alphavantage_api_key: str = Field(..., alias="ALPHAVANTAGE_API_KEY")
    default_symbol: str = Field(default="BTC", alias="DEFAULT_SYMBOL")
    default_market: str = Field(default="USD", alias="DEFAULT_MARKET")
    alphavantage_base_url: str = "https://www.alphavantage.co/query"

    # Database configuration
    database_url: str = Field(
        default="postgresql://crypto_user:crypto_pass@localhost:5432/crypto_db",
        alias="DATABASE_URL"
    )
    postgres_db: str = Field(default="crypto_db", alias="POSTGRES_DB")
    postgres_user: str = Field(default="crypto_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="crypto_pass", alias="POSTGRES_PASSWORD")

    # Database connection pool settings
    db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    db_echo: bool = Field(default=False, alias="DB_ECHO")  # Log SQL queries

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

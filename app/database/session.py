"""
Database session management and connection pooling.
Handles SQLAlchemy engine creation and session lifecycle.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import Pool
from typing import Generator
import logging

from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.db_echo,  # Log SQL queries (useful for development)
)

# Add connection pool event listeners for monitoring (useful for learning/debugging)
@event.listens_for(Pool, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log when a new database connection is established."""
    logger.debug("Database connection established")


@event.listens_for(Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log when a connection is checked out from the pool."""
    logger.debug("Connection checked out from pool")


@event.listens_for(Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log when a connection is returned to the pool."""
    logger.debug("Connection returned to pool")


# Create session factory
# autocommit=False: Transactions must be explicitly committed
# autoflush=False: Don't automatically flush changes (more control)
# bind=engine: Associate sessions with our engine
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class for all database models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function that provides a database session.

    This function is designed to be used with FastAPI's Depends() system.
    It creates a new database session for each request and automatically
    closes it when the request is complete.

    Usage in FastAPI:
        @app.get("/some-endpoint")
        def some_endpoint(db: Session = Depends(get_db)):
            # Use db session here
            pass

    Yields:
        Session: SQLAlchemy database session

    Example:
        with next(get_db()) as db:
            # Use db session
            pass
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This function should be called when the application starts.
    It creates all tables defined in the Base metadata (all models
    that inherit from Base).

    Note: In production, you should use Alembic migrations instead
    of this function. This is useful for development and testing.
    """
    try:
        # Import all models here to ensure they are registered with Base
        from app.database import models  # noqa: F401

        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


def check_db_connection() -> bool:
    """
    Check if the database connection is working.

    Returns:
        bool: True if connection is successful, False otherwise

    Example:
        if check_db_connection():
            print("Database is accessible")
        else:
            print("Database connection failed")
    """
    try:
        # Try to connect and execute a simple query
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection check successful")
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_db_info() -> dict:
    """
    Get information about the database connection and pool.

    Useful for monitoring and debugging.

    Returns:
        dict: Database connection information
    """
    pool = engine.pool
    return {
        "database_url": settings.database_url.split("@")[-1],  # Hide credentials
        "pool_size": pool.size(),
        "checked_in_connections": pool.checkedin(),
        "overflow": pool.overflow(),
        "checked_out_connections": pool.checkedout(),
    }

"""Convert crypto_prices to TimescaleDB hypertable

Revision ID: a1ab1bdb31b1
Revises: 2844afb4c2af
Create Date: 2025-11-04 09:37:25.767451

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1ab1bdb31b1'
down_revision: Union[str, None] = '2844afb4c2af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert crypto_prices table to TimescaleDB hypertable."""
    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # Convert crypto_prices to hypertable partitioned by timestamp
    # chunk_time_interval = 7 days (good for cryptocurrency data)
    op.execute("""
        SELECT create_hypertable(
            'crypto_prices',
            'timestamp',
            chunk_time_interval => INTERVAL '7 days',
            if_not_exists => TRUE
        );
    """)

    # Add compression policy (compress data older than 30 days)
    op.execute("""
        ALTER TABLE crypto_prices SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'currency_id',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
    """)

    op.execute("""
        SELECT add_compression_policy('crypto_prices', INTERVAL '30 days');
    """)

    # Add retention policy (keep data for 1 year)
    op.execute("""
        SELECT add_retention_policy('crypto_prices', INTERVAL '1 year');
    """)


def downgrade() -> None:
    """Remove TimescaleDB hypertable configuration."""
    # Remove retention policy
    op.execute("""
        SELECT remove_retention_policy('crypto_prices', if_exists => TRUE);
    """)

    # Remove compression policy
    op.execute("""
        SELECT remove_compression_policy('crypto_prices', if_exists => TRUE);
    """)

    # Note: Cannot directly convert hypertable back to regular table
    # This would require recreating the table and migrating data
    # For now, we'll just remove the policies

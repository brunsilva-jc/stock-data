-- Initialize TimescaleDB extension and create initial schema
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create extension for UUID generation (useful for future features)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'TimescaleDB initialized successfully';
END $$;

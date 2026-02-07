-- PostgreSQL initialization script for Django Finance
-- This script runs on first container creation

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Grant permissions to the postgres user
GRANT ALL PRIVILEGES ON DATABASE django_finance TO postgres;

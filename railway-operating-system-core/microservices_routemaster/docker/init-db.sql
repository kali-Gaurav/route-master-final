-- Railway Operating System - Multi-Tenant Database Schema
-- PostgreSQL initialization script

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create base schema for system-wide tables
CREATE SCHEMA IF NOT EXISTS system;

-- ===============================================
-- SYSTEM TABLES (Shared across all tenants)
-- ===============================================

-- Tenants table (stores client organizations)
CREATE TABLE system.tenants (
    tenant_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_name VARCHAR(255) NOT NULL UNIQUE,
    tenant_domain VARCHAR(255) UNIQUE,
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    subscription_plan VARCHAR(50) DEFAULT 'basic',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys table
CREATE TABLE system.api_keys (
    api_key_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES system.tenants(tenant_id) ON DELETE CASCADE,
    api_key_hash VARCHAR(255) NOT NULL UNIQUE,
    api_key_name VARCHAR(100),
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_minute INTEGER DEFAULT 1000,
    rate_limit_per_hour INTEGER DEFAULT 10000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- System audit log
CREATE TABLE system.audit_log (
    audit_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID REFERENCES system.tenants(tenant_id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    user_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ===============================================
-- TENANT SCHEMA CREATION FUNCTION
-- ===============================================

-- Function to create a new tenant schema
CREATE OR REPLACE FUNCTION system.create_tenant_schema(tenant_uuid UUID, tenant_name TEXT)
RETURNS VOID AS $$
DECLARE
    schema_name TEXT;
BEGIN
    -- Create schema name from tenant UUID (remove hyphens and prefix)
    schema_name := 'tenant_' || replace(tenant_uuid::TEXT, '-', '');

    -- Create the tenant schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', schema_name);

    -- Create tenant-specific tables
    EXECUTE format('
        -- Stations master table
        CREATE TABLE %I.stations_master (
            station_id SERIAL PRIMARY KEY,
            station_code VARCHAR(10) NOT NULL UNIQUE,
            station_name VARCHAR(255) NOT NULL,
            city VARCHAR(100),
            state VARCHAR(100),
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            is_junction BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Trains master table
        CREATE TABLE %I.trains_master (
            train_id SERIAL PRIMARY KEY,
            train_no INTEGER NOT NULL UNIQUE,
            train_name VARCHAR(255) NOT NULL,
            train_type VARCHAR(50),
            source_station VARCHAR(10),
            destination_station VARCHAR(10),
            distance INTEGER,
            duration_minutes INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Train schedule table
        CREATE TABLE %I.train_schedule (
            schedule_id SERIAL PRIMARY KEY,
            train_no INTEGER NOT NULL REFERENCES %I.trains_master(train_no),
            station_code VARCHAR(10) NOT NULL,
            station_name VARCHAR(255),
            arrival_time TIME,
            departure_time TIME,
            day_of_journey INTEGER DEFAULT 0,
            distance_from_source INTEGER DEFAULT 0,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Train running days
        CREATE TABLE %I.train_running_days (
            train_no INTEGER PRIMARY KEY REFERENCES %I.trains_master(train_no),
            mon BOOLEAN DEFAULT false,
            tue BOOLEAN DEFAULT false,
            wed BOOLEAN DEFAULT false,
            thu BOOLEAN DEFAULT false,
            fri BOOLEAN DEFAULT false,
            sat BOOLEAN DEFAULT false,
            sun BOOLEAN DEFAULT false,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        -- Route cache table
        CREATE TABLE %I.route_cache (
            cache_id SERIAL PRIMARY KEY,
            cache_key VARCHAR(255) NOT NULL UNIQUE,
            route_data JSONB NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP + INTERVAL ''1 hour''
        );

        -- Job queue table
        CREATE TABLE %I.job_queue (
            job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            job_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) DEFAULT ''pending'',
            payload JSONB,
            result JSONB,
            error_message TEXT,
            priority INTEGER DEFAULT 1,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP WITH TIME ZONE,
            completed_at TIMESTAMP WITH TIME ZONE,
            tenant_id UUID NOT NULL
        );

        -- Create indexes for performance
        CREATE INDEX idx_stations_code ON %I.stations_master(station_code);
        CREATE INDEX idx_stations_name ON %I.stations_master(station_name);
        CREATE INDEX idx_trains_no ON %I.trains_master(train_no);
        CREATE INDEX idx_schedule_train ON %I.train_schedule(train_no);
        CREATE INDEX idx_schedule_station ON %I.train_schedule(station_code);
        CREATE INDEX idx_route_cache_key ON %I.route_cache(cache_key);
        CREATE INDEX idx_route_cache_expires ON %I.route_cache(expires_at);
        CREATE INDEX idx_jobs_status ON %I.job_queue(status);
        CREATE INDEX idx_jobs_tenant ON %I.job_queue(tenant_id);
        CREATE INDEX idx_jobs_created ON %I.job_queue(created_at);
    ', schema_name, schema_name, schema_name, schema_name, schema_name, schema_name,
       schema_name, schema_name, schema_name, schema_name, schema_name, schema_name);

    -- Insert tenant metadata
    INSERT INTO system.tenants (tenant_id, tenant_name, is_active)
    VALUES (tenant_uuid, tenant_name, true);

END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- UTILITY FUNCTIONS
-- ===============================================

-- Function to get tenant schema name
CREATE OR REPLACE FUNCTION system.get_tenant_schema(tenant_uuid UUID)
RETURNS TEXT AS $$
BEGIN
    RETURN 'tenant_' || replace(tenant_uuid::TEXT, '-', '');
END;
$$ LANGUAGE plpgsql;

-- Function to validate API key and return tenant info
CREATE OR REPLACE FUNCTION system.validate_api_key(api_key_hash TEXT)
RETURNS TABLE(
    tenant_id UUID,
    tenant_name TEXT,
    is_active BOOLEAN,
    rate_limit_per_minute INTEGER,
    rate_limit_per_hour INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.tenant_id,
        t.tenant_name,
        t.is_active,
        ak.rate_limit_per_minute,
        ak.rate_limit_per_hour
    FROM system.api_keys ak
    JOIN system.tenants t ON ak.tenant_id = t.tenant_id
    WHERE ak.api_key_hash = api_key_hash
    AND ak.is_active = true
    AND (ak.expires_at IS NULL OR ak.expires_at > CURRENT_TIMESTAMP)
    AND t.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- ===============================================
-- INITIAL DATA SETUP
-- ===============================================

-- Create default tenant for development
INSERT INTO system.tenants (tenant_id, tenant_name, tenant_domain)
VALUES ('550e8400-e29b-41d4-a716-446655440000', 'Default Tenant', 'default.railwayos.com');

-- Create default API key for development
INSERT INTO system.api_keys (tenant_id, api_key_hash, api_key_name, rate_limit_per_minute, rate_limit_per_hour)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    encode(digest('dev-api-key-12345', 'sha256'), 'hex'),
    'Development API Key',
    1000,
    10000
);

-- Create the default tenant schema
SELECT system.create_tenant_schema('550e8400-e29b-41d4-a716-446655440000', 'Default Tenant');

-- ===============================================
-- PERFORMANCE AND SECURITY
-- ===============================================

-- Create indexes on system tables
CREATE INDEX idx_api_keys_hash ON system.api_keys(api_key_hash);
CREATE INDEX idx_api_keys_tenant ON system.api_keys(tenant_id);
CREATE INDEX idx_tenants_domain ON system.tenants(tenant_domain);
CREATE INDEX idx_audit_tenant ON system.audit_log(tenant_id);
CREATE INDEX idx_audit_created ON system.audit_log(created_at);

-- Row Level Security (RLS) policies
ALTER TABLE system.tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE system.api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE system.audit_log ENABLE ROW LEVEL SECURITY;

-- Policies will be implemented in the application layer for now
-- as PostgreSQL RLS requires careful consideration of multi-tenant access patterns
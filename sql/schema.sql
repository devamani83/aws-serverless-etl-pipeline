-- Advisory Performance Database Schema
-- Production-ready schema with indexes for high performance

-- Create database (run separately if needed)
-- CREATE DATABASE advisory_performance;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id VARCHAR(50) PRIMARY KEY,
    account_name VARCHAR(255) NOT NULL,
    portfolio_id VARCHAR(50),
    client_id VARCHAR(50),
    account_type VARCHAR(50),
    inception_date DATE,
    status VARCHAR(20) DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance data table (partitioned by date for better performance)
CREATE TABLE IF NOT EXISTS performance_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL REFERENCES accounts(account_id),
    as_of_date DATE NOT NULL,
    beginning_market_value DECIMAL(18,2),
    contributions DECIMAL(18,2) DEFAULT 0,
    distributions DECIMAL(18,2) DEFAULT 0,
    income DECIMAL(18,2) DEFAULT 0,
    appreciation DECIMAL(18,2) DEFAULT 0,
    fees DECIMAL(18,2) DEFAULT 0,
    other_adjustments DECIMAL(18,2) DEFAULT 0,
    ending_market_value DECIMAL(18,2),
    
    -- Calculated fields
    net_flow DECIMAL(18,2),
    cumulative_net_flow DECIMAL(18,2),
    calculated_twrr DECIMAL(12,8),
    cumulative_twrr DECIMAL(12,8),
    
    -- Vendor provided data
    vendor_twrr DECIMAL(12,8),
    benchmark_return DECIMAL(12,8),
    
    -- Data quality and reconciliation
    twrr_tolerance_check BOOLEAN,
    twrr_variance DECIMAL(12,8),
    reconciliation_status VARCHAR(20) DEFAULT 'PENDING',
    data_source VARCHAR(50),
    file_name VARCHAR(255),
    
    -- Audit fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_by VARCHAR(100),
    
    -- Constraints
    UNIQUE(account_id, as_of_date)
) PARTITION BY RANGE (as_of_date);

-- Create partitions for current and future years
CREATE TABLE IF NOT EXISTS performance_data_2024 PARTITION OF performance_data
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE IF NOT EXISTS performance_data_2025 PARTITION OF performance_data
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

CREATE TABLE IF NOT EXISTS performance_data_2026 PARTITION OF performance_data
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- ETL processing log table
CREATE TABLE IF NOT EXISTS etl_processing_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500),
    vendor VARCHAR(50),
    processing_start_time TIMESTAMP,
    processing_end_time TIMESTAMP,
    records_processed INTEGER,
    records_inserted INTEGER,
    records_updated INTEGER,
    records_failed INTEGER,
    status VARCHAR(20) DEFAULT 'PROCESSING',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Data quality issues table
CREATE TABLE IF NOT EXISTS data_quality_issues (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    etl_log_id UUID REFERENCES etl_processing_log(id),
    account_id VARCHAR(50),
    as_of_date DATE,
    issue_type VARCHAR(50),
    issue_description TEXT,
    field_name VARCHAR(50),
    expected_value VARCHAR(255),
    actual_value VARCHAR(255),
    severity VARCHAR(20) DEFAULT 'MEDIUM',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reconciliation results table
CREATE TABLE IF NOT EXISTS reconciliation_results (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    as_of_date DATE NOT NULL,
    field_name VARCHAR(50),
    calculated_value DECIMAL(18,8),
    vendor_value DECIMAL(18,8),
    variance DECIMAL(18,8),
    tolerance_threshold DECIMAL(18,8),
    within_tolerance BOOLEAN,
    reconciliation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT
);

-- Indexes for high performance queries
CREATE INDEX IF NOT EXISTS idx_performance_data_account_date 
    ON performance_data (account_id, as_of_date DESC);

CREATE INDEX IF NOT EXISTS idx_performance_data_date 
    ON performance_data (as_of_date DESC);

CREATE INDEX IF NOT EXISTS idx_performance_data_reconciliation 
    ON performance_data (reconciliation_status, as_of_date);

CREATE INDEX IF NOT EXISTS idx_accounts_portfolio 
    ON accounts (portfolio_id);

CREATE INDEX IF NOT EXISTS idx_etl_log_status_date 
    ON etl_processing_log (status, processing_start_time DESC);

CREATE INDEX IF NOT EXISTS idx_data_quality_severity 
    ON data_quality_issues (severity, created_at DESC);

-- Function to calculate net flow
CREATE OR REPLACE FUNCTION calculate_net_flow(
    p_contributions DECIMAL,
    p_distributions DECIMAL
) RETURNS DECIMAL AS $$
BEGIN
    RETURN COALESCE(p_contributions, 0) - COALESCE(p_distributions, 0);
END;
$$ LANGUAGE plpgsql;

-- Function to calculate TWRR for a single period
CREATE OR REPLACE FUNCTION calculate_twrr_single_period(
    p_beginning_mv DECIMAL,
    p_ending_mv DECIMAL,
    p_net_flow DECIMAL
) RETURNS DECIMAL AS $$
DECLARE
    adjusted_beginning_mv DECIMAL;
BEGIN
    -- Handle zero or negative beginning market value
    IF p_beginning_mv <= 0 THEN
        RETURN NULL;
    END IF;
    
    -- Adjust beginning market value by net flow (simplified mid-period assumption)
    adjusted_beginning_mv := p_beginning_mv + (COALESCE(p_net_flow, 0) / 2);
    
    -- Calculate TWRR
    RETURN (p_ending_mv - adjusted_beginning_mv) / adjusted_beginning_mv;
END;
$$ LANGUAGE plpgsql;

-- Function to update cumulative calculations
CREATE OR REPLACE FUNCTION update_cumulative_calculations()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate net flow
    NEW.net_flow := calculate_net_flow(NEW.contributions, NEW.distributions);
    
    -- Calculate TWRR for this period
    NEW.calculated_twrr := calculate_twrr_single_period(
        NEW.beginning_market_value,
        NEW.ending_market_value,
        NEW.net_flow
    );
    
    -- Check TWRR tolerance
    IF NEW.vendor_twrr IS NOT NULL AND NEW.calculated_twrr IS NOT NULL THEN
        NEW.twrr_variance := ABS(NEW.calculated_twrr - NEW.vendor_twrr);
        NEW.twrr_tolerance_check := NEW.twrr_variance <= 0.0001; -- 1 basis point tolerance
    END IF;
    
    -- Update timestamp
    NEW.updated_at := CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate fields on insert/update
CREATE TRIGGER trigger_update_calculations
    BEFORE INSERT OR UPDATE ON performance_data
    FOR EACH ROW
    EXECUTE FUNCTION update_cumulative_calculations();

-- View for performance summary
CREATE OR REPLACE VIEW performance_summary AS
SELECT 
    pd.account_id,
    a.account_name,
    a.portfolio_id,
    pd.as_of_date,
    pd.beginning_market_value,
    pd.ending_market_value,
    pd.net_flow,
    pd.calculated_twrr,
    pd.vendor_twrr,
    pd.twrr_variance,
    pd.twrr_tolerance_check,
    pd.reconciliation_status,
    pd.data_source
FROM performance_data pd
JOIN accounts a ON pd.account_id = a.account_id
WHERE a.status = 'ACTIVE';

-- View for data quality dashboard
CREATE OR REPLACE VIEW data_quality_dashboard AS
SELECT 
    DATE_TRUNC('day', dqi.created_at) as issue_date,
    dqi.issue_type,
    dqi.severity,
    COUNT(*) as issue_count,
    COUNT(DISTINCT dqi.account_id) as affected_accounts
FROM data_quality_issues dqi
WHERE dqi.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE_TRUNC('day', dqi.created_at), dqi.issue_type, dqi.severity
ORDER BY issue_date DESC, issue_count DESC;

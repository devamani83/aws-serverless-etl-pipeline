# Advisory Performance ETL Pipeline - Operations Guide

## Overview

This document provides operational guidance for managing and maintaining the AWS serverless ETL pipeline for advisory performance data processing.

## Architecture Summary

The pipeline consists of:
- **AWS S3**: Data lake storage (raw, processed, temp, archive buckets)
- **AWS Lambda**: Event-driven orchestration and data processing
- **AWS Glue**: Large-scale ETL jobs and data cataloging
- **AWS Step Functions**: Workflow orchestration
- **Amazon RDS PostgreSQL**: Production database with millions of records
- **AWS CloudWatch**: Monitoring, logging, and alerting
- **AWS Secrets Manager**: Secure credential management

## Daily Operations

### 1. Morning Health Check

**Dashboard Review (5 minutes)**
```bash
# Check CloudWatch dashboard
aws cloudwatch get-dashboard --dashboard-name advisory-performance-etl-dashboard

# Review overnight processing
aws logs filter-log-events \
    --log-group-name /aws/glue/advisory-performance-etl \
    --start-time $(date -d "yesterday" +%s)000 \
    --filter-pattern "ERROR"
```

**Key Metrics to Review:**
- Pipeline success rate (target: >99%)
- Data quality score (target: >95%)
- TWRR reconciliation pass rate (target: >95%)
- Database performance (CPU <80%, connections <80)

### 2. File Processing Status

**Check S3 Buckets**
```bash
# Raw data bucket - new files
aws s3 ls s3://advisory-etl-raw-data/incoming/ --recursive

# Processing folder - currently processing
aws s3 ls s3://advisory-etl-raw-data/processing/ --recursive

# Archive folder - completed files
aws s3 ls s3://advisory-etl-archive/ --recursive | tail -10
```

**Step Functions Status**
```bash
# Check recent executions
aws stepfunctions list-executions \
    --state-machine-arn $(aws stepfunctions list-state-machines \
    --query "stateMachines[?name=='advisory-performance-etl-workflow'].stateMachineArn" \
    --output text) \
    --max-items 10
```

### 3. Database Health Check

**Connection Test**
```bash
# Test database connectivity
python3 scripts/test_db_connection.py
```

**Performance Metrics**
```sql
-- Active connections
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';

-- Recent ETL runs
SELECT 
    file_name,
    vendor,
    status,
    records_processed,
    processing_end_time - processing_start_time as duration
FROM etl_processing_log 
WHERE processing_start_time >= CURRENT_DATE - INTERVAL '1 day'
ORDER BY processing_start_time DESC;

-- Data quality summary
SELECT 
    DATE(created_at) as date,
    severity,
    COUNT(*) as issue_count
FROM data_quality_issues 
WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY DATE(created_at), severity
ORDER BY date DESC, severity;
```

## Weekly Operations

### 1. Performance Review

**Generate Weekly Report**
```bash
python3 scripts/generate_weekly_report.py --start-date $(date -d "7 days ago" +%Y-%m-%d)
```

**Review Metrics:**
- Total records processed
- Average processing time per file
- Error rates by vendor
- Data quality trends
- Cost analysis

### 2. Database Maintenance

**Partition Management**
```sql
-- Create next month's partition
SELECT create_monthly_partition('performance_data', 'YYYY-MM-DD');

-- Check partition sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE tablename LIKE 'performance_data_%'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Index Optimization**
```sql
-- Check index usage
SELECT 
    indexrelname,
    idx_tup_read,
    idx_tup_fetch,
    idx_scan
FROM pg_stat_user_indexes 
WHERE schemaname = 'public'
ORDER BY idx_scan DESC;

-- Reindex if needed
REINDEX INDEX CONCURRENTLY idx_performance_data_account_date;
```

### 3. Storage Cleanup

**S3 Lifecycle Management**
```bash
# Check storage usage
aws s3 ls s3://advisory-etl-temp/ --recursive --summarize

# Clean up old temp files (manual if needed)
aws s3 rm s3://advisory-etl-temp/ --recursive --exclude "*" --include "*$(date -d '7 days ago' +%Y-%m-%d)*"
```

## Monthly Operations

### 1. Security Review

**Access Review**
```bash
# Review IAM policies
aws iam list-attached-role-policies --role-name GlueServiceRole
aws iam list-attached-role-policies --role-name LambdaExecutionRole

# Check secrets rotation
aws secretsmanager describe-secret --secret-id advisory-etl/db-password
```

**Compliance Check**
- Review data retention policies
- Verify encryption at rest and in transit
- Check access logs and audit trails

### 2. Capacity Planning

**Database Growth Analysis**
```sql
-- Table growth trends
SELECT 
    DATE_TRUNC('month', created_at) as month,
    COUNT(*) as records,
    pg_size_pretty(SUM(pg_column_size(ROW(*)))) as estimated_size
FROM performance_data 
WHERE created_at >= CURRENT_DATE - INTERVAL '6 months'
GROUP BY DATE_TRUNC('month', created_at)
ORDER BY month;
```

**Cost Analysis**
```bash
# AWS Cost Explorer API (requires setup)
aws ce get-cost-and-usage \
    --time-period Start=$(date -d "30 days ago" +%Y-%m-%d),End=$(date +%Y-%m-%d) \
    --granularity MONTHLY \
    --metrics BlendedCost \
    --group-by Type=DIMENSION,Key=SERVICE
```

## Troubleshooting Guide

### Common Issues

#### 1. Glue Job Failures

**Symptoms:**
- Glue job status shows FAILED
- CloudWatch alarms triggered
- Step Functions execution failed

**Diagnosis:**
```bash
# Check Glue job logs
aws logs filter-log-events \
    --log-group-name /aws/glue/advisory-performance-etl \
    --filter-pattern "ERROR" \
    --start-time $(date -d "1 hour ago" +%s)000

# Get job run details
aws glue get-job-run --job-name advisory-performance-etl --run-id <RUN_ID>
```

**Common Fixes:**
- Memory/CPU scaling: Increase `MaxCapacity` in Glue job
- Data format issues: Check vendor mapping configurations
- Database connectivity: Verify security groups and network access

#### 2. Lambda Timeout/Memory Issues

**Symptoms:**
- Lambda function timeouts
- Memory exceeded errors
- S3 event processing delays

**Diagnosis:**
```bash
# Check Lambda metrics
aws logs filter-log-events \
    --log-group-name /aws/lambda/advisory-etl-orchestrator \
    --filter-pattern "REPORT" \
    --start-time $(date -d "1 hour ago" +%s)000
```

**Fixes:**
- Increase timeout and memory allocation
- Optimize file processing logic
- Implement batch processing for large files

#### 3. Database Performance Issues

**Symptoms:**
- High CPU utilization
- Connection pool exhaustion
- Query timeouts

**Diagnosis:**
```sql
-- Check active queries
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query 
FROM pg_stat_activity 
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';

-- Check locks
SELECT * FROM pg_locks WHERE NOT granted;
```

**Fixes:**
- Scale up RDS instance
- Optimize queries and indexes
- Implement connection pooling
- Consider read replicas for reporting

#### 4. Data Quality Issues

**Symptoms:**
- Low reconciliation pass rates
- High variance in calculations
- Missing or invalid data

**Diagnosis:**
```sql
-- Check recent quality issues
SELECT 
    issue_type,
    COUNT(*) as count,
    AVG(CASE WHEN actual_value ~ '^[0-9\.]+$' 
        THEN actual_value::numeric ELSE NULL END) as avg_actual_value
FROM data_quality_issues 
WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'
GROUP BY issue_type;
```

**Fixes:**
- Review vendor data mapping
- Adjust tolerance thresholds
- Implement additional validation rules
- Contact vendor for data quality issues

### Emergency Procedures

#### 1. Pipeline Outage

**Immediate Actions:**
1. Check AWS Service Health Dashboard
2. Review CloudWatch alarms and logs
3. Verify network connectivity and security groups
4. Contact on-call engineer if needed

**Recovery Steps:**
1. Identify root cause from logs
2. Apply temporary fix if possible
3. Re-run failed Step Functions executions
4. Verify data integrity after recovery

#### 2. Data Corruption

**Immediate Actions:**
1. Stop all processing immediately
2. Identify affected time period and accounts
3. Backup current database state
4. Document the incident

**Recovery Steps:**
1. Restore from backup if necessary
2. Re-process affected files
3. Run data validation scripts
4. Generate reconciliation reports

## Performance Optimization

### 1. Database Optimization

**Partitioning Strategy:**
```sql
-- Auto-create monthly partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date text)
RETURNS void AS $$
DECLARE
    partition_name text;
    start_date_val date;
    end_date_val date;
BEGIN
    start_date_val := start_date::date;
    end_date_val := start_date_val + interval '1 month';
    partition_name := table_name || '_' || to_char(start_date_val, 'YYYY_MM');
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I
                    FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date_val, end_date_val);
END;
$$ LANGUAGE plpgsql;
```

**Index Optimization:**
```sql
-- Performance monitoring
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_data_reconciliation_status 
ON performance_data (reconciliation_status, as_of_date) 
WHERE reconciliation_status != 'COMPLETED';

-- Query-specific indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_data_vendor_date 
ON performance_data (data_source, as_of_date DESC);
```

### 2. ETL Performance

**Glue Job Optimization:**
```python
# Optimize Spark configuration
spark_config = {
    "spark.sql.adaptive.enabled": "true",
    "spark.sql.adaptive.coalescePartitions.enabled": "true",
    "spark.sql.adaptive.skewJoin.enabled": "true",
    "spark.sql.adaptive.localShuffleReader.enabled": "true",
    "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
    "spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold": "0"
}
```

**Lambda Optimization:**
- Use connection pooling for database connections
- Implement caching for configuration data
- Optimize memory allocation based on file sizes

## Monitoring and Alerting

### Key Performance Indicators (KPIs)

1. **Pipeline Reliability**
   - Success Rate: >99%
   - Mean Time to Recovery: <30 minutes
   - Data Processing Latency: <2 hours

2. **Data Quality**
   - Reconciliation Pass Rate: >95%
   - Data Completeness: >99%
   - Tolerance Violations: <1%

3. **Performance**
   - Processing Time per File: <30 minutes
   - Database Query Response: <5 seconds
   - System Availability: >99.9%

### Alert Configuration

**Critical Alerts (Immediate Response):**
- Pipeline failures
- Database connectivity issues
- Security breaches
- Data corruption

**Warning Alerts (Response within 4 hours):**
- Performance degradation
- Data quality issues
- Capacity thresholds
- Cost anomalies

## Disaster Recovery

### Backup Strategy

**Database Backups:**
- Automated daily snapshots (7-day retention)
- Point-in-time recovery enabled
- Cross-region backup for critical data

**Configuration Backups:**
- S3 versioning enabled for all configuration files
- Infrastructure as Code in version control
- Documentation maintained in Git

### Recovery Procedures

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 1 hour

**Recovery Steps:**
1. Assess impact and scope
2. Restore from backup if needed
3. Verify data integrity
4. Resume processing
5. Validate results
6. Document lessons learned

## Contact Information

**Primary On-Call:** Data Engineering Team  
**Secondary:** Platform Engineering Team  
**Escalation:** CTO Office  

**Email:** etl-support@company.com  
**Slack:** #data-engineering-alerts  
**Phone:** Emergency escalation only  

---

*This document should be reviewed and updated monthly. Last updated: $(date)*

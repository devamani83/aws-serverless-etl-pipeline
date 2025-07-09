# AWS Serverless ETL Pipeline for Advisory Performance Data

This project implements a comprehensive serverless ETL pipeline for processing advisory performance data from multiple vendors with different file formats and schemas.

## Architecture Overview

The solution leverages the following AWS services:
- **AWS Glue**: Data cataloging, ETL jobs, and data quality checks
- **AWS Lambda**: Serverless compute for custom processing logic
- **AWS Step Functions**: Orchestration of ETL workflows
- **Amazon S3**: Data lake storage for raw and processed data
- **Amazon RDS PostgreSQL**: Production database for final results
- **AWS EventBridge**: Event-driven architecture
- **AWS CloudWatch**: Monitoring and logging
- **AWS Secrets Manager**: Database credentials management

## Key Features

1. **Multi-vendor data ingestion** with automatic schema detection
2. **Financial calculations**: Net flow, cumulative net flow, ending market value
3. **Performance metrics**: Time-weighted rate of return (TWRR), cumulative TWRR
4. **Data quality**: Tolerance checks and validation
5. **Account reconciliation** with existing records
6. **High-performance database operations** for millions of records
7. **Error handling and monitoring**
8. **Cost optimization** through serverless architecture

## Financial Calculations

### Net Flow
Net flow represents the cash movements (contributions minus distributions) during a period.

### Time-Weighted Rate of Return (TWRR)
TWRR eliminates the impact of cash flows timing, providing a true measure of investment performance:
```
TWRR = [(1 + R1) × (1 + R2) × ... × (1 + Rn)] - 1
```

### Cumulative TWRR
Cumulative TWRR compounds the returns over multiple periods.

## Project Structure

```
aws-glue/
├── infrastructure/          # CloudFormation/CDK templates
├── glue-jobs/              # AWS Glue ETL scripts
├── lambda-functions/       # Lambda function code
├── step-functions/         # Step Function definitions
├── data-models/           # Data schemas and mappings
├── sql/                   # Database scripts
├── config/                # Configuration files
├── tests/                 # Unit and integration tests
└── scripts/               # Deployment and utility scripts
```

## Getting Started

1. **Prerequisites**
   - AWS CLI configured
   - Python 3.9+
   - AWS CDK installed
   - PostgreSQL client

2. **Setup**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Deploy infrastructure
   cd infrastructure
   cdk deploy
   
   # Setup database
   python scripts/setup_database.py
   ```

3. **Configuration**
   - Update `config/environment.json` with your settings
   - Configure vendor-specific mappings in `data-models/`

## Usage

The pipeline is triggered automatically when files are uploaded to the designated S3 buckets. Manual execution is also supported through the AWS console or CLI.

## Monitoring

- CloudWatch dashboards for pipeline health
- Automated alerts for failures
- Performance metrics tracking
- Cost monitoring

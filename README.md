# AWS Serverless ETL Pipeline for Advisory Performance Data

[![Deploy Pipeline](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/deploy.yml/badge.svg)](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/deploy.yml)
[![Code Quality](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/code-quality.yml/badge.svg)](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/code-quality.yml)
[![Security Scan](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/security.yml/badge.svg)](https://github.com/devamani83/aws-serverless-etl-pipeline/actions/workflows/security.yml)

This project implements a **production-grade serverless ETL pipeline** for processing advisory performance data from multiple vendors with different file formats and schemas. The solution includes comprehensive CI/CD automation, monitoring, and security features.

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

## 🚀 CI/CD Pipeline

This project includes a comprehensive CI/CD pipeline with GitHub Actions that provides:

### 🔄 Automated Deployments
- **Staging Environment**: Auto-deployed on pushes to `develop` branch
- **Production Environment**: Auto-deployed on pushes to `main` branch
- **Manual Deployments**: Triggered via GitHub Actions UI

### 🧪 Quality Assurance
- **Automated Testing**: Unit tests, integration tests, and security scans
- **Code Quality**: Linting, formatting, and complexity analysis
- **Security Scanning**: Vulnerability detection and secret scanning
- **Documentation**: Spell checking and link validation

### 📊 Monitoring & Alerts
- **Health Checks**: Automated health monitoring every 15 minutes
- **Performance Metrics**: Real-time performance and cost tracking
- **Notifications**: Slack integration for failure alerts
- **Database Safety**: Automated backups before migrations

### 🛡️ Security Features
- **Infrastructure Security**: CDK security validation with cdk-nag
- **Dependency Scanning**: Automated vulnerability detection
- **Secret Management**: Secure credential handling
- **Compliance Checks**: Automated compliance validation

## 📋 Workflows

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| **Deploy Pipeline** | Push to main/develop | Full deployment with testing |
| **Code Quality** | Push/PR | Linting, formatting, testing |
| **Security Scan** | Push/PR/Schedule | Vulnerability & secret scanning |
| **Database Migration** | Manual | Safe database migrations |
| **Monitoring** | Schedule/Manual | Health checks & metrics |

## 🔧 Setup CI/CD

1. **Configure GitHub Secrets**:
   ```bash
   # Required secrets in GitHub repository settings:
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   
   # Optional:
   SLACK_WEBHOOK_URL=your_slack_webhook
   SONAR_TOKEN=your_sonar_token
   ```

2. **Environment Protection**:
   - Production requires manual approval
   - Staging deploys automatically
   - All environments require status checks

3. **First Deployment**:
   ```bash
   # Push to trigger initial deployment
   git push origin main
   
   # Monitor in GitHub Actions tab
   # https://github.com/your-username/aws-serverless-etl-pipeline/actions
   ```

For detailed CI/CD setup instructions, see [.github/SECRETS.md](.github/SECRETS.md).

## 🔍 Monitoring Dashboard

The pipeline automatically creates monitoring dashboards with:
- **Real-time Metrics**: Processing rates, error counts, latency
- **Cost Tracking**: Daily spend analysis and budget alerts
- **Health Status**: Service availability and performance
- **Data Quality**: Processing success rates and reconciliation metrics

Access monitoring at: `https://<cloudfront-domain>/dashboard`

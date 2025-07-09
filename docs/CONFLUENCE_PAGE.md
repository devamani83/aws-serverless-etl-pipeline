# Advisory Performance ETL Pipeline - Project Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture Overview](#architecture-overview)
3. [System Components](#system-components)
4. [Data Flow Architecture](#data-flow-architecture)
5. [Process Flow Diagrams](#process-flow-diagrams)
6. [Sequence Diagrams](#sequence-diagrams)
7. [Database Schema](#database-schema)
8. [API Documentation](#api-documentation)
9. [Deployment Guide](#deployment-guide)
10. [Operations & Monitoring](#operations--monitoring)
11. [Troubleshooting](#troubleshooting)

---

## Project Overview

### Business Purpose
The Advisory Performance ETL Pipeline is a serverless, cloud-native solution designed to process multi-vendor advisory performance data with high accuracy, scalability, and reliability. The system handles millions of records in production while ensuring data quality and performing complex financial calculations.

### Key Features
- **Multi-vendor data ingestion** with automatic schema detection and mapping
- **Financial calculations**: Net flow, cumulative net flow, ending market value
- **Performance metrics**: Time-weighted rate of return (TWRR), cumulative TWRR  
- **Data quality validation** and tolerance checking
- **Account reconciliation** with existing records
- **High-performance database operations** optimized for millions of records
- **Real-time monitoring** and alerting
- **Web-based UI** for data visualization and management

### Technology Stack
- **Cloud Platform**: AWS (Amazon Web Services)
- **Compute**: AWS Lambda, AWS Glue
- **Storage**: Amazon S3, Amazon RDS PostgreSQL
- **Orchestration**: AWS Step Functions
- **Monitoring**: Amazon CloudWatch
- **Frontend**: React.js with Material-UI
- **Backend**: Flask (Python)
- **Infrastructure**: AWS CDK (Infrastructure as Code)

---

## Architecture Overview

```mermaid
graph TB
    subgraph "Data Sources"
        VA[Vendor A<br/>CSV Files]
        VB[Vendor B<br/>Excel Files] 
        VC[Vendor C<br/>JSON Files]
    end
    
    subgraph "AWS Cloud Infrastructure"
        subgraph "Data Ingestion Layer"
            S3RAW[S3 Raw Data Bucket]
            S3PROC[S3 Processing Bucket]
            S3ARCH[S3 Archive Bucket]
        end
        
        subgraph "Processing Layer"
            LAMBDA1[Lambda Orchestrator]
            SF[Step Functions<br/>Workflow]
            GLUE[AWS Glue<br/>ETL Jobs]
            LAMBDA2[Lambda Reconciliation<br/>Engine]
        end
        
        subgraph "Data Storage Layer"
            RDS[(RDS PostgreSQL<br/>Production Database)]
            S3TEMP[S3 Temp Storage]
        end
        
        subgraph "Monitoring & Security"
            CW[CloudWatch<br/>Monitoring]
            SM[Secrets Manager]
            SNS[SNS Notifications]
        end
        
        subgraph "Application Layer"
            UI[React Web UI]
            API[Flask API Backend]
        end
    end
    
    subgraph "Users"
        ANALYST[Data Analysts]
        OPS[Operations Team]
        BUSINESS[Business Users]
    end
    
    VA --> S3RAW
    VB --> S3RAW
    VC --> S3RAW
    
    S3RAW --> LAMBDA1
    LAMBDA1 --> SF
    SF --> GLUE
    SF --> LAMBDA2
    GLUE --> RDS
    LAMBDA2 --> RDS
    
    GLUE --> S3PROC
    S3PROC --> S3ARCH
    
    RDS --> API
    API --> UI
    
    UI --> ANALYST
    UI --> OPS
    UI --> BUSINESS
    
    CW --> SNS
    SM --> GLUE
    SM --> LAMBDA2
```

### Architecture Principles
1. **Serverless-First**: Minimize operational overhead with managed services
2. **Event-Driven**: Reactive processing based on data arrival
3. **Scalable**: Auto-scaling components handle variable workloads
4. **Resilient**: Built-in error handling and retry mechanisms
5. **Secure**: Encryption at rest/transit, least privilege access
6. **Cost-Optimized**: Pay-per-use pricing model

---

## System Components

### Core AWS Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **AWS S3** | Data lake storage with lifecycle policies | 4 buckets: raw, processed, temp, archive |
| **AWS Lambda** | Serverless compute for orchestration | Python 3.9, 5-15 min timeout |
| **AWS Glue** | Large-scale ETL processing | Spark-based, auto-scaling |
| **AWS Step Functions** | Workflow orchestration | State machine with error handling |
| **Amazon RDS** | Production PostgreSQL database | Multi-AZ, encrypted, automated backups |
| **Amazon CloudWatch** | Monitoring and logging | Custom dashboards and alarms |
| **AWS Secrets Manager** | Credential management | Automatic rotation enabled |

### Custom Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **ETL Orchestrator** | Lambda Function | File processing initiation |
| **Reconciliation Engine** | Lambda Function | Data validation and reconciliation |
| **Performance Calculator** | Glue Job | Financial calculations (TWRR, etc.) |
| **Data Quality Checker** | Glue Job | Data validation and quality scoring |
| **Web UI** | React + Material-UI | User interface for data visualization |
| **API Backend** | Flask + SQLAlchemy | REST API for data access |

---

## Data Flow Architecture

```mermaid
flowchart TD
    subgraph "Ingestion Phase"
        A[File Upload to S3] --> B[S3 Event Trigger]
        B --> C[Lambda Orchestrator]
        C --> D{Validate File Format}
        D -->|Valid| E[Move to Processing Folder]
        D -->|Invalid| F[Move to Error Folder]
    end
    
    subgraph "Processing Phase"
        E --> G[Start Step Function Workflow]
        G --> H[Data Profiling Job]
        H --> I[Main ETL Job]
        I --> J[Data Quality Checks]
        J --> K[Reconciliation Engine]
    end
    
    subgraph "Validation Phase"
        K --> L{Reconciliation Results}
        L -->|Pass| M[Update Status: COMPLETED]
        L -->|Fail| N[Update Status: COMPLETED_WITH_ISSUES]
        L -->|Error| O[Update Status: FAILED]
    end
    
    subgraph "Storage Phase"
        M --> P[Archive Successful File]
        N --> Q[Send Warning Notification]
        O --> R[Archive Error File]
        Q --> P
        R --> S[Send Error Notification]
    end
    
    subgraph "Presentation Phase"
        P --> T[Data Available in UI]
        T --> U[Generate Reports]
        U --> V[Business Intelligence]
    end
```

### Data Transformation Pipeline

```mermaid
graph LR
    subgraph "Raw Data"
        CSV[CSV Files<br/>Vendor A]
        XLSX[Excel Files<br/>Vendor B] 
        JSON[JSON Files<br/>Vendor C]
    end
    
    subgraph "Normalization"
        MAP[Field Mapping<br/>& Schema Validation]
        TYPE[Data Type<br/>Conversion]
        CLEAN[Data Cleansing<br/>& Validation]
    end
    
    subgraph "Calculations"
        NETFLOW[Net Flow<br/>Calculation]
        TWRR[TWRR<br/>Calculation]
        CUMULATIVE[Cumulative<br/>Metrics]
    end
    
    subgraph "Quality Checks"
        TOLERANCE[Tolerance<br/>Checking]
        RECONCILE[Account<br/>Reconciliation]
        VALIDATION[Cross-Account<br/>Validation]
    end
    
    subgraph "Output"
        DB[(PostgreSQL<br/>Database)]
        REPORTS[Reconciliation<br/>Reports]
        ALERTS[Quality<br/>Alerts]
    end
    
    CSV --> MAP
    XLSX --> MAP
    JSON --> MAP
    
    MAP --> TYPE
    TYPE --> CLEAN
    
    CLEAN --> NETFLOW
    NETFLOW --> TWRR
    TWRR --> CUMULATIVE
    
    CUMULATIVE --> TOLERANCE
    TOLERANCE --> RECONCILE
    RECONCILE --> VALIDATION
    
    VALIDATION --> DB
    DB --> REPORTS
    VALIDATION --> ALERTS
```

---

## Process Flow Diagrams

### 1. File Processing Workflow

```mermaid
sequenceDiagram
    participant U as User/System
    participant S3 as S3 Bucket
    participant L1 as Lambda Orchestrator
    participant SF as Step Functions
    participant G as Glue ETL Job
    participant L2 as Reconciliation Lambda
    participant DB as PostgreSQL DB
    participant UI as Web UI
    
    U->>S3: Upload data file
    S3->>L1: S3 Event notification
    L1->>L1: Validate file format
    L1->>S3: Move to processing folder
    L1->>SF: Start workflow execution
    
    SF->>G: Start data profiling
    G->>DB: Save profiling results
    G-->>SF: Profiling complete
    
    SF->>G: Start main ETL job
    G->>G: Process data & calculate metrics
    G->>DB: Insert/update performance data
    G-->>SF: ETL complete
    
    SF->>L2: Start reconciliation
    L2->>DB: Retrieve processed data
    L2->>L2: Perform reconciliation checks
    L2->>DB: Save reconciliation results
    L2-->>SF: Reconciliation complete
    
    SF->>S3: Archive processed file
    SF->>UI: Notify completion
    
    UI->>DB: Query results for display
    DB-->>UI: Return data
```

### 2. Data Quality Validation Process

```mermaid
flowchart TD
    A[Raw Data Input] --> B[Schema Validation]
    B --> C{Schema Valid?}
    C -->|No| D[Log Schema Error]
    C -->|Yes| E[Data Type Validation]
    E --> F{Types Valid?}
    F -->|No| G[Log Type Error]
    F -->|Yes| H[Business Rule Validation]
    H --> I{Rules Pass?}
    I -->|No| J[Log Business Rule Error]
    I -->|Yes| K[Calculate Financial Metrics]
    K --> L[Tolerance Checking]
    L --> M{Within Tolerance?}
    M -->|No| N[Flag Tolerance Violation]
    M -->|Yes| O[Cross-Account Validation]
    O --> P{Validation Pass?}
    P -->|No| Q[Log Validation Warning]
    P -->|Yes| R[Mark as High Quality]
    
    D --> S[Generate Quality Report]
    G --> S
    J --> S
    N --> S
    Q --> S
    R --> S
    S --> T[Update Quality Score]
    T --> U[Store in Database]
```

### 3. Reconciliation Process Flow

```mermaid
graph TD
    A[Start Reconciliation] --> B[Retrieve Processed Data]
    B --> C[For Each Account Record]
    C --> D[Market Value Reconciliation]
    D --> E[TWRR Reconciliation]
    E --> F[Net Flow Reconciliation]
    F --> G{More Records?}
    G -->|Yes| C
    G -->|No| H[Cross-Account Validation]
    H --> I[Portfolio Consistency Check]
    I --> J[Outlier Detection]
    J --> K[Generate Reconciliation Report]
    K --> L[Calculate Pass Rate]
    L --> M{Pass Rate > 95%?}
    M -->|Yes| N[Status: COMPLETED]
    M -->|No| O[Status: COMPLETED_WITH_ISSUES]
    N --> P[Archive File]
    O --> Q[Send Alert]
    Q --> P
    P --> R[Update Database Status]
    R --> S[End Process]
```

---

## Sequence Diagrams

### 1. End-to-End Processing Sequence

```mermaid
sequenceDiagram
    participant Vendor as Data Vendor
    participant S3 as S3 Raw Bucket
    participant Orchestrator as Lambda Orchestrator
    participant StepFunc as Step Functions
    participant Glue as Glue ETL
    participant Reconciler as Reconciliation Engine
    participant DB as PostgreSQL
    participant Monitor as CloudWatch
    participant UI as Web Interface
    participant User as End User
    
    Vendor->>S3: Upload performance data file
    S3->>Orchestrator: Trigger S3 event
    
    Orchestrator->>Orchestrator: Validate file format & vendor
    Orchestrator->>S3: Move file to processing folder
    Orchestrator->>StepFunc: Start ETL workflow
    Orchestrator->>Monitor: Log processing start
    
    StepFunc->>Glue: Start data profiling job
    Glue->>DB: Save data profile results
    Glue->>StepFunc: Return profiling status
    
    StepFunc->>Glue: Start main ETL job
    Glue->>Glue: Normalize & validate data
    Glue->>Glue: Calculate TWRR & financial metrics
    Glue->>DB: Insert performance data
    Glue->>Monitor: Log ETL metrics
    Glue->>StepFunc: Return ETL status
    
    StepFunc->>Reconciler: Start reconciliation
    Reconciler->>DB: Query processed data
    Reconciler->>Reconciler: Perform tolerance checks
    Reconciler->>Reconciler: Generate reconciliation report
    Reconciler->>DB: Save reconciliation results
    Reconciler->>Monitor: Log reconciliation metrics
    Reconciler->>StepFunc: Return reconciliation status
    
    StepFunc->>S3: Archive processed file
    StepFunc->>Monitor: Log workflow completion
    StepFunc->>UI: Notify data available
    
    User->>UI: Access dashboard
    UI->>DB: Query performance data
    DB->>UI: Return results
    UI->>User: Display data & reports
```

### 2. Error Handling Sequence

```mermaid
sequenceDiagram
    participant SF as Step Functions
    participant Glue as Glue Job
    participant Lambda as Lambda Function
    participant DB as Database
    participant SNS as SNS Alerts
    participant S3 as S3 Storage
    participant Ops as Operations Team
    
    SF->>Glue: Start ETL job
    Glue->>Glue: Process data
    Glue-->>SF: Job failed with error
    
    SF->>SF: Evaluate error type
    SF->>Lambda: Trigger error handler
    
    Lambda->>DB: Log error details
    Lambda->>S3: Move file to error folder
    Lambda->>SNS: Send error notification
    
    SNS->>Ops: Email/Slack alert
    
    Ops->>SF: Review error logs
    Ops->>Glue: Check job details
    Ops->>S3: Examine error file
    
    Ops->>SF: Restart workflow (if fixable)
    SF->>Glue: Retry processing
    
    alt Retry Successful
        Glue->>DB: Save processed data
        Glue->>SF: Return success
        SF->>SNS: Send success notification
    else Retry Failed
        SF->>Lambda: Escalate error
        Lambda->>SNS: Send escalation alert
        SNS->>Ops: Critical alert
    end
```

### 3. Data Quality Monitoring Sequence

```mermaid
sequenceDiagram
    participant ETL as ETL Process
    participant DQ as Data Quality Checker
    participant DB as Database
    participant CW as CloudWatch
    participant Dashboard as Monitoring Dashboard
    participant Analyst as Data Analyst
    
    ETL->>DQ: Trigger quality check
    DQ->>DB: Query processed data
    
    DQ->>DQ: Run validation rules
    DQ->>DQ: Calculate quality score
    DQ->>DQ: Identify issues
    
    DQ->>DB: Save quality results
    DQ->>CW: Publish quality metrics
    
    CW->>CW: Evaluate alarm thresholds
    
    alt Quality Score < 90%
        CW->>Dashboard: Trigger alert
        Dashboard->>Analyst: Send notification
        Analyst->>Dashboard: Review quality issues
        Analyst->>DB: Query detailed results
        Analyst->>ETL: Request data reprocessing
    else Quality Score >= 90%
        CW->>Dashboard: Update metrics
        Dashboard->>Analyst: Show status (optional)
    end
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    ACCOUNTS ||--o{ PERFORMANCE_DATA : "has"
    PERFORMANCE_DATA ||--o{ RECONCILIATION_RESULTS : "generates"
    ETL_PROCESSING_LOG ||--o{ DATA_QUALITY_ISSUES : "tracks"
    
    ACCOUNTS {
        varchar account_id PK
        varchar account_name
        varchar portfolio_id
        varchar client_id
        varchar account_type
        date inception_date
        varchar status
        timestamp created_at
        timestamp updated_at
    }
    
    PERFORMANCE_DATA {
        uuid id PK
        varchar account_id FK
        date as_of_date
        decimal beginning_market_value
        decimal contributions
        decimal distributions
        decimal income
        decimal appreciation
        decimal fees
        decimal other_adjustments
        decimal ending_market_value
        decimal net_flow
        decimal cumulative_net_flow
        decimal calculated_twrr
        decimal cumulative_twrr
        decimal vendor_twrr
        decimal benchmark_return
        boolean twrr_tolerance_check
        decimal twrr_variance
        varchar reconciliation_status
        varchar data_source
        varchar file_name
        timestamp created_at
        timestamp updated_at
        varchar processed_by
    }
    
    RECONCILIATION_RESULTS {
        uuid id PK
        varchar account_id
        date as_of_date
        varchar field_name
        decimal calculated_value
        decimal vendor_value
        decimal variance
        decimal tolerance_threshold
        boolean within_tolerance
        timestamp reconciliation_date
        text notes
    }
    
    ETL_PROCESSING_LOG {
        uuid id PK
        varchar file_name
        varchar file_path
        varchar vendor
        timestamp processing_start_time
        timestamp processing_end_time
        integer records_processed
        integer records_inserted
        integer records_updated
        integer records_failed
        varchar status
        text error_message
        timestamp created_at
    }
    
    DATA_QUALITY_ISSUES {
        uuid id PK
        uuid etl_log_id FK
        varchar account_id
        date as_of_date
        varchar issue_type
        text issue_description
        varchar field_name
        varchar expected_value
        varchar actual_value
        varchar severity
        timestamp created_at
    }
```

### Key Database Features

1. **Partitioning**: Performance data table partitioned by date for better query performance
2. **Indexing**: Strategic indexes on frequently queried columns
3. **Constraints**: Foreign key relationships and data validation
4. **Triggers**: Automatic calculation of derived fields
5. **Functions**: Stored procedures for complex calculations
6. **Views**: Materialized views for reporting and dashboards

---

## API Documentation

### REST API Endpoints

| Endpoint | Method | Purpose | Parameters |
|----------|--------|---------|------------|
| `/api/vendors` | GET | List all vendors | - |
| `/api/vendors/{vendor}/files` | GET | Get files for vendor | `vendor`, `status`, `date_range` |
| `/api/files/{file_id}/details` | GET | Get file processing details | `file_id` |
| `/api/files/{file_id}/data` | GET | Get processed data | `file_id`, `page`, `limit` |
| `/api/reconciliation/{file_id}` | GET | Get reconciliation results | `file_id` |
| `/api/accounts/{account_id}` | GET | Get account details | `account_id`, `date_range` |
| `/api/dashboard/summary` | GET | Get dashboard metrics | `date_range` |
| `/api/quality/score` | GET | Get data quality metrics | `vendor`, `date_range` |

### API Response Format

```json
{
  "status": "success",
  "data": {
    // Response data
  },
  "metadata": {
    "timestamp": "2025-07-08T10:30:00Z",
    "total_records": 1000,
    "page": 1,
    "per_page": 50
  },
  "message": "Request processed successfully"
}
```

---

## Deployment Guide

### Prerequisites
- AWS CLI configured with appropriate permissions
- Python 3.9+ and pip
- Node.js 16+ and npm
- Docker (for containerized deployment)

### Deployment Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd advisory-performance-etl
   ```

2. **Deploy Infrastructure**
   ```bash
   ./scripts/deploy.sh --environment production
   ```

3. **Setup Database**
   ```bash
   python scripts/setup_database.py
   ```

4. **Deploy Web Application**
   ```bash
   cd ui-application
   ./setup.sh
   docker-compose up -d
   ```

### Environment Configuration

| Environment | Purpose | Configuration |
|-------------|---------|---------------|
| **Development** | Local testing | Single instance, minimal resources |
| **Staging** | Pre-production testing | Production-like, with test data |
| **Production** | Live system | Multi-AZ, auto-scaling, monitoring |

---

## Operations & Monitoring

### Key Performance Indicators

| Metric | Target | Threshold |
|--------|--------|-----------|
| Pipeline Success Rate | >99% | Alert if <95% |
| Data Quality Score | >95% | Alert if <90% |
| TWRR Reconciliation Pass Rate | >95% | Alert if <90% |
| Processing Latency | <2 hours | Alert if >4 hours |
| Database Query Response | <5 seconds | Alert if >10 seconds |
| System Availability | >99.9% | Alert if <99% |

### Monitoring Dashboard

```mermaid
graph TB
    subgraph "Executive Dashboard"
        A[Pipeline Health Score]
        B[Data Quality Trends]
        C[Processing Volume]
        D[Cost Analysis]
    end
    
    subgraph "Operational Dashboard"
        E[Active Jobs Status]
        F[Error Rate Trends]
        G[Performance Metrics]
        H[Resource Utilization]
    end
    
    subgraph "Technical Dashboard"
        I[Infrastructure Health]
        J[Database Performance]
        K[API Response Times]
        L[Storage Usage]
    end
```

### Alerting Strategy

1. **Critical Alerts** (Immediate Response)
   - Pipeline failures
   - Data corruption
   - Security incidents

2. **Warning Alerts** (4-hour Response)
   - Performance degradation
   - Quality issues
   - Capacity concerns

3. **Informational Alerts** (Next Business Day)
   - Successful completions
   - Scheduled maintenance
   - Usage reports

---

## Troubleshooting

### Common Issues and Solutions

| Issue | Symptoms | Root Cause | Solution |
|-------|----------|------------|----------|
| **Glue Job Timeout** | Job fails after 48 hours | Large file size, insufficient resources | Increase max capacity, optimize queries |
| **Lambda Memory Error** | Function timeout, memory exceeded | Large files, complex processing | Increase memory allocation, implement streaming |
| **Database Lock** | Query timeouts, high CPU | Concurrent processing, long transactions | Optimize queries, implement connection pooling |
| **S3 Event Delay** | Processing delays | High event volume, throttling | Implement SQS buffer, batch processing |
| **Data Quality Issues** | Low reconciliation rates | Vendor data changes, mapping errors | Update vendor mappings, adjust tolerances |

### Diagnostic Commands

```bash
# Check Glue job status
aws glue get-job-runs --job-name advisory-performance-etl --max-items 5

# Review Lambda logs
aws logs filter-log-events --log-group-name /aws/lambda/advisory-etl-orchestrator --filter-pattern "ERROR"

# Check database performance
psql -h $DB_HOST -U $DB_USER -d advisory_performance -c "SELECT * FROM pg_stat_activity WHERE state = 'active';"

# Monitor S3 event processing
aws s3 ls s3://advisory-etl-raw-data/processing/ --recursive
```

---

## Change Management

### Version Control Strategy
- **Git Flow**: Feature branches, develop, main
- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Release Tags**: Annotated tags for production releases

### Deployment Pipeline
1. **Development**: Feature development and unit testing
2. **Staging**: Integration testing and performance validation
3. **Production**: Blue-green deployment with rollback capability

### Configuration Management
- Infrastructure as Code (AWS CDK)
- Environment-specific configuration files
- Secrets management via AWS Secrets Manager
- Database migrations with version control

---

## Security & Compliance

### Security Measures
- **Encryption**: At-rest (S3, RDS) and in-transit (TLS 1.2+)
- **Access Control**: IAM roles with least privilege
- **Network Security**: VPC, security groups, NACLs
- **Monitoring**: CloudTrail, GuardDuty, Config

### Compliance Requirements
- **Data Privacy**: GDPR, CCPA compliance
- **Financial Regulations**: SOX, audit trails
- **Data Retention**: Configurable retention policies
- **Access Logging**: Comprehensive audit logs

---

## Performance Optimization

### Database Optimization
```sql
-- Partition maintenance
SELECT create_monthly_partition('performance_data', '2025-08-01');

-- Index analysis
SELECT * FROM pg_stat_user_indexes WHERE idx_scan < 10;

-- Query performance
EXPLAIN ANALYZE SELECT * FROM performance_data WHERE as_of_date = '2025-07-01';
```

### ETL Optimization
- **Spark Tuning**: Adaptive query execution, partition coalescing
- **Memory Management**: Optimal driver and executor configuration
- **Parallelization**: Concurrent processing of independent tasks
- **Caching**: Strategic use of persist() for iterative operations

---

## Future Enhancements

### Roadmap Items
1. **Real-time Processing**: Stream processing for near real-time updates
2. **Machine Learning**: Anomaly detection and predictive analytics
3. **Enhanced UI**: Advanced visualization and interactive reports
4. **API Extensions**: GraphQL API, webhook notifications
5. **Multi-Region**: Disaster recovery and global deployment

### Technical Debt
- Refactor legacy data mapping logic
- Implement comprehensive integration tests
- Add performance benchmarking suite
- Enhance error handling and recovery

---

## Appendices

### A. Glossary of Terms
- **TWRR**: Time-Weighted Rate of Return
- **ETL**: Extract, Transform, Load
- **VPC**: Virtual Private Cloud
- **CDK**: Cloud Development Kit

### B. Reference Links
- [AWS Glue Documentation](https://docs.aws.amazon.com/glue/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [React Best Practices](https://reactjs.org/docs/thinking-in-react.html)

### C. Contact Information
- **Project Owner**: Data Engineering Team
- **Technical Lead**: [Your Name]
- **Support**: etl-support@company.com
- **Emergency**: #data-engineering-alerts (Slack)

---

*Document Version: 1.0*  
*Last Updated: July 8, 2025*  
*Next Review: August 8, 2025*

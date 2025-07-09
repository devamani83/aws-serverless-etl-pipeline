# Additional Technical Diagrams

This document contains specialized sequence diagrams and architectural views that complement the main Confluence documentation.

## Error Handling and Recovery Sequence

```mermaid
sequenceDiagram
    participant S3 as S3 Bucket
    participant L1 as Lambda Orchestrator
    participant SF as Step Functions
    participant G as Glue ETL Job
    participant DB as PostgreSQL DB
    participant SNS as SNS Notifications
    participant DLQ as Dead Letter Queue
    participant OPS as Operations Team
    
    S3->>L1: File upload event
    L1->>L1: Validate file format
    
    alt File validation fails
        L1->>S3: Move to error folder
        L1->>SNS: Send validation error alert
        SNS->>OPS: Email/Slack notification
        L1->>DB: Log error in ETL_PROCESSING_LOG
    else File validation passes
        L1->>SF: Start workflow
        SF->>G: Start ETL job
        
        alt ETL job fails
            G->>SF: Return error status
            SF->>SF: Retry logic (3x with backoff)
            
            alt Max retries exceeded
                SF->>DLQ: Send to dead letter queue
                SF->>SNS: Send critical alert
                SF->>DB: Update status to FAILED
                SNS->>OPS: Page on-call engineer
            else Retry succeeds
                G->>DB: Process data successfully
                SF->>S3: Archive processed file
            end
            
        else ETL job succeeds
            G->>DB: Insert/update data
            SF->>S3: Archive processed file
            SF->>SNS: Send success notification
        end
    end
```

## Real-time Data Reconciliation Flow

```mermaid
sequenceDiagram
    participant ETL as ETL Job
    participant DB as Database
    participant RC as Reconciliation Engine
    participant CACHE as Redis Cache
    participant API as Web API
    participant UI as Web Interface
    participant ALERT as Alert System
    
    ETL->>DB: Insert new performance data
    DB->>RC: Trigger reconciliation
    
    RC->>DB: Fetch vendor data
    RC->>DB: Fetch calculated data
    RC->>RC: Compare values
    
    loop For each account
        RC->>RC: Calculate variance
        
        alt Variance within tolerance
            RC->>DB: Mark as PASSED
            RC->>CACHE: Cache result (TTL: 1h)
        else Variance exceeds tolerance
            RC->>DB: Mark as FAILED
            RC->>ALERT: Send tolerance violation alert
            RC->>CACHE: Cache result (TTL: 1h)
        end
    end
    
    RC->>DB: Generate reconciliation summary
    
    UI->>API: Request reconciliation status
    API->>CACHE: Check cached results
    
    alt Cache hit
        CACHE-->>API: Return cached data
    else Cache miss
        API->>DB: Query reconciliation results
        DB-->>API: Return results
        API->>CACHE: Update cache
    end
    
    API-->>UI: Display reconciliation status
```

## Multi-Vendor Data Processing Pipeline

```mermaid
flowchart TD
    subgraph "Vendor A - CSV Processing"
        A1[CSV File Upload] --> A2[Schema Validation]
        A2 --> A3[Data Type Conversion]
        A3 --> A4[Field Mapping]
        A4 --> A5[Calculate Metrics]
    end
    
    subgraph "Vendor B - Excel Processing"
        B1[Excel File Upload] --> B2[Sheet Detection]
        B2 --> B3[Header Row Identification]
        B3 --> B4[Data Extraction]
        B4 --> B5[Field Mapping]
        B5 --> B6[Calculate Metrics]
    end
    
    subgraph "Vendor C - JSON Processing"
        C1[JSON File Upload] --> C2[Schema Validation]
        C2 --> C3[Nested Object Flattening]
        C3 --> C4[Field Mapping]
        C4 --> C5[Calculate Metrics]
    end
    
    subgraph "Common Processing Pipeline"
        D1[Data Normalization]
        D2[Quality Validation]
        D3[TWRR Calculation]
        D4[Tolerance Checking]
        D5[Database Upsert]
        D6[Reconciliation]
    end
    
    A5 --> D1
    B6 --> D1
    C5 --> D1
    
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> D5
    D5 --> D6
    
    D6 --> E1[Archive Success]
    D2 --> E2[Quarantine Failed]
    
    style A1 fill:#e1f5fe
    style B1 fill:#f3e5f5
    style C1 fill:#e8f5e8
    style D1 fill:#fff3e0
```

## Database Transaction Flow

```mermaid
sequenceDiagram
    participant APP as Application
    participant POOL as Connection Pool
    participant DB as PostgreSQL
    participant AUDIT as Audit Log
    participant BACKUP as Backup System
    
    APP->>POOL: Request connection
    POOL->>DB: Establish connection
    
    APP->>DB: BEGIN TRANSACTION
    
    loop Batch Insert/Update
        APP->>DB: UPSERT performance_data
        DB->>DB: Check constraints
        
        alt Constraint violation
            DB-->>APP: Return error
            APP->>DB: ROLLBACK
            APP->>AUDIT: Log error details
        else Success
            DB->>AUDIT: Log data changes
        end
    end
    
    APP->>DB: COMMIT TRANSACTION
    DB->>BACKUP: Trigger incremental backup
    
    APP->>POOL: Return connection
    POOL->>POOL: Connection available for reuse
    
    Note over BACKUP: Continuous backup<br/>Point-in-time recovery
```

## Performance Monitoring Sequence

```mermaid
sequenceDiagram
    participant ETL as ETL Pipeline
    participant CW as CloudWatch
    participant DASH as Dashboard
    participant ALERT as Alerting
    participant ONCALL as On-Call Engineer
    participant SLACK as Slack Channel
    
    ETL->>CW: Send custom metrics
    Note over CW: Processing time<br/>Record count<br/>Error rate<br/>Memory usage
    
    CW->>CW: Evaluate alarm thresholds
    
    alt Metrics normal
        CW->>DASH: Update dashboard
    else Threshold exceeded
        CW->>ALERT: Trigger alarm
        ALERT->>ONCALL: Page engineer
        ALERT->>SLACK: Send notification
        
        ONCALL->>DASH: Check metrics
        ONCALL->>ETL: Investigate issue
        
        alt Issue resolved
            ONCALL->>SLACK: Update resolution
            ONCALL->>CW: Acknowledge alarm
        else Escalation needed
            ONCALL->>ONCALL: Escalate to senior engineer
        end
    end
    
    loop Every 5 minutes
        DASH->>CW: Refresh metrics
        CW-->>DASH: Return latest data
    end
```

## API Rate Limiting and Caching

```mermaid
sequenceDiagram
    participant CLIENT as Client App
    participant LB as Load Balancer
    participant API as API Gateway
    participant CACHE as Redis Cache
    participant APP as Flask App
    participant DB as Database
    
    CLIENT->>LB: HTTP Request
    LB->>API: Forward request
    
    API->>API: Check rate limit
    
    alt Rate limit exceeded
        API-->>CLIENT: 429 Too Many Requests
    else Within limits
        API->>CACHE: Check cache
        
        alt Cache hit
            CACHE-->>API: Return cached data
            API-->>CLIENT: 200 OK (cached)
        else Cache miss
            API->>APP: Forward request
            APP->>DB: Query database
            DB-->>APP: Return data
            APP->>CACHE: Store in cache (TTL: 300s)
            APP-->>API: Return response
            API-->>CLIENT: 200 OK (fresh)
        end
    end
    
    Note over CACHE: Cache Strategy:<br/>- GET requests: 5min TTL<br/>- User data: 1min TTL<br/>- Static data: 1hour TTL
```

## Disaster Recovery Workflow

```mermaid
flowchart TD
    A[Incident Detection] --> B{Severity Assessment}
    
    B -->|Critical| C[Activate DR Plan]
    B -->|High| D[Standard Response]
    B -->|Medium| E[Monitor & Log]
    
    C --> F[Notify Stakeholders]
    F --> G[Switch to Backup Region]
    G --> H[Validate Backup Systems]
    H --> I[Update DNS/Load Balancer]
    I --> J[Resume Operations]
    
    D --> K[Investigate Root Cause]
    K --> L[Apply Hotfix if Available]
    L --> M{Issue Resolved?}
    M -->|Yes| N[Monitor Systems]
    M -->|No| C
    
    E --> O[Schedule Maintenance Window]
    O --> P[Apply Standard Fix]
    
    J --> Q[Post-Incident Review]
    N --> Q
    P --> Q
    
    Q --> R[Update Runbooks]
    R --> S[Improve Monitoring]
    S --> T[Document Lessons Learned]
    
    style C fill:#ff6b6b
    style G fill:#ffa726
    style J fill:#66bb6a
```

## Data Lineage and Audit Trail

```mermaid
graph LR
    subgraph "Source Systems"
        VA[Vendor A System]
        VB[Vendor B System] 
        VC[Vendor C System]
    end
    
    subgraph "Data Ingestion"
        S3RAW[S3 Raw Bucket]
        META1[Metadata Capture]
    end
    
    subgraph "Processing Layer"
        ETL[Glue ETL Job]
        CALC[Calculation Engine]
        META2[Processing Metadata]
    end
    
    subgraph "Quality Layer"
        VALID[Data Validation]
        RECON[Reconciliation]
        META3[Quality Metadata]
    end
    
    subgraph "Storage Layer"
        DB[(PostgreSQL)]
        ARCHIVE[S3 Archive]
        META4[Storage Metadata]
    end
    
    subgraph "Audit System"
        AUDIT[(Audit Database)]
        LINEAGE[Data Lineage Tracker]
    end
    
    VA --> S3RAW
    VB --> S3RAW
    VC --> S3RAW
    
    S3RAW --> META1
    META1 --> ETL
    ETL --> CALC
    CALC --> META2
    
    META2 --> VALID
    VALID --> RECON
    RECON --> META3
    
    META3 --> DB
    DB --> ARCHIVE
    ARCHIVE --> META4
    
    META1 --> AUDIT
    META2 --> AUDIT
    META3 --> AUDIT
    META4 --> AUDIT
    
    AUDIT --> LINEAGE
    
    style AUDIT fill:#e3f2fd
    style LINEAGE fill:#e8f5e8
```

## Cost Optimization Flow

```mermaid
flowchart TD
    A[Daily Cost Analysis] --> B[Identify High-Cost Resources]
    B --> C{Cost > Threshold?}
    
    C -->|No| D[Continue Monitoring]
    C -->|Yes| E[Analyze Usage Patterns]
    
    E --> F{Under-utilized?}
    F -->|Yes| G[Right-size Resources]
    F -->|No| H[Optimize Configuration]
    
    G --> I[Schedule Downsize]
    H --> J[Tune Performance]
    
    I --> K[Monitor Impact]
    J --> K
    
    K --> L{Performance OK?}
    L -->|No| M[Rollback Changes]
    L -->|Yes| N[Document Savings]
    
    M --> O[Investigate Alternative]
    N --> P[Update Baseline]
    
    O --> H
    P --> D
    
    style G fill:#81c784
    style N fill:#66bb6a
    style M fill:#ffab91
```

---

## Diagram Legend

| Symbol | Meaning |
|--------|---------|
| 🔴 | Critical/Error state |
| 🟡 | Warning/Attention needed |
| 🟢 | Success/Normal operation |
| ⚡ | Real-time/Fast operation |
| 🔄 | Retry/Loop operation |
| 📊 | Monitoring/Metrics |
| 🔒 | Security/Authentication |
| 💾 | Data persistence |
| 🌐 | Network/API call |
| ⏰ | Scheduled/Time-based |

---

## Notes

- All sequence diagrams assume normal network conditions and service availability
- Error handling paths are simplified for clarity - actual implementation includes more detailed error scenarios
- Performance metrics and thresholds should be adjusted based on actual production requirements
- Caching TTL values are suggestions and should be optimized based on data freshness requirements

# Documentation Index

This is a comprehensive index of all documentation available for the AWS Advisory Performance ETL Pipeline project.

## 📚 Main Documentation

### 1. [Confluence Page](./CONFLUENCE_FORMATTED.confluence)
**Format:** Confluence Wiki Markup  
**Purpose:** Primary project documentation for stakeholder review  
**Contents:**
- ✅ Project Overview & Business Purpose
- ✅ High-Level Architecture Diagram
- ✅ Technology Stack Overview
- ✅ System Components Description
- ✅ Data Flow Architecture
- ✅ End-to-End Process Flow Diagrams
- ✅ File Processing Sequence Diagrams
- ✅ Database ERD (Entity Relationship Diagram)
- ✅ Data Quality Validation Process
- ✅ Reconciliation Process Flow
- ✅ API Documentation
- ✅ Operations & Monitoring Setup
- ✅ Security & Compliance Framework
- ✅ Performance Optimization Guide
- ✅ Troubleshooting Guide
- ✅ Deployment Instructions
- ✅ Future Roadmap

### 2. [Markdown Documentation](./CONFLUENCE_PAGE.md)
**Format:** Markdown  
**Purpose:** Developer-friendly version with same content as Confluence  
**Contents:** Same as Confluence page but in standard Markdown format

### 3. [Operations Guide](./OPERATIONS_GUIDE.md)
**Format:** Markdown  
**Purpose:** Detailed operational procedures and maintenance  
**Contents:**
- Daily operational procedures
- Monitoring and alerting setup
- Backup and recovery processes
- Performance tuning guidelines
- Incident response procedures

### 4. [Additional Technical Diagrams](./ADDITIONAL_DIAGRAMS.md)
**Format:** Markdown with Mermaid diagrams  
**Purpose:** Specialized diagrams for specific technical scenarios  
**Contents:**
- ✅ Error Handling and Recovery Sequence
- ✅ Real-time Data Reconciliation Flow
- ✅ Multi-Vendor Data Processing Pipeline
- ✅ Database Transaction Flow
- ✅ Performance Monitoring Sequence
- ✅ API Rate Limiting and Caching
- ✅ Disaster Recovery Workflow
- ✅ Data Lineage and Audit Trail
- ✅ Cost Optimization Flow

## 🏗️ Architecture Diagrams

### High-Level Architecture
- **Location:** Confluence Page, Section "Architecture Overview"
- **Type:** System architecture diagram
- **Shows:** AWS services, data flow, user interactions

### Data Flow Architecture
- **Location:** Confluence Page, Section "Data Flow Architecture"
- **Type:** Process flow diagram
- **Shows:** Data ingestion → processing → validation → storage

### Database Schema (ERD)
- **Location:** Confluence Page, Section "Database Schema"
- **Type:** Entity Relationship Diagram
- **Shows:** Table relationships, key constraints, data model

## 🔄 Process Flow Diagrams

### File Processing Workflow
- **Location:** Confluence Page, Section "Process Flow Diagrams"
- **Type:** Flowchart
- **Shows:** File upload → validation → processing → archival

### Data Quality Validation Process
- **Location:** Confluence Page, Section "Data Quality Validation Process"
- **Type:** Decision flowchart
- **Shows:** Validation steps, quality scoring, error handling

### Reconciliation Process Flow
- **Location:** Confluence Page, Section "Reconciliation Process Flow"
- **Type:** Process flowchart
- **Shows:** Account reconciliation, tolerance checking, reporting

## ⏰ Sequence Diagrams

### End-to-End Processing Sequence
- **Location:** Confluence Page, Section "File Processing Workflow"
- **Type:** Sequence diagram
- **Shows:** Complete flow from file upload to UI display

### Error Handling Sequence
- **Location:** Additional Diagrams, Section "Error Handling and Recovery Sequence"
- **Type:** Sequence diagram with error paths
- **Shows:** Retry logic, dead letter queues, alerting

### Real-time Reconciliation
- **Location:** Additional Diagrams, Section "Real-time Data Reconciliation Flow"
- **Type:** Sequence diagram
- **Shows:** Live reconciliation process with caching

### Database Transactions
- **Location:** Additional Diagrams, Section "Database Transaction Flow"
- **Type:** Sequence diagram
- **Shows:** Connection pooling, transactions, backup triggers

### Performance Monitoring
- **Location:** Additional Diagrams, Section "Performance Monitoring Sequence"
- **Type:** Sequence diagram
- **Shows:** Metrics collection, alerting, incident response

## 📖 Code Documentation

### Core ETL Job
- **Location:** `/glue-jobs/advisory_performance_etl.py`
- **Type:** Inline code documentation
- **Coverage:** Financial calculations, data validation, database operations

### Lambda Functions
- **Location:** `/lambda-functions/`
- **Files:** `etl_orchestrator.py`, `reconciliation_engine.py`
- **Type:** Docstrings and inline comments

### Infrastructure Code
- **Location:** `/infrastructure/app.py`
- **Type:** CDK infrastructure documentation
- **Coverage:** AWS resource configuration and dependencies

## 🚀 Deployment & Operations

### Deployment Scripts
- **Location:** `/scripts/deploy.sh`
- **Type:** Shell script with embedded documentation
- **Purpose:** Automated infrastructure deployment

### Database Setup
- **Location:** `/scripts/setup_database.py`
- **Type:** Python script with documentation
- **Purpose:** Database schema creation and initial configuration

### Sample Data Generation
- **Location:** `/scripts/generate_sample_data.py`
- **Type:** Python script
- **Purpose:** Test data generation for development and testing

## 🧪 Testing Documentation

### Test Suite
- **Location:** `/tests/test_etl_pipeline.py`
- **Type:** Unit and integration tests with documentation
- **Coverage:** ETL functions, validation logic, database operations

## 📊 Configuration Examples

### Environment Configuration
- **Location:** `/config/environment.json`
- **Type:** JSON configuration with comments
- **Purpose:** Environment-specific settings

### Monitoring Configuration
- **Location:** `/config/monitoring.py`
- **Type:** Python configuration
- **Purpose:** CloudWatch metrics and alerting setup

### Vendor Mapping
- **Location:** `/data-models/vendor_a_mapping.json`
- **Type:** JSON schema mapping
- **Purpose:** Field mapping between vendor formats and internal schema

## 🎨 UI Documentation

### Frontend Application
- **Location:** `/ui-application/frontend/`
- **Type:** React component documentation
- **Coverage:** Component structure, props, state management

### Backend API
- **Location:** `/ui-application/backend/`
- **Type:** Flask API documentation
- **Coverage:** Endpoints, request/response formats, authentication

## 📋 How to Use This Documentation

### For Stakeholders
1. Start with the **Confluence Page** for high-level overview
2. Review **Architecture Diagrams** for system understanding
3. Check **Operations Guide** for ongoing maintenance requirements

### For Developers
1. Read the **Markdown Documentation** for technical details
2. Study **Additional Technical Diagrams** for implementation specifics
3. Review **Code Documentation** in source files
4. Run **Test Suite** to understand expected behavior

### For Operations Team
1. Focus on **Operations Guide** for daily procedures
2. Study **Process Flow Diagrams** for troubleshooting
3. Review **Monitoring Configuration** for alerting setup
4. Use **Deployment Scripts** for infrastructure management

### For Business Users
1. Review **Project Overview** section in Confluence
2. Check **API Documentation** for integration possibilities
3. Study **UI Documentation** for user interface capabilities

## 🔍 Quick Reference

| Need | Document | Section |
|------|----------|---------|
| System Overview | Confluence Page | Project Overview |
| Architecture | Confluence Page | Architecture Overview |
| Data Flow | Confluence Page | Data Flow Architecture |
| Error Handling | Additional Diagrams | Error Handling Sequence |
| Database Schema | Confluence Page | Database Schema |
| API Details | Confluence Page | API Documentation |
| Deployment | Confluence Page | Deployment Guide |
| Troubleshooting | Confluence Page | Troubleshooting |
| Operations | Operations Guide | All sections |
| Performance | Confluence Page | Performance Optimization |
| Security | Confluence Page | Security & Compliance |

## 📝 Document Status

| Document | Status | Last Updated | Next Review |
|----------|--------|-------------|-------------|
| Confluence Page | ✅ Complete | 2025-07-08 | 2025-08-08 |
| Markdown Documentation | ✅ Complete | 2025-07-08 | 2025-08-08 |
| Operations Guide | ✅ Complete | 2025-07-08 | 2025-08-08 |
| Additional Diagrams | ✅ Complete | 2025-07-08 | 2025-08-08 |
| Code Documentation | 🔄 In Progress | 2025-07-08 | 2025-07-15 |
| UI Documentation | 📝 Planned | - | 2025-07-15 |

## 💡 Documentation Standards

### Diagram Standards
- Use Mermaid format for all diagrams
- Include legend for symbols and colors
- Keep diagrams focused and readable
- Update diagrams when architecture changes

### Code Documentation Standards
- Use docstrings for all functions and classes
- Include type hints in Python code
- Document complex business logic inline
- Maintain README files in each directory

### Version Control
- Tag documentation versions with code releases
- Maintain changelog for major documentation updates
- Review documentation quarterly
- Archive outdated versions

---

**Note:** This documentation index is maintained automatically. For questions or updates, contact the Data Engineering team.

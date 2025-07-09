# Advisory ETL UI Application

A comprehensive web-based user interface for monitoring and managing the Advisory Performance ETL pipeline. This application provides real-time visibility into data processing, reconciliation results, and data quality metrics.

## Features

### Dashboard
- Real-time ETL pipeline metrics
- Processing volume trends
- Data quality indicators
- Reconciliation pass rates
- Key performance statistics

### Vendor Management
- View all data vendors
- Browse processed files by vendor
- File processing status tracking
- Record count summaries

### File Details
- Detailed file processing information
- Sample data preview
- Performance analytics charts
- TWRR comparison visualizations
- Market value trends

### Reconciliation Results
- Comprehensive tolerance checking results
- Field-level reconciliation status
- Variance analysis
- Pass/fail rate monitoring
- Exportable reconciliation reports

### Account Performance
- Individual account performance tracking
- Historical performance charts
- TWRR trend analysis
- Market value evolution
- Net flow tracking

## Architecture

### Backend (Flask)
- RESTful API with comprehensive endpoints
- PostgreSQL database integration
- AWS Secrets Manager for secure configuration
- Data export capabilities
- Error handling and logging

### Frontend (React)
- Modern responsive web interface
- Ant Design component library
- Interactive charts with Recharts
- Real-time data updates
- Advanced filtering and search

## Prerequisites

- Python 3.8 or later
- Node.js 16 or later
- PostgreSQL database with ETL schema
- AWS credentials (for production)

## Quick Start

1. **Run the setup script:**
   ```bash
   chmod +x ui-application/setup.sh
   ./ui-application/setup.sh
   ```

2. **Configure environment variables:**
   ```bash
   # Backend configuration
   cp ui-application/backend/.env.example ui-application/backend/.env
   # Edit .env with your database details
   
   # Frontend configuration  
   cp ui-application/frontend/.env.example ui-application/frontend/.env
   ```

3. **Start the application:**
   ```bash
   ./ui-application/start-all.sh
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:5000/api

## Manual Setup

### Backend Setup

1. **Create virtual environment:**
   ```bash
   cd ui-application/backend
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start backend server:**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Install dependencies:**
   ```bash
   cd ui-application/frontend
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env if needed
   ```

3. **Start development server:**
   ```bash
   npm start
   ```

## Environment Configuration

### Backend (.env)
```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=advisory_performance
DB_USERNAME=postgres
DB_PASSWORD=password
DB_PASSWORD_SECRET=advisory-etl/db-password
AWS_REGION=us-east-1
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:5000/api
```

## API Endpoints

### Core Endpoints
- `GET /api/health` - Health check
- `GET /api/vendors` - List all vendors
- `GET /api/files` - List processed files
- `GET /api/file/{filename}/details` - File details
- `GET /api/dashboard/metrics` - Dashboard metrics

### Reconciliation Endpoints
- `GET /api/reconciliation/results` - Reconciliation results
- `GET /api/reconciliation/summary` - Reconciliation summary
- `GET /api/export/reconciliation-report` - Export reports

### Account Endpoints
- `GET /api/accounts` - Account performance data
- `GET /api/account/{id}/history` - Account history

## Database Schema

The application expects the following PostgreSQL tables:
- `performance_data` - Main ETL results
- `reconciliation_results` - Tolerance check results
- `vendor_mappings` - Vendor configuration

See `sql/schema.sql` for complete schema definition.

## Production Deployment

### Backend Deployment
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Using Docker
docker build -t advisory-etl-backend .
docker run -p 5000:5000 advisory-etl-backend
```

### Frontend Deployment
```bash
# Build for production
npm run build

# Serve with nginx or any static file server
# See build/ directory for optimized files
```

### AWS Deployment
The application can be deployed on AWS using:
- **Backend**: ECS Fargate or Lambda
- **Frontend**: S3 + CloudFront
- **Database**: RDS PostgreSQL
- **Secrets**: AWS Secrets Manager

## Features in Detail

### Dashboard Metrics
- Files processed (daily/weekly/monthly)
- Total accounts under management
- Assets under management (AUM)
- Reconciliation pass rates
- Average TWRR across portfolio

### Data Quality Monitoring
- Real-time tolerance checking
- Variance analysis by field
- Cross-account validation
- Historical trend analysis
- Automated alerts for failures

### Reconciliation Reporting
- Detailed variance reports
- Field-level analysis
- Account-specific results
- Exportable CSV reports
- Visual trend analysis

### Performance Analytics
- TWRR calculation verification
- Market value reconciliation
- Net flow analysis
- Historical performance tracking
- Benchmark comparisons

## Troubleshooting

### Common Issues

**Backend won't start:**
- Check PostgreSQL connection
- Verify environment variables
- Check Python dependencies

**Frontend won't load:**
- Verify Node.js version
- Check for port conflicts
- Ensure backend is running

**Database connection errors:**
- Verify database credentials
- Check network connectivity
- Ensure PostgreSQL is running

### Logs

Backend logs are available in:
- Console output (development)
- `ui-application/backend/logs/` (production)

Frontend logs are available in:
- Browser console
- Network tab for API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Security

- Environment variables for sensitive data
- AWS Secrets Manager integration
- CORS configuration for production
- Input validation and sanitization
- SQL injection prevention

## License

This project is licensed under the MIT License.

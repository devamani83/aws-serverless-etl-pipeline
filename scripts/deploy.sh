#!/bin/bash

# Deployment script for Advisory Performance ETL Pipeline
# This script deploys the complete serverless ETL infrastructure

set -e  # Exit on any error

echo "=== Advisory Performance ETL Pipeline Deployment ==="
echo "Starting deployment at $(date)"

# Configuration
PROJECT_NAME="advisory-performance-etl"
AWS_REGION=${AWS_REGION:-"us-east-1"}
ENVIRONMENT=${ENVIRONMENT:-"production"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check CDK
    if ! command -v cdk &> /dev/null; then
        print_error "AWS CDK is not installed. Please install it first."
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured. Please run 'aws configure' first."
        exit 1
    fi
    
    print_status "Prerequisites check passed ✓"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_status "Python environment setup complete ✓"
}

# Upload configuration files to S3
upload_configs() {
    print_status "Uploading configuration files..."
    
    # Create config bucket if it doesn't exist
    CONFIG_BUCKET="${PROJECT_NAME}-config-${RANDOM}"
    aws s3 mb "s3://${CONFIG_BUCKET}" --region ${AWS_REGION} || true
    
    # Upload configuration files
    aws s3 cp config/ "s3://${CONFIG_BUCKET}/config/" --recursive
    aws s3 cp data-models/ "s3://${CONFIG_BUCKET}/data-models/" --recursive
    aws s3 cp glue-jobs/ "s3://${CONFIG_BUCKET}/scripts/" --recursive
    
    print_status "Configuration files uploaded to s3://${CONFIG_BUCKET} ✓"
    echo "CONFIG_BUCKET=${CONFIG_BUCKET}" > .env
}

# Bootstrap CDK if needed
bootstrap_cdk() {
    print_status "Bootstrapping CDK..."
    
    # Get account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    
    # Bootstrap CDK
    cdk bootstrap aws://${ACCOUNT_ID}/${AWS_REGION}
    
    print_status "CDK bootstrapping complete ✓"
}

# Deploy infrastructure
deploy_infrastructure() {
    print_status "Deploying infrastructure..."
    
    cd infrastructure
    
    # Install CDK dependencies
    pip install -r requirements.txt
    
    # Synthesize the stack
    cdk synth
    
    # Deploy the stack
    cdk deploy --require-approval never
    
    cd ..
    
    print_status "Infrastructure deployment complete ✓"
}

# Setup database schema
setup_database() {
    print_status "Setting up database schema..."
    
    # Get database endpoint from CDK outputs
    DB_ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`DatabaseEndpoint`].OutputValue' \
        --output text)
    
    if [ -z "$DB_ENDPOINT" ]; then
        print_error "Could not retrieve database endpoint from CloudFormation"
        exit 1
    fi
    
    # Get database password from Secrets Manager
    DB_PASSWORD=$(aws secretsmanager get-secret-value \
        --secret-id advisory-etl/db-password \
        --query SecretString --output text | jq -r '.password')
    
    # Run database setup script
    PGPASSWORD=$DB_PASSWORD psql \
        -h $DB_ENDPOINT \
        -U etl_user \
        -d advisory_performance \
        -f sql/schema.sql
    
    print_status "Database schema setup complete ✓"
}

# Create sample data
create_sample_data() {
    print_status "Creating sample data files..."
    
    python3 scripts/generate_sample_data.py
    
    print_status "Sample data created ✓"
}

# Run tests
run_tests() {
    print_status "Running tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run unit tests
    python -m pytest tests/ -v
    
    print_status "Tests completed ✓"
}

# Deploy frontend application
deploy_frontend() {
    print_status "Deploying frontend application..."
    
    # Run the frontend deployment script
    chmod +x scripts/deploy_frontend.sh
    ./scripts/deploy_frontend.sh --environment $ENVIRONMENT --skip-infrastructure
    
    print_status "Frontend deployment complete ✓"
}

# Main deployment function
main() {
    print_status "Starting deployment process..."
    
    check_prerequisites
    setup_python_env
    upload_configs
    bootstrap_cdk
    deploy_infrastructure
    
    # Wait a bit for resources to be fully ready
    print_status "Waiting for resources to be ready..."
    sleep 30
    
    setup_database
    create_sample_data
    deploy_frontend
    
    # Optionally run tests
    if [ "$RUN_TESTS" = "true" ]; then
        run_tests
    fi
    
    print_status "=== Deployment Complete ==="
    print_status "Time: $(date)"
    
    # Display important information
    echo ""
    echo "=== Deployment Summary ==="
    echo "Project: $PROJECT_NAME"
    echo "Region: $AWS_REGION"
    echo "Environment: $ENVIRONMENT"
    echo ""
    echo "Next steps:"
    echo "1. Upload your data files to the raw data S3 bucket"
    echo "2. Monitor the pipeline execution in AWS Step Functions console"
    echo "3. Check CloudWatch logs for detailed execution information"
    echo "4. Review the generated reports and reconciliation results"
    echo ""
    echo "For more information, see the README.md file."
}

# Handle command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            AWS_REGION="$2"
            shift 2
            ;;
        --environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --run-tests)
            RUN_TESTS="true"
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --region REGION       AWS region (default: us-east-1)"
            echo "  --environment ENV     Environment name (default: production)"
            echo "  --run-tests          Run tests after deployment"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main

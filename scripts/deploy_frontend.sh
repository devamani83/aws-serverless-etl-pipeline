#!/bin/bash

# Frontend Deployment Script for Advisory ETL Pipeline
# Builds React application and deploys to S3 with CloudFront invalidation

set -e

# Configuration
FRONTEND_DIR="ui-application/frontend"
BACKEND_DIR="ui-application/backend"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-production}"
S3_BUCKET="advisory-etl-frontend-${ENVIRONMENT}"
CLOUDFRONT_DISTRIBUTION_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    if ! command_exists aws; then
        print_error "AWS CLI is not installed"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity > /dev/null 2>&1; then
        print_error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Deploy infrastructure using CDK
deploy_infrastructure() {
    print_status "Deploying infrastructure with CDK..."
    
    cd infrastructure
    
    # Install CDK dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    
    # Deploy the stack
    cdk deploy AdvisoryPerformanceETLStack --require-approval never
    
    # Get CloudFront distribution ID from CDK outputs
    CLOUDFRONT_DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontDistributionId`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    # Get S3 bucket name from CDK outputs
    S3_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`FrontendBucket`].OutputValue' \
        --output text 2>/dev/null || echo "$S3_BUCKET")
    
    cd ..
    print_success "Infrastructure deployment completed"
}

# Build React frontend
build_frontend() {
    print_status "Building React frontend application..."
    
    cd $FRONTEND_DIR
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing npm dependencies..."
        npm install
    fi
    
    # Set environment variables for build
    export REACT_APP_API_URL=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`APIGatewayURL`].OutputValue' \
        --output text 2>/dev/null || echo "https://api.advisory-etl.example.com")
    
    export REACT_APP_ENVIRONMENT=$ENVIRONMENT
    
    # Build the application
    print_status "Building application for $ENVIRONMENT environment..."
    npm run build
    
    if [ ! -d "build" ]; then
        print_error "Build failed - build directory not found"
        exit 1
    fi
    
    cd ../..
    print_success "Frontend build completed"
}

# Deploy to S3
deploy_to_s3() {
    print_status "Deploying frontend to S3 bucket: $S3_BUCKET"
    
    # Check if bucket exists
    if ! aws s3 ls "s3://$S3_BUCKET" > /dev/null 2>&1; then
        print_error "S3 bucket $S3_BUCKET does not exist"
        exit 1
    fi
    
    # Sync build files to S3
    aws s3 sync "$FRONTEND_DIR/build/" "s3://$S3_BUCKET" \
        --delete \
        --cache-control "public, max-age=31536000" \
        --exclude "*.html" \
        --exclude "service-worker.js" \
        --exclude "manifest.json"
    
    # Upload HTML files with shorter cache
    aws s3 sync "$FRONTEND_DIR/build/" "s3://$S3_BUCKET" \
        --delete \
        --cache-control "public, max-age=300" \
        --include "*.html" \
        --include "service-worker.js" \
        --include "manifest.json"
    
    print_success "Frontend deployed to S3"
}

# Invalidate CloudFront cache
invalidate_cloudfront() {
    if [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
        print_warning "CloudFront distribution ID not found, skipping cache invalidation"
        return
    fi
    
    print_status "Invalidating CloudFront cache for distribution: $CLOUDFRONT_DISTRIBUTION_ID"
    
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text)
    
    print_status "Invalidation created with ID: $INVALIDATION_ID"
    print_status "Waiting for invalidation to complete..."
    
    aws cloudfront wait invalidation-completed \
        --distribution-id "$CLOUDFRONT_DISTRIBUTION_ID" \
        --id "$INVALIDATION_ID"
    
    print_success "CloudFront cache invalidation completed"
}

# Deploy backend API
deploy_backend() {
    print_status "Deploying backend API..."
    
    cd $BACKEND_DIR
    
    # Install dependencies
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt -t .
    fi
    
    # The backend is deployed as part of the CDK stack
    # So we just need to update the Lambda function code
    
    # Create deployment package
    zip -r ../backend-deployment.zip . -x "*.pyc" "__pycache__/*" "*.git*"
    
    # Update Lambda function
    LAMBDA_FUNCTION_NAME=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`APILambdaFunction`].OutputValue' \
        --output text 2>/dev/null || echo "")
    
    if [ -n "$LAMBDA_FUNCTION_NAME" ]; then
        aws lambda update-function-code \
            --function-name "$LAMBDA_FUNCTION_NAME" \
            --zip-file fileb://../backend-deployment.zip
        
        print_success "Backend API updated"
    else
        print_warning "Backend Lambda function name not found in stack outputs"
    fi
    
    cd ../..
}

# Run health checks
run_health_checks() {
    print_status "Running health checks..."
    
    # Get CloudFront URL
    FRONTEND_URL=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`CloudFrontURL`].OutputValue' \
        --output text 2>/dev/null)
    
    # Get API URL
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[?OutputKey==`APIGatewayURL`].OutputValue' \
        --output text 2>/dev/null)
    
    if [ -n "$FRONTEND_URL" ]; then
        print_status "Testing frontend URL: $FRONTEND_URL"
        if curl -f -s "$FRONTEND_URL" > /dev/null; then
            print_success "Frontend is accessible"
        else
            print_warning "Frontend may not be ready yet (this is normal right after deployment)"
        fi
    fi
    
    if [ -n "$API_URL" ]; then
        print_status "Testing API health endpoint: ${API_URL}api/health"
        if curl -f -s "${API_URL}api/health" > /dev/null; then
            print_success "API is healthy"
        else
            print_warning "API health check failed"
        fi
    fi
}

# Display deployment information
show_deployment_info() {
    print_success "Deployment completed successfully!"
    echo
    print_status "Deployment Information:"
    echo "========================="
    
    # Get all outputs from CloudFormation
    aws cloudformation describe-stacks \
        --stack-name AdvisoryPerformanceETLStack \
        --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue,Description]' \
        --output table
    
    echo
    print_status "Next steps:"
    echo "1. Test the frontend application at the CloudFront URL"
    echo "2. Verify API endpoints are working"
    echo "3. Upload a test file to trigger the ETL pipeline"
    echo "4. Monitor CloudWatch for any errors"
}

# Main deployment function
main() {
    echo "🚀 Advisory ETL Frontend Deployment Script"
    echo "=========================================="
    echo
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --skip-infrastructure)
                SKIP_INFRASTRUCTURE=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --environment ENV    Set deployment environment (default: production)"
                echo "  --skip-infrastructure Skip CDK infrastructure deployment"
                echo "  --skip-build        Skip frontend build step"
                echo "  --help             Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    print_status "Deploying to environment: $ENVIRONMENT"
    echo
    
    # Run deployment steps
    check_prerequisites
    
    if [ "$SKIP_INFRASTRUCTURE" != "true" ]; then
        deploy_infrastructure
    fi
    
    if [ "$SKIP_BUILD" != "true" ]; then
        build_frontend
    fi
    
    deploy_to_s3
    invalidate_cloudfront
    deploy_backend
    
    # Wait a bit for propagation
    print_status "Waiting for deployment to propagate..."
    sleep 30
    
    run_health_checks
    show_deployment_info
}

# Run main function
main "$@"

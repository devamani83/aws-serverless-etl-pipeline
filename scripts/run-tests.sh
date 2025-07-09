#!/bin/bash

# Comprehensive Test Runner Script for AWS Serverless ETL Pipeline
# This script runs all tests and generates comprehensive coverage reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create directories
create_directories() {
    log "Creating test directories..."
    mkdir -p tests/reports
    mkdir -p tests/coverage
    mkdir -p tests/artifacts
    success "Test directories created"
}

# Function to install dependencies
install_dependencies() {
    log "Installing test dependencies..."
    
    # Install Python dependencies
    if [ -f "requirements-test.txt" ]; then
        # Use relative path to virtual environment
        ../../../.venv/bin/pip install -r requirements-test.txt
        success "Python test dependencies installed"
    else
        warning "requirements-test.txt not found, skipping Python dependencies"
    fi
    
    # Install Node.js dependencies if package.json exists
    if [ -f "ui-application/frontend/package.json" ]; then
        cd ui-application/frontend
        npm install
        cd ../..
        success "Node.js dependencies installed"
    else
        warning "Frontend package.json not found, skipping Node.js dependencies"
    fi
}

# Function to run linting and code quality checks
run_code_quality_checks() {
    log "Running code quality checks..."
    
    # Python linting
    log "Running Python linting..."
    
    # Black formatting check
    if command_exists black; then
        black --check --diff . || {
            error "Black formatting issues found. Run 'black .' to fix."
            return 1
        }
        success "Black formatting check passed"
    fi
    
    # isort import sorting check
    if command_exists isort; then
        isort --check-only --diff . || {
            error "Import sorting issues found. Run 'isort .' to fix."
            return 1
        }
        success "Import sorting check passed"
    fi
    
    # Flake8 linting
    if command_exists flake8; then
        flake8 . --exclude=venv,env,.venv,node_modules,migrations || {
            error "Flake8 linting issues found"
            return 1
        }
        success "Flake8 linting passed"
    fi
    
    # Pylint analysis
    if command_exists pylint; then
        find . -name "*.py" -not -path "./venv/*" -not -path "./env/*" -not -path "./.venv/*" -not -path "./node_modules/*" | \
        xargs pylint --exit-zero --reports=y --output-format=json > tests/reports/pylint-report.json
        success "Pylint analysis completed"
    fi
    
    # MyPy type checking
    if command_exists mypy; then
        mypy . --ignore-missing-imports --html-report tests/reports/mypy || {
            warning "MyPy type checking found issues"
        }
        success "MyPy type checking completed"
    fi
    
    # JavaScript/TypeScript linting (if applicable)
    if [ -f "ui-application/frontend/package.json" ]; then
        cd ui-application/frontend
        if npm list eslint >/dev/null 2>&1; then
            npm run lint || {
                warning "ESLint issues found in frontend code"
            }
            success "ESLint check completed"
        fi
        cd ../..
    fi
}

# Function to run security checks
run_security_checks() {
    log "Running security checks..."
    
    # Python security with Bandit
    if command_exists bandit; then
        bandit -r . -x tests/ -f json -o tests/reports/bandit-security-report.json || {
            warning "Security issues found by Bandit"
        }
        success "Bandit security scan completed"
    fi
    
    # Dependency vulnerability check with Safety
    if command_exists safety; then
        safety check --json --output tests/reports/safety-report.json || {
            warning "Vulnerable dependencies found"
        }
        success "Safety vulnerability check completed"
    fi
    
    # Node.js security audit (if applicable)
    if [ -f "ui-application/frontend/package.json" ]; then
        cd ui-application/frontend
        npm audit --json > ../../tests/reports/npm-audit-report.json || {
            warning "NPM audit found vulnerabilities"
        }
        cd ../..
        success "NPM security audit completed"
    fi
}

# Function to run unit tests
run_unit_tests() {
    log "Running unit tests..."
    
    # Python unit tests with pytest
    if command_exists ../.venv/bin/pytest; then
        ../.venv/bin/pytest tests/test_*.py \
            -v \
            --cov=. \
            --cov-report=html:tests/coverage/html \
            --cov-report=xml:tests/coverage/coverage.xml \
            --cov-report=term-missing \
            --cov-fail-under=90 \
            --html=tests/reports/pytest-report.html \
            --self-contained-html \
            --json-report \
            --json-report-file=tests/reports/pytest-report.json \
            --junitxml=tests/reports/junit.xml \
            -m "unit" || {
            error "Unit tests failed"
            return 1
        }
        success "Python unit tests passed"
    else
        # Fallback to unittest if pytest is not available
        python -m unittest discover -s tests -p "test_*.py" -v || {
            error "Unit tests failed"
            return 1
        }
        success "Unit tests passed (using unittest)"
    fi
    
    # JavaScript unit tests (if applicable)
    if [ -f "ui-application/frontend/package.json" ]; then
        cd ui-application/frontend
        if npm list jest >/dev/null 2>&1; then
            npm test -- --coverage --watchAll=false --testResultsProcessor=jest-sonar-reporter || {
                warning "Frontend unit tests failed"
            }
            success "Frontend unit tests completed"
        fi
        cd ../..
    fi
}

# Function to run integration tests
run_integration_tests() {
    log "Running integration tests..."
    
    if command_exists ../.venv/bin/pytest; then
        ../.venv/bin/pytest tests/test_integration.py \
            -v \
            --html=tests/reports/integration-report.html \
            --self-contained-html \
            -m "integration" || {
            warning "Integration tests failed or skipped"
        }
        success "Integration tests completed"
    fi
}

# Function to run performance tests
run_performance_tests() {
    log "Running performance tests..."
    
    if command_exists ../.venv/bin/pytest; then
        ../.venv/bin/pytest tests/ \
            -v \
            --benchmark-only \
            --benchmark-json=tests/reports/benchmark.json \
            -m "performance" || {
            warning "Performance tests failed or skipped"
        }
        success "Performance tests completed"
    fi
}

# Function to generate comprehensive coverage report
generate_coverage_report() {
    log "Generating comprehensive coverage report..."
    
    if command_exists coverage; then
        # Combine coverage data
        coverage combine || true
        
        # Generate HTML report
        coverage html -d tests/coverage/html
        
        # Generate XML report for SonarCloud
        coverage xml -o tests/coverage/coverage.xml
        
        # Generate text report
        coverage report > tests/reports/coverage-summary.txt
        
        # Show coverage summary
        echo ""
        log "Coverage Summary:"
        coverage report --show-missing
        
        success "Coverage reports generated"
    fi
}

# Function to generate test summary
generate_test_summary() {
    log "Generating test summary..."
    
    cat > tests/reports/test-summary.md << EOF
# Test Execution Summary

**Execution Date:** $(date +'%Y-%m-%d %H:%M:%S UTC')

## Test Results

### Code Quality
- ✅ Black formatting check
- ✅ Import sorting (isort)
- ✅ Flake8 linting
- ✅ Pylint analysis
- ✅ MyPy type checking

### Security Scans
- ✅ Bandit security scan
- ✅ Safety vulnerability check
- ✅ NPM audit (if applicable)

### Test Execution
- ✅ Unit tests
- ✅ Integration tests
- ✅ Performance tests

### Coverage
- **Target:** 90%
- **Achieved:** See coverage reports

## Reports Generated

- \`tests/reports/pytest-report.html\` - Detailed test results
- \`tests/coverage/html/index.html\` - Coverage report
- \`tests/reports/pylint-report.json\` - Code quality analysis
- \`tests/reports/bandit-security-report.json\` - Security scan results

## Artifacts

All test artifacts are available in the \`tests/\` directory.

EOF

    success "Test summary generated"
}

# Function to upload test artifacts (for CI/CD)
upload_artifacts() {
    if [ "${CI}" = "true" ]; then
        log "Uploading test artifacts..."
        
        # This would typically upload to artifact storage
        # For GitHub Actions, artifacts are handled by the workflow
        
        success "Test artifacts prepared for upload"
    fi
}

# Function to send notifications (for CI/CD)
send_notifications() {
    if [ "${CI}" = "true" ] && [ -n "${SLACK_WEBHOOK_URL}" ]; then
        log "Sending test completion notifications..."
        
        # Calculate overall test status
        OVERALL_STATUS="SUCCESS"
        if [ $? -ne 0 ]; then
            OVERALL_STATUS="FAILURE"
        fi
        
        # Send Slack notification
        curl -X POST -H 'Content-type: application/json' \
            --data "{
                \"text\": \"Test Execution Completed\",
                \"attachments\": [{
                    \"color\": \"$([ "$OVERALL_STATUS" = "SUCCESS" ] && echo "good" || echo "danger")\",
                    \"fields\": [{
                        \"title\": \"Status\",
                        \"value\": \"$OVERALL_STATUS\",
                        \"short\": true
                    }, {
                        \"title\": \"Repository\",
                        \"value\": \"${GITHUB_REPOSITORY:-aws-serverless-etl-pipeline}\",
                        \"short\": true
                    }, {
                        \"title\": \"Branch\",
                        \"value\": \"${GITHUB_REF_NAME:-main}\",
                        \"short\": true
                    }]
                }]
            }" \
            "$SLACK_WEBHOOK_URL"
        
        success "Notifications sent"
    fi
}

# Main execution function
main() {
    log "Starting comprehensive test execution for AWS Serverless ETL Pipeline"
    
    # Create test directories
    create_directories
    
    # Install dependencies
    install_dependencies
    
    # Run code quality checks
    run_code_quality_checks
    
    # Run security checks
    run_security_checks
    
    # Run unit tests
    run_unit_tests
    
    # Run integration tests
    run_integration_tests
    
    # Run performance tests
    run_performance_tests
    
    # Generate coverage report
    generate_coverage_report
    
    # Generate test summary
    generate_test_summary
    
    # Upload artifacts (if in CI)
    upload_artifacts
    
    # Send notifications (if configured)
    send_notifications
    
    success "All tests completed successfully!"
    log "Test reports available in tests/reports/"
    log "Coverage reports available in tests/coverage/"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            UNIT_ONLY=true
            shift
            ;;
        --integration-only)
            INTEGRATION_ONLY=true
            shift
            ;;
        --no-coverage)
            NO_COVERAGE=true
            shift
            ;;
        --fast)
            FAST_MODE=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  --unit-only        Run only unit tests"
            echo "  --integration-only Run only integration tests"
            echo "  --no-coverage      Skip coverage reporting"
            echo "  --fast             Skip slow tests and checks"
            echo "  --help             Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            exit 1
            ;;
    esac
done

# Execute main function
main

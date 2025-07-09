# GitHub Actions Secrets Configuration

This document describes the required secrets and environment variables for the CI/CD pipeline.

## Required Secrets

### AWS Configuration
- `AWS_ACCESS_KEY_ID`: AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key for deployment

### Optional Secrets
- `SLACK_WEBHOOK_URL`: Slack webhook for notifications
- `SONAR_TOKEN`: SonarCloud token for code analysis

## Environment Setup

### Staging Environment
The staging environment is automatically deployed when:
- Pushing to `develop` branch
- Manual workflow dispatch selecting "staging"

### Production Environment
The production environment is automatically deployed when:
- Pushing to `main` branch
- Manual workflow dispatch selecting "production"

## Setting Up Secrets

1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add the following secrets:

### AWS Credentials Setup

```bash
# Create IAM user for GitHub Actions
aws iam create-user --user-name github-actions-advisory-etl

# Attach necessary policies
aws iam attach-user-policy \
  --user-name github-actions-advisory-etl \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess

# Create access key
aws iam create-access-key --user-name github-actions-advisory-etl
```

### Required IAM Permissions

The GitHub Actions user needs the following permissions:
- `PowerUserAccess` (or more granular permissions including):
  - CloudFormation (full)
  - S3 (full)
  - Lambda (full)
  - RDS (full)
  - Glue (full)
  - CloudFront (full)
  - IAM (limited)
  - CloudWatch (full)
  - Secrets Manager (read)

### Environment Variables in Workflows

The following environment variables are automatically set in workflows:
- `AWS_REGION`: us-east-1 (configurable)
- `PYTHON_VERSION`: 3.9
- `NODE_VERSION`: 18

## Slack Integration (Optional)

To enable Slack notifications:

1. Create a Slack app in your workspace
2. Enable incoming webhooks
3. Add the webhook URL as `SLACK_WEBHOOK_URL` secret
4. The pipeline will send notifications for:
   - Deployment success/failure
   - Health check failures
   - Database migration completion

## SonarCloud Integration (Optional)

To enable code quality scanning:

1. Sign up at https://sonarcloud.io
2. Import your GitHub repository
3. Get your project token
4. Add the token as `SONAR_TOKEN` secret

## Environment Protection Rules

### Production Environment
- Requires manual approval for deployments
- Limited to `main` branch
- Requires all status checks to pass

### Staging Environment  
- Automatic deployment
- Available for `develop` and feature branches
- Used for testing and validation

## Manual Workflow Triggers

### Database Migration
```bash
# Go to Actions → Database Migration → Run workflow
# Select environment and migration type
# For production, type "CONFIRM" in the confirmation field
```

### Health Checks
```bash
# Go to Actions → Monitoring and Health Checks → Run workflow
# Select environment to check (staging/production/all)
```

## Monitoring Setup

The pipeline automatically sets up:
- CloudWatch dashboards
- Health check endpoints
- Performance monitoring
- Cost tracking alerts

## Troubleshooting

### Common Issues

1. **AWS Credentials Error**
   - Verify AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are correct
   - Check IAM permissions

2. **CDK Deployment Fails**
   - Ensure CDK bootstrap has been run
   - Check for resource conflicts

3. **Tests Failing**
   - Review test logs in Actions tab
   - Check for missing dependencies

4. **Security Scan Failures**
   - Review security reports in artifacts
   - Update vulnerable dependencies

### Getting Help

- Check workflow logs in GitHub Actions
- Review CloudWatch logs for runtime issues
- Consult the troubleshooting section in the main README

# GitHub Branch Strategy & Workflow

This document outlines the branching strategy, workflow, and best practices for the AWS Serverless ETL Pipeline project.

## 🌳 Branch Strategy Overview

We follow a **GitFlow-inspired** branching strategy optimized for continuous deployment and feature development.

### Branch Types

```
main (production)
├── develop (staging)
    ├── feature/feature-name
    ├── bugfix/bug-description  
    ├── hotfix/critical-fix
    └── release/version-number
```

## 📋 Branch Descriptions

### 🎯 Main Branches

#### `main` 
- **Purpose**: Production-ready code
- **Protection**: ⚠️ **Highly Protected**
- **Deployment**: Automatically deploys to **Production**
- **Merge Policy**: Only from `develop` via PR
- **Required Reviews**: 2+ approvals
- **Status Checks**: All CI/CD checks must pass

#### `develop`
- **Purpose**: Integration branch for features
- **Protection**: 🛡️ **Protected** 
- **Deployment**: Automatically deploys to **Staging**
- **Merge Policy**: From feature branches via PR
- **Required Reviews**: 1+ approval
- **Status Checks**: All CI/CD checks must pass

### 🚀 Feature Branches

#### `feature/feature-name`
- **Purpose**: New features and enhancements
- **Naming**: `feature/add-twrr-calculation`
- **Source**: Branch from `develop`
- **Merge**: Into `develop` via PR
- **Lifecycle**: Delete after merge
- **CI/CD**: Runs tests and quality checks

#### `bugfix/bug-description`
- **Purpose**: Non-critical bug fixes
- **Naming**: `bugfix/fix-reconciliation-error`
- **Source**: Branch from `develop`
- **Merge**: Into `develop` via PR
- **Lifecycle**: Delete after merge

#### `hotfix/critical-fix`
- **Purpose**: Critical production fixes
- **Naming**: `hotfix/fix-security-vulnerability`
- **Source**: Branch from `main`
- **Merge**: Into both `main` and `develop`
- **Lifecycle**: Delete after merge
- **Priority**: 🚨 **High Priority**

#### `release/version-number`
- **Purpose**: Release preparation and testing
- **Naming**: `release/v1.2.0`
- **Source**: Branch from `develop`
- **Merge**: Into `main` and back-merge to `develop`
- **Lifecycle**: Delete after release

## 🔒 Branch Protection Rules

### `main` Branch Protection

```yaml
Protection Rules:
  - Require pull request reviews: 2
  - Dismiss stale reviews: true
  - Require review from code owners: true
  - Restrict pushes to matching branches: true
  - Require status checks: true
  - Require conversation resolution: true
  - Require linear history: true
  - Required status checks:
    - Test and Validate
    - Code Quality / Python Code Quality
    - Code Quality / JavaScript/React Code Quality
    - Security Scan / Security Vulnerability Scan
    - Security Scan / Secret Scanning
```

### `develop` Branch Protection

```yaml
Protection Rules:
  - Require pull request reviews: 1
  - Dismiss stale reviews: true
  - Require status checks: true
  - Required status checks:
    - Test and Validate
    - Code Quality / Python Code Quality  
    - Code Quality / JavaScript/React Code Quality
    - Security Scan / Security Vulnerability Scan
```

## 🔄 Workflow Process

### 1. Feature Development

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/add-performance-metrics

# 3. Develop and commit
git add .
git commit -m "feat: add TWRR calculation with validation"

# 4. Push and create PR
git push origin feature/add-performance-metrics
# Create PR via GitHub UI
```

### 2. Code Review Process

#### PR Creation Checklist
- [ ] **Title**: Clear, descriptive title
- [ ] **Description**: Complete PR template filled out
- [ ] **Labels**: Appropriate labels assigned
- [ ] **Reviewers**: Assign relevant team members
- [ ] **Milestone**: Link to project milestone
- [ ] **Size**: Keep PRs under 500 lines when possible

#### Review Requirements
- **Feature PRs**: 1+ approval from team members
- **Main PRs**: 2+ approvals, including code owner
- **All status checks** must pass
- **Conversations resolved** before merge

### 3. Merge Strategies

#### Feature → Develop
- **Strategy**: Squash and Merge
- **Commit Message**: `feat: descriptive feature summary`
- **Branch Cleanup**: Delete feature branch

#### Develop → Main  
- **Strategy**: Create a Merge Commit
- **Commit Message**: `release: version bump and changelog`
- **Branch Cleanup**: Keep develop branch

#### Hotfix Process
```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/fix-critical-bug

# 2. Fix and commit
git commit -m "fix: resolve critical security issue"

# 3. PR to main (expedited review)
git push origin hotfix/fix-critical-bug

# 4. After merge to main, also merge to develop
git checkout develop
git merge main
```

## 🏷️ Naming Conventions

### Branch Names
```bash
feature/add-vendor-mapping       # New features
feature/improve-etl-performance  # Enhancements
bugfix/fix-data-validation      # Bug fixes
hotfix/patch-security-flaw      # Critical fixes
release/v1.2.0                  # Release preparation
docs/update-api-documentation   # Documentation
refactor/optimize-database      # Code refactoring
```

### Commit Messages
Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
feat: add new TWRR calculation algorithm
fix: resolve reconciliation timeout issue
docs: update deployment documentation
style: format code with black
refactor: optimize database query performance
test: add integration tests for ETL pipeline
chore: update dependencies to latest versions
ci: improve GitHub Actions workflow efficiency
```

### PR Titles
```bash
feat: Add real-time data quality monitoring
fix: Resolve Lambda memory allocation issue  
docs: Update infrastructure deployment guide
refactor: Optimize Glue job performance
security: Patch dependency vulnerabilities
```

## 🚀 Release Process

### 1. Version Strategy
We use [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes (`1.0.0` → `2.0.0`)
- **MINOR**: New features (`1.0.0` → `1.1.0`)
- **PATCH**: Bug fixes (`1.0.0` → `1.0.1`)

### 2. Release Workflow
```bash
# 1. Create release branch
git checkout develop
git checkout -b release/v1.2.0

# 2. Update version and changelog
# - Update version in package.json, pyproject.toml
# - Update CHANGELOG.md
# - Final testing and bug fixes

# 3. Create PR to main
# Title: "release: v1.2.0 - Feature summary"

# 4. After merge, create GitHub release
# - Tag: v1.2.0
# - Release notes from CHANGELOG.md

# 5. Back-merge to develop
git checkout develop
git merge main
```

## 🎯 Code Owner Rules

Create `.github/CODEOWNERS` file:

```bash
# Global ownership
* @devamani83

# Infrastructure changes
infrastructure/ @devamani83 @platform-team
.github/workflows/ @devamani83 @devops-team

# Database changes  
sql/ @devamani83 @data-team
scripts/setup_database.py @devamani83 @data-team

# Frontend changes
ui-application/frontend/ @devamani83 @frontend-team

# Security-sensitive files
.github/workflows/security.yml @devamani83 @security-team
*.yml @devamani83
```

## 📊 Automation & Integrations

### GitHub Actions Integration
- **Feature Branches**: Run tests and quality checks
- **Develop Branch**: Deploy to staging environment
- **Main Branch**: Deploy to production environment
- **PR Creation**: Run full CI/CD pipeline

### Automated Checks
- ✅ **Code Quality**: Linting, formatting, complexity
- ✅ **Security**: Vulnerability scanning, secret detection
- ✅ **Testing**: Unit, integration, end-to-end tests
- ✅ **Documentation**: Link checking, spell checking
- ✅ **Performance**: Load testing on staging

### Deployment Gates
- **Staging**: Automatic deployment + health checks
- **Production**: Manual approval required
- **Rollback**: Automated rollback on failure

## 🛡️ Security Considerations

### Sensitive Changes
Changes requiring extra security review:
- IAM permissions and policies
- Database schema modifications
- API authentication/authorization
- Secrets management
- Infrastructure configurations

### Security Review Process
1. **Automatic Security Scan**: Runs on all PRs
2. **Manual Security Review**: Required for sensitive changes
3. **Penetration Testing**: For major releases
4. **Compliance Check**: Automated compliance validation

## 📈 Metrics & Monitoring

### Branch Health Metrics
- **PR Merge Time**: Target < 2 days
- **Build Success Rate**: Target > 95%
- **Code Coverage**: Target > 80%
- **Security Scan Pass Rate**: Target 100%

### Quality Gates
- All tests must pass
- Code coverage must not decrease
- Security scans must pass
- Performance tests must pass
- Documentation must be updated

## 🎓 Best Practices

### Do's ✅
- **Small PRs**: Keep changes focused and reviewable
- **Clear Commits**: Write descriptive commit messages
- **Test Coverage**: Add tests for new functionality
- **Documentation**: Update docs with changes
- **Security**: Follow security best practices
- **Performance**: Consider performance impact

### Don'ts ❌
- **Direct Push**: Never push directly to main/develop
- **Large PRs**: Avoid PRs with >500 lines of changes
- **Broken Tests**: Don't merge with failing tests
- **Missing Reviews**: Don't merge without required approvals
- **Incomplete PRs**: Don't create draft PRs for long periods

## 🔧 Tools & Integrations

### Required Tools
- **Git**: Version control
- **GitHub CLI**: For automation
- **Pre-commit hooks**: Code quality enforcement
- **Conventional Commits**: Commit message formatting

### IDE Integrations
- **VSCode**: GitLens, GitHub Pull Requests
- **IntelliJ**: GitHub integration
- **Git hooks**: Pre-commit quality checks

## 📞 Support & Troubleshooting

### Common Issues

#### Branch Behind Main
```bash
git checkout feature/your-branch
git rebase origin/main
git push --force-with-lease origin feature/your-branch
```

#### Merge Conflicts
```bash
git checkout feature/your-branch
git merge origin/develop
# Resolve conflicts
git commit -m "resolve: merge conflicts with develop"
git push origin feature/your-branch
```

#### Failed CI/CD Checks
1. Check workflow logs in GitHub Actions
2. Run tests locally: `npm test && python -m pytest`
3. Run linting: `npm run lint && flake8 .`
4. Fix issues and push updates

### Getting Help
- 📖 **Documentation**: Project Wiki
- 💬 **Team Chat**: #engineering-support Slack channel
- 🐛 **Issues**: GitHub Issues
- 📧 **Maintainer**: @devamani83

---

**Remember**: This branching strategy ensures code quality, security, and maintainability while enabling rapid development and deployment! 🚀

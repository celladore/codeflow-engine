# CodeFlow Dependency Management

This document describes the dependency management process for CodeFlow repositories.

---

## Overview

CodeFlow uses multiple package managers across different repositories:
- **Python:** Poetry (codeflow-engine)
- **Node.js:** pnpm (codeflow-desktop, codeflow-vscode-extension, codeflow-website)
- **Infrastructure:** Bicep modules (codeflow-infrastructure)

---

## Dependency Update Process

### Regular Updates

#### Weekly Minor Updates
- Review and update patch/minor versions
- Test updates in development
- Merge to main after testing

#### Monthly Major Updates
- Review major version updates
- Test thoroughly
- Update documentation if needed
- Coordinate across repos if dependencies are shared

### Security Updates

#### Immediate Action
1. **Identify Vulnerability**
   - Check Dependabot alerts
   - Review security advisories
   - Check CVE databases

2. **Assess Impact**
   - Determine affected components
   - Assess severity
   - Check if exploit is public

3. **Update Dependencies**
   - Update to patched version
   - Test thoroughly
   - Deploy immediately

4. **Documentation**
   - Update CHANGELOG.md
   - Create security advisory (if needed)
   - Notify users (if critical)

---

## Dependency Review Process

### Automated Reviews

#### Dependabot
- **Configuration:** `.github/dependabot.yml`
- **Frequency:** Daily checks
- **Scope:** All dependencies
- **Actions:** Create PRs for updates

#### Security Scanning
- **GitHub Advanced Security:** Dependency scanning
- **Snyk:** Optional additional scanning
- **Safety:** Python-specific security checks

### Manual Reviews

#### Before Merging Updates
1. **Review Changelog**
   - Check breaking changes
   - Review new features
   - Check deprecations

2. **Test Updates**
   - Run test suite
   - Check integration tests
   - Manual testing if needed

3. **Check Compatibility**
   - Verify compatibility with other dependencies
   - Check Python/Node.js version requirements
   - Verify platform compatibility

---

## Dependency Update Schedule

### Python (codeflow-engine)

#### Weekly
- Security patches
- Patch version updates

#### Monthly
- Minor version updates
- Review major updates

#### Quarterly
- Major version updates
- Python version updates

### Node.js (codeflow-desktop, codeflow-vscode-extension, codeflow-website)

#### Weekly
- Security patches
- Patch version updates

#### Monthly
- Minor version updates
- Review major updates

#### Quarterly
- Major version updates
- Node.js version updates

### Infrastructure (codeflow-infrastructure)

#### Monthly
- Bicep module updates
- Azure SDK updates

#### Quarterly
- Major infrastructure updates
- Azure resource provider updates

---

## Breaking Changes

### Handling Breaking Changes

1. **Identify Breaking Changes**
   - Review dependency changelog
   - Check migration guides
   - Test in development

2. **Plan Migration**
   - Create migration plan
   - Update code
   - Update tests
   - Update documentation

3. **Coordinate Release**
   - Bump major version if needed
   - Update CHANGELOG.md
   - Create migration guide
   - Announce breaking changes

### Examples

#### Python Dependency
```python
# Before
requests==2.28.0

# After (breaking change)
requests==3.0.0  # Requires code changes
```

#### Node.js Dependency
```json
{
  "dependencies": {
    "react": "^18.0.0"  // Breaking change from 17.x
  }
}
```

---

## Dependency Security

### Security Scanning Tools

#### GitHub Dependabot
- **Configuration:** `.github/dependabot.yml`
- **Alerts:** Automatic vulnerability detection
- **Updates:** Automated security PRs

#### Safety (Python)
```bash
# Check Python dependencies
safety check
```

#### pnpm audit (Node.js)
```bash
# Check Node.js dependencies
pnpm audit
pnpm audit --fix
```

### Security Update Process

1. **Receive Alert**
   - Dependabot alert
   - Security advisory
   - CVE notification

2. **Assess Severity**
   - Critical: Immediate action
   - High: Update within 24 hours
   - Medium: Update within 1 week
   - Low: Update in next regular cycle

3. **Update Dependency**
   - Update to patched version
   - Test thoroughly
   - Deploy immediately (if critical)

4. **Documentation**
   - Update CHANGELOG.md
   - Create security advisory (if needed)

---

## Dependency Lock Files

### Python (Poetry)
- **File:** `poetry.lock`
- **Purpose:** Lock exact versions
- **Update:** `poetry update`
- **Commit:** Always commit lock file

### Node.js (pnpm)
- **File:** `pnpm-lock.yaml`
- **Purpose:** Lock exact versions
- **Update:** `pnpm update`
- **Commit:** Always commit lock file

### Node.js (yarn)
- **File:** `yarn.lock`
- **Purpose:** Lock exact versions
- **Update:** `yarn upgrade`
- **Commit:** Always commit lock file

---

## Dependency Versioning Strategy

### Version Ranges

#### Python (Poetry)
```toml
# Exact version
requests = "2.28.0"

# Compatible release
requests = "^2.28.0"  # >=2.28.0, <3.0.0

# Wildcard
requests = "~2.28.0"  # >=2.28.0, <2.29.0
```

#### Node.js (pnpm)
```json
{
  "dependencies": {
    "react": "18.0.0",        // Exact
    "react": "^18.0.0",      // Compatible
    "react": "~18.0.0",      // Patch updates
    "react": ">=18.0.0"      // Minimum
  }
}
```

### Best Practices

1. **Use Compatible Ranges**
   - `^` for minor updates
   - `~` for patch updates
   - Exact versions for critical dependencies

2. **Lock Files**
   - Always commit lock files
   - Use lock files in CI/CD
   - Review lock file changes

3. **Regular Updates**
   - Update regularly
   - Test updates
   - Review changelogs

---

## Dependency Review Checklist

### Before Updating

- [ ] Review dependency changelog
- [ ] Check for breaking changes
- [ ] Review security advisories
- [ ] Check compatibility with other dependencies
- [ ] Verify platform compatibility

### After Updating

- [ ] Run test suite
- [ ] Check integration tests
- [ ] Manual testing (if needed)
- [ ] Update documentation (if needed)
- [ ] Update CHANGELOG.md
- [ ] Commit lock files

---

## Dependabot Configuration

### Example `.github/dependabot.yml`

```yaml
version: 2
updates:
  # Python dependencies
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "team-leads"
    labels:
      - "dependencies"
      - "python"

  # Node.js dependencies
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "team-leads"
    labels:
      - "dependencies"
      - "javascript"
```

---

## Additional Resources

- [Poetry Documentation](https://python-poetry.org/docs/)
- [pnpm Documentation](https://pnpm.io/)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [Security Best Practices](./SECURITY_BEST_PRACTICES.md)

---

## Support

For dependency questions:
- GitHub Issues: [codeflow-orchestration/issues](https://github.com/JustAGhosT/codeflow-orchestration/issues)
- Documentation: This document


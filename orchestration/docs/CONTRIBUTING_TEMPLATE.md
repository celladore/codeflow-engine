# Contributing to CodeFlow

Thank you for your interest in contributing to CodeFlow! This document provides guidelines and instructions for contributing to any CodeFlow repository.

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style Guidelines](#code-style-guidelines)
- [Testing Requirements](#testing-requirements)
- [Pull Request Process](#pull-request-process)
- [Commit Message Format](#commit-message-format)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

---

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive feedback
- Respect different viewpoints and experiences

---

## Getting Started

### Prerequisites

- Git installed and configured
- Repository-specific requirements (see README.md)
- Development tools for your platform

### Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
   cd REPO_NAME
   ```
3. **Set up development environment** (see README.md)
4. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   ```

---

## Development Workflow

### Branch Naming

Use descriptive branch names with prefixes:

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test additions/changes
- `chore/` - Maintenance tasks

**Examples:**
- `feature/add-user-authentication`
- `fix/resolve-database-connection-issue`
- `docs/update-deployment-guide`

### Making Changes

1. **Make your changes** in your feature branch
2. **Test your changes** thoroughly
3. **Update documentation** as needed
4. **Commit your changes** (see [Commit Message Format](#commit-message-format))
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

---

## Code Style Guidelines

### Python (codeflow-engine)

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters
- Use `ruff` for linting and formatting
- Use `mypy` for type checking

**Before committing:**
```bash
ruff check .
ruff format .
mypy codeflow_engine
```

### TypeScript/JavaScript (codeflow-desktop, codeflow-vscode-extension, codeflow-website)

- Follow ESLint configuration
- Use Prettier for formatting
- Use TypeScript for new code
- Maximum line length: 100 characters
- Use meaningful variable and function names

**Before committing:**
```bash
pnpm run lint
pnpm run format
pnpm run type-check
```

### PowerShell (Scripts)

- Follow [PSScriptAnalyzer](https://github.com/PowerShell/PSScriptAnalyzer) rules
- Use approved verbs for function names
- Add comprehensive help comments
- Use proper error handling

**Before committing:**
```bash
Invoke-ScriptAnalyzer -Path .\scripts\*.ps1
```

### Documentation

- Use Markdown format
- Follow existing documentation style
- Include code examples where helpful
- Keep documentation up to date

---

## Testing Requirements

### Unit Tests

- Write tests for all new features
- Maintain or improve test coverage
- Tests should be fast and isolated
- Use descriptive test names

### Integration Tests

- Add integration tests for API changes
- Test cross-component interactions
- Verify database operations

### Running Tests

**Python:**
```bash
pytest
pytest --cov=codeflow_engine
```

**TypeScript/JavaScript:**
```bash
pnpm test
pnpm run test:coverage
```

### Test Coverage

- **codeflow-engine**: Target >80% for critical components
- **codeflow-desktop**: Target >70% for UI components
- **codeflow-vscode-extension**: Target >70% for core functionality
- **codeflow-website**: Target >60% for pages

---

## Pull Request Process

### Before Submitting

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Test coverage maintained or improved
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)
- [ ] No merge conflicts

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How was this tested?

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Create pull request** with clear description
2. **Wait for review** - maintainers will review your PR
3. **Address feedback** - make requested changes
4. **Get approval** - at least one maintainer approval required
5. **Merge** - maintainer will merge when ready

### Review Guidelines

**For Reviewers:**
- Be respectful and constructive
- Focus on code quality and maintainability
- Ask questions if something is unclear
- Approve when satisfied with changes

**For Contributors:**
- Respond to feedback promptly
- Be open to suggestions
- Ask questions if feedback is unclear
- Thank reviewers for their time

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks
- `perf`: Performance improvements
- `ci`: CI/CD changes

### Examples

```
feat(engine): add user authentication

Implement OAuth2 authentication flow with GitHub.
Add user session management and token refresh.

Closes #123
```

```
fix(extension): resolve connection timeout issue

Increase timeout for API calls from 30s to 60s.
Add retry logic for failed connections.

Fixes #456
```

```
docs(deployment): update Azure deployment guide

Add Kubernetes deployment section.
Update environment variables reference.
```

---

## Reporting Issues

### Bug Reports

Use the GitHub issue template and include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, versions, configuration
- **Logs**: Relevant error messages or logs
- **Screenshots**: If applicable

### Security Issues

**Do NOT** create a public issue for security vulnerabilities.

Instead, email: security@codeflow.io

---

## Feature Requests

Use the GitHub issue template and include:

- **Description**: Clear description of the feature
- **Use Case**: Why this feature is needed
- **Proposed Solution**: How it should work
- **Alternatives**: Other solutions considered
- **Additional Context**: Any other relevant information

---

## Questions?

- **GitHub Discussions**: For questions and general discussion
- **GitHub Issues**: For bug reports and feature requests
- **Documentation**: Check README.md and docs/ directory

---

## Additional Resources

- [CodeFlow Documentation](https://codeflow.io/docs)
- [Development Setup Guide](../scripts/dev-setup.ps1)
- [Code Style Guides](#code-style-guidelines)

---

Thank you for contributing to CodeFlow! 🎉


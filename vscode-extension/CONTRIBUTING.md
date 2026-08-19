# Contributing to CodeFlow VS Code Extension

Thank you for your interest in contributing to the CodeFlow VS Code extension! This document provides guidelines specific to the extension.

---

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Set up development environment**:
   ```bash
   pnpm install
   ```
4. **Create a branch** for your changes

---

## Development Workflow

### Prerequisites

- Node.js 20+
- VS Code (for testing)
- TypeScript knowledge

### Running Locally

```bash
# Compile TypeScript
pnpm run compile

# Watch mode
pnpm run watch

# Launch extension (press F5 in VS Code)
```

### Code Style

- Follow ESLint configuration
- Use Prettier for formatting
- Use TypeScript for all code
- Follow VS Code extension API best practices

**Before committing:**
```bash
pnpm run lint
pnpm run format
pnpm run compile
```

### Testing

```bash
# Run tests
pnpm test

# Run with coverage
pnpm run test:coverage
```

**Target Coverage:** >70% for core functionality

---

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure tests pass** and coverage is maintained
3. **Test extension** in VS Code
4. **Update documentation** as needed
5. **Create a pull request** with a clear description

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Extension tested in VS Code
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Tested on Windows, macOS, and Linux

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(extension): add workspace analysis command

Implement codeflow.checkWorkspace command.
Add progress indicator and result display.

Closes #123
```

---

## Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- VS Code version
- Extension version
- Logs from Output panel

---

## Questions?

- GitHub Discussions: For questions
- GitHub Issues: For bugs and features
- See [main CONTRIBUTING guide](../../codeflow-orchestration/docs/CONTRIBUTING_TEMPLATE.md) for more details

---

Thank you for contributing! 🎉


# Contributing to CodeFlow Desktop

Thank you for your interest in contributing to CodeFlow Desktop! This document provides guidelines specific to the desktop application.

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
- Rust (latest stable)
- Tauri CLI: `pnpm add -g @tauri-apps/cli`

### Running Locally

```bash
# Development mode
pnpm run tauri dev

# Build
pnpm run tauri build
```

### Code Style

- Follow ESLint configuration
- Use Prettier for formatting
- Use TypeScript for all new code
- Follow React best practices

**Before committing:**
```bash
pnpm run lint
pnpm run format
pnpm run type-check
```

### Testing

```bash
# Run tests
pnpm test

# Run with coverage
pnpm run test:coverage
```

**Target Coverage:** >70% for UI components

---

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure tests pass** and coverage is maintained
3. **Update documentation** as needed
4. **Create a pull request** with a clear description
5. **Address review feedback** promptly

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Tested on Windows, macOS, and Linux (if applicable)

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(desktop): add dark mode toggle

Implement dark mode with system preference detection.
Add settings UI for manual theme selection.

Closes #123
```

---

## Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, versions)
- Screenshots if applicable

---

## Questions?

- GitHub Discussions: For questions
- GitHub Issues: For bugs and features
- See [main CONTRIBUTING guide](../../codeflow-orchestration/docs/CONTRIBUTING_TEMPLATE.md) for more details

---

Thank you for contributing! 🎉


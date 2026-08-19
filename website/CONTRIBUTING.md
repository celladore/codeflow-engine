# Contributing to CodeFlow Website

Thank you for your interest in contributing to the CodeFlow website! This document provides guidelines specific to the website.

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
- Next.js knowledge
- React/TypeScript experience

### Running Locally

```bash
# Development server
pnpm run dev

# Build
pnpm run build

# Start production server
pnpm start
```

### Code Style

- Follow ESLint configuration
- Use Prettier for formatting
- Use TypeScript for all new code
- Follow Next.js best practices
- Use Tailwind CSS for styling

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

**Target Coverage:** >60% for pages

---

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure tests pass** and coverage is maintained
3. **Test locally** in development and production modes
4. **Update documentation** as needed
5. **Create a pull request** with a clear description

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Site tested locally
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Responsive design verified

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(website): add pricing page

Create new pricing page with tier comparison.
Add responsive design and animations.

Closes #123
```

---

## Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Browser and OS information
- Screenshots if applicable

---

## Questions?

- GitHub Discussions: For questions
- GitHub Issues: For bugs and features
- See [main CONTRIBUTING guide](../../codeflow-orchestration/docs/CONTRIBUTING_TEMPLATE.md) for more details

---

Thank you for contributing! 🎉


# CodeFlow Website

Marketing website for CodeFlow AI built with Next.js.

> Canonical source: [website](website) in the CodeFlow monorepo.
> Legacy split repo: https://github.com/JustAGhosT/codeflow-website

## Overview

This is the marketing website for CodeFlow AI, providing information about the platform, features, and getting started guides.

## Technology Stack

- **Framework**: [Next.js 15.x](https://nextjs.org/) with App Router
- **Language**: [TypeScript](https://www.typescriptlang.org/)
- **Styling**: [Tailwind CSS 4.x](https://tailwindcss.com/)
- **Testing**: [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/react)
- **Deployment**: [Azure Static Web Apps](https://azure.microsoft.com/services/app-service/static/)

## Development

### Prerequisites

- Node.js 18+
- pnpm

### Getting Started

```bash
# Install dependencies
pnpm install

# Run development server
pnpm run dev

# Build for production
pnpm run build

# Start production server
pnpm start
```

### Testing

```bash
# Run tests
pnpm test

# Run tests in watch mode
pnpm run test:watch

# Run tests with coverage report
pnpm run test:coverage
```

**Coverage Thresholds**: 60% for statements, branches, functions, and lines.

### Linting

```bash
# Run ESLint
pnpm run lint
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

| Document                                                     | Description                                                |
| ------------------------------------------------------------ | ---------------------------------------------------------- |
| [Project Context](docs/project-context.md)                   | Business goals, target users, and user journeys            |
| [Design System](docs/design-system.md)                       | Design tokens, typography, colors, and component inventory |
| [Architecture Overview](docs/architecture-overview.md)       | System architecture, data flow, and deployment pipeline    |
| [Tech Stack](docs/tech-stack.md)                             | Detailed technology breakdown by layer                     |
| [Best Practices Benchmark](docs/best-practices-benchmark.md) | Industry standards and evaluation criteria                 |
| [Audit Findings](docs/audit-findings.md)                     | Code audit results and recommendations                     |
| [Technical Debt Registry](docs/technical-debt-registry.md)   | Tracked issues, priorities, and resolution status          |

## Deployment

The website is deployed to Azure Static Web Apps. See [`codeflow-infrastructure`](https://github.com/JustAGhosT/codeflow-infrastructure) for deployment infrastructure.

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Build**: Compiles the Next.js application
- **Test**: Runs Vitest test suite (blocking)
- **Lint**: Runs ESLint checks (blocking)
- **Deploy**: Deploys to Azure Static Web Apps on push to main

## Contributing

### Code Quality Standards

1. **TypeScript**: All code must be properly typed
2. **Testing**: New features should include unit tests
3. **Linting**: Code must pass ESLint without errors
4. **Accessibility**: Follow WCAG 2.1 AA guidelines

### Commit Message Format

Use semantic commit messages:

```text
feat: add new feature
fix: resolve bug
docs: update documentation
test: add or update tests
refactor: code improvements without behavior change
```

## Related Repositories

- [`codeflow-engine`](https://github.com/JustAGhosT/codeflow-engine) - Core engine
- [`codeflow-infrastructure`](https://github.com/JustAGhosT/codeflow-infrastructure) - Production infrastructure
- [`codeflow-desktop`](https://github.com/JustAGhosT/codeflow-desktop) - Desktop application (contains shared design system)
- [`codeflow-vscode-extension`](https://github.com/JustAGhosT/codeflow-vscode-extension) - VS Code extension
- [`codeflow-azure-setup`](https://github.com/JustAGhosT/codeflow-azure-setup) - Azure bootstrap scripts

## License

MIT

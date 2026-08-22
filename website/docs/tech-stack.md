# CodeFlow Website - Technology Stack Overview

This document provides a comprehensive overview of the technology stack used in the CodeFlow Website, including versions, configurations, and layer-by-layer breakdown.

---

## Stack Summary

| Layer | Technology | Version | Status |
|-------|------------|---------|--------|
| Framework | Next.js | 16.0.7 | Production |
| UI Library | React | 19.2.0 | Production |
| Language | TypeScript | ^5.x | Production |
| Styling | Tailwind CSS | ^4.x | Production |
| Linting | ESLint | ^9.x | Development |
| Runtime | Node.js | 20.x | Production |
| Deployment | Azure Static Web Apps | - | Production |

---

## Frontend Stack

### Framework: Next.js 16.x

| Attribute | Value |
|-----------|-------|
| Version | 16.0.7 |
| Output Mode | Static Export (`output: 'export'`) |
| Image Optimization | Disabled (unoptimized: true) |
| Routing | App Router (app directory) |
| Trailing Slashes | Enabled |

**Configuration** (`next.config.ts`):
- Static site generation for Azure Static Web Apps compatibility
- Unoptimized images (no Next.js Image Optimization API)
- Trailing slashes enabled for clean URLs

### UI Library: React 19.x

| Attribute | Value |
|-----------|-------|
| Version | 19.2.0 |
| React DOM | 19.2.0 |
| JSX Transform | react-jsx (automatic) |

**Features Used**:
- Function components
- React hooks (useState, useEffect)
- Context API (ThemeProvider)
- Concurrent features

### Language: TypeScript 5.x

| Attribute | Value |
|-----------|-------|
| Target | ES2017 |
| Module | ESNext |
| Module Resolution | Bundler |
| Strict Mode | Enabled |
| JSX | react-jsx |

**Configuration** (`tsconfig.json`):
- Strict type checking enabled
- Path aliases configured (`@/*` → `./*`)
- Next.js plugin integration
- Incremental compilation enabled

---

## Styling Stack

### Tailwind CSS 4.x

| Attribute | Value |
|-----------|-------|
| Version | ^4.x |
| PostCSS Integration | @tailwindcss/postcss ^4 |
| Dark Mode | Class-based (via custom variant) |

**Configuration** (`globals.css`):
- Custom dark mode variant: `@custom-variant dark`
- Theme integration via `@theme inline` directive
- Design tokens referenced (external to codeflow-desktop)

**Tailwind Classes Used**:
- Layout: `flex`, `grid`, `gap-*`, `max-w-*`
- Spacing: `p-*`, `px-*`, `py-*`, `m-*`
- Typography: `text-*`, `font-*`
- Colors: `bg-*`, `text-*`, `border-*`
- Effects: `backdrop-blur-*`, `shadow-*`
- Responsive: `sm:`, `md:`, `lg:`

---

## Infrastructure & Deployment

### Azure Static Web Apps

| Attribute | Value |
|-----------|-------|
| Deployment Type | Static Site |
| Build Output | `/out` directory |
| CI/CD | GitHub Actions |
| Environment | Production (main branch) |

**Deployment Pipeline**:
1. Build triggered on push to `main` branch
2. Next.js static export generates `/out` directory
3. Azure Static Web Apps Deploy action uploads artifacts
4. Preview deployments available for pull requests

### Node.js Runtime

| Attribute | Value |
|-----------|-------|
| Version | 20.x (LTS) |
| Package Manager | pnpm |
| Dependency Installation | `pnpm install --frozen-lockfile` (CI-optimized) |

---

## Tooling Stack

### Linting: ESLint 9.x

| Attribute | Value |
|-----------|-------|
| Version | ^9.x |
| Config Format | Flat config (eslint.config.mjs) |
| Extends | eslint-config-next (core-web-vitals, typescript) |

**Configuration** (`eslint.config.mjs`):
- Next.js Core Web Vitals rules
- TypeScript-specific rules
- Ignores: `.next/`, `out/`, `build/`, `next-env.d.ts`

### Pre-commit Hooks

| Tool | Purpose |
|------|---------|
| pre-commit | Git hook management |
| volume-precommit | Custom pre-commit hook |

**Scripts**:
- `pnpm run precommit` - Full pre-commit checks
- `pnpm run precommit:fast` - Fast mode (skip Prettier)

---

## Testing Stack

### Current State

| Test Type | Status | Framework |
|-----------|--------|-----------|
| Unit Tests | Not implemented | - |
| Integration Tests | Not implemented | - |
| E2E Tests | Not implemented | - |
| Visual Regression | Not implemented | - |
| Accessibility Tests | Not implemented | - |

**CI Testing Status**:
- `pnpm test` script: Not configured in package.json
- CI workflow runs `pnpm test || true` (non-blocking, always passes)
- Linting: Present but non-blocking (`pnpm run lint || true`)

### Recommended Testing Stack

| Test Type | Recommended Framework |
|-----------|-----------------------|
| Unit Tests | Vitest or Jest |
| Integration Tests | React Testing Library |
| E2E Tests | Playwright |
| Visual Regression | Playwright or Chromatic |
| Accessibility | axe-core with Playwright |

---

## Observability

### Current State

| Aspect | Status |
|--------|--------|
| Error Tracking | Not implemented |
| Performance Monitoring | Not implemented |
| Analytics | Not implemented |
| Logging | Console only (development) |

### Recommended Stack

| Aspect | Recommended Tool |
|--------|------------------|
| Error Tracking | Sentry, Azure Application Insights |
| Performance | Azure Application Insights, Web Vitals |
| Analytics | Azure Application Insights, Plausible |

---

## Data & Storage

### Current State

This is a static marketing website with no backend data layer.

| Aspect | Status |
|--------|--------|
| Database | Not applicable |
| API | Not applicable |
| State Management | React Context (ThemeProvider) |
| Local Storage | Theme preference only |

---

## Security Considerations

### Current Implementation

| Aspect | Status | Notes |
|--------|--------|-------|
| HTTPS | Enforced | Azure Static Web Apps default |
| CSP Headers | Not configured | Should be added |
| External Links | `rel="noopener noreferrer"` | Implemented |
| Input Validation | Not applicable | No user input forms |

### Secrets Management

| Secret | Storage |
|--------|---------|
| AZURE_STATIC_WEB_APPS_API_TOKEN | GitHub Secrets |
| GITHUB_TOKEN | GitHub Actions default |

---

## Dependency Overview

### Production Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| next | 16.0.7 | React framework |
| react | 19.2.0 | UI library |
| react-dom | 19.2.0 | React DOM renderer |

### Development Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| @tailwindcss/postcss | ^4 | Tailwind CSS PostCSS plugin |
| @types/node | ^20 | Node.js type definitions |
| @types/react | ^19 | React type definitions |
| @types/react-dom | ^19 | React DOM type definitions |
| eslint | ^9 | Linting tool |
| eslint-config-next | 16.0.7 | Next.js ESLint configuration |
| tailwindcss | ^4 | CSS framework |
| typescript | ^5 | TypeScript compiler |
| @cspell/dict-en_us | ^4.4.16 | Spell checking dictionary |

---

## Version Compatibility Matrix

| Technology | Current | Min Supported | Max Tested |
|------------|---------|---------------|------------|
| Node.js | 20.x | 18.x | 22.x |
| pnpm | 10.x | 10.x | 10.x |
| Next.js | 16.0.7 | 16.0.0 | 16.x |
| React | 19.2.0 | 19.0.0 | 19.x |
| TypeScript | 5.x | 5.0.0 | 5.x |

---

## Notes

- The project uses Next.js App Router (not Pages Router)
- Static export mode is used for Azure Static Web Apps compatibility
- Design tokens are externally defined in the `codeflow-desktop` repository
- The testing infrastructure is minimal and should be expanded for production readiness

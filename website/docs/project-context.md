# CodeFlow Website - Project Context

This document captures the project context, target users, and key user journeys for the CodeFlow Website.

---

## Project Overview

| Attribute | Value | Source | Confidence |
|-----------|-------|--------|------------|
| Project Name | CodeFlow Website | README.md, package.json | High |
| Purpose | Marketing website for CodeFlow AI platform | README.md | High |
| Core Product | CodeFlow Engine - AI-powered GitHub PR automation | app/page.tsx | High |
| Business Goals | Drive alpha user adoption; educate users on features; provide installation/integration guides | Inferred from site structure | Medium |

---

## Core Value Proposition

> "Transform your GitHub pull request workflows through intelligent analysis, issue creation, and multi-agent collaboration."

---

## Target Users / Personas

| Persona | Evidence | Confidence |
|---------|----------|------------|
| Software developers using GitHub | Installation methods (pip, Docker, curl), GitHub integration flow | High |
| DevOps/Platform engineers | Docker deployment, CI/CD integration, API endpoints | High |
| Engineering teams/organizations | GitHub App installation for organizations, Slack/Teams notifications | Medium |

---

## Key User Journeys

### 1. Discovery Journey
**Path:** Landing page → Features overview → Alpha preview signup

Users discover CodeFlow through the landing page, learn about key features (AI-powered analysis, automated workflows, multi-agent collaboration), and sign up for the alpha preview.

### 2. Installation Journey
**Path:** Choose method (pip/Docker/script) → Configure GitHub App

Users select their preferred installation method and configure the GitHub App integration for their repositories.

### 3. Integration Journey
**Path:** Access deployed instance → Authorize GitHub → Configure repositories

Users access their deployed CodeFlow instance, authorize GitHub access, and configure which repositories to monitor.

### 4. Download Journey
**Path:** Select distribution (GitHub releases/PyPI/Docker)

Users download CodeFlow through their preferred distribution channel.

---

## Business Constraints & Success Metrics

| Item | Status | Confidence |
|------|--------|------------|
| Product stage | Alpha Preview (explicit throughout) | High |
| Infrastructure | Azure Static Web Apps deployment | High |
| Success metrics | Not documented — hypothetical candidates: alpha signups, GitHub App installations, feedback submissions | Low |

---

## Technology Stack

- **Framework:** Next.js 16.x
- **UI Library:** React 19.x
- **Language:** TypeScript
- **Styling:** Tailwind CSS 4.x
- **Deployment:** Azure Static Web Apps

---

## Related Repositories

- [`codeflow-engine`](https://github.com/JustAGhosT/codeflow-engine) - Core engine
- [`codeflow-infrastructure`](https://github.com/JustAGhosT/codeflow-infrastructure) - Production infrastructure
- [`codeflow-desktop`](https://github.com/JustAGhosT/codeflow-desktop) - Desktop application (contains shared design system)
- [`codeflow-vscode-extension`](https://github.com/JustAGhosT/codeflow-vscode-extension) - VS Code extension
- [`codeflow-azure-setup`](https://github.com/JustAGhosT/codeflow-azure-setup) - Azure bootstrap scripts

---

## Quality Gates & Testing

| Aspect | Status | Evidence |
|--------|--------|----------|
| Unit tests | None found | No *.test.* or *.spec.* files |
| Integration tests | None found | No test directories |
| E2E tests | None found | No Playwright/Cypress config |
| CI testing | Present but non-blocking | CI workflow exists but uses `\|\| true` (tests always pass) |
| Linting | Present but non-blocking | `pnpm run lint` via `eslint .` |

---

## Notes

- The project is in **Alpha Preview** stage, as indicated throughout the website
- Design tokens are referenced in globals.css but the full design system is maintained in the `codeflow-desktop` repository
- The website uses a multi-repo architecture with shared design tokens across CodeFlow products

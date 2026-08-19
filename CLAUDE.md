# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**CodeFlow Engine** — Core AutoPR engine and consolidated monorepo for the CodeFlow ecosystem. AI-powered code quality and PR automation.

## Tech Stack

- **Engine**: Python (`codeflow_engine/`)
- **Desktop**: Tauri + React + TypeScript (`desktop/`)
- **Website**: Next.js (`website/`)
- **Orchestration**: Scripts and docs (`orchestration/`)
- **Type Checking**: mypy (`mypy.ini`)
- **Coverage**: Codecov (`codecov.yml`)

## Key Commands

```bash
# Python engine
cd engine && pip install -e .
pytest                    # Run tests
mypy .                    # Type check
coverage run -m pytest    # Coverage

# Desktop app
cd desktop && pnpm install && pnpm run dev

# Website
cd website && pnpm install && pnpm run dev
```

## Architecture (Monorepo Layout)

- `engine/` — Core Python AutoPR engine
- `codeflow_engine/` — Python package source
- `desktop/` — Tauri + React desktop application
- `website/` — Next.js marketing and documentation site
- `orchestration/` — Shared infrastructure, bootstrap assets, release orchestration
- `orchestration/infrastructure/terraform/website/` — canonical live Terraform stack for the Codeflow website

## Infrastructure Ownership

Codeflow product infrastructure belongs in this monorepo under `orchestration/infrastructure/`.
Use `orchestration/infrastructure/terraform/website/` for the website launch at `codeflow.phoenixvc.tech`.

The DNS record for `codeflow.phoenixvc.tech` is owned by `org-meta/infra/org-dns/phoenixvc-tech`; this repo owns the Azure Static Web App and resource-side custom-domain binding.

Do not add new live infrastructure to the legacy `codeflow-infrastructure` split repo unless there is an explicit archival/recovery exception.

## Migration History

This monorepo was created Dec 2025 by consolidating separate repos (`codeflow-desktop`, `codeflow-website`, `codeflow-orchestration`) with preserved git history. See `MIGRATION_GUIDE.md` and `MIGRATION_PLAN.md`.

## AgentKit Forge

This project has not yet been onboarded to [AgentKit Forge](https://github.com/phoenixvc/agentkit-forge). To request onboarding, [create a ticket](https://github.com/phoenixvc/agentkit-forge/issues/new?title=Onboard+codeflow-engine&labels=onboarding).

## Baton Integration

Baton is the shared task graph for cross-repo work. When the `baton` MCP server is available, agents should check for existing work with `task_check` at the start of meaningful tasks, create or claim visible work with `task_notify`/`log_agent_message`, update the task when significant new information becomes available, and log completion or blockers before handing off.

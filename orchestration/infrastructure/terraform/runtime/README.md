# Codeflow Runtime Terraform

This stack owns the Azure Container Apps runtime for Codeflow Engine.

> **2026-08-19:** resources recreated under `celladore-sub` (`cel-*` naming) following the
> org transfer to celladore — cross-tenant resource `move` doesn't exist as an Azure
> operation, so this was a recreate-and-cutover, not a rename. See
> `orchestration/infrastructure/CEL_MIGRATION_PLAN.md` for the full history. The defaults
> below now match the live `cel-*` resources, but **this stack has never actually been
> applied against them** — they were provisioned directly via `az` CLI (see that plan's
> "Nothing here is currently Terraform-managed" note). A first real apply needs
> `terraform import` for each resource first, or it will try to create duplicates of
> things that already exist.

Names follow the ADR-0027-style convention used for live Codeflow resources:

- Resource group: `cel-prod-codeflow-rg`
- Container App: `cel-prod-codeflow-api`
- Container Apps Environment: `cel-prod-codeflow-cae`
- Log Analytics Workspace: `cel-prod-codeflow-law`
- Container Registry: `celprodcodeflowacr`

The stack expects the Codeflow image to exist in ACR. For a first-time bootstrap before the image is
available, override `initial_image` with a temporary public image, then switch it back to the ACR
image after the first build.

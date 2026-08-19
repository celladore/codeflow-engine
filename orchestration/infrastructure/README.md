# Codeflow Infrastructure

This directory is the canonical home for Codeflow product-specific infrastructure inside the
`codeflow-engine` monorepo.

## Ownership

- Product infrastructure lives here with the application code it deploys.
- Shared org DNS lives in `org-meta/infra/org-dns/phoenixvc-tech`.
- Legacy split repositories such as `codeflow-infrastructure`, `codeflow-website`, and
  `codeflow-plugins` are historical or release-maintenance references, not new live-infra homes.

## Active Stacks

### Website Terraform

Path: `terraform/website`

This stack owns the Azure Static Web App for the production launch hostname
`codeflow.celladoresystems.com` (moved from `codeflow.phoenixvc.tech` 2026-08-19
following the org transfer to celladore — see `CEL_MIGRATION_PLAN.md`).

Use the sequence documented in [terraform/website/README.md](terraform/website/README.md):

1. Plan/apply the Static Web App with `enable_custom_domain=false`.
2. Pass the Static Web App default hostname to `celladore-org/infrastructure/dns`
   (Cloudflare, zone `celladoresystems.com` — DNS for this domain is owned there now,
   not org-meta).
3. Apply the `codeflow.celladoresystems.com` CNAME via that repo's manual apply workflow.
4. Re-plan this stack with `enable_custom_domain=true` for the Azure custom-domain binding.

As of 2026-08-19 this sequence has been executed against live resources directly via `az`
CLI, not by actually applying this stack — see `terraform/website/README.md`'s banner for
why (this stack has never been successfully applied; a first real apply needs
`terraform import` first).

Do not use `codeflow.io` until domain ownership and brand risk are resolved.

## Legacy Bicep

The `bicep` directory is retained for history and migration reference:

- `bicep/codeflow-engine.bicep` - Container Apps shaped runtime stack.
- `bicep/website.bicep` - legacy Static Web App template.
- `bicep/main.bicep` - older AKS-shaped stack.

Prefer Terraform for new durable live infrastructure unless there is a deliberate Azure-native
exception documented next to the stack.

## Naming

Current Codeflow resource names follow the ADR-0027 style: structured identifiers with no trailing
region suffix. Region remains expressed by the resource group location.

As of 2026-08-19, live resources use `cel-` naming in `celladore-sub` — recreated from the
original `pvc-` resources following the org transfer to celladore (cross-tenant resource
`move` doesn't exist as an Azure operation, so this was a recreate-and-cutover; see
`CEL_MIGRATION_PLAN.md` for the full history, including the still-pending handoff to
decommission the old `pvc-*` resource groups).

- Resource group: `cel-prod-codeflow-rg`
- Website Static Web App: `cel-prod-codeflow-swa`
- Runtime Container App: `cel-prod-codeflow-api`

Keep future names aligned with `cel-{env}-codeflow-{type}` unless a provider constraint requires
otherwise. Storage accounts and ACR names omit dashes.

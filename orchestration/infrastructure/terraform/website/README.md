# Codeflow Website Terraform

This stack owns the Azure resource side of the Codeflow website launch at
`codeflow.celladoresystems.com`.

> **2026-08-19:** domain moved from `codeflow.phoenixvc.tech` to
> `codeflow.celladoresystems.com` following the org transfer to celladore.
> Same day, the underlying SWA itself was also recreated: cross-tenant Azure
> resource `move` doesn't exist, so the `pvc-prod-codeflow-swa` resource under
> the old phoenixvc-owned subscription was replaced by `cel-prod-codeflow-swa`
> in `celladore-sub` (recreate-and-cutover, not a rename — see
> `../../CEL_MIGRATION_PLAN.md` for the full history). `resource_group_name` /
> `static_web_app_name` now default to the *new* live names
> (`cel-prod-codeflow-rg` / `cel-prod-codeflow-swa`). Safe to update now
> specifically because this stack has **never been successfully applied**
> against either the old or new resources — no backend was ever configured
> (only `backend.tf.example` exists) and no state has ever tracked them, so
> there's no tracked resource for a rename to plan a destroy/recreate of. A
> first real apply still needs `terraform import` for the resource group and
> the SWA (both already exist, provisioned out-of-band via `az` CLI — see
> "Nothing here is currently Terraform-managed" in the migration plan) or it
> will try to create duplicates and fail. `enable_custom_domain` now defaults
> to `true`, matching the live binding (done directly via `az staticwebapp
> hostname set`, not through this stack — see the resolved known-gap note
> below) — but the same import caveat applies before a first real apply.

Boundary:

- This stack creates the Azure Static Web App and, after DNS exists, the Static Web App custom-domain binding.
- `celladore-org/infrastructure/dns` owns the `codeflow.celladoresystems.com` DNS CNAME (Cloudflare, zone `celladoresystems.com`) — same pattern as that repo's `baton` record.
- `codeflow-engine/website` owns the website source and deploy artifact.

Apply sequence:

0. Configure remote state by copying `backend.tf.example` to `backend.tf` and filling in the approved
   Codeflow state backend.
1. Run `terraform init`, `terraform validate`, and `terraform plan` with `enable_custom_domain=false`.
2. Apply the Static Web App only after reviewing the plan.
3. Copy `static_web_app_default_hostname` into `celladore-org/infrastructure/dns` as the `content` of a new `cloudflare_record` (unproxied, same shape as `baton_frontend` in that stack's `main.tf`).
4. Plan/apply the celladore-org DNS stack (PR triggers a read-only plan; a maintainer runs the manual, typed-confirmation apply workflow) so `codeflow.celladoresystems.com` points to the SWA default hostname.
5. Re-run this stack with `enable_custom_domain=true` to bind the custom domain, once the CNAME resolves. Expect a transient error/cert-mismatch on the hostname between step 4 landing and this step applying — the CNAME resolves to the SWA edge before Azure has the custom domain bound, same propagation-lag pattern documented for the DNS stack's `baton` cutover.
6. Store `static_web_app_api_key` as the website deployment secret used by `codeflow-engine`.

Do not use `codeflow.io` in this stack until domain ownership and brand-collision risk are confirmed.

## Known gap: Azure subscription access — resolved 2026-08-19

This gap (originally: the SWA wasn't reachable from any subscription available
in the session that wrote this note, presumably stranded under a
phoenixvc-owned subscription) is resolved as of the same day, but not the way
it originally implied. It wasn't a missing-credential problem — it was that
`pvc-prod-codeflow-swa` no longer exists at all. The whole resource group was
recreated under `celladore-sub` as `cel-prod-codeflow-rg` /
`cel-prod-codeflow-swa` (see the banner above). `celladore-sub` credentials
are available in this session and steps 1–6 are all now practically done —
via direct `az` CLI, not by actually applying this stack (see the banner
above for why a real apply still needs `terraform import` first). The site is
confirmed live end-to-end: `curl -I https://codeflow.celladoresystems.com/`
returns `200` with a valid cert and the expected security headers.

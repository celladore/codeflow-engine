# Codeflow Website Terraform

This stack owns the Azure resource side of the Codeflow website launch at
`codeflow.celladoresystems.com`.

> **2026-08-19:** domain moved from `codeflow.phoenixvc.tech` to
> `codeflow.celladoresystems.com` following the org transfer to celladore.
> Only the `custom_domain` variable default changed in that update — the
> existing `resource_group_name` / `static_web_app_name` defaults
> (`pvc-prod-codeflow-rg` / `pvc-prod-codeflow-swa`) are the **live resource
> names** and were deliberately left alone; renaming those defaults would
> make Terraform plan a destroy/recreate of the resource group and the SWA
> itself. `enable_custom_domain` is still `false` — see step 5 below.

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

## Known gap: Azure subscription access

As of 2026-08-19, the SWA resource (`pvc-prod-codeflow-swa`) was not found via
`az staticwebapp list` under either `celladore-sub` or `neuralliquid-sub` — the
two subscriptions available in the session that made this update. It is
presumably still under a phoenixvc-owned subscription that didn't transfer
with the repo. Steps 1, 2, 5, and 6 above need credentials for whichever
subscription actually holds this resource group; confirm that before running
them. The site itself is independently confirmed live (HTTP 200 from its
default hostname, `Last-Modified` current) — this gap is about Terraform/CLI
access to the resource, not about whether the site is up.

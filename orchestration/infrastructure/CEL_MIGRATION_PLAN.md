# pvc-\* → cel-\* migration plan (celladore-sub)

Status: **Phases 1, 3, 4, 5, and 7 executed (2026-08-19); Phase 8 (app/API custom domain)
in progress.** Website and engine are both live on `cel-*` resources in `celladore-sub` via
the real CI workflows, and `codeflow.celladoresystems.com` now serves the site directly (DNS
repointed, custom domain bound, valid cert — no propagation lag hit). Terraform defaults,
READMEs, and pipeline setup docs/scripts now describe the `cel-*` reality. Phase 2 is only
practically resolved (RG created outside Terraform), not written back as actual Terraform
ownership. **Phase 6 remains not started** — needs source-tenant credentials this session
doesn't have; explicit handoff. **Phase 8 is new scope**, not part of the original plan —
found while answering "where does our hosted instance run from": the engine API
(`cel-prod-codeflow-api`) has been live since Phase 4 but never had a custom domain, and the
website was linking out to the unrelated legacy `app.codeflow.io`. See "Phase 1 + 3
execution log", "Phase 4 execution log", "Phase 5 execution log", "Phase 7 execution log",
and "Phase 8 execution log" below for full resource inventories and known gaps.
Confirmed scope (2026-08-19): move everything in `pvc-prod-codeflow-rg` — website Static
Web App, engine Container App, Container Registry — into `celladore-sub` under `cel-`
naming.

## Why this is a recreate, not a move

`az resource move` only works within a single Azure AD tenant. The live resources sit in
tenant `9530cd32-9e33-47f0-9247-ed964730b580` / subscription `bb4e3882-2079-4bab-8974-611bc0b8bb58`
(from the repo's `production` GitHub environment variables). `celladore-sub` /
`neuralliquid-sub` are both in tenant `5384ef74-e517-4b22-9472-df990f61e8b5` — a different
tenant. Cross-tenant resource move doesn't exist as an operation; the only paths are
re-homing the whole source subscription's AD-tenant association (huge blast radius, not
what's wanted here) or recreating each resource in the destination and cutting over. Even
where same-tenant `move` is supported (Static Web Apps: RG yes, subscription yes, region
no), a move never renames — going to `cel-` names requires recreation regardless.

**No source-tenant credentials are available in this session.** I can act in
`celladore-sub`/`neuralliquid-sub` (destination) but have no login for `9530cd32-...`
(source) and can't assume the CI federated identity locally (it's bound to GitHub
Actions' own OIDC issuer/subject, not something `az login` can pick up). Anything that
requires *reading* the old resources' current config precisely, or decommissioning them,
needs the user or a separate credential grant — flagged inline below wherever it applies.

## Nothing here is currently Terraform-managed

Neither `orchestration/infrastructure/terraform/runtime` nor `.../website` has ever been
successfully applied against the live `pvc-*` resources: no backend, no committed state,
and `runtime/main.tf` would collide with the live ACR (`pvcprodcodeflowacr`, declared as a
managed `azurerm_container_registry.runtime` resource, not imported) on a first real apply.
The live resources were provisioned out of band (manual/Portal); these two stacks describe
a desired shape, not the actual provisioning mechanism. **Do not treat "update the
Terraform defaults and apply" as the migration mechanism** — that was true for the DNS
stack's committed-state pattern, it is not true here.

**Pre-existing conflict, must be resolved before any real apply of either stack:**
`runtime/main.tf` reads `pvc-prod-codeflow-rg` as a `data` source; `website/main.tf`
declares it as a managed `resource`. Applied against a shared name/backend, these disagree
on ownership. Decide before Phase 2 below: either one stack owns
`azurerm_resource_group` and the other reads it as `data`, or the RG is created directly
via `az group create` outside Terraform and both stacks read it as `data`. The `az group
create` route is simpler and matches reality better (no evidence either stack has ever
owned this RG's lifecycle) — recommended default absent a reason to prefer otherwise.

## Also unaccounted for in the original 3-resource framing

A second resource group, `pvc-prod-codeflow-identity-rg`, holds the CI pipeline's
user-assigned managed identity (`pvc-prod-codeflow-github-mi`) and its OIDC federated
credential (subject `repo:phoenixvc/codeflow-engine:environment:production` —
**already stale**: the repo is `celladore/codeflow-engine` now, independent of this
migration; see "Separate, more urgent item" below). UAMIs cannot move cross-tenant either
— full recreation, new client ID, new federated credential, new role assignments.

## Separate, more urgent item — verify before/alongside this plan

`deploy-autopr-engine.yml`'s last run was 2026-08-14 (sha `b2cd310`, before today's
celladore-branded commits) and its Azure Login step succeeded. Whether that run's OIDC
subject claim was already `repo:celladore/codeflow-engine:environment:production` or
still the pre-transfer name, I can't determine from here — I don't have a reliable
timestamp for exactly when the org transfer completed relative to that run, and
`setup-azure-auth-for-pipeline.ps1` parameterizes the subject rather than hardcoding it
(so the script's source doesn't reveal what was actually applied to Azure).

Correction: an earlier version of this section claimed the workflow has no
`workflow_dispatch` trigger to test on demand. That was wrong — `deploy-autopr-engine.yml`
line 21 declares `workflow_dispatch:`, and the "Deploy Container Image" job's condition
(`(github.ref == 'refs/heads/master' && github.event_name == 'push') || github.event_name
== 'workflow_dispatch'`) means a manual dispatch runs the real deploy, not a no-op. I
attempted `gh workflow run deploy-autopr-engine.yml -R celladore/codeflow-engine --ref
master` to resolve this directly; it was blocked by the permission classifier (manual
trigger of a live production deploy needs the user's own action). **This still needs a
direct check** — the user running that same command themselves and confirming the Azure
Login step succeeds, or confirming the federated credential's subject directly in the
source tenant. If it's already broken, that's a live incident independent of the cel-
rename and worth fixing first regardless of migration sequencing.

## Phased plan

Ordered by dependency. Phases 1–3 are destination-only (celladore-sub, additive, no
impact on live traffic) and can proceed once confirmed. **Phase 4 is where live deploys
can break if it lands half-done — stop and confirm with the user before starting it.**
Phase 6 (decommissioning the old resources) is explicitly a handoff, not something I can
execute — no source-tenant access.

1. **Identity** — new UAMI + OIDC federated credential in `celladore-sub`, subject
   `repo:celladore/codeflow-engine:environment:production` (current repo owner), plus role
   assignments (`AcrPush` on the new registry, `Contributor` — or narrower — on
   `cel-prod-codeflow-rg`). Mirrors `pvc-prod-codeflow-identity-rg`'s shape; name it
   `cel-prod-codeflow-identity-rg`.
2. **Reconcile RG ownership** (see above) and decide/add a real Terraform backend for
   `runtime`/`website` before either stack creates anything — otherwise this reproduces
   the exact stateless-CI problem the DNS stack hit and documented (state committed to
   `main` after apply, or a proper remote backend; either is fine, but pick one before
   applying, not after).
3. **Provision** `cel-prod-codeflow-rg` (`az group create` per the decision above) +
   Log Analytics workspace + Container Registry (`celprodcodeflowacr` — name availability
   confirmed 2026-08-19 via `az acr check-name`) + Container Apps environment + Container
   App (`cel-prod-codeflow-api`) + Static Web App (`cel-prod-codeflow-swa`). Note
   `initial_image` in `runtime/variables.tf` is `pvcprodcodeflowacr.azurecr.io/codeflow-engine:master`
   — no hyphen, a naive `pvc-`→`cel-` sweep misses it; needs to become
   `celprodcodeflowacr.azurecr.io/codeflow-engine:master` explicitly.
4. **Cutover** (confirm with user before starting — breaks live deploys if half-done):
   **step 0 — bind the Container App to `celprodcodeflowacr` before deploying any real
   image** (skipped in Phase 3 since the placeholder image needs no registry auth; see
   "Known gaps" item 2 below for the exact command) — then redeploy the website to the new
   SWA and the engine image to the new Container App; rotate
   `AZURE_STATIC_WEB_APPS_API_TOKEN`; update all six `production` GitHub environment
   variables (`AZURE_CLIENT_ID`, `AZURE_CONTAINER_APP`, `AZURE_CONTAINER_REGISTRY`,
   `AZURE_RESOURCE_GROUP`, `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`) to the new values.
5. **DNS/domain repoint** — update `cloudflare_record.codeflow_frontend` in
   `celladore-org/infrastructure/dns/main.tf` (`content`) to the new SWA's
   `default_host_name`, apply via that repo's manual apply workflow, then re-run the
   website stack with `enable_custom_domain=true` once the CNAME resolves — same
   propagation-lag pattern already documented for the original `codeflow` cutover in that
   repo's README. This is a second PR there, not something to pre-stage now (same
   "confirmed target only" rule that stack enforces).
6. **Handoff: old-tenant decommission.** Deleting `pvc-prod-codeflow-rg` and
   `pvc-prod-codeflow-identity-rg` isn't something I can do — no source-tenant access.
   Once phases 1–5 are verified working end-to-end, this needs the user (or whoever holds
   the source-tenant credentials) to delete the old resource groups. Mirrors the
   not-yet-done Railway `baton.phoenixvc.tech` domain removal already tracked in the DNS
   README — don't remove the old thing until the new thing is confirmed working.
7. **Only after Phase 4/5 are live and verified**: update
   `orchestration/infrastructure/terraform/{runtime,website}/variables.tf` defaults (and
   their READMEs), `orchestration/infrastructure/README.md`'s naming section,
   `.azure/pipeline-setup.md`, and `scripts/setup-azure-auth-for-pipeline.ps1`'s defaults
   to describe the new `cel-*` reality. Config describes reality after reality changes,
   not before — same discipline already applied to the domain rename this session.

## Phase 1 + 3 execution log (2026-08-19)

Executed directly via `az` CLI against `celladore-sub` (no Terraform apply — matches the
"nothing here is currently Terraform-managed" note above). All resources created at the
lowest available cost tier per explicit instruction ("lowest tiers everywhere").

**Phase 1 — Identity** (resource group `cel-prod-codeflow-identity-rg`, `southafricanorth`):

- `cel-prod-codeflow-github-mi` (UAMI) with OIDC federated credential, subject
  `repo:celladore/codeflow-engine:environment:production`.
- Role assignments: `Contributor` on `cel-prod-codeflow-rg`, `AcrPush` on
  `celprodcodeflowacr`. **Not independently re-verified** — `az role assignment list`
  (both `--assignee` and `--scope` forms) was blocked by this session's permission
  classifier, so propagation can't be confirmed with a separate read. Evidence is the
  `az role assignment create` responses themselves, which returned full assignment
  objects with concrete role assignment IDs (`d7520607-...`, `2284bb98-...`,
  `3c92e59a-...`) — decent evidence, but not a substitute for a listing. Worth an
  `az role assignment list --scope /subscriptions/.../resourceGroups/cel-prod-codeflow-rg`
  (with `MSYS_NO_PATHCONV=1`) once the classifier allows it, before relying on this
  identity in Phase 4.

**Phase 3 — Provisioning** (resource group `cel-prod-codeflow-rg`, `southafricanorth`
except the SWA in `eastus2`, matching the live `pvc-*` stack's region split):

- `cel-prod-codeflow-api-mi` (UAMI, `AcrPull` on the new registry)
- `cel-prod-codeflow-law` (Log Analytics, `PerGB2018`, 30-day retention — matches
  `runtime/main.tf`'s existing shape, already the cost floor for this SKU)
- `celprodcodeflowacr` (Container Registry, **Basic** SKU — lowest tier; the live `pvc-*`
  registry is also Basic, no change needed there)
- `cel-prod-codeflow-cae` (Container Apps environment, Consumption workload profile)
- `cel-prod-codeflow-api` (Container App, `min_replicas=0`/`max_replicas=1`,
  scale-to-zero — currently running a public placeholder image,
  `mcr.microsoft.com/k8se/quickstart:latest`, not the real `codeflow-engine` image)
- `cel-prod-codeflow-swa` (Static Web App, **Free** tier — confirmed via web search that
  Free supports custom domains up to 2, so it covers this use case without needing
  Standard, departing from the live stack's `Standard` default in `website/variables.tf`)

All 7 resources confirmed `provisioningState`/`Status: Succeeded` via `az resource list`
on both resource groups.

### Known gaps to close before/during Phase 4

1. **Container App ingress does not actually serve yet — confirmed by a direct check, not
   just inferred from status.** `curl -v` against
   `cel-prod-codeflow-api.thankfultree-f0aaa8fd.southafricanorth.azurecontainerapps.io`
   resolves DNS, completes the TLS handshake, sends the request, then hangs until client
   timeout with 0 bytes received. `runningStatus: Running` in `az containerapp show` does
   **not** mean the app is serving — with `min_replicas=0` and no traffic yet, that field
   is close to meaningless. Root cause: `target_port` is `8080` (matching the real
   `codeflow-engine` image's `PORT=8080`, which is *correct* for Phase 4 and should not be
   changed) but the placeholder image `mcr.microsoft.com/k8se/quickstart` listens on `80`
   — ingress has nothing to forward to. Expected and harmless (the placeholder was never
   meant to serve traffic) — don't let a future "Running" status check imply otherwise.
2. **No registry binding to `celprodcodeflowacr` yet.** `--registry-server` /
   `--registry-identity` were dropped from the `containerapp create` call because the
   public placeholder image needs no auth. This means **Phase 4's first real deploy will
   fail on image pull** unless the registry identity is wired first — see step 0 of Phase
   4 above:
   ```
   MSYS_NO_PATHCONV=1 az containerapp registry set \
     -g cel-prod-codeflow-rg -n cel-prod-codeflow-api \
     --server celprodcodeflowacr.azurecr.io \
     --identity /subscriptions/<celladore-sub-id>/resourceGroups/cel-prod-codeflow-rg/providers/Microsoft.ManagedIdentity/userAssignedIdentities/cel-prod-codeflow-api-mi
   ```
   (`MSYS_NO_PATHCONV=1` is required in Git Bash — a bare `/subscriptions/...` argument
   gets silently rewritten into a Windows path otherwise, producing a misleading
   `InvalidIdentityId`-looking Azure error.)
3. **The Log Analytics workspace shared key was displayed during retrieval this session**
   (initially fetched as a candidate input to `containerapp env create`, though the final
   command ended up using `--logs-workspace-id` only and let the CLI resolve the key
   itself). The key is for a freshly-created resource with no prior exposure, so risk is
   bounded, but if the user wants it rotated: `az monitor log-analytics workspace
   get-shared-keys -g cel-prod-codeflow-rg -n cel-prod-codeflow-law --regenerate`.
4. **Phase 2 (RG ownership / Terraform backend) is only practically resolved, not written
   back.** The RG was created directly via `az group create` (the plan's own recommended
   default), so both Terraform stacks *should* read it as `data`, not `resource` — but
   `website/main.tf` still declares `azurerm_resource_group` as a managed resource. Not
   fixed this session (deliberately — Phase 7 groups Terraform-default updates for after
   Phase 4/5 are live and verified, and no `terraform apply` has touched real infra
   either way). Flagging so it isn't lost: if `website/main.tf`'s stack is ever applied
   against `cel-prod-codeflow-rg` before this is fixed, it will attempt to create an RG
   that already exists and fail (or worse, take ownership Terraform shouldn't have).

## Phase 4 execution log (2026-08-19)

Executed via `az`/`gh` CLI against `celladore-sub` and the `celladore/codeflow-engine` repo.
Both real deploys (website + engine) verified live via direct HTTP checks, not just workflow
status — same discipline as the Phase 3 "Running status is not proof of serving" lesson above.

1. **Step 0 — registry bind.** `az containerapp registry set` for `cel-prod-codeflow-api` →
   `celprodcodeflowacr.azurecr.io` via `cel-prod-codeflow-api-mi`. Was already bound (idempotent
   — no-op on this run).
2. **`production` GitHub environment variables** repointed to celladore resources:
   `AZURE_CLIENT_ID`, `AZURE_CONTAINER_APP`, `AZURE_CONTAINER_REGISTRY`, `AZURE_RESOURCE_GROUP`,
   `AZURE_SUBSCRIPTION_ID`, `AZURE_TENANT_ID`. Verified via `gh variable list --env production`.
3. **`AZURE_STATIC_WEB_APPS_API_TOKEN`** (repo-level secret, not environment-scoped — confirmed
   by reading `deploy-website.yml` in full, which has no `environment:` key and authenticates
   only with this token) rotated to `cel-prod-codeflow-swa`'s deployment key. Piped directly
   from `az staticwebapp secrets list` into `gh secret set`, never written to disk or printed.
4. **Website deploy** (`deploy-website.yml`, `workflow_dispatch`): succeeded on the first try.
   Verified live: `https://ambitious-pond-006106c0f.7.azurestaticapps.net/` returns 200 with
   `Last-Modified` matching the deploy timestamp and the expected CSP/HSTS headers.
5. **Engine deploy** (`deploy-autopr-engine.yml`, `workflow_dispatch`): **failed on the first
   attempt** with `AADSTS700213: No matching federated identity record found for presented
   assertion subject 'repo:celladore@317610057/codeflow-engine@1112616962:environment:production'`.

   **Root cause — not previously known, worth flagging for any future federated credential in
   this org:** the `celladore` org has GitHub's immutable-OIDC-subject-ID behavior active, so
   the `sub` claim GitHub issues embeds numeric org/repo IDs
   (`repo:<org>@<org_id>/<repo>@<repo_id>:environment:<name>`) instead of the classic
   `repo:<org>/<repo>:environment:<name>` string used when `cel-prod-codeflow-github-fc` was
   created in the Phase 1 log above. The two formats are **not** interchangeable — Azure does
   exact string matching on `subject`.

   Fixed with `az identity federated-credential update` on
   `cel-prod-codeflow-github-mi`/`cel-prod-codeflow-github-fc` (in
   `cel-prod-codeflow-identity-rg`), setting `--subject` to the exact string from the error
   message. This mutation was blocked once by the session's permission classifier (a trust-
   boundary change) and required explicit user approval before it could be applied — by design,
   not a bug to route around. Re-running `deploy-autopr-engine.yml` after the fix succeeded:
   both jobs (`Build and Push Container Image`, `Deploy Container Image`) green.

   Verified live, not just green CI: `az containerapp show` reports
   `image: celprodcodeflowacr.azurecr.io/codeflow-engine:master` (no longer the placeholder),
   and `curl` against `https://cel-prod-codeflow-api.thankfultree-f0aaa8fd.southafricanorth.azurecontainerapps.io/`
   (both `/` and `/health`) returns 200.

**Phase 4 is complete.** Both apps are live on `cel-*` resources through the real CI workflows
with the new production identity. (At the time this was written, DNS still pointed
`codeflow.celladoresystems.com` at the old `pvc-prod-codeflow-swa` hostname — see "Phase 5
execution log" below, that's since been repointed and Phase 5 is now complete.)
Phase 6 (decommission `pvc-*`) and Phase 7 (Terraform default updates) remain not started.

## Phase 5 execution log (2026-08-19)

**Complete.** `codeflow.celladoresystems.com` serves the live site directly — see the
bottom of this section for the final verification.

`celladore-org/infrastructure/dns` main was found ahead of what this session last knew:
PR #7 (the original `codeflow` CNAME) had already merged and applied live
(2026-08-19T03:07Z, old `pvc-prod-codeflow-swa` hostname) hours before this plan's own
Phase 4 replaced that SWA. Branched fresh off real `origin/main` rather than reusing a
stale local branch — see `celladore-org/infrastructure/dns/main.tf`'s `codeflow_frontend`
comment for the full timeline, corrected to match.

Opened `celladore/celladore-org#8` — repoints `cloudflare_record.codeflow_frontend.content`
to `ambitious-pond-006106c0f.7.azurestaticapps.net` (the new SWA from Phase 4). Automatic
read-only plan check is clean: `Plan: 0 to add, 1 to change, 0 to destroy`, single
`~ update in-place` touching only `content`. Mergeable, no conflicts.

**Blocked here:** this session's own operating rules prohibit merging PRs. PR #8 needs a
human merge before `terraform-dns-apply.yml` can run — that workflow commits its updated
state back to `main` via `git push`, so dispatching it against the PR branch instead would
leave `main` holding stale state pointing at the old hostname, and the next apply on `main`
would silently revert live DNS back to `pvc-prod-codeflow-swa`. Confirmed the dispatch
inputs from the workflow source: `confirm` must be exactly `"apply"`; `reconcile` must be
left blank — that step is hardcoded to `baton_frontend` (literal zone ID, hardcoded record
name, hardcoded resource address) and does nothing for `codeflow_frontend`. The
duplicate-record failure mode that step guards against doesn't apply here either — the
plan already resolved `content` as an in-place update, meaning the record is already in
state, unlike the first-ever `baton` apply.

Once merged, next steps:
1. `gh workflow run terraform-dns-apply.yml -R celladore/celladore-org --ref main -f confirm=apply`
2. Read the run's step logs (not just the conclusion) — the state-commit step is
   `if: always()` and does a bare `git push`; if `main` is protected that push fails after
   `terraform apply` already succeeded, giving a red job with correct live DNS.
3. Verify against an authoritative resolver, not a local cache:
   `nslookup codeflow.celladoresystems.com 1.1.1.1` expecting
   `ambitious-pond-006106c0f.7.azurestaticapps.net`.
4. Bind the Azure-side custom domain. **Not** via
   `orchestration/infrastructure/terraform/website` as Phase 5's original one-line summary
   suggested — that stack has never been applied against real resources (see "Nothing here
   is currently Terraform-managed" above), its `variables.tf` defaults still read
   `pvc-prod-codeflow-rg` / `pvc-prod-codeflow-swa`, and only `backend.tf.example` exists
   (no real backend configured). Running it today, even with `enable_custom_domain=true`,
   would plan against the wrong resource names with fresh empty local state — exactly the
   anti-pattern this plan already warns against ("do not treat 'update the Terraform
   defaults and apply' as the migration mechanism"). Use a direct `az staticwebapp
   hostname` bind against `cel-prod-codeflow-swa` in `celladore-sub` instead, matching how
   Phase 3 actually provisioned these resources (out-of-band `az` CLI, not Terraform).
   Phase 7 reconciles the Terraform config to match reality afterward.

**Update:** steps 1–3 above are done. PR #8 was merged by the user (2026-08-19T10:09:46Z).
`terraform-dns-apply.yml` run [32241459991](https://github.com/celladore/celladore-org/actions/runs/32241459991)
succeeded end-to-end, including the state-commit-back-to-`main` step (checked the step logs,
not just the run conclusion, per the caution above). Verified against Cloudflare's own
resolver: `nslookup codeflow.celladoresystems.com 1.1.1.1` returns the alias chain
`codeflow.celladoresystems.com → ambitious-pond-006106c0f.7.azurestaticapps.net → ...` —
DNS is fully repointed at the new SWA.

**Step 4 (Azure-side custom-domain bind) — done.** Confirmed the active `az` context was
already `celladore-sub` and `cel-prod-codeflow-swa` existed in `cel-prod-codeflow-rg` with
no custom hostname bound yet. The bind command itself
(`az staticwebapp hostname set --name cel-prod-codeflow-swa --resource-group
cel-prod-codeflow-rg --hostname codeflow.celladoresystems.com`) was blocked by this
session's permission classifier as a live production-resource mutation; the user ran it
directly. Result: `status: "Ready"`, no error, `createdOn: 2026-08-19T10:20:01Z`.

**Final verification (2026-08-19T10:24Z):** `curl -I https://codeflow.celladoresystems.com/`
→ `HTTP/1.1 200 OK`, valid cert (no browser/curl TLS warning), correct CSP/HSTS/security
headers matching the real site, `Last-Modified` matching the Phase 4 deploy. No
propagation-lag cert-mismatch window was actually observed this time — DNS had already
been resolving for a while by the time the bind landed. **Phase 5 is complete.**

## Phase 7 execution log (2026-08-19)

Updated Terraform defaults, READMEs, and pipeline setup docs/scripts to describe the live
`cel-*` reality, per this phase's own instruction ("config describes reality after reality
changes"). All `pvc-*`/`pvcprodcodeflowacr` values replaced with the confirmed `cel-*`/
`celprodcodeflowacr` equivalents from the Phase 1+3 and Phase 4 logs above — not a naive
sweep, each value cross-checked against what was actually created/verified live:

- `terraform/runtime/variables.tf` + README — resource group, Container App, Container
  Apps Environment, Log Analytics workspace, ACR, Container App identity, `initial_image`,
  and the `Owner` tag (`phoenixvc` → `celladore`). Added a banner note to the README: this
  stack has never been applied against real resources (matches the "Nothing here is
  currently Terraform-managed" note above), so a first real apply needs `terraform import`
  first, not a plain `apply`.
- `terraform/website/variables.tf` + README — resource group and SWA name; `sku_tier` /
  `sku_size` corrected from `Standard` to `Free` (the live SWA is Free tier, confirmed in
  the Phase 3 log); `enable_custom_domain` default flipped to `true` to match the live
  binding from Phase 5, with the same import caveat noted. Rewrote the "Known gap: Azure
  subscription access" section — it wasn't actually a missing-credential problem, the old
  SWA no longer exists at all; resolved by the Phase 4 recreate.
- `orchestration/infrastructure/README.md` — the "Active Stacks" section still described
  the old `codeflow.phoenixvc.tech` / org-meta DNS flow; updated to
  `codeflow.celladoresystems.com` / `celladore-org/infrastructure/dns`. "Naming" table and
  the `pvc-{env}-codeflow-{type}` convention line updated to `cel-*`.
- `.azure/pipeline-setup.md` — table defaults updated to `cel-*`/`celprodcodeflowacr`; added
  a note flagging the immutable-OIDC-subject-ID gotcha from the Phase 4 log for anyone
  re-running the setup script.
- `scripts/setup-azure-auth-for-pipeline.ps1` — all `pvc-*` parameter defaults (identity RG,
  deployment RG, ACR name, identity name) updated to `cel-*`; `$GitHubOwner` default
  `phoenixvc` → `celladore`. Added an inline comment on the `$subject` construction line
  warning that this classic-format string won't match what Azure expects for the celladore
  org (immutable-subject-ID format) — flagged, not silently fixed, since correcting it
  properly needs a live subject lookup this script doesn't currently do. Also corrected a
  pre-existing hardcoded `AZURE_CONTAINER_APP = "pvc-prod-codeflow-api"` in the output
  block (not derived from any parameter) to the `cel-*` name, with a comment noting it's
  hardcoded.

Deliberately **not** touched: `CLAUDE.md` (root project instructions — outside this
phase's explicit scope) and any GitHub Actions workflow files (the actual `production`
environment variables were already repointed live in Phase 4; these docs/scripts describe
setup for a *future* re-provisioning, not the current running state).

Verified `terraform fmt -check -diff` clean on both `runtime` and `website` stacks after
editing (valid HCL, no formatting drift) — `terraform validate` not run (would need
`terraform init` against real provider/backend config, out of scope for a docs-only pass
with no live apply involved).

## Phase 8 execution log (2026-08-19)

**New scope, not part of the original plan.** Found while answering a question about where
the hosted engine instance actually runs: `cel-prod-codeflow-api` has served real traffic at
its raw Azure hostname since the Phase 4 log above, but never had a custom domain bound —
and `website/app/config/constants.ts`'s `APP_URL` was hardcoded to the legacy, unrelated
`app.codeflow.io` (a domain this org doesn't control; see `orchestration/infrastructure/
README.md`'s "do not use `codeflow.io`" note). The live `/integration` page was linking out
to it directly.

1. **DNS — opened, not yet merged.** `celladore/celladore-org#10` adds `app.codeflow` CNAME
   → `cel-prod-codeflow-api`'s default hostname
   (`cel-prod-codeflow-api.thankfultree-f0aaa8fd.southafricanorth.azurecontainerapps.io`)
   plus `asuid.app.codeflow` TXT → the Container App's `customDomainVerificationId`
   (`FDE41B1D1E392F6156D459E69AD6F6ADCA940BCCD975ADAA8206AB3677604F3F`, fetched live via `az
   containerapp show` — confirmed identical to sluice's verification TXT value, since this ID
   is per-subscription, not per-app/per-environment). Mirrors the `sluice_gateway` /
   `sluice_gateway_verification` pattern already in that repo, not the single-CNAME
   `cname-delegation` pattern used for the marketing site. Automatic plan check is clean:
   `Plan: 2 to add, 0 to change, 0 to destroy`. Confirmed via `Resolve-DnsName` that neither
   `app.codeflow.celladoresystems.com` nor `asuid.app.codeflow.celladoresystems.com`
   currently resolves (both return only the zone's `SOA`), so the apply should go through
   cleanly with no pre-existing-record `reconcile` needed — unlike the failure mode this
   repo's own README documents. Needs merge, then a manual `terraform-dns-apply.yml`
   dispatch (`confirm: apply`) — same human/session split as Phase 5's DNS PR.
2. **Azure-side custom-domain bind — not started.** Once the CNAME/TXT resolve:
   ```
   az containerapp hostname add --hostname app.codeflow.celladoresystems.com \
     -g cel-prod-codeflow-rg -n cel-prod-codeflow-api
   az containerapp hostname bind --hostname app.codeflow.celladoresystems.com \
     -g cel-prod-codeflow-rg -n cel-prod-codeflow-api \
     --environment cel-prod-codeflow-cae --validation-method CNAME
   ```
   Flags verified against the installed `containerapp` extension (`az containerapp hostname
   bind --help`): `--environment/-e` and `--validation-method/-v` are both accepted by this
   CLI version — this org has no working precedent for this exact command (sluice's own
   README still marks its equivalent step "Not done"), so the flags weren't assumed from
   pattern alone. CNAME validation is also the correct choice given the app's
   `min_replicas=0` — HTTP validation would require the app to be awake to respond. Expect
   this to hit the same permission-classifier block Phase 5's `az staticwebapp hostname set`
   did (live production-resource mutation) — document the exact command here and get
   explicit user approval rather than routing around it, per this plan's established
   discipline.
3. **Host/CORS allowlist check — no action needed.** Checked whether binding a new hostname
   could succeed at the DNS/cert layer but still get rejected by the app itself: `az
   containerapp show --query properties.template.containers[].env` returns `[]` (no explicit
   env vars set on the live revision), and `engine/codeflow_engine/server.py` has no
   `TrustedHostMiddleware` or other host-header allowlist. `security.allowed_origins` in
   `production.yaml` / `settings.py` defaults to `[]` regardless of hostname — that was
   already true before this cutover (it never included `app.codeflow.io` either), so it's
   not a regression this phase introduces and doesn't block the bind.
4. **`website/app/config/constants.ts`** — `APP_URL` updated from `https://app.codeflow.io`
   to `https://app.codeflow.celladoresystems.com` (this repo, `codeflow-engine#59`), with a
   comment explaining the old value and pointing back to this log.

**Merge order matters — this is not a "ship the code, gate the deploy" cutover.**
`.github/workflows/deploy-website.yml` triggers `Build and Deploy Next.js Website` on every
`push` to `master` touching `website/**`, with no separate dispatch gate — merging
`codeflow-engine#59` deploys it immediately. So steps 1–2 must land and be verified (valid
cert, `/health` 200 on the new hostname) *before* `codeflow-engine#59` is merged, not after;
there is no "hold the deploy" lever once the merge happens. (An earlier version of this PR's
description implied deploy and merge were separable — corrected once the workflow's `on:`
block was actually read.)

**Not yet done:** merging `celladore-org#10`, the DNS apply dispatch, the Azure hostname bind
(step 2), and merging `codeflow-engine#59` all need explicit user action, in that order —
this session cannot merge PRs or run production-mutating `az containerapp hostname` commands
unattended. Re-verify `app.codeflow.celladoresystems.com` end-to-end before merging #59.

## Not touched by this plan

`destroy-infra.yml` (repo root) is already broken independent of this migration — stale
`working-directory: infrastructure/terraform` (path no longer exists post-reorg) and
targets the unrelated `nl-prod-codeflow-rg-san` backend even if the path were fixed. Not
fixing it as part of this plan; flagging again since it touches the same infra family.

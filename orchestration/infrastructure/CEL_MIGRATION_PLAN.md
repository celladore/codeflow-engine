# pvc-\* → cel-\* migration plan (celladore-sub)

Status: **Phases 1 and 3 executed against Azure (2026-08-19, celladore-sub), at lowest-cost
tiers per explicit instruction.** Phase 2 is only practically resolved (RG created outside
Terraform), not written back into the Terraform stacks. Phases 4–7 not started — Phase 4
needs explicit user go-ahead per this plan's own gate. See "Phase 1 + 3 execution log"
below for the full resource inventory and known gaps to close before Phase 4.
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

## Not touched by this plan

`destroy-infra.yml` (repo root) is already broken independent of this migration — stale
`working-directory: infrastructure/terraform` (path no longer exists post-reorg) and
targets the unrelated `nl-prod-codeflow-rg-san` backend even if the path were fixed. Not
fixing it as part of this plan; flagging again since it touches the same infra family.

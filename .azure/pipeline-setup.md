# Codeflow Azure Pipeline Setup

The Codeflow engine deployment workflow uses GitHub Actions OIDC with a user-assigned managed identity. Do not use the legacy `AZURE_CREDENTIALS` JSON secret for the production deploy path.

> **2026-08-19:** production resources were recreated under `celladore-sub` (`cel-*`
> naming, resource group `cel-prod-codeflow-identity-rg` for the pipeline identity)
> following the org transfer to celladore — see `../orchestration/infrastructure/CEL_MIGRATION_PLAN.md`.
> Also worth knowing if you re-run the setup script below: the `celladore` org has
> GitHub's immutable-OIDC-subject-ID behavior active, so the federated credential's
> `subject` needs the `repo:<org>@<org_id>/<repo>@<repo_id>:environment:<name>` form, not
> the classic `repo:<org>/<repo>:environment:<name>` string — the two are not
> interchangeable and Azure does exact string matching. The current production credential
> was fixed to the correct subject after hitting `AADSTS700213` on this exact mismatch;
> see the migration plan's Phase 4 log for the full story.

## Production Environment Values

Create a GitHub environment named `production` and configure these environment variables:

| Variable | Purpose |
| --- | --- |
| `AZURE_CLIENT_ID` | Client ID of the pipeline user-assigned managed identity. |
| `AZURE_TENANT_ID` | Tenant ID for the Azure subscription. |
| `AZURE_SUBSCRIPTION_ID` | Subscription containing Codeflow production resources. |
| `AZURE_RESOURCE_GROUP` | Production resource group, expected default: `cel-prod-codeflow-rg`. |
| `AZURE_CONTAINER_APP` | Production Container App, expected default: `cel-prod-codeflow-api`. |
| `AZURE_CONTAINER_REGISTRY` | ACR name for production images, expected default: `celprodcodeflowacr`. |

The workflow deploys only to existing infrastructure. Provision or import the production Container App and ACR before running the deploy job.

Do not apply the root `orchestration/infrastructure/terraform` stack as the runtime prerequisite without reviewing it first; that stack still reflects an older AKS-shaped deployment. Use `orchestration/infrastructure/terraform/runtime` for the production Container App runtime stack.

## Azure Setup

Run `scripts/setup-azure-auth-for-pipeline.ps1` after confirming the production resource group exists. The script creates a dedicated pipeline identity, assigns resource-group scoped RBAC, grants ACR push access, and adds a federated credential for the GitHub `production` environment.

The signed-in Azure CLI identity running the script must be allowed to create role assignments on the deployment resource group or subscription. Use `Owner`, `User Access Administrator`, `Role Based Access Control Administrator`, or another role that includes `Microsoft.Authorization/roleAssignments/write`; `Contributor` alone is not sufficient for the RBAC step.

After setup, store the script outputs in the GitHub `production` environment variables. Keep any approval gates on the environment so pushes to `master` still require explicit deployment approval.

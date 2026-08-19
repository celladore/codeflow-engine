# CodeFlow Website Deployment Guide

This document describes the Next.js website and Azure deployment setup for
`codeflow.celladoresystems.com`.

> **Canonical doc.** This is the single source of truth for website deployment.
> `website/docs/DEPLOYMENT.md` is a pointer to this file — don't let the two
> drift again; edit only this one.

## Overview

The CodeFlow Engine website is a Next.js application that provides:
- **Home Page**: Project promotion and key features
- **Installation Guide**: Step-by-step installation instructions
- **Download Page**: Links to various download methods (GitHub, PyPI, Docker)

## Architecture

### Technology Stack

- **Framework**: Next.js (static export, `output: "export"`)
- **Styling**: Tailwind CSS
- **Deployment**: Azure Static Web Apps
- **CI/CD**: GitHub Actions (`.github/workflows/deploy-website.yml`)

### Azure Resources

Live resources (celladore-sub, recreated 2026-08-19 from the old
phoenixvc-owned `pvc-*` resources — see
`orchestration/infrastructure/CEL_MIGRATION_PLAN.md` for the full cutover
history):

- **Static Web App**: `cel-prod-codeflow-swa`
- **Resource Group**: `cel-prod-codeflow-rg`
- **Location**: `eastus2`
- **SKU**: Free tier (supports up to 2 custom domains — sufficient for this site)
- **Custom Domain**: `codeflow.celladoresystems.com`

There is no CDN or Application Insights component provisioned for this site —
only the Static Web App itself. If you need those, they'd have to be added
first, not just documented.

### Infrastructure as Code

The Terraform stack for this site lives at
`orchestration/infrastructure/terraform/website/` (this repo's canonical live
Terraform for the website — see the root `CLAUDE.md`). As of 2026-08-19 it has
**never been successfully applied**: no backend is configured (only
`backend.tf.example` exists) and no state tracks the live resources, which
were created out-of-band via `az` CLI. A first real `terraform apply` needs
`terraform import` for the resource group and the Static Web App first, or it
will try to create duplicates. See that stack's own `README.md` for the exact
apply sequence and known gaps — don't treat it as already the deployment
mechanism; the GitHub Actions workflow below is what actually ships the site
today.

There is no `infrastructure/bicep/` directory in this repo — ignore any prior
references to Bicep-based deployment for this site.

## Local Development

```bash
cd website
pnpm install
pnpm run dev
```

Visit `http://localhost:3000` to view the site.

## Deployment

### Automatic Deployment

`.github/workflows/deploy-website.yml` deploys automatically when:
- Changes are pushed to the **`master`** branch touching `website/**` or the
  workflow file itself
- The workflow is manually triggered via `workflow_dispatch`

A pull request touching those paths runs a separate build-only validation job
(no deploy).

The deploy job builds with `pnpm install --frozen-lockfile` + `pnpm run build`, then uploads the static
export in `website/out` via `Azure/static-web-apps-deploy@v1`
(`skip_app_build: true` — the action does not rebuild, it just uploads what
the workflow already built).

### Manual Deployment

```bash
cd website
pnpm run build

pnpm add -g @azure/static-web-apps-cli
swa deploy ./out --deployment-token <YOUR_TOKEN>
```

## Configuration

### Required GitHub Secret

- `AZURE_STATIC_WEB_APPS_API_TOKEN`: deployment token for `cel-prod-codeflow-swa`.
  If unset, the deploy step is skipped and the workflow just confirms the
  build succeeded (see the "Skip deploy when token is missing" step).

### Getting the Deployment Token

```bash
az staticwebapp secrets list \
  --name cel-prod-codeflow-swa \
  --resource-group cel-prod-codeflow-rg \
  --query "properties.apiKey" \
  --output tsv
```

### Environment variables

There is no `NEXT_PUBLIC_API_URL` or other runtime env var wired into the
site. `APP_URL` / `API_URL` are compile-time constants in
`website/app/config/constants.ts` — edit that file directly and redeploy
rather than looking for a `.env.production`.

## Custom Domain Setup

The custom domain is already live. This is the sequence that was actually
used, for reference if it ever needs to be redone:

1. `celladore-org/infrastructure/dns` (Cloudflare, zone `celladoresystems.com`)
   owns the `codeflow.celladoresystems.com` CNAME pointing at the Static Web
   App's default hostname. This repo does not own that DNS record.
2. Once the CNAME resolves, bind the custom domain on the Static Web App:
   ```bash
   az staticwebapp hostname set \
     --name cel-prod-codeflow-swa \
     --resource-group cel-prod-codeflow-rg \
     --hostname codeflow.celladoresystems.com
   ```
3. Azure provisions the SSL certificate automatically (`cname-delegation`
   validation, no TXT record needed since DNS already points at the SWA
   default hostname).
4. Verify:
   ```bash
   az staticwebapp hostname show \
     --name cel-prod-codeflow-swa \
     --resource-group cel-prod-codeflow-rg \
     --hostname codeflow.celladoresystems.com
   ```
   or simply `curl -I https://codeflow.celladoresystems.com/` and check for
   `200` with a valid cert.

## Project Structure

```
website/
├── app/
│   ├── page.tsx              # Home page
│   ├── installation/
│   │   └── page.tsx          # Installation guide
│   ├── download/
│   │   └── page.tsx          # Download page
│   ├── config/
│   │   └── constants.ts      # APP_URL / API_URL etc. (compile-time)
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── public/                   # Static assets
├── next.config.ts            # Next.js configuration
├── package.json
└── README.md

orchestration/infrastructure/terraform/website/
├── main.tf                   # Resource group + Static Web App + custom domain
├── variables.tf
├── outputs.tf
└── README.md                 # Apply sequence, known gaps (see above)

.github/workflows/
└── deploy-website.yml        # CI/CD pipeline
```

## Next.js Configuration

The site is configured for static export:

```typescript
// next.config.ts
{
  output: 'export',
  images: {
    unoptimized: true,
  },
  trailingSlash: true,
}
```

This ensures compatibility with Azure Static Web Apps.

## Monitoring

- **GitHub Actions**: deployment status and build logs
- **Azure Portal**: Static Web App overview for basic traffic/availability
  (no Application Insights component is provisioned — don't expect
  app-level telemetry beyond that)
- **Custom Domain**: DNS and SSL certificate status via
  `az staticwebapp hostname show` (see above)

## Troubleshooting

### Build Failures

- Check Node.js version (workflow uses 20)
- Verify all dependencies are installed
- Review build logs in GitHub Actions

### Deployment Failures

- Verify `AZURE_STATIC_WEB_APPS_API_TOKEN` is set in repo secrets — if it's
  missing, the workflow silently skips the deploy step instead of failing
- Check `cel-prod-codeflow-swa` exists and is accessible
- Review deployment logs in GitHub Actions

### Custom Domain Issues

- Verify the CNAME in `celladore-org/infrastructure/dns` still resolves
- Check domain validation status in Azure Portal or via
  `az staticwebapp hostname show`
- A transient cert-mismatch right after DNS changes is expected — the CNAME
  can resolve before Azure finishes binding the custom domain

## Cost

Live SKU is **Free tier** — no static-web-app hosting cost for this site at
current traffic. If usage ever requires moving to Standard, re-check current
Azure pricing before quoting a number here; don't assume a stale figure.

## References

- [Next.js Documentation](https://nextjs.org/docs)
- [Azure Static Web Apps Documentation](https://learn.microsoft.com/azure/static-web-apps/)
- `orchestration/infrastructure/CEL_MIGRATION_PLAN.md` — full cutover history
  (DNS, custom domain, and the celladore-sub recreate-and-cutover)
- `orchestration/infrastructure/terraform/website/README.md` — Terraform apply
  sequence and known gaps

# GitHub App Quick Start

## 🚀 5-Minute Setup

### Step 1: Create GitHub App (2 minutes)

1. Go to: https://github.com/settings/apps/new?manifest=1
2. Copy the contents of `.github/app-manifest.yml`
3. Paste into the manifest editor
4. Click "Create GitHub App"
5. **Save these values:**
   - App ID
   - Client ID
   - Client Secret
   - Private Key (download the .pem file)

### Step 2: Install Dependencies (1 minute)

```bash
pnpm add @octokit/auth-app @octokit/rest libsodium-wrappers
```

### Step 3: Configure Environment (1 minute)

Add to `.env.local` or Azure App Service:

```env
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"
GITHUB_APP_CLIENT_ID=your_client_id
GITHUB_APP_CLIENT_SECRET=your_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_REDIRECT_URI=https://your-app.azurewebsites.net/api/github-app/callback
```

### Step 4: Update Webhook URL (1 minute)

1. Go to: https://github.com/settings/apps/YOUR_APP_NAME
2. Update "Webhook URL" to: `https://your-app.azurewebsites.net/api/github-app/webhook`
3. Save

### Step 5: Deploy & Test

1. Deploy to Azure App Service
2. Visit: `https://your-app.azurewebsites.net/api/github-app/install`
3. Or add install button to README:

```markdown
[![Install App](https://img.shields.io/badge/Install-GitHub%20App-28a745)](https://github.com/apps/YOUR_APP_NAME/installations/new)
```

## ✅ Done!

Users can now click "Install" and secrets will be configured automatically!

## Troubleshooting

- **Webhook not receiving events:** Check webhook URL is accessible and secret matches
- **Secrets not being set:** Verify app has "secrets: write" permission
- **OAuth errors:** Check client ID/secret are correct

## Next Steps

- Customize secret values (use Azure Key Vault)
- Add setup validation
- Implement proper encryption (libsodium-wrappers)


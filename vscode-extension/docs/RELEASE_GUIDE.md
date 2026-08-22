# CodeFlow VS Code Extension - Release Guide

This guide covers the complete process of building, testing, and publishing the CodeFlow VS Code extension to the VS Code Marketplace.

---

## Prerequisites

- Node.js 20+
- pnpm
- VS Code (for testing)
- VS Code Marketplace publisher account
- Personal Access Token (PAT) for publishing

---

## Development Setup

### 1. Clone and Install

```bash
git clone https://github.com/phoenixvc/codeflow-engine.git
cd codeflow-engine/vscode-extension
pnpm install
```

### 2. Development Mode

```bash
# Compile TypeScript
pnpm run compile

# Watch mode (auto-compile on changes)
pnpm run watch

# Launch extension in new VS Code window
# Press F5 in VS Code
```

---

## Build Process

### Local Build

```bash
# Install dependencies
pnpm install --frozen-lockfile

# Compile TypeScript
pnpm run compile

# Package extension
pnpm run package
```

This creates a `.vsix` file in the root directory:

``` text
codeflow-1.0.10.vsix
```

### Verify Package

```bash
# Install VS Code CLI (if not already installed)
pnpm add -g @vscode/vsce

# Check package contents
vsce ls codeflow-*.vsix
```

---

## Testing Locally

### 1. Install Extension from VSIX

```bash
# In VS Code
# Press Ctrl+Shift+P (Cmd+Shift+P on Mac)
# Type: "Extensions: Install from VSIX..."
# Select the .vsix file
```

### 2. Test Extension

1. Open a workspace with code files
2. Test all commands:
   - `codeflow.checkFile` - Check current file
   - `codeflow.checkWorkspace` - Check workspace
   - `codeflow.openDashboard` - Open dashboard
   - `codeflow.viewHistory` - View history
3. Verify tree views appear
4. Check output panel for logs
5. Test configuration options

### 3. Test on Different Platforms

- Windows
- macOS
- Linux

---

## Publishing to VS Code Marketplace

### 1. Get Publisher Account

1. Go to [Azure DevOps](https://dev.azure.com)
2. Create organization (if needed)
3. Create Personal Access Token (PAT) with Marketplace (Manage) scope
4. Note your publisher ID

### 2. Configure Publisher

```bash
# Login to VS Code Marketplace
vsce login <publisher-id>

# Or use PAT
vsce login <publisher-id> --pat <your-pat-token>
```

### 3. Update Version

Update version in `package.json`:

```json
{
  "version": "1.0.11"
}
```

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### 4. Update CHANGELOG.md

Add entry for new version:

```markdown
## [1.0.11] - 2025-01-XX

### Added
- New feature X

### Fixed
- Bug fix Y

### Changed
- Improvement Z
```

### 5. Publish

```bash
# Publish to marketplace
vsce publish

# Or publish specific version
vsce publish 1.0.11
```

### 6. Verify Publication

1. Go to [VS Code Marketplace](https://marketplace.visualstudio.com/)
2. Search for "CodeFlow"
3. Verify new version is available
4. Test installation from marketplace

---

## Version Management

### Automated Versioning

Create a script `scripts/bump-version.sh`:

```bash
#!/bin/bash
VERSION=$1
if [ -z "$VERSION" ]; then
  echo "Usage: ./scripts/bump-version.sh <version>"
  exit 1
fi

# Update package.json
npm version $VERSION --no-git-tag-version

# Update CHANGELOG.md (manual)
echo "Update CHANGELOG.md with version $VERSION"

echo "Version bumped to $VERSION"
```

### Release Checklist

- [ ] Update version in `package.json`
- [ ] Update `CHANGELOG.md`
- [ ] Run tests: `pnpm test`
- [ ] Build package: `pnpm run package`
- [ ] Test VSIX locally
- [ ] Commit changes
- [ ] Create git tag: `git tag vscode-extension-v0.2.0-alpha.1`
- [ ] Push tag: `git push origin vscode-extension-v0.2.0-alpha.1`
- [ ] Publish: `pnpm run publish`
- [ ] Verify on marketplace
- [ ] Update release notes on GitHub

---

## CI/CD Integration

### GitHub Actions Workflow

The extension includes a release workflow (`../../.github/workflows/release-vscode-extension.yml`) that:

1. Triggers on version tag push
2. Builds the extension
3. Packages as VSIX
4. Publishes to marketplace
5. Creates GitHub release

### Manual Release Process

If not using CI/CD:

```bash
# 1. Update version
npm version patch  # or minor, major

# 2. Build and test
pnpm run compile
pnpm run package
pnpm test

# 3. Commit and tag
git add .
git commit -m "Release vscode-extension-v0.2.0-alpha.1"
git tag vscode-extension-v0.2.0-alpha.1
git push origin master --tags

# 4. Publish
pnpm run publish
```

---

## Troubleshooting

### Build Errors

**TypeScript compilation errors:**

```bash
# Clean and rebuild
rm -rf node_modules out
pnpm install
pnpm run compile
```

**Package errors:**

```bash
# Verify package.json is valid
pnpm run package -- --yarn

# Check for missing dependencies
pnpm audit
```

### Publishing Errors

**Authentication failed:**

```bash
# Re-login
vsce logout
vsce login <publisher-id>
```

**Version already exists:**

- Increment version in `package.json`
- Update CHANGELOG.md
- Retry publish

**Marketplace validation errors:**

- Check `package.json` for required fields
- Verify all icons/images exist
- Check README.md formatting
- Verify license file exists

---

## Best Practices

1. **Test thoroughly** before publishing
2. **Follow semantic versioning** strictly
3. **Update CHANGELOG.md** for every release
4. **Test on all platforms** (Windows, macOS, Linux)
5. **Monitor marketplace reviews** and respond promptly
6. **Keep dependencies updated** and secure
7. **Document breaking changes** clearly

---

## Additional Resources

- [VS Code Extension Publishing Guide](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [VS Code Extension Guidelines](https://code.visualstudio.com/api/references/extension-guidelines)
- [Semantic Versioning](https://semver.org/)
- [VS Code Extension API](https://code.visualstudio.com/api)

---

## Support

For issues or questions:

- GitHub Issues: [codeflow-engine/issues](https://github.com/phoenixvc/codeflow-engine/issues)
- Documentation: [README.md](./README.md)

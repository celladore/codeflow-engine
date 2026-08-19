# Package Publishing Quick Start

**Phase:** Wave 4, Phase 8.2  
**Status:** Ready to Publish  
**Purpose:** Quick-start guide for publishing CodeFlow utility packages

---

## Overview

This guide provides a quick checklist for publishing the CodeFlow utility packages to PyPI and npm.

---

## Prerequisites Checklist

### Python Package (codeflow-utils-python)

- [ ] PyPI account created at https://pypi.org
- [ ] API token generated at https://pypi.org/manage/account/token/
- [ ] GitHub secret `PYPI_API_TOKEN` added to repository
- [ ] Package version updated in `pyproject.toml`
- [ ] README and LICENSE files present

### TypeScript Package (@codeflow/utils)

- [ ] npm account created at https://www.npmjs.com
- [ ] Access token generated at https://www.npmjs.com/settings/[username]/tokens
- [ ] GitHub secret `NPM_TOKEN` added to repository
- [ ] Package version updated in `package.json`
- [ ] README and LICENSE files present

---

## Quick Setup

### Option 1: Use Setup Script

```powershell
.\scripts\setup-package-publishing.ps1
```

This script will guide you through the setup process step-by-step.

### Option 2: Manual Setup

Follow the detailed guide: [PACKAGE_PUBLISHING_GUIDE.md](./PACKAGE_PUBLISHING_GUIDE.md)

---

## Publishing Steps

### Python Package

1. **Update Version:**
   ```bash
   cd packages/codeflow-utils-python
   # Edit pyproject.toml version
   ```

2. **Test Build:**
   ```bash
   python -m pip install --upgrade build twine
   python -m build
   twine check dist/*
   ```

3. **Test Upload (TestPyPI):**
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **Publish:**
   - Create GitHub release with tag (e.g., `v0.1.0`)
   - Publishing workflow will run automatically

### TypeScript Package

1. **Update Version:**
   ```bash
   cd packages/@codeflow/utils
   # Edit package.json version
   ```

2. **Test Build:**
   ```bash
   pnpm install
   pnpm run build
   pnpm pack --dry-run
   ```

3. **Publish:**
   - Create GitHub release with tag (e.g., `v0.1.0`)
   - Publishing workflow will run automatically

---

## Verification

### After Publishing

1. **Verify Package Availability:**
   ```bash
   # Python
   pip search codeflow-utils-python  # or check PyPI website
   
   # TypeScript
   npm view @codeflow/utils
   ```

2. **Test Installation:**
   ```bash
   # Python
   pip install codeflow-utils-python
   
   # TypeScript
   npm install @codeflow/utils
   ```

3. **Verify Functionality:**
   ```python
   # Python
   from codeflow_utils import validate_url, format_datetime
   print(validate_url("https://example.com"))
   ```

   ```typescript
   // TypeScript
   import { validateUrl, formatDateTime } from "@codeflow/utils";
   console.log(validateUrl("https://example.com"));
   ```

---

## Troubleshooting

### Common Issues

**Issue:** GitHub workflow fails with authentication error
- **Solution:** Verify secret is set correctly in repository settings
- **Solution:** Check token has correct permissions

**Issue:** Package build fails
- **Solution:** Check `pyproject.toml` or `package.json` syntax
- **Solution:** Verify all dependencies are listed

**Issue:** Publishing fails
- **Solution:** Check version number is unique
- **Solution:** Verify package name is available

---

## Next Steps

After publishing:

1. ✅ **Integrate packages** into existing repos
2. ✅ **Update imports** to use published packages
3. ✅ **Remove duplicate code** from repos
4. ✅ **Monitor usage** and gather feedback
5. ✅ **Expand utilities** based on usage

---

## Support

For detailed instructions, see:
- [PACKAGE_PUBLISHING_GUIDE.md](./PACKAGE_PUBLISHING_GUIDE.md) - Complete guide
- [SHARED_UTILITIES_IMPLEMENTATION.md](./SHARED_UTILITIES_IMPLEMENTATION.md) - Implementation details

---

**Last Updated:** 2025-01-XX


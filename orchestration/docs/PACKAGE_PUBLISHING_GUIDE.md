# Package Publishing Guide

**Phase:** Wave 4, Phase 8.2  
**Status:** Implementation Guide  
**Purpose:** Guide for publishing shared utility packages

---

## Overview

This guide provides step-by-step instructions for publishing the CodeFlow shared utility packages to their respective registries.

---

## Python Package: `codeflow-utils-python`

### Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org
   - Generate API token at https://pypi.org/manage/account/token/
   - Store token as GitHub secret: `PYPI_API_TOKEN`

2. **Package Setup**
   - Ensure `pyproject.toml` is configured correctly
   - Version number is set correctly
   - README and LICENSE files are present

### Publishing Process

#### Manual Publishing

1. **Build Package:**
   ```bash
   cd packages/codeflow-utils-python
   python -m pip install --upgrade build twine
   python -m build
   ```

2. **Check Package:**
   ```bash
   twine check dist/*
   ```

3. **Test Upload (TestPyPI):**
   ```bash
   twine upload --repository testpypi dist/*
   ```

4. **Publish to PyPI:**
   ```bash
   twine upload dist/*
   ```

#### Automated Publishing (GitHub Actions)

The package includes a GitHub Actions workflow (`.github/workflows/publish.yml`) that automatically publishes when a release is created:

1. **Create Release:**
   - Go to GitHub repository
   - Create a new release
   - Tag version (e.g., `v0.1.0`)
   - Publish release

2. **Workflow Automatically:**
   - Builds the package
   - Publishes to PyPI
   - Uses `PYPI_API_TOKEN` secret

### Version Management

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `pyproject.toml`
- Create git tag matching version
- Update CHANGELOG.md (if exists)

### Installation

After publishing, users can install:

```bash
pip install codeflow-utils-python
```

---

## TypeScript Package: `@codeflow/utils`

### Prerequisites

1. **npm Account**
   - Create account at https://www.npmjs.com
   - Generate access token at https://www.npmjs.com/settings/[username]/tokens
   - Store token as GitHub secret: `NPM_TOKEN`

2. **Package Setup**
   - Ensure `package.json` is configured correctly
   - Version number is set correctly
   - README and LICENSE files are present

### Publishing Process

#### Manual Publishing

1. **Build Package:**
   ```bash
   cd packages/@codeflow/utils
   pnpm install
   pnpm run build
   ```

2. **Test Package:**
   ```bash
   pnpm test
   pnpm pack --dry-run
   ```

3. **Publish to npm:**
   ```bash
   npm publish --access public
   ```

#### Automated Publishing (GitHub Actions)

The package includes a GitHub Actions workflow (`.github/workflows/publish.yml`) that automatically publishes when a release is created:

1. **Create Release:**
   - Go to GitHub repository
   - Create a new release
   - Tag version (e.g., `v0.1.0`)
   - Publish release

2. **Workflow Automatically:**
   - Builds the package
   - Publishes to npm
   - Uses `NPM_TOKEN` secret

### Version Management

- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update version in `package.json`
- Create git tag matching version
- Update CHANGELOG.md (if exists)

### Installation

After publishing, users can install:

```bash
npm install @codeflow/utils
```

---

## CI/CD Setup

### GitHub Secrets Required

**For Python Package:**
- `PYPI_API_TOKEN` - PyPI API token

**For TypeScript Package:**
- `NPM_TOKEN` - npm access token

### Workflow Files

Both packages include:
- `.github/workflows/ci.yml` - Continuous integration (test, lint, build)
- `.github/workflows/publish.yml` - Automated publishing on release

---

## Integration into Existing Repos

### Python (`codeflow-engine`)

1. **Add Dependency:**
   ```toml
   # pyproject.toml
   [project.dependencies]
   codeflow-utils-python = "^0.1.0"
   ```

2. **Update Imports:**
   ```python
   # Before
   from codeflow_engine.config.validation import validate_configuration
   
   # After
   from codeflow_utils.validation import validate_config
   ```

3. **Remove Duplicate Code:**
   - Remove duplicate utility functions
   - Update all imports
   - Test thoroughly

### TypeScript (Frontend Repos)

1. **Add Dependency:**
   ```json
   {
     "dependencies": {
       "@codeflow/utils": "^0.1.0"
     }
   }
   ```

2. **Update Imports:**
   ```typescript
   // Before
   import { validateUrl } from "./utils/validation";
   
   // After
   import { validateUrl } from "@codeflow/utils/validation";
   ```

3. **Remove Duplicate Code:**
   - Remove duplicate utility functions
   - Update all imports
   - Test thoroughly

---

## Release Checklist

### Before Publishing

- [ ] All tests passing
- [ ] Code linted and formatted
- [ ] Version number updated
- [ ] CHANGELOG updated (if exists)
- [ ] README updated with latest features
- [ ] Documentation complete
- [ ] License file present

### Publishing

- [ ] Build package successfully
- [ ] Test package locally
- [ ] Create git tag
- [ ] Create GitHub release
- [ ] Verify automated publishing
- [ ] Test installation from registry

### After Publishing

- [ ] Verify package is available in registry
- [ ] Test installation in clean environment
- [ ] Update documentation with new version
- [ ] Announce release (if applicable)

---

## Troubleshooting

### Python Package Issues

**Issue:** `twine upload` fails with authentication error
- **Solution:** Check `PYPI_API_TOKEN` is set correctly
- **Solution:** Ensure token has upload permissions

**Issue:** Package build fails
- **Solution:** Check `pyproject.toml` syntax
- **Solution:** Ensure all dependencies are listed

### TypeScript Package Issues

**Issue:** `npm publish` fails with authentication error
- **Solution:** Check `NPM_TOKEN` is set correctly
- **Solution:** Ensure token has publish permissions

**Issue:** TypeScript compilation errors
- **Solution:** Check `tsconfig.json` configuration
- **Solution:** Ensure all types are properly defined

---

## Next Steps

1. ✅ **Create publishing guide** (this document)
2. **Set up GitHub secrets** for publishing
3. **Test publishing process** (TestPyPI / pnpm test)
4. **Publish initial versions**
5. **Integrate into existing repos**
6. **Monitor usage and feedback**

---

**Last Updated:** 2025-01-XX


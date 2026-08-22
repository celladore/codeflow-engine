# Package Integration Guide

**Phase:** Wave 4, Phase 8.2  
**Status:** Implementation Guide  
**Purpose:** Guide for integrating CodeFlow utility packages into existing repositories

---

## Overview

This guide provides step-by-step instructions for integrating the CodeFlow utility packages (`codeflow-utils-python` and `@codeflow/utils`) into existing CodeFlow repositories.

---

## Python Package Integration

### Step 1: Install Package

#### Option A: From PyPI (After Publishing)

```bash
pip install codeflow-utils-python
```

#### Option B: From Local Development

```bash
cd packages/codeflow-utils-python
pip install -e .
```

#### Option C: Add to Dependencies

**For Poetry (`pyproject.toml`):**
```toml
[tool.poetry.dependencies]
codeflow-utils-python = "^0.1.0"
```

**For pip (`requirements.txt`):**
```
codeflow-utils-python>=0.1.0
```

---

### Step 2: Update Imports

#### Before (Using Local Utilities)

```python
# Old imports
from codeflow_engine.config.validation import validate_configuration
from codeflow_engine.utils.formatting import format_datetime
from codeflow_engine.utils.retry import retry
```

#### After (Using Shared Package)

```python
# New imports
from codeflow_utils.validation import validate_config, validate_environment_variables
from codeflow_utils.formatting import format_datetime, format_number
from codeflow_utils.common import retry, RateLimiter, rate_limit
```

---

### Step 3: Replace Duplicate Code

#### Example: Validation Utilities

**Before:**
```python
# codeflow_engine/config/validation.py
def validate_configuration(settings):
    # Local implementation
    pass
```

**After:**
```python
# Use shared utility
from codeflow_utils.validation import validate_config

result = validate_config(settings)
```

#### Example: Formatting Utilities

**Before:**
```python
# codeflow_engine/utils/formatting.py
def format_datetime(dt):
    # Local implementation
    pass
```

**After:**
```python
# Use shared utility
from codeflow_utils.formatting import format_datetime

formatted = format_datetime(datetime.now())
```

#### Example: Retry Logic

**Before:**
```python
# codeflow_engine/utils/retry.py
@retry(max_attempts=3)
def api_call():
    # Local retry implementation
    pass
```

**After:**
```python
# Use shared utility
from codeflow_utils.common import retry

@retry(max_attempts=3, delay=1.0)
def api_call():
    # Shared retry implementation
    pass
```

---

### Step 4: Update Tests

#### Update Test Imports

```python
# Before
from codeflow_engine.utils.formatting import format_datetime

# After
from codeflow_utils.formatting import format_datetime
```

#### Remove Duplicate Test Files

If you have tests for utilities that are now in the shared package:
- Remove local test files
- Tests are covered in the shared package
- Update integration tests to use shared utilities

---

### Step 5: Verify Integration

#### Run Tests

```bash
pytest tests/ -v
```

#### Check for Import Errors

```bash
python -c "from codeflow_utils import validate_url, format_datetime, retry; print('Imports OK')"
```

#### Verify Functionality

```python
from codeflow_utils import validate_url, format_datetime, retry

# Test validation
assert validate_url("https://example.com") is True

# Test formatting
from datetime import datetime
formatted = format_datetime(datetime.now())
assert isinstance(formatted, str)

# Test retry
@retry(max_attempts=3)
def test_function():
    return "success"

assert test_function() == "success"
```

---

## TypeScript Package Integration

### Step 1: Install Package

#### Option A: From npm (After Publishing)

```bash
npm install @codeflow/utils
```

#### Option B: From Local Development

```bash
cd packages/@codeflow/utils
pnpm install
pnpm run build
pnpm link --global
cd ../../codeflow-desktop  # or other repo
pnpm link --global @codeflow/utils
```

#### Option C: Add to Dependencies

**In `package.json`:**
```json
{
  "dependencies": {
    "@codeflow/utils": "^0.1.0"
  }
}
```

---

### Step 2: Update Imports

#### Before (Using Local Utilities)

```typescript
// Old imports
import { validateUrl } from "./utils/validation";
import { formatDateTime } from "./utils/formatting";
```

#### After (Using Shared Package)

```typescript
// New imports
import { validateUrl, isValidUrl } from "@codeflow/utils/validation";
import { formatDateTime, formatRelativeTime } from "@codeflow/utils/formatting";
```

---

### Step 3: Replace Duplicate Code

#### Example: URL Validation

**Before:**
```typescript
// src/utils/validation.ts
export function validateUrl(url: string): boolean {
  // Local implementation
}
```

**After:**
```typescript
// Use shared utility
import { validateUrl } from "@codeflow/utils/validation";

const isValid = validateUrl("https://example.com");
```

#### Example: Date Formatting

**Before:**
```typescript
// src/utils/formatting.ts
export function formatDateTime(date: Date): string {
  // Local implementation
}
```

**After:**
```typescript
// Use shared utility
import { formatDateTime } from "@codeflow/utils/formatting";

const formatted = formatDateTime(new Date());
```

---

### Step 4: Update Build Configuration

#### TypeScript Configuration

Ensure your `tsconfig.json` includes the package:

```json
{
  "compilerOptions": {
    "paths": {
      "@codeflow/utils/*": ["../packages/@codeflow/utils/src/*"]
    }
  }
}
```

---

### Step 5: Verify Integration

#### Run Tests

```bash
pnpm test
```

#### Check for Import Errors

```bash
pnpm run build
```

#### Verify Functionality

```typescript
import { validateUrl, formatDateTime } from "@codeflow/utils";

// Test validation
console.assert(validateUrl("https://example.com") === true);

// Test formatting
const formatted = formatDateTime(new Date());
console.assert(typeof formatted === "string");
```

---

## Migration Checklist

### Pre-Migration

- [ ] Review existing utility code
- [ ] Identify code to replace
- [ ] Check for breaking changes
- [ ] Plan migration timeline

### Migration

- [ ] Install shared package
- [ ] Update imports
- [ ] Replace duplicate code
- [ ] Update tests
- [ ] Remove old utility files

### Post-Migration

- [ ] Run all tests
- [ ] Verify functionality
- [ ] Update documentation
- [ ] Commit changes

---

## Common Integration Patterns

### Pattern 1: Gradual Migration

1. Install package alongside existing code
2. Migrate one module at a time
3. Update tests incrementally
4. Remove old code after verification

### Pattern 2: Big Bang Migration

1. Install package
2. Update all imports at once
3. Remove all duplicate code
4. Run full test suite
5. Fix any issues

### Pattern 3: Feature-Based Migration

1. Migrate utilities for new features first
2. Gradually migrate existing features
3. Keep old code until fully migrated

---

## Troubleshooting

### Import Errors

**Issue:** Cannot import from package

**Solutions:**
- Verify package is installed: `pip list | grep codeflow-utils` or `npm list @codeflow/utils`
- Check Python path or TypeScript paths configuration
- Verify package version matches requirements

### Function Signature Mismatches

**Issue:** Function signatures differ from local implementation

**Solutions:**
- Review package documentation
- Check function parameters
- Update calling code if needed
- Create adapter functions if necessary

### Test Failures

**Issue:** Tests fail after migration

**Solutions:**
- Review test expectations
- Check for behavior differences
- Update test assertions
- Verify package version compatibility

---

## Benefits of Integration

### Code Reuse
- Single source of truth for utilities
- Consistent behavior across repos
- Reduced maintenance burden

### Quality
- Shared utilities are well-tested
- Community-reviewed code
- Regular updates and improvements

### Efficiency
- Faster development
- Less code duplication
- Easier onboarding

---

## Next Steps

1. ✅ **Integration guide created**
2. **Choose integration approach** (gradual, big bang, or feature-based)
3. **Start with one repository** (recommend codeflow-engine)
4. **Migrate utilities incrementally**
5. **Monitor and gather feedback**
6. **Expand to other repositories**

---

**Last Updated:** 2025-01-XX


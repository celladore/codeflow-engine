# Shared Utilities Implementation Guide

**Phase:** Wave 4, Phase 8.2  
**Status:** Implementation Guide  
**Purpose:** Guide for creating and using shared utility packages

---

## Overview

This guide provides step-by-step instructions for creating, implementing, and using the shared utility packages for CodeFlow.

---

## Python Package: `codeflow-utils-python`

### Step 1: Create Package Structure

```bash
# Create new repository or directory
mkdir codeflow-utils-python
cd codeflow-utils-python

# Create package structure
mkdir -p codeflow_utils/{validation,formatting,common}
mkdir -p tests
```

### Step 2: Initialize Package Files

**`pyproject.toml`:**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codeflow-utils-python"
version = "0.1.0"
description = "Shared utility functions for CodeFlow Python projects"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "CodeFlow Team"}
]
keywords = ["codeflow", "utilities", "validation", "formatting"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-cov>=4.0",
    "black>=23.0",
    "ruff>=0.1.0",
    "mypy>=1.0",
]

[tool.setuptools]
packages = ["codeflow_utils"]

[tool.black]
line-length = 100
target-version = ['py310']

[tool.ruff]
line-length = 100
target-version = "py310"
```

### Step 3: Implement Core Utilities

**`codeflow_utils/validation/__init__.py`:**
```python
"""Validation utilities for CodeFlow."""

from .config import validate_config, validate_environment_variables
from .input import sanitize_input, validate_input
from .url import validate_url, is_valid_url

__all__ = [
    "validate_config",
    "validate_environment_variables",
    "sanitize_input",
    "validate_input",
    "validate_url",
    "is_valid_url",
]
```

**`codeflow_utils/validation/config.py`:**
```python
"""Configuration validation utilities."""

from typing import Any


def validate_config(config: dict[str, Any], required_keys: list[str]) -> tuple[bool, list[str]]:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        required_keys: List of required keys
        
    Returns:
        Tuple of (is_valid, missing_keys)
    """
    missing_keys = [key for key in required_keys if key not in config]
    return len(missing_keys) == 0, missing_keys


def validate_environment_variables(required_vars: list[str]) -> dict[str, Any]:
    """
    Check for required environment variables.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        Dictionary with validation results
    """
    import os
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    return {
        "valid": len(missing_vars) == 0,
        "missing": missing_vars,
        "found": [var for var in required_vars if var not in missing_vars],
    }
```

**`codeflow_utils/validation/input.py`:**
```python
"""Input validation and sanitization utilities."""

import re
from typing import Any


def sanitize_input(value: str, max_length: int | None = None) -> str:
    """
    Sanitize input string.
    
    Args:
        value: Input string to sanitize
        max_length: Maximum length (None for no limit)
        
    Returns:
        Sanitized string
    """
    # Remove leading/trailing whitespace
    sanitized = value.strip()
    
    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_input(value: Any, input_type: type, required: bool = True) -> tuple[bool, str | None]:
    """
    Validate input value.
    
    Args:
        value: Value to validate
        input_type: Expected type
        required: Whether value is required
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if value is None:
        if required:
            return False, "Value is required"
        return True, None
    
    if not isinstance(value, input_type):
        return False, f"Expected {input_type.__name__}, got {type(value).__name__}"
    
    return True, None
```

**`codeflow_utils/validation/url.py`:**
```python
"""URL validation utilities."""

import re
from urllib.parse import urlparse


def validate_url(url: str, schemes: list[str] | None = None) -> tuple[bool, str | None]:
    """
    Validate URL format.
    
    Args:
        url: URL string to validate
        schemes: Allowed URL schemes (None for any)
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"
    
    try:
        parsed = urlparse(url)
        
        if not parsed.scheme:
            return False, "URL must include a scheme (e.g., https://)"
        
        if not parsed.netloc:
            return False, "URL must include a domain"
        
        if schemes and parsed.scheme not in schemes:
            return False, f"URL scheme must be one of: {', '.join(schemes)}"
        
        return True, None
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"


def is_valid_url(url: str, schemes: list[str] | None = None) -> bool:
    """
    Check if URL is valid.
    
    Args:
        url: URL string to check
        schemes: Allowed URL schemes (None for any)
        
    Returns:
        True if URL is valid, False otherwise
    """
    is_valid, _ = validate_url(url, schemes)
    return is_valid
```

**`codeflow_utils/common/retry.py`:**
```python
"""Retry logic utilities."""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Retry decorator for functions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
        
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
```

**`codeflow_utils/formatting/date.py`:**
```python
"""Date and time formatting utilities."""

from datetime import datetime
from typing import Optional


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string (default: ISO-like format)
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)


def format_iso_datetime(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 string.
    
    Args:
        dt: Datetime object
        
    Returns:
        ISO 8601 formatted string
    """
    return dt.isoformat()


def format_relative_time(dt: datetime, now: Optional[datetime] = None) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago").
    
    Args:
        dt: Datetime object
        now: Current datetime (defaults to now)
        
    Returns:
        Relative time string
    """
    if now is None:
        now = datetime.now()
    
    delta = now - dt
    
    if delta.days > 365:
        years = delta.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif delta.days > 30:
        months = delta.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif delta.days > 0:
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    elif delta.seconds > 3600:
        hours = delta.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif delta.seconds > 60:
        minutes = delta.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "just now"
```

### Step 4: Add Tests

**`tests/test_validation.py`:**
```python
"""Tests for validation utilities."""

import pytest
from codeflow_utils.validation import (
    validate_config,
    validate_environment_variables,
    sanitize_input,
    validate_input,
    validate_url,
)


def test_validate_config():
    """Test configuration validation."""
    config = {"key1": "value1", "key2": "value2"}
    is_valid, missing = validate_config(config, ["key1", "key2"])
    assert is_valid
    assert len(missing) == 0
    
    is_valid, missing = validate_config(config, ["key1", "key3"])
    assert not is_valid
    assert "key3" in missing


def test_sanitize_input():
    """Test input sanitization."""
    assert sanitize_input("  test  ") == "test"
    assert sanitize_input("test\x00null") == "testnull"
    assert sanitize_input("test" * 10, max_length=10) == "test" * 2 + "te"


def test_validate_url():
    """Test URL validation."""
    is_valid, _ = validate_url("https://example.com")
    assert is_valid
    
    is_valid, _ = validate_url("invalid-url")
    assert not is_valid
```

### Step 5: Usage Example

```python
from codeflow_utils.validation import validate_config, validate_url
from codeflow_utils.common.retry import retry
from codeflow_utils.formatting.date import format_iso_datetime

# Validate configuration
config = {"api_key": "test", "base_url": "https://api.example.com"}
is_valid, missing = validate_config(config, ["api_key", "base_url"])

# Validate URL
is_valid, error = validate_url("https://api.example.com", schemes=["https"])

# Retry logic
@retry(max_attempts=3, delay=1.0)
def api_call():
    # API call that might fail
    pass

# Format datetime
from datetime import datetime
formatted = format_iso_datetime(datetime.now())
```

---

## TypeScript Package: `@codeflow/utils`

### Step 1: Create Package Structure

```bash
mkdir @codeflow/utils
cd @codeflow/utils
pnpm init
```

### Step 2: Configure Package

**`package.json`:**
```json
{
  "name": "@codeflow/utils",
  "version": "0.1.0",
  "description": "Shared utility functions for CodeFlow TypeScript/JavaScript projects",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest",
    "lint": "eslint src",
    "format": "prettier --write src"
  },
  "keywords": ["codeflow", "utilities", "validation", "formatting"],
  "author": "CodeFlow Team",
  "license": "MIT",
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.0.0",
    "jest": "^29.0.0",
    "prettier": "^3.0.0",
    "typescript": "^5.0.0"
  }
}
```

### Step 3: Implement Core Utilities

**`src/validation/url.ts`:**
```typescript
/**
 * URL validation utilities.
 */

export interface UrlValidationResult {
  valid: boolean;
  error?: string;
}

export function validateUrl(
  url: string,
  schemes?: string[]
): UrlValidationResult {
  if (!url || typeof url !== "string") {
    return { valid: false, error: "URL must be a non-empty string" };
  }

  try {
    const parsed = new URL(url);

    if (schemes && !schemes.includes(parsed.protocol.slice(0, -1))) {
      return {
        valid: false,
        error: `URL scheme must be one of: ${schemes.join(", ")}`,
      };
    }

    return { valid: true };
  } catch (error) {
    return { valid: false, error: `Invalid URL format: ${error}` };
  }
}

export function isValidUrl(url: string, schemes?: string[]): boolean {
  return validateUrl(url, schemes).valid;
}
```

**`src/formatting/date.ts`:**
```typescript
/**
 * Date and time formatting utilities.
 */

export function formatDateTime(date: Date, format?: string): string {
  if (format === "iso") {
    return date.toISOString();
  }

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  const hours = String(date.getHours()).padStart(2, "0");
  const minutes = String(date.getMinutes()).padStart(2, "0");
  const seconds = String(date.getSeconds()).padStart(2, "0");

  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
}

export function formatRelativeTime(date: Date, now: Date = new Date()): string {
  const delta = now.getTime() - date.getTime();
  const seconds = Math.floor(delta / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  if (days > 365) {
    const years = Math.floor(days / 365);
    return `${years} year${years > 1 ? "s" : ""} ago`;
  } else if (days > 30) {
    const months = Math.floor(days / 30);
    return `${months} month${months > 1 ? "s" : ""} ago`;
  } else if (days > 0) {
    return `${days} day${days > 1 ? "s" : ""} ago`;
  } else if (hours > 0) {
    return `${hours} hour${hours > 1 ? "s" : ""} ago`;
  } else if (minutes > 0) {
    return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
  } else {
    return "just now";
  }
}
```

---

## Publishing Strategy

### Python Package

1. **Build Package:**
   ```bash
   python -m build
   ```

2. **Publish to PyPI:**
   ```bash
   python -m twine upload dist/*
   ```

3. **Install in Projects:**
   ```bash
   pip install codeflow-utils-python
   ```

### TypeScript Package

1. **Build Package:**
   ```bash
   pnpm run build
   ```

2. **Publish to npm:**
   ```bash
   npm publish --access public
   ```

3. **Install in Projects:**
   ```bash
   npm install @codeflow/utils
   ```

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

---

## Next Steps

1. ✅ **Create implementation guide** (this document)
2. **Create package repositories**
3. **Implement initial utilities**
4. **Add comprehensive tests**
5. **Set up CI/CD for publishing**
6. **Publish initial versions**
7. **Integrate into existing repos**

---

**Last Updated:** 2025-01-XX


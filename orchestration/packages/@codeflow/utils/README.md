# @codeflow/utils

Shared utility functions for CodeFlow TypeScript/JavaScript projects.

## Installation

```bash
npm install @codeflow/utils
```

## Usage

### Validation

```typescript
import { validateUrl, isValidUrl } from "@codeflow/utils/validation";

// Validate URL
const result = validateUrl("https://api.example.com", ["https"]);
if (result.valid) {
  console.log("URL is valid");
}

// Simple check
if (isValidUrl("https://api.example.com")) {
  console.log("URL is valid");
}
```

### Formatting

```typescript
import { formatDateTime, formatRelativeTime } from "@codeflow/utils/formatting";

// Format datetime
const formatted = formatDateTime(new Date(), "iso");

// Relative time
const relative = formatRelativeTime(new Date(2025, 0, 1));
```

## Development

```bash
# Install dependencies
pnpm install

# Build
pnpm run build

# Run tests
pnpm test

# Lint
pnpm run lint

# Format
pnpm run format
```

## License

MIT License


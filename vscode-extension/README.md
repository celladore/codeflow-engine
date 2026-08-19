# CodeFlow VS Code Extension

AI-Powered Code Quality and Automation for VS Code

> Canonical source: `vscode-extension` in the CodeFlow monorepo.
> Legacy split repo: https://github.com/phoenixvc/codeflow-plugins

## Features

### Quality Analysis
- **Multi-mode Analysis**: Ultra-fast, Fast, Smart, Comprehensive, and AI-Enhanced modes
- **Real-time Feedback**: Instant quality checks as you code
- **File & Workspace Analysis**: Check individual files or entire workspaces
- **Intelligent Issue Detection**: AI-powered code quality analysis

### Auto-Fix Capabilities
- **Automatic Issue Resolution**: Fix common code quality issues automatically
- **Smart Suggestions**: AI-driven recommendations for code improvements
- **Safe Auto-fix**: Preview changes before applying

### Dashboard & Metrics
- **Quality Dashboard**: Web-based interface for detailed analysis
- **Performance Metrics**: Track code quality improvements over time
- **Issue History**: View and manage quality issues

## Installation

### From VS Code Marketplace

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search for "CodeFlow" or "CodeFlow"
4. Click Install

### From Source

1. Clone this repository
2. Navigate to the extension directory
3. Run `pnpm install`
4. Run `pnpm run compile`
5. Press F5 to launch the extension in a new VS Code window

## Usage

### Quick Start

1. Open a Python, JavaScript, or TypeScript file
2. Right-click in the editor or use Command Palette (Ctrl+Shift+P)
3. Select "CodeFlow: Check Current File"
4. View results in the CodeFlow output panel

### Commands

#### Quality Analysis
- **CodeFlow: Run Quality Check** - Quick quality check with default settings
- **CodeFlow: Check Current File** - Analyze the currently open file
- **CodeFlow: Check Workspace** - Analyze all files in the workspace

#### File Operations
- **CodeFlow: Split Large File** - Split large files into manageable components
- **CodeFlow: Auto-Fix Issues** - Automatically fix detected issues

#### Configuration
- **CodeFlow: Show Dashboard** - Open the web-based dashboard
- **CodeFlow: Configure** - Open extension settings

## Configuration

### Extension Settings

| Setting                      | Description                    | Default  |
| ---------------------------- | ------------------------------ | -------- |
| `codeflow.enabled`           | Enable/disable the extension   | `true`   |
| `codeflow.qualityMode`       | Default quality analysis mode  | `fast`   |
| `codeflow.autoFixEnabled`    | Enable automatic fixing        | `false`  |
| `codeflow.showNotifications` | Show operation notifications   | `true`   |
| `codeflow.pythonPath`        | Path to Python executable      | `python` |
| `codeflow.maxFileSize`       | Maximum file size for analysis | `10000`  |

## Development

### Prerequisites
- Node.js 16+
- TypeScript 4.8+
- VS Code Extension Development Tools

### Build Commands

```bash
pnpm install          # Install dependencies
pnpm run compile      # Compile TypeScript
pnpm run watch        # Watch for changes
pnpm run lint         # Run ESLint
pnpm run test         # Run tests
```

### Building for Release

The extension is built in CI and `.vsix` files are attached to GitHub Releases. To build locally:

```bash
pnpm run package      # Creates .vsix file
```

**Note**: `.vsix` files are build artifacts and should not be committed to the repository long-term.

## Communication with Engine

The extension communicates with CodeFlow Engine via:
- **HTTP API**: REST endpoints for engine operations
- **Well-defined contracts**: No hard-coded dependencies on engine repo structure

## Related Repositories

- [`codeflow-engine`](https://github.com/phoenixvc/codeflow-engine) - Canonical monorepo for engine, website, desktop, orchestration, infrastructure, and extension source
- [`codeflow-infrastructure`](https://github.com/phoenixvc/codeflow-infrastructure) - Archived split infrastructure history
- [`codeflow-website`](https://github.com/phoenixvc/codeflow-website) - Archived split website history

## License

MIT

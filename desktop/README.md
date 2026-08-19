# CodeFlow Desktop

A cross-platform desktop application for CodeFlow Engine built with Tauri, React, and TypeScript.

> Canonical source: [desktop](desktop) in the CodeFlow monorepo.
> Legacy split repo: [JustAGhosT/codeflow-desktop](https://github.com/JustAGhosT/codeflow-desktop)

## Overview

CodeFlow Desktop provides a user-friendly interface for managing and monitoring CodeFlow workflows, configurations, and platform analytics. The application combines a modern React frontend with a lightweight Rust backend, leveraging Tauri for native desktop capabilities.

## Features

- **Dashboard**: Real-time workflow status and platform detection overview
- **Configuration Management**: Visual editor for CodeFlow settings and workflows
- **Platform Analytics**: Detailed insights into detected platforms and compatibility
- **Live Logs**: Real-time log streaming via WebSocket connection
- **Python Sidecar**: Embedded Python runtime for CodeFlow Engine integration

## Architecture

```
codeflow-desktop/
├── src/                    # React frontend (TypeScript)
│   ├── pages/             # Application pages
│   │   ├── Dashboard.tsx
│   │   ├── Configuration.tsx
│   │   ├── PlatformAnalytics.tsx
│   │   └── Logs.tsx
│   ├── components/        # Reusable UI components
│   └── App.tsx            # Main application component
├── src-tauri/             # Rust backend
│   ├── src/
│   │   ├── main.rs       # Tauri application entry point
│   │   └── lib.rs        # Core library functions
│   └── tauri.conf.json   # Tauri configuration
└── sidecar/               # Python sidecar process
    ├── main.py           # Sidecar entry point
    ├── websocket_handler.py
    └── requirements.txt
```

## Prerequisites

### Required

1. **Node.js** (v20 or higher)
2. **Rust** (latest stable)
3. **Python** (3.8 or higher)

## Getting Started

### Installation

1. **Navigate to the desktop app directory:**
   ```bash
   cd codeflow-desktop
   ```

2. **Install Node.js dependencies:**
   ```bash
   pnpm install
   ```

3. **Install Python dependencies for the sidecar:**
   ```bash
   pip install -r sidecar/requirements.txt
   ```

### Development

**Start the development server:**
```bash
pnpm run tauri dev
```

This command will:
1. Start the Vite dev server (React frontend) at http://localhost:1420
2. Compile the Rust backend
3. Launch the Python sidecar process
4. Open the desktop application window

## Building for Production

**Build the application:**
```bash
pnpm run build
```

**Create distributable packages:**
```bash
pnpm run tauri build
```

This generates platform-specific installers in `src-tauri/target/release/bundle/`:
- **Windows**: `.msi` installer
- **macOS**: `.dmg` disk image and `.app` bundle
- **Linux**: `.deb`, `.AppImage`, or `.rpm`

## Communication with Engine

The desktop application communicates with CodeFlow Engine via:
- **HTTP API**: REST endpoints for engine operations
- **WebSocket**: Real-time log streaming
- **Sidecar Contract**: Well-defined Python sidecar interface

**Important**: This application has no hard-coded dependencies on the engine repository structure. All communication is via API contracts.

## Technology Stack

### Frontend
- **React 19**: UI framework
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS 4**: Utility-first CSS framework
- **shadcn/ui**: Accessible component library

### Backend
- **Tauri 2**: Native desktop framework
- **Rust**: System programming language
- **Python Sidecar**: Embedded Python runtime for CodeFlow Engine integration

## Related Repositories

- [`codeflow-engine`](https://github.com/JustAGhosT/codeflow-engine) - Core engine (communicates via API)
- [`codeflow-infrastructure`](https://github.com/JustAGhosT/codeflow-infrastructure) - Production infrastructure
- [`codeflow-vscode-extension`](https://github.com/JustAGhosT/codeflow-vscode-extension) - VS Code extension
- [`codeflow-azure-setup`](https://github.com/JustAGhosT/codeflow-azure-setup) - Azure bootstrap scripts
- [`codeflow-website`](https://github.com/JustAGhosT/codeflow-website) - Marketing website

## License

MIT

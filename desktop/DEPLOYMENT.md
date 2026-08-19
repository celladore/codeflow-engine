<!-- markdownlint-disable MD022 MD024 MD031 MD032 MD036 MD040 -->

# CodeFlow Desktop - Deployment Guide

This guide covers building and deploying CodeFlow Desktop for production.

## Table of Contents

- [Build Process](#build-process)
- [Platform-Specific Builds](#platform-specific-builds)
- [Code Signing](#code-signing)
- [Distribution](#distribution)
- [Auto-Updates](#auto-updates)
- [Release Checklist](#release-checklist)

## Build Process

### Prerequisites

Ensure all development dependencies are installed:
- Node.js 20+
- Rust (latest stable)
- Python 3.8+
- Platform-specific build tools (see below)

### Production Build

```bash
# Navigate to the desktop app directory
cd codeflow-desktop

# Install dependencies
pnpm install
pip install -r sidecar/requirements.txt

# Build the application
pnpm run tauri build
```

The build process will:
1. Compile TypeScript and bundle the React app
2. Optimize assets (minification, tree-shaking)
3. Compile Rust backend in release mode
4. Package the Python sidecar
5. Create platform-specific installers

### Build Artifacts

Built applications are located in:
```
src-tauri/target/release/bundle/
```

**Windows:**
- `msi/` - Windows Installer (.msi)
- `nsis/` - NSIS Installer (.exe) (if configured)

**macOS:**
- `dmg/` - Disk Image (.dmg)
- `macos/` - Application Bundle (.app)

**Linux:**
- `deb/` - Debian Package (.deb)
- `appimage/` - AppImage (.AppImage)
- `rpm/` - RPM Package (.rpm) (if configured)

## Platform-Specific Builds

### Windows

#### Requirements
- Windows 10/11
- Microsoft Visual C++ Build Tools
- Windows SDK
- WiX Toolset (for .msi installer)

#### Build Commands
```powershell
# Standard build
pnpm run tauri build

# Build with specific features
pnpm run tauri build -- --features "feature1,feature2"
```

#### Code Signing (Windows)
```powershell
# Sign the executable
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com /fd SHA256 codeflow-desktop.exe

# Verify signature
signtool verify /pa codeflow-desktop.exe
```

### macOS

#### Requirements
- macOS 10.15+
- Xcode Command Line Tools
- Apple Developer Account (for distribution)

#### Build Commands
```bash
# Standard build
pnpm run tauri build

# Build universal binary (Intel + Apple Silicon)
pnpm run tauri build -- --target universal-apple-darwin
```

#### Code Signing (macOS)
```bash
# Sign the app
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" codeflow-desktop.app

# Create notarized dmg
xcrun notarytool submit codeflow-desktop.dmg --apple-id user@example.com --password app-specific-password --team-id TEAM_ID

# Staple the notarization
xcrun stapler staple codeflow-desktop.dmg
```

### Linux

#### Requirements
- Linux (Ubuntu 20.04+ recommended)
- Build essentials
- Platform-specific dependencies

**Ubuntu/Debian:**
```bash
sudo apt install libwebkit2gtk-4.1-dev \
  build-essential \
  curl \
  wget \
  file \
  libxdo-dev \
  libssl-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev
```

**Fedora:**
```bash
sudo dnf install webkit2gtk4.0-devel \
  openssl-devel \
  curl \
  wget \
  file \
  libappindicator-gtk3-devel \
  librsvg2-devel
```

#### Build Commands
```bash
# Standard build
pnpm run tauri build

# Build specific package types
pnpm run tauri build -- --bundles deb
pnpm run tauri build -- --bundles appimage
```

## Code Signing

### Why Code Signing?

- **Windows**: SmartScreen warning without signature
- **macOS**: Gatekeeper blocks unsigned apps
- **Linux**: Optional, but recommended for trust

### Getting Certificates

**Windows:**
- Purchase code signing certificate from Digicert, Sectigo, etc.
- Use EV certificate to avoid SmartScreen warnings

**macOS:**
- Join Apple Developer Program ($99/year)
- Create Developer ID certificate in Apple Developer Portal

**Linux:**
- Generally not required
- Can use GPG signing for package repositories

### Configuring Tauri for Signing

Edit `tauri.conf.json`:

```json
{
  "bundle": {
    "windows": {
      "certificateThumbprint": "YOUR_CERT_THUMBPRINT",
      "timestampUrl": "http://timestamp.digicert.com"
    },
    "macOS": {
      "signingIdentity": "Developer ID Application: Your Name",
      "entitlements": "entitlements.plist"
    }
  }
}
```

## Distribution

### Direct Download

Host installers on your website or GitHub Releases:

```bash
# Create a new release
gh release create v1.0.0 \
  src-tauri/target/release/bundle/msi/codeflow-desktop.msi \
  src-tauri/target/release/bundle/dmg/codeflow-desktop.dmg \
  src-tauri/target/release/bundle/deb/codeflow-desktop.deb
```

### Windows Store

1. Create Windows Store package:
   ```bash
   pnpm run tauri build -- --bundles appx
   ```

2. Submit to Windows Partner Center

### Mac App Store

1. Build for App Store:
   ```bash
   pnpm run tauri build -- --target mas
   ```

2. Submit via Xcode or Application Loader

### Linux Package Repositories

**Ubuntu PPA:**
```bash
# Build source package
debuild -S

# Upload to Launchpad
dput ppa:your-ppa codeflow-desktop_1.0.0_source.changes
```

**AUR (Arch User Repository):**
Create PKGBUILD and submit to AUR

**Flatpak:**
Create flatpak manifest and submit to Flathub

## Auto-Updates

### Configuring Updates

1. **Install Tauri Update plugin:**
   ```bash
   cd src-tauri
   cargo add tauri-plugin-updater
   ```

2. **Configure in `tauri.conf.json`:**
   ```json
   {
     "plugins": {
       "updater": {
         "active": true,
         "endpoints": [
           "https://your-domain.com/updates/{{target}}/{{current_version}}"
         ],
         "dialog": true,
         "pubkey": "YOUR_PUBLIC_KEY"
       }
     }
   }
   ```

3. **Generate update manifest:**
   ```bash
   pnpm run tauri build
   # Update manifest is generated automatically
   ```

4. **Host update files:**
   - Upload installer to update server
   - Upload signature file (.sig)
   - Create/update JSON manifest

### Update Server Setup

**Example update.json:**
```json
{
  "version": "1.0.1",
  "notes": "Bug fixes and improvements",
  "pub_date": "2025-01-21T10:00:00Z",
  "platforms": {
    "windows-x86_64": {
      "signature": "BASE64_SIGNATURE",
      "url": "https://your-domain.com/releases/codeflow-desktop-1.0.1.msi"
    },
    "darwin-x86_64": {
      "signature": "BASE64_SIGNATURE",
      "url": "https://your-domain.com/releases/codeflow-desktop-1.0.1.dmg"
    },
    "linux-x86_64": {
      "signature": "BASE64_SIGNATURE",
      "url": "https://your-domain.com/releases/codeflow-desktop-1.0.1.AppImage"
    }
  }
}
```

## Release Checklist

### Pre-Release

- [ ] Update version in `package.json`
- [ ] Update version in `src-tauri/Cargo.toml`
- [ ] Update version in `src-tauri/tauri.conf.json`
- [ ] Update CHANGELOG.md
- [ ] Run all tests: `pnpm test && cargo test`
- [ ] Test on all target platforms
- [ ] Update documentation

### Build

- [ ] Clean previous builds: `pnpm run clean`
- [ ] Build for all platforms
- [ ] Verify build artifacts
- [ ] Test installers on clean systems

### Code Signing

- [ ] Sign Windows installer
- [ ] Sign and notarize macOS app
- [ ] Verify signatures

### Distribution

- [ ] Create GitHub release
- [ ] Upload installers
- [ ] Update website download links
- [ ] Update auto-update manifest
- [ ] Announce release (blog, social media)

### Post-Release

- [ ] Monitor error reports
- [ ] Update documentation
- [ ] Tag release in Git: `git tag desktop-v0.2.0-alpha.1`
- [ ] Push tags: `git push --tags`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Release

on:
  push:
    tags:
      - 'desktop-v*'

jobs:
  build:
    strategy:
      matrix:
        platform: [windows-latest, macos-latest, ubuntu-latest]

    runs-on: ${{ matrix.platform }}

    steps:
      - uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'pnpm'

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install dependencies
        run: |
          cd codeflow-desktop
          pnpm install --frozen-lockfile

      - name: Build application
        run: |
          cd codeflow-desktop
          pnpm run tauri build

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: ${{ matrix.platform }}-build
          path: codeflow-desktop/src-tauri/target/release/bundle/

      - name: Create Release
        if: startsWith(github.ref, 'refs/tags/')
        uses: softprops/action-gh-release@v1
        with:
          files: codeflow-desktop/src-tauri/target/release/bundle/**/*
```

## Troubleshooting

### Build Failures

**"Rust compilation failed"**
- Update Rust: `rustup update`
- Clear cargo cache: `cargo clean`

**"Node modules error"**
- Delete `node_modules` and `pnpm-lock.yaml`
- Run `pnpm install` again

**"Tauri CLI not found"**
- Install globally: `pnpm add -g @tauri-apps/cli`
- Or use pnpm exec: `pnpm exec tauri build`

### Code Signing Issues

**Windows SmartScreen warning persists**
- Use EV certificate
- Build reputation over time (100+ downloads)

**macOS notarization fails**
- Check hardened runtime: `codesign --display --verbose codeflow-desktop.app`
- Verify entitlements
- Check Apple Developer account status

## Resources

- [Tauri Building Documentation](https://tauri.app/v2/guides/building/)
- [Tauri Updater Plugin](https://tauri.app/v2/guides/distribution/updater/)
- [Windows Code Signing](https://learn.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools)
- [macOS Notarization](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github)

<!-- markdownlint-enable MD022 MD024 MD031 MD032 MD036 MD040 -->

<#
.SYNOPSIS
Sets up local development environment for all CodeFlow repositories.

.DESCRIPTION
Clones all CodeFlow repositories (if not present), installs dependencies, and sets up development environment.

.PARAMETER ReposPath
Path where repositories should be cloned. Default: parent directory of this script.

.PARAMETER SkipClone
Skip cloning repositories if they already exist.

.EXAMPLE
.\dev-setup.ps1
#>

[CmdletBinding()]
param(
    [string]$ReposPath = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent),
    [switch]$SkipClone
)

$ErrorActionPreference = 'Stop'

$repos = @(
    @{ Name = "codeflow-engine"; Type = "Python"; Setup = "poetry install" },
    @{ Name = "codeflow-desktop"; Type = "Node"; Setup = "pnpm install" },
    @{ Name = "codeflow-vscode-extension"; Type = "Node"; Setup = "pnpm install" },
    @{ Name = "codeflow-website"; Type = "Node"; Setup = "pnpm install" },
    @{ Name = "codeflow-infrastructure"; Type = "IaC"; Setup = "az bicep build --file bicep/codeflow-engine.bicep" },
    @{ Name = "codeflow-azure-setup"; Type = "Scripts"; Setup = "Write-Host 'No dependencies'" },
    @{ Name = "codeflow-orchestration"; Type = "Scripts"; Setup = "Write-Host 'No dependencies'" }
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeFlow Development Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositories path: $ReposPath" -ForegroundColor Yellow
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow
$prereqs = @{
    "Node.js" = "node --version"
    "Python" = "python --version"
    "Poetry" = "poetry --version"
    "Azure CLI" = "az --version"
    "Git" = "git --version"
}

$missing = @()
foreach ($prereq in $prereqs.Keys) {
    try {
        $null = Invoke-Expression $prereqs[$prereq] 2>&1
        Write-Host "  ✓ $prereq" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ $prereq (missing)" -ForegroundColor Red
        $missing += $prereq
    }
}

if ($missing.Count -gt 0) {
    Write-Host ""
    Write-Host "Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
    Write-Host "Please install missing tools before continuing." -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Setup each repository
foreach ($repo in $repos) {
    $repoPath = Join-Path $ReposPath $repo.Name
    
    Write-Host "=== $($repo.Name) ($($repo.Type)) ===" -ForegroundColor Cyan
    
    # Clone if needed
    if (-not (Test-Path $repoPath)) {
        if ($SkipClone) {
            Write-Host "  ⚠ Skipping (not found and SkipClone specified)" -ForegroundColor Yellow
            continue
        }
        Write-Host "  Cloning repository..." -ForegroundColor Gray
        $repoUrl = "https://github.com/JustAGhosT/$($repo.Name).git"
        git clone $repoUrl $repoPath
        if ($LASTEXITCODE -ne 0) {
            Write-Host "  ✗ Failed to clone" -ForegroundColor Red
            continue
        }
        Write-Host "  ✓ Cloned" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Repository exists" -ForegroundColor Green
    }
    
    # Install dependencies
    Push-Location $repoPath
    try {
        Write-Host "  Installing dependencies..." -ForegroundColor Gray
        if ($repo.Type -eq "Python") {
            if (Test-Path "pyproject.toml") {
                poetry install
            } else {
                Write-Host "  ⚠ No pyproject.toml found" -ForegroundColor Yellow
            }
        } elseif ($repo.Type -eq "Node") {
            if (Test-Path "package.json") {
                pnpm install
            } else {
                Write-Host "  ⚠ No package.json found" -ForegroundColor Yellow
            }
        } elseif ($repo.Type -eq "IaC") {
            Write-Host "  Validating Bicep templates..." -ForegroundColor Gray
            Get-ChildItem -Path "bicep" -Filter "*.bicep" -Recurse | ForEach-Object {
                az bicep build --file $_.FullName --no-restore 2>&1 | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "    ✓ $($_.Name)" -ForegroundColor Green
                } else {
                    Write-Host "    ✗ $($_.Name)" -ForegroundColor Red
                }
            }
        } else {
            Write-Host "  ✓ No dependencies to install" -ForegroundColor Green
        }
        Write-Host "  ✓ Setup complete" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ Setup failed: $_" -ForegroundColor Red
    } finally {
        Pop-Location
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Open VS Code workspace: codeflow.code-workspace" -ForegroundColor White
Write-Host "2. Set up local services (optional):" -ForegroundColor White
Write-Host "   cd codeflow-engine && docker-compose up -d" -ForegroundColor Gray
Write-Host "3. Review each repository's README for specific setup instructions" -ForegroundColor White
Write-Host "4. Run tests to verify setup: Use VS Code tasks or run manually" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see:" -ForegroundColor Yellow
Write-Host "- Quick Start: codeflow-engine/docs/deployment/QUICK_START.md" -ForegroundColor Gray
Write-Host "- Contributing: See CONTRIBUTING.md in each repository" -ForegroundColor Gray


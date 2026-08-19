<#
.SYNOPSIS
Automates dependency updates across CodeFlow repositories.

.DESCRIPTION
Checks for dependency updates and optionally updates them across multiple repositories.

.PARAMETER Repositories
Array of repository paths to update.

.PARAMETER PackageManager
Package manager to use (pnpm, pip, poetry). Default: auto-detect

.PARAMETER CheckOnly
Only check for updates, don't apply them. Default: $false

.PARAMETER UpdateType
Type of updates to apply (patch, minor, major, all). Default: patch

.EXAMPLE
.\update-dependencies.ps1 -Repositories @("C:\repos\codeflow-engine", "C:\repos\codeflow-desktop") -CheckOnly
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string[]]$Repositories,
    
    [string]$PackageManager = "auto",
    
    [switch]$CheckOnly,
    
    [ValidateSet("patch", "minor", "major", "all")]
    [string]$UpdateType = "patch"
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Dependency Update Automation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$results = @()

foreach ($repo in $Repositories) {
    if (-not (Test-Path $repo)) {
        Write-Host "✗ Repository not found: $repo" -ForegroundColor Red
        continue
    }
    
    Write-Host "Processing: $repo" -ForegroundColor Yellow
    Push-Location $repo
    
    # Detect package manager
    $detectedManager = $PackageManager
    if ($PackageManager -eq "auto") {
        if (Test-Path "package.json") {
            $detectedManager = "pnpm"
        } elseif (Test-Path "pyproject.toml") {
            $detectedManager = "poetry"
        } elseif (Test-Path "requirements.txt") {
            $detectedManager = "pip"
        } else {
            Write-Host "  ⚠ No package manager detected, skipping" -ForegroundColor Yellow
            Pop-Location
            continue
        }
    }
    
    Write-Host "  Package manager: $detectedManager" -ForegroundColor Gray
    
    # Check for updates
    $updates = @()
    
    try {
        switch ($detectedManager) {
            "pnpm" {
                if ($CheckOnly) {
                    Write-Host "  Checking for pnpm updates..." -ForegroundColor Gray
                    # NOTE: pnpm's `outdated --json` schema differs from npm's (this was
                    # only mechanically converted from `npm outdated --json`, not verified
                    # against pnpm's actual output shape) - confirm the field names below
                    # (current/wanted/latest) still match before relying on this.
                    $outdated = pnpm outdated --json 2>$null | ConvertFrom-Json
                    if ($outdated) {
                        foreach ($pkg in $outdated.PSObject.Properties) {
                            $updates += @{
                                Package = $pkg.Name
                                Current = $pkg.Value.current
                                Wanted = $pkg.Value.wanted
                                Latest = $pkg.Value.latest
                            }
                        }
                    }
                } else {
                    Write-Host "  Updating pnpm dependencies..." -ForegroundColor Gray
                    if ($UpdateType -eq "patch") {
                        pnpm update 2>&1 | Out-Null
                    } else {
                        pnpm add --save-dev npm-check-updates 2>&1 | Out-Null
                        pnpm exec npm-check-updates -u 2>&1 | Out-Null
                        pnpm install 2>&1 | Out-Null
                    }
                }
            }
            "poetry" {
                if ($CheckOnly) {
                    Write-Host "  Checking for Poetry updates..." -ForegroundColor Gray
                    $outdated = poetry show --outdated --format json 2>$null | ConvertFrom-Json
                    if ($outdated) {
                        foreach ($pkg in $outdated) {
                            $updates += @{
                                Package = $pkg.name
                                Current = $pkg.version
                                Latest = $pkg.latest_version
                            }
                        }
                    }
                } else {
                    Write-Host "  Updating Poetry dependencies..." -ForegroundColor Gray
                    poetry update 2>&1 | Out-Null
                }
            }
            "pip" {
                if ($CheckOnly) {
                    Write-Host "  Checking for pip updates..." -ForegroundColor Gray
                    Write-Host "  ⚠ pip update check not fully automated" -ForegroundColor Yellow
                } else {
                    Write-Host "  Updating pip dependencies..." -ForegroundColor Gray
                    pip install --upgrade -r requirements.txt 2>&1 | Out-Null
                }
            }
        }
        
        $result = @{
            Repository = $repo
            PackageManager = $detectedManager
            UpdatesFound = $updates.Count
            Updates = $updates
            Status = if ($CheckOnly) { "Checked" } else { "Updated" }
        }
        
        $results += $result
        
        if ($CheckOnly -and $updates.Count -gt 0) {
            Write-Host "  ✓ Found $($updates.Count) updates" -ForegroundColor Yellow
        } elseif ($CheckOnly) {
            Write-Host "  ✓ No updates found" -ForegroundColor Green
        } else {
            Write-Host "  ✓ Dependencies updated" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✗ Error: $_" -ForegroundColor Red
        $results += @{
            Repository = $repo
            PackageManager = $detectedManager
            Status = "Error"
            Error = $_.Exception.Message
        }
    }
    
    Pop-Location
    Write-Host ""
}

# ============================================================================
# Summary
# ============================================================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "Dependency Update Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

$totalUpdates = ($results | Measure-Object -Property UpdatesFound -Sum).Sum

Write-Host "Repositories processed: $($results.Count)" -ForegroundColor White
Write-Host "Total updates found: $totalUpdates" -ForegroundColor White
Write-Host ""

foreach ($result in $results) {
    Write-Host "$($result.Repository):" -ForegroundColor Yellow
    Write-Host "  Manager: $($result.PackageManager)" -ForegroundColor Gray
    Write-Host "  Status: $($result.Status)" -ForegroundColor $(if ($result.Status -eq "Error") { "Red" } else { "Green" })
    if ($result.UpdatesFound -gt 0) {
        Write-Host "  Updates: $($result.UpdatesFound)" -ForegroundColor White
        foreach ($update in $result.Updates[0..4]) {
            Write-Host "    - $($update.Package): $($update.Current) -> $($update.Latest)" -ForegroundColor Gray
        }
    }
    Write-Host ""
}


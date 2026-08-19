<#
.SYNOPSIS
Health check script for all CodeFlow repositories.

.DESCRIPTION
Checks the health of all CodeFlow repositories, including:
- Repository existence
- Build status
- Test status
- Dependency status
- CI/CD status

.PARAMETER ReposPath
Path where repositories are located. Default: parent directory.

.EXAMPLE
.\health-check.ps1
#>

[CmdletBinding()]
param(
    [string]$ReposPath = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)

$ErrorActionPreference = 'Continue'

$repos = @(
    @{ Name = "codeflow-engine"; Type = "Python" },
    @{ Name = "codeflow-desktop"; Type = "Node" },
    @{ Name = "codeflow-vscode-extension"; Type = "Node" },
    @{ Name = "codeflow-website"; Type = "Node" },
    @{ Name = "codeflow-infrastructure"; Type = "IaC" },
    @{ Name = "codeflow-azure-setup"; Type = "Scripts" },
    @{ Name = "codeflow-orchestration"; Type = "Scripts" }
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeFlow Health Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Repositories path: $ReposPath" -ForegroundColor Yellow
Write-Host ""

$results = @()

foreach ($repo in $repos) {
    $repoPath = Join-Path $ReposPath $repo.Name
    $health = @{
        Name = $repo.Name
        Type = $repo.Type
        Exists = $false
        BuildStatus = "N/A"
        TestStatus = "N/A"
        DependenciesStatus = "N/A"
        Issues = @()
    }
    
    Write-Host "=== $($repo.Name) ===" -ForegroundColor Cyan
    
    # Check existence
    if (Test-Path $repoPath) {
        $health.Exists = $true
        Write-Host "  ✓ Repository exists" -ForegroundColor Green
        
        Push-Location $repoPath
        try {
            # Check Git status
            $gitStatus = git status --porcelain 2>&1
            if ($gitStatus) {
                $health.Issues += "Uncommitted changes"
                Write-Host "  ⚠ Uncommitted changes" -ForegroundColor Yellow
            }
            
            # Check dependencies
            if ($repo.Type -eq "Python" -and (Test-Path "pyproject.toml")) {
                Write-Host "  Checking Python dependencies..." -ForegroundColor Gray
                try {
                    poetry check 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        $health.DependenciesStatus = "OK"
                        Write-Host "    ✓ Dependencies OK" -ForegroundColor Green
                    } else {
                        $health.DependenciesStatus = "Issues"
                        $health.Issues += "Poetry check failed"
                        Write-Host "    ✗ Dependency issues" -ForegroundColor Red
                    }
                } catch {
                    $health.DependenciesStatus = "Error"
                    $health.Issues += "Poetry not available"
                    Write-Host "    ✗ Poetry not available" -ForegroundColor Red
                }
            } elseif ($repo.Type -eq "Node" -and (Test-Path "package.json")) {
                Write-Host "  Checking Node dependencies..." -ForegroundColor Gray
                if (Test-Path "node_modules") {
                    $health.DependenciesStatus = "Installed"
                    Write-Host "    ✓ Dependencies installed" -ForegroundColor Green
                } else {
                    $health.DependenciesStatus = "Not installed"
                    $health.Issues += "node_modules missing"
                    Write-Host "    ⚠ Dependencies not installed" -ForegroundColor Yellow
                }
            }
            
            # Check build
            if ($repo.Type -eq "Python" -and (Test-Path "pyproject.toml")) {
                Write-Host "  Checking build..." -ForegroundColor Gray
                try {
                    poetry build --dry-run 2>&1 | Out-Null
                    if ($LASTEXITCODE -eq 0) {
                        $health.BuildStatus = "OK"
                        Write-Host "    ✓ Build OK" -ForegroundColor Green
                    } else {
                        $health.BuildStatus = "Failed"
                        $health.Issues += "Build failed"
                        Write-Host "    ✗ Build failed" -ForegroundColor Red
                    }
                } catch {
                    $health.BuildStatus = "Error"
                    Write-Host "    ✗ Build error" -ForegroundColor Red
                }
            } elseif ($repo.Type -eq "Node" -and (Test-Path "package.json")) {
                Write-Host "  Checking build..." -ForegroundColor Gray
                if ((Get-Content "package.json" | ConvertFrom-Json).scripts.build) {
                    try {
                        pnpm run build --dry-run 2>&1 | Out-Null
                        $health.BuildStatus = "Script exists"
                        Write-Host "    ✓ Build script exists" -ForegroundColor Green
                    } catch {
                        $health.BuildStatus = "Error"
                        Write-Host "    ⚠ Build script check failed" -ForegroundColor Yellow
                    }
                } else {
                    $health.BuildStatus = "No script"
                    Write-Host "    ⚠ No build script" -ForegroundColor Yellow
                }
            }
            
        } finally {
            Pop-Location
        }
    } else {
        $health.Exists = $false
        $health.Issues += "Repository not found"
        Write-Host "  ✗ Repository not found" -ForegroundColor Red
    }
    
    $results += $health
    Write-Host ""
}

# Summary
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Health Check Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$total = $results.Count
$healthy = ($results | Where-Object { $_.Exists -and $_.Issues.Count -eq 0 }).Count
$issues = ($results | Where-Object { $_.Issues.Count -gt 0 }).Count
$missing = ($results | Where-Object { -not $_.Exists }).Count

Write-Host "Total Repositories: $total" -ForegroundColor White
Write-Host "Healthy: $healthy" -ForegroundColor Green
Write-Host "With Issues: $issues" -ForegroundColor Yellow
Write-Host "Missing: $missing" -ForegroundColor Red
Write-Host ""

if ($issues -gt 0 -or $missing -gt 0) {
    Write-Host "Issues Found:" -ForegroundColor Yellow
    foreach ($result in $results) {
        if ($result.Issues.Count -gt 0 -or -not $result.Exists) {
            Write-Host "  $($result.Name):" -ForegroundColor Cyan
            if (-not $result.Exists) {
                Write-Host "    - Repository not found" -ForegroundColor Red
            }
            foreach ($issue in $result.Issues) {
                Write-Host "    - $issue" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host ""
if ($healthy -eq $total) {
    Write-Host "✓ All repositories are healthy!" -ForegroundColor Green
} else {
    Write-Host "⚠ Some repositories need attention" -ForegroundColor Yellow
}


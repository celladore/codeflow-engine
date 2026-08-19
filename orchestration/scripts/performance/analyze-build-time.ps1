<#
.SYNOPSIS
Analyzes build times for projects.

.DESCRIPTION
Measures and analyzes build times to identify optimization opportunities.

.PARAMETER ProjectPath
Path to the project directory.

.PARAMETER BuildCommand
Build command to execute. Default: "pnpm run build"

.PARAMETER Iterations
Number of build iterations to run. Default: 3

.EXAMPLE
.\analyze-build-time.ps1 -ProjectPath "C:\repos\codeflow-desktop" -Iterations 5
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,
    
    [string]$BuildCommand = "pnpm run build",
    
    [int]$Iterations = 3
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Build Time Analysis" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $ProjectPath)) {
    Write-Host "✗ Project path not found: $ProjectPath" -ForegroundColor Red
    exit 1
}

Push-Location $ProjectPath

# ============================================================================
# Warm-up Build
# ============================================================================

Write-Host "Running warm-up build..." -ForegroundColor Yellow
try {
    Invoke-Expression $BuildCommand 2>&1 | Out-Null
    Write-Host "  ✓ Warm-up complete" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Warm-up build failed" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host ""

# ============================================================================
# Measure Build Times
# ============================================================================

Write-Host "Measuring build times ($Iterations iterations)..." -ForegroundColor Yellow

$buildTimes = @()

for ($i = 1; $i -le $Iterations; $i++) {
    Write-Host "  Build $i of $Iterations..." -ForegroundColor Gray
    
    # Clean build directory if it exists
    $buildDirs = @("dist", "build", "out", ".next")
    foreach ($dir in $buildDirs) {
        if (Test-Path $dir) {
            Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    
    # Measure build time
    $startTime = Get-Date
    try {
        Invoke-Expression $BuildCommand 2>&1 | Out-Null
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        $buildTimes += $duration
        Write-Host "    ✓ Completed in $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
    } catch {
        Write-Host "    ✗ Build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
}

Pop-Location

Write-Host ""

# ============================================================================
# Analyze Results
# ============================================================================

Write-Host "Analyzing results..." -ForegroundColor Yellow

$avgTime = ($buildTimes | Measure-Object -Average).Average
$minTime = ($buildTimes | Measure-Object -Minimum).Minimum
$maxTime = ($buildTimes | Measure-Object -Maximum).Maximum
$totalTime = ($buildTimes | Measure-Object -Sum).Sum

Write-Host "  ✓ Analysis complete" -ForegroundColor Green
Write-Host ""

# ============================================================================
# Generate Recommendations
# ============================================================================

$recommendations = @()

if ($avgTime -gt 60) {
    $recommendations += "Build time is slow ($([math]::Round($avgTime, 2))s) - consider optimization"
}

if (($maxTime - $minTime) / $avgTime -gt 0.2) {
    $recommendations += "Build time variance is high - check for non-deterministic builds"
}

if ($avgTime -gt 120) {
    $recommendations += "Consider parallelizing build steps"
    $recommendations += "Consider incremental builds"
    $recommendations += "Review and optimize dependencies"
}

# ============================================================================
# Display Results
# ============================================================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "Build Time Analysis Results" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Iterations: $Iterations" -ForegroundColor White
Write-Host "Average Time: $([math]::Round($avgTime, 2)) seconds" -ForegroundColor White
Write-Host "Minimum Time: $([math]::Round($minTime, 2)) seconds" -ForegroundColor White
Write-Host "Maximum Time: $([math]::Round($maxTime, 2)) seconds" -ForegroundColor White
Write-Host "Total Time: $([math]::Round($totalTime, 2)) seconds" -ForegroundColor White
Write-Host ""

if ($recommendations.Count -gt 0) {
    Write-Host "Recommendations:" -ForegroundColor Yellow
    foreach ($rec in $recommendations) {
        Write-Host "  • $rec" -ForegroundColor Gray
    }
    Write-Host ""
}


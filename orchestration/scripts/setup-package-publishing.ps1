<#
.SYNOPSIS
Sets up package publishing for CodeFlow utility packages.

.DESCRIPTION
Guides through the setup of GitHub secrets and publishing configuration for package publishing.

.PARAMETER PackageType
Type of package (python, typescript, both). Default: both

.EXAMPLE
.\setup-package-publishing.ps1 -PackageType python
#>

[CmdletBinding()]
param(
    [ValidateSet("python", "typescript", "both")]
    [string]$PackageType = "both"
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Package Publishing Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# Python Package Setup
# ============================================================================

if ($PackageType -in @("python", "both")) {
    Write-Host "Python Package (codeflow-utils-python)" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "1. Create PyPI Account:" -ForegroundColor Cyan
    Write-Host "   - Go to: https://pypi.org/account/register/" -ForegroundColor Gray
    Write-Host "   - Create an account" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "2. Generate API Token:" -ForegroundColor Cyan
    Write-Host "   - Go to: https://pypi.org/manage/account/token/" -ForegroundColor Gray
    Write-Host "   - Click 'Add API token'" -ForegroundColor Gray
    Write-Host "   - Name: 'codeflow-utils-python'" -ForegroundColor Gray
    Write-Host "   - Scope: 'Entire account' or 'Project: codeflow-utils-python'" -ForegroundColor Gray
    Write-Host "   - Copy the token (you won't see it again!)" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "3. Add GitHub Secret:" -ForegroundColor Cyan
    Write-Host "   - Go to repository settings" -ForegroundColor Gray
    Write-Host "   - Navigate to: Settings > Secrets and variables > Actions" -ForegroundColor Gray
    Write-Host "   - Click 'New repository secret'" -ForegroundColor Gray
    Write-Host "   - Name: PYPI_API_TOKEN" -ForegroundColor Gray
    Write-Host "   - Value: [Your PyPI API token]" -ForegroundColor Gray
    Write-Host "   - Click 'Add secret'" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "4. Test Publishing (TestPyPI):" -ForegroundColor Cyan
    Write-Host "   cd packages/codeflow-utils-python" -ForegroundColor Gray
    Write-Host "   python -m pip install --upgrade build twine" -ForegroundColor Gray
    Write-Host "   python -m build" -ForegroundColor Gray
    Write-Host "   twine upload --repository testpypi dist/*" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "5. Publish to PyPI:" -ForegroundColor Cyan
    Write-Host "   - Create a GitHub release" -ForegroundColor Gray
    Write-Host "   - Tag version (e.g., v0.1.0)" -ForegroundColor Gray
    Write-Host "   - Publishing workflow will run automatically" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# TypeScript Package Setup
# ============================================================================

if ($PackageType -in @("typescript", "both")) {
    Write-Host "TypeScript Package (@codeflow/utils)" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "1. Create npm Account:" -ForegroundColor Cyan
    Write-Host "   - Go to: https://www.npmjs.com/signup" -ForegroundColor Gray
    Write-Host "   - Create an account" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "2. Generate Access Token:" -ForegroundColor Cyan
    Write-Host "   - Go to: https://www.npmjs.com/settings/[username]/tokens" -ForegroundColor Gray
    Write-Host "   - Click 'Generate New Token'" -ForegroundColor Gray
    Write-Host "   - Token type: 'Automation'" -ForegroundColor Gray
    Write-Host "   - Copy the token (you won't see it again!)" -ForegroundColor Yellow
    Write-Host ""
    
    Write-Host "3. Add GitHub Secret:" -ForegroundColor Cyan
    Write-Host "   - Go to repository settings" -ForegroundColor Gray
    Write-Host "   - Navigate to: Settings > Secrets and variables > Actions" -ForegroundColor Gray
    Write-Host "   - Click 'New repository secret'" -ForegroundColor Gray
    Write-Host "   - Name: NPM_TOKEN" -ForegroundColor Gray
    Write-Host "   - Value: [Your npm access token]" -ForegroundColor Gray
    Write-Host "   - Click 'Add secret'" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "4. Test Publishing:" -ForegroundColor Cyan
    Write-Host "   cd packages/@codeflow/utils" -ForegroundColor Gray
    Write-Host "   pnpm install" -ForegroundColor Gray
    Write-Host "   pnpm run build" -ForegroundColor Gray
    Write-Host "   pnpm pack --dry-run" -ForegroundColor Gray
    Write-Host ""
    
    Write-Host "5. Publish to npm:" -ForegroundColor Cyan
    Write-Host "   - Create a GitHub release" -ForegroundColor Gray
    Write-Host "   - Tag version (e.g., v0.1.0)" -ForegroundColor Gray
    Write-Host "   - Publishing workflow will run automatically" -ForegroundColor Gray
    Write-Host ""
}

# ============================================================================
# Verification
# ============================================================================

Write-Host "========================================" -ForegroundColor Green
Write-Host "Setup Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Follow the steps above to set up accounts and tokens" -ForegroundColor White
Write-Host "2. Add GitHub secrets as described" -ForegroundColor White
Write-Host "3. Test publishing to test registries" -ForegroundColor White
Write-Host "4. Create GitHub releases to trigger publishing" -ForegroundColor White
Write-Host ""
Write-Host "For detailed instructions, see:" -ForegroundColor Yellow
Write-Host "  docs/PACKAGE_PUBLISHING_GUIDE.md" -ForegroundColor Gray
Write-Host ""


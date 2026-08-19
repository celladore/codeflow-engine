<#
.SYNOPSIS
Deploys the entire CodeFlow stack to Azure.

.DESCRIPTION
Orchestrates deployment of all CodeFlow components:
1. Azure infrastructure bootstrap (codeflow-azure-setup)
2. Core infrastructure (codeflow-infrastructure)
3. CodeFlow Engine (codeflow-engine)
4. Website (codeflow-website)
5. Desktop App (codeflow-desktop)
6. VS Code Extension (codeflow-vscode-extension)

.PARAMETER OrgCode
Short org code (e.g. nl, tws, mys).

.PARAMETER Environment
Environment name (dev, test, uat, prod).

.PARAMETER Project
Project name (e.g. codeflow).

.PARAMETER RegionShort
Short region code used in names (e.g. san, euw, wus).

.PARAMETER Location
Azure location (e.g. southafricanorth, westeurope).

.PARAMETER SubscriptionId
Azure subscription GUID.

.PARAMETER CreateKeyVault
Switch to also create a Key Vault in the resource group.

.PARAMETER SkipComponents
Array of component names to skip during deployment.

.EXAMPLE
.\scripts\deploy-all.ps1 `
  -OrgCode nl `
  -Environment dev `
  -Project codeflow `
  -RegionShort san `
  -Location southafricanorth `
  -SubscriptionId 00000000-0000-0000-0000-000000000000 `
  -CreateKeyVault
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$OrgCode,
    
    [Parameter(Mandatory = $true)]
    [string]$Environment,
    
    [Parameter(Mandatory = $true)]
    [string]$Project,
    
    [Parameter(Mandatory = $true)]
    [string]$RegionShort,
    
    [Parameter(Mandatory = $true)]
    [string]$Location,
    
    [Parameter(Mandatory = $true)]
    [string]$SubscriptionId,
    
    [switch]$CreateKeyVault,
    
    [string[]]$SkipComponents = @()
)

$ErrorActionPreference = 'Stop'

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "CodeFlow Stack Deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

Write-Host "Configuration:" -ForegroundColor Yellow
Write-Host "  Org Code: $OrgCode" -ForegroundColor White
Write-Host "  Environment: $Environment" -ForegroundColor White
Write-Host "  Project: $Project" -ForegroundColor White
Write-Host "  Region: $RegionShort" -ForegroundColor White
Write-Host "  Location: $Location" -ForegroundColor White
Write-Host "  Subscription: $SubscriptionId" -ForegroundColor White
Write-Host ""

# Step 1: Azure Infrastructure Bootstrap
if ($SkipComponents -notcontains "azure-setup") {
    Write-Host "Step 1: Deploying Azure Infrastructure Bootstrap..." -ForegroundColor Green
    $AzureSetupPath = Join-Path $RepoRoot ".." "codeflow-azure-setup"
    
    if (Test-Path $AzureSetupPath) {
        Push-Location $AzureSetupPath
        
        # Use absolute path for output JSON to avoid path issues
        $OutputJson = Join-Path $AzureSetupPath "az-env-$Environment-$Project.json"
        $Params = @{
            OrgCode = $OrgCode
            Environment = $Environment
            Project = $Project
            RegionShort = $RegionShort
            Location = $Location
            SubscriptionId = $SubscriptionId
            OutputJsonPath = $OutputJson
        }
        
        if ($CreateKeyVault) {
            $Params['CreateKeyVault'] = $true
        }
        
        Write-Host "  Running New-AzRepoEnvironment.ps1..." -ForegroundColor Gray
        & ".\scripts\New-AzRepoEnvironment.ps1" @Params
        
        # Check if file was created (could be in current directory or specified path)
        $JsonFile = $OutputJson
        if (-not (Test-Path $JsonFile)) {
            # Try relative path in case script changed directory
            $JsonFile = "az-env-$Environment-$Project.json"
        }
        if (-not (Test-Path $JsonFile)) {
            # Try in parent directory (codeflow) as fallback
            $JsonFile = Join-Path (Split-Path (Split-Path $AzureSetupPath -Parent) -Parent) "codeflow" "az-env-$Environment-$Project.json"
        }
        
        if (Test-Path $JsonFile) {
            Write-Host "  âœ“ Azure infrastructure created" -ForegroundColor Green
            Write-Host "  âœ“ Environment summary: $JsonFile" -ForegroundColor Gray
            # Store path for use in next steps
            $script:AzureEnvJson = $JsonFile
        } else {
            Write-Host "  âš  JSON file not found, but script may have succeeded" -ForegroundColor Yellow
            Write-Host "  Check Azure Portal to verify resources were created" -ForegroundColor Gray
            Write-Host "  Continuing with next steps..." -ForegroundColor Gray
        }
        
        # Verify resources were actually created by checking resource group
        $ResourceGroup = "$OrgCode-$Environment-$Project-rg-$RegionShort"
        Write-Host "  Verifying resource group: $ResourceGroup" -ForegroundColor Gray
        $rgExists = az group show --name $ResourceGroup --query "name" --output tsv 2>$null
        if ($rgExists) {
            Write-Host "  âœ“ Resource group exists, continuing..." -ForegroundColor Green
        } else {
            Write-Host "  âœ— Resource group not found, deployment may have failed" -ForegroundColor Red
            throw "Azure infrastructure deployment failed - resource group not found"
        }
        
        Pop-Location
    } else {
        Write-Host "  âš  codeflow-azure-setup not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 2: Core Infrastructure
if ($SkipComponents -notcontains "infrastructure") {
    Write-Host "Step 2: Deploying Core Infrastructure..." -ForegroundColor Green
    $InfraPath = Join-Path $RepoRoot ".." "codeflow-infrastructure"
    
    if (Test-Path $InfraPath) {
        Push-Location (Join-Path $InfraPath "bicep")
        
        $ResourceGroup = "$OrgCode-$Environment-$Project-rg-$RegionShort"
        
        Write-Host "  Deploying to resource group: $ResourceGroup" -ForegroundColor Gray
        
        & ".\deploy-codeflow-engine.sh" $Environment $RegionShort $Location $Location "" "" $OrgCode $Project
        
        Pop-Location
        Write-Host "  âœ“ Core infrastructure deployed" -ForegroundColor Green
    } else {
        Write-Host "  âš  codeflow-infrastructure not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 3: CodeFlow Engine
if ($SkipComponents -notcontains "engine") {
    Write-Host "Step 3: Building and Deploying CodeFlow Engine..." -ForegroundColor Green
    $EnginePath = Join-Path $RepoRoot ".." "codeflow-engine"
    
    if (Test-Path $EnginePath) {
        Write-Host "  âš  Engine deployment requires container image build" -ForegroundColor Yellow
        Write-Host "  See: codeflow-engine/.github/workflows/deploy-codeflow-engine.yml" -ForegroundColor Gray
    } else {
        Write-Host "  âš  codeflow-engine not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 4: Website
if ($SkipComponents -notcontains "website") {
    Write-Host "Step 4: Building Website..." -ForegroundColor Green
    $WebsitePath = Join-Path $RepoRoot ".." "codeflow-website"
    
    if (Test-Path $WebsitePath) {
        Push-Location $WebsitePath
        
        Write-Host "  Building Next.js application..." -ForegroundColor Gray
        pnpm run build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  âœ“ Website built successfully" -ForegroundColor Green
        } else {
            Write-Host "  âœ— Website build failed" -ForegroundColor Red
        }
        
        Pop-Location
    } else {
        Write-Host "  âš  codeflow-website not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 5: Desktop App
if ($SkipComponents -notcontains "desktop") {
    Write-Host "Step 5: Building Desktop App..." -ForegroundColor Green
    $DesktopPath = Join-Path $RepoRoot ".." "codeflow-desktop"
    
    if (Test-Path $DesktopPath) {
        Push-Location $DesktopPath
        
        Write-Host "  Building Tauri application..." -ForegroundColor Gray
        pnpm run build
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  âœ“ Desktop app built successfully" -ForegroundColor Green
        } else {
            Write-Host "  âœ— Desktop app build failed" -ForegroundColor Red
        }
        
        Pop-Location
    } else {
        Write-Host "  âš  codeflow-desktop not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

# Step 6: VS Code Extension
if ($SkipComponents -notcontains "vscode-extension") {
    Write-Host "Step 6: Building VS Code Extension..." -ForegroundColor Green
    $ExtensionPath = Join-Path $RepoRoot ".." "codeflow-vscode-extension"
    
    if (Test-Path $ExtensionPath) {
        Push-Location $ExtensionPath
        
        Write-Host "  Compiling TypeScript..." -ForegroundColor Gray
        pnpm run compile
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  âœ“ Extension compiled successfully" -ForegroundColor Green
        } else {
            Write-Host "  âœ— Extension compilation failed" -ForegroundColor Red
        }
        
        Pop-Location
    } else {
        Write-Host "  âš  codeflow-vscode-extension not found, skipping..." -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Verify all components are running" -ForegroundColor White
Write-Host "  2. Check Azure Portal for resource status" -ForegroundColor White
Write-Host "  3. Test each component individually" -ForegroundColor White
Write-Host ""


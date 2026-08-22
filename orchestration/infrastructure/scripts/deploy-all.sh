#!/bin/bash
# Deploys the entire CodeFlow stack to Azure.
#
# Usage:
#   ./scripts/deploy-all.sh \
#     --org-code nl \
#     --environment dev \
#     --project codeflow \
#     --region-short san \
#     --location southafricanorth \
#     --subscription-id <subscription-id> \
#     [--create-key-vault] \
#     [--skip-components component1,component2]

set -e

# Default values
ORG_CODE=""
ENVIRONMENT=""
PROJECT=""
REGION_SHORT=""
LOCATION=""
SUBSCRIPTION_ID=""
CREATE_KEY_VAULT=false
SKIP_COMPONENTS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --org-code)
      ORG_CODE="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --project)
      PROJECT="$2"
      shift 2
      ;;
    --region-short)
      REGION_SHORT="$2"
      shift 2
      ;;
    --location)
      LOCATION="$2"
      shift 2
      ;;
    --subscription-id)
      SUBSCRIPTION_ID="$2"
      shift 2
      ;;
    --create-key-vault)
      CREATE_KEY_VAULT=true
      shift
      ;;
    --skip-components)
      SKIP_COMPONENTS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Validate required parameters
if [[ -z "$ORG_CODE" || -z "$ENVIRONMENT" || -z "$PROJECT" || -z "$REGION_SHORT" || -z "$LOCATION" || -z "$SUBSCRIPTION_ID" ]]; then
  echo "Error: Missing required parameters"
  echo "Usage: $0 --org-code <code> --environment <env> --project <project> --region-short <region> --location <location> --subscription-id <id>"
  exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "========================================"
echo "CodeFlow Stack Deployment"
echo "========================================"
echo ""
echo "Configuration:"
echo "  Org Code: $ORG_CODE"
echo "  Environment: $ENVIRONMENT"
echo "  Project: $PROJECT"
echo "  Region: $REGION_SHORT"
echo "  Location: $LOCATION"
echo "  Subscription: $SUBSCRIPTION_ID"
echo ""

# Helper function to check if component should be skipped
should_skip() {
  local component=$1
  if [[ -n "$SKIP_COMPONENTS" ]]; then
    IFS=',' read -ra SKIP_ARRAY <<< "$SKIP_COMPONENTS"
    for skip in "${SKIP_ARRAY[@]}"; do
      if [[ "$skip" == "$component" ]]; then
        return 0
      fi
    done
  fi
  return 1
}

# Step 1: Azure Infrastructure Bootstrap
if ! should_skip "azure-setup"; then
  echo "Step 1: Deploying Azure Infrastructure Bootstrap..."
  AZURE_SETUP_PATH="$REPO_ROOT/../codeflow-azure-setup"
  
  if [[ -d "$AZURE_SETUP_PATH" ]]; then
    cd "$AZURE_SETUP_PATH"
    
    OUTPUT_JSON="az-env-$ENVIRONMENT-$PROJECT.json"
    
    if [[ "$CREATE_KEY_VAULT" == "true" ]]; then
      ./scripts/New-AzRepoEnvironment.ps1 \
        -OrgCode "$ORG_CODE" \
        -Environment "$ENVIRONMENT" \
        -Project "$PROJECT" \
        -RegionShort "$REGION_SHORT" \
        -Location "$LOCATION" \
        -SubscriptionId "$SUBSCRIPTION_ID" \
        -CreateKeyVault \
        -OutputJsonPath "$OUTPUT_JSON"
    else
      ./scripts/New-AzRepoEnvironment.ps1 \
        -OrgCode "$ORG_CODE" \
        -Environment "$ENVIRONMENT" \
        -Project "$PROJECT" \
        -RegionShort "$REGION_SHORT" \
        -Location "$LOCATION" \
        -SubscriptionId "$SUBSCRIPTION_ID" \
        -OutputJsonPath "$OUTPUT_JSON"
    fi
    
    if [[ -f "$OUTPUT_JSON" ]]; then
      echo "  âœ“ Azure infrastructure created"
      echo "  âœ“ Environment summary: $OUTPUT_JSON"
    else
      echo "  âœ— Failed to create Azure infrastructure"
      exit 1
    fi
  else
    echo "  âš  codeflow-azure-setup not found, skipping..."
  fi
  echo ""
fi

# Step 2: Core Infrastructure
if ! should_skip "infrastructure"; then
  echo "Step 2: Deploying Core Infrastructure..."
  INFRA_PATH="$REPO_ROOT/../codeflow-infrastructure"
  
  if [[ -d "$INFRA_PATH" ]]; then
    cd "$INFRA_PATH/bicep"
    
    RESOURCE_GROUP="$ORG_CODE-$ENVIRONMENT-$PROJECT-rg-$REGION_SHORT"
    
    echo "  Deploying to resource group: $RESOURCE_GROUP"
    
    ./deploy-codeflow-engine.sh "$ENVIRONMENT" "$REGION_SHORT" "$LOCATION" "$LOCATION" "" "" "$ORG_CODE" "$PROJECT"
    
    echo "  âœ“ Core infrastructure deployed"
  else
    echo "  âš  codeflow-infrastructure not found, skipping..."
  fi
  echo ""
fi

# Step 3: CodeFlow Engine
if ! should_skip "engine"; then
  echo "Step 3: Building and Deploying CodeFlow Engine..."
  ENGINE_PATH="$REPO_ROOT/../codeflow-engine"
  
  if [[ -d "$ENGINE_PATH" ]]; then
    echo "  âš  Engine deployment requires container image build"
    echo "  See: codeflow-engine/.github/workflows/deploy-codeflow-engine.yml"
  else
    echo "  âš  codeflow-engine not found, skipping..."
  fi
  echo ""
fi

# Step 4: Website
if ! should_skip "website"; then
  echo "Step 4: Building Website..."
  WEBSITE_PATH="$REPO_ROOT/../codeflow-website"
  
  if [[ -d "$WEBSITE_PATH" ]]; then
    cd "$WEBSITE_PATH"
    
    echo "  Building Next.js application..."
    pnpm run build
    
    if [[ $? -eq 0 ]]; then
      echo "  âœ“ Website built successfully"
    else
      echo "  âœ— Website build failed"
    fi
  else
    echo "  âš  codeflow-website not found, skipping..."
  fi
  echo ""
fi

# Step 5: Desktop App
if ! should_skip "desktop"; then
  echo "Step 5: Building Desktop App..."
  DESKTOP_PATH="$REPO_ROOT/../codeflow-desktop"
  
  if [[ -d "$DESKTOP_PATH" ]]; then
    cd "$DESKTOP_PATH"
    
    echo "  Building Tauri application..."
    pnpm run build
    
    if [[ $? -eq 0 ]]; then
      echo "  âœ“ Desktop app built successfully"
    else
      echo "  âœ— Desktop app build failed"
    fi
  else
    echo "  âš  codeflow-desktop not found, skipping..."
  fi
  echo ""
fi

# Step 6: VS Code Extension
if ! should_skip "vscode-extension"; then
  echo "Step 6: Building VS Code Extension..."
  EXTENSION_PATH="$REPO_ROOT/../codeflow-vscode-extension"
  
  if [[ -d "$EXTENSION_PATH" ]]; then
    cd "$EXTENSION_PATH"
    
    echo "  Compiling TypeScript..."
    pnpm run compile
    
    if [[ $? -eq 0 ]]; then
      echo "  âœ“ Extension compiled successfully"
    else
      echo "  âœ— Extension compilation failed"
    fi
  else
    echo "  âš  codeflow-vscode-extension not found, skipping..."
  fi
  echo ""
fi

echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Verify all components are running"
echo "  2. Check Azure Portal for resource status"
echo "  3. Test each component individually"
echo ""


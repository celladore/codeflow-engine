#!/bin/bash
# Sets up local development environment for all CodeFlow repositories

set -e

REPOS_PATH="${1:-$(dirname $(dirname $(dirname $(realpath "$0"))))}"
SKIP_CLONE="${2:-false}"

repos=(
    "codeflow-engine:Python:poetry install"
    "codeflow-desktop:Node:pnpm install"
    "codeflow-vscode-extension:Node:pnpm install"
    "codeflow-website:Node:pnpm install"
    "codeflow-infrastructure:IaC:az bicep build --file bicep/codeflow-engine.bicep"
    "codeflow-azure-setup:Scripts:echo 'No dependencies'"
    "codeflow-orchestration:Scripts:echo 'No dependencies'"
)

echo "========================================"
echo "CodeFlow Development Environment Setup"
echo "========================================"
echo ""
echo "Repositories path: $REPOS_PATH"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
check_prereq() {
    if command -v "$1" &> /dev/null; then
        echo "  ✓ $2"
        return 0
    else
        echo "  ✗ $2 (missing)"
        return 1
    fi
}

missing=0
check_prereq node "Node.js" || missing=1
check_prereq python3 "Python" || missing=1
check_prereq poetry "Poetry" || missing=1
check_prereq az "Azure CLI" || missing=1
check_prereq git "Git" || missing=1

if [ $missing -eq 1 ]; then
    echo ""
    echo "Missing prerequisites. Please install missing tools before continuing."
    exit 1
fi

echo ""

# Setup each repository
for repo_info in "${repos[@]}"; do
    IFS=':' read -r repo_name repo_type setup_cmd <<< "$repo_info"
    repo_path="$REPOS_PATH/$repo_name"
    
    echo "=== $repo_name ($repo_type) ==="
    
    # Clone if needed
    if [ ! -d "$repo_path" ]; then
        if [ "$SKIP_CLONE" = "true" ]; then
            echo "  ⚠ Skipping (not found and SKIP_CLONE specified)"
            continue
        fi
        echo "  Cloning repository..."
        repo_url="https://github.com/JustAGhosT/$repo_name.git"
        git clone "$repo_url" "$repo_path"
        echo "  ✓ Cloned"
    else
        echo "  ✓ Repository exists"
    fi
    
    # Install dependencies
    cd "$repo_path"
    echo "  Installing dependencies..."
    
    case "$repo_type" in
        Python)
            if [ -f "pyproject.toml" ]; then
                poetry install
            else
                echo "  ⚠ No pyproject.toml found"
            fi
            ;;
        Node)
            if [ -f "package.json" ]; then
                pnpm install
            else
                echo "  ⚠ No package.json found"
            fi
            ;;
        IaC)
            echo "  Validating Bicep templates..."
            find bicep -name "*.bicep" -type f | while read -r bicep_file; do
                if az bicep build --file "$bicep_file" --no-restore &> /dev/null; then
                    echo "    ✓ $(basename "$bicep_file")"
                else
                    echo "    ✗ $(basename "$bicep_file")"
                fi
            done
            ;;
        *)
            echo "  ✓ No dependencies to install"
            ;;
    esac
    
    echo "  ✓ Setup complete"
    echo ""
done

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Open VS Code workspace: codeflow.code-workspace"
echo "2. Set up local services (optional):"
echo "   cd codeflow-engine && docker-compose up -d"
echo "3. Review each repository's README for specific setup instructions"
echo "4. Run tests to verify setup: Use VS Code tasks or run manually"
echo ""
echo "For more information, see:"
echo "- Quick Start: codeflow-engine/docs/deployment/QUICK_START.md"
echo "- Contributing: See CONTRIBUTING.md in each repository"


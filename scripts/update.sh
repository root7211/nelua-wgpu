#!/bin/bash
# update.sh - Full automated update pipeline
#
# This script performs a complete update cycle:
#   1. Fetch latest headers from upstream
#   2. Regenerate Nelua bindings via nelua-decl
#   3. Regenerate macro constants
#   4. Run validation tests
#   5. Show a diff summary of changes
#
# Usage:
#   ./scripts/update.sh              # update to latest
#   ./scripts/update.sh --tag v27.0.4.0  # update to specific version
#   ./scripts/update.sh --skip-tests # skip validation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

SKIP_TESTS=false
TAG_ARGS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag)
            TAG_ARGS="--tag $2"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--tag <version>] [--skip-tests]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "============================================"
echo "  nelua-wgpu Automated Update Pipeline"
echo "============================================"
echo ""

# Step 1: Fetch headers
echo "[1/5] Fetching latest headers..."
bash "$SCRIPT_DIR/fetch_headers.sh" $TAG_ARGS
echo ""

# Step 2: Generate macro constants (always works, no GCC plugin needed)
echo "[2/5] Generating macro constants..."
cd "$PROJECT_DIR/wgpu-c/codegen"
python3 "$PROJECT_DIR/scripts/extract_macros.py" webgpu.h wgpu.h > ../webgpu_macros.nelua
MACRO_LINES=$(wc -l < ../webgpu_macros.nelua)
echo "  -> webgpu_macros.nelua: $MACRO_LINES lines"
echo ""

# Step 3: Generate bindings via nelua-decl
echo "[3/5] Generating Nelua bindings via nelua-decl..."
if make generate 2>/dev/null; then
    echo "  -> Bindings generated successfully"
else
    echo "  -> WARNING: nelua-decl generation failed (GCC Lua plugin not available?)"
    echo "     Macro constants were still updated."
    echo "     To generate full bindings, ensure nelua-decl is set up."
    echo "     See: https://github.com/edubart/nelua-decl"
fi
echo ""

# Step 4: Run validation
if [ "$SKIP_TESTS" = false ]; then
    echo "[4/5] Running validation..."
    cd "$PROJECT_DIR"
    if [ -f tests/validate_bindings.py ]; then
        python3 tests/validate_bindings.py
    else
        echo "  -> No validation tests found, skipping"
    fi
else
    echo "[4/5] Skipping tests (--skip-tests)"
fi
echo ""

# Step 5: Show changes
echo "[5/5] Change summary..."
cd "$PROJECT_DIR"
if command -v git &>/dev/null && [ -d .git ]; then
    echo ""
    echo "--- Files changed ---"
    git diff --stat -- 'wgpu-c/*.nelua' 'VERSION' 2>/dev/null || true
    echo ""
    echo "Review full changes with: git diff"
else
    echo "  -> Not a git repo, skipping diff"
fi

echo ""
echo "============================================"
echo "  Update complete!"
echo "============================================"
cat "$PROJECT_DIR/VERSION" 2>/dev/null || true

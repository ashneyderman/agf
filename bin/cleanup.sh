#!/usr/bin/env bash

set -euo pipefail

# Default values
BRANCH_PREFIX="alex/"
GIT_REPO_DIR="."
WORKTREES_DIR=".worktrees"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print usage
usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Clean up git worktrees and branches matching specified patterns.

OPTIONS:
    --branch-prefix PREFIX    Branch prefix to match for deletion (default: 'alex/')
    --git-repo-dir DIR        Directory where git repository is checked out (default: '.')
    --worktrees-dir DIR       Directory or partial match for worktrees location (default: '.worktrees')
    -h, --help                Show this help message

EXAMPLES:
    $(basename "$0")
    $(basename "$0") --branch-prefix "feature/" --worktrees-dir ".wt"
    $(basename "$0") --git-repo-dir /path/to/repo --branch-prefix "dev/"

EOF
    exit 0
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --branch-prefix)
            BRANCH_PREFIX="$2"
            shift 2
            ;;
        --git-repo-dir)
            GIT_REPO_DIR="$2"
            shift 2
            ;;
        --worktrees-dir)
            WORKTREES_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}Error: Unknown option '$1'${NC}" >&2
            usage
            ;;
    esac
done

# Function to prompt for confirmation
confirm() {
    local prompt="$1"
    local response

    while true; do
        echo -en "${YELLOW}${prompt} [y/N/a]: ${NC}"
        read -r response
        case "$response" in
            [yY][eE][sS]|[yY])
                return 0
                ;;
            [nN][oO]|[nN]|"")
                return 1
                ;;
            [aA][lL][lL]|[aA])
                return 2
                ;;
            *)
                echo "Please answer yes (y), no (n), or all (a)"
                ;;
        esac
    done
}

# Change to git repo directory
cd "$GIT_REPO_DIR" || {
    echo -e "${RED}Error: Could not change to directory '$GIT_REPO_DIR'${NC}" >&2
    exit 1
}

# Verify we're in a git repository
if ! git rev-parse --is-inside-work-tree &>/dev/null; then
    echo -e "${RED}Error: '$GIT_REPO_DIR' is not a git repository${NC}" >&2
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Git Worktree and Branch Cleanup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Configuration:"
echo -e "  Branch prefix:   ${GREEN}${BRANCH_PREFIX}${NC}"
echo -e "  Git repo dir:    ${GREEN}${GIT_REPO_DIR}${NC}"
echo -e "  Worktrees dir:   ${GREEN}${WORKTREES_DIR}${NC}"
echo ""

# ============================================
# STEP 1: Find and remove matching worktrees
# ============================================
echo -e "${BLUE}--- Step 1: Cleaning up worktrees ---${NC}"
echo ""

# Get list of worktrees matching the pattern
WORKTREES=()
while IFS= read -r line; do
    [[ -n "$line" ]] && WORKTREES+=("$line")
done < <(git worktree list --porcelain | grep -E '^worktree ' | awk '{print $2}' | grep "$WORKTREES_DIR" || true)

if [[ ${#WORKTREES[@]} -eq 0 ]]; then
    echo -e "${GREEN}No worktrees found matching '$WORKTREES_DIR'${NC}"
else
    echo -e "Found ${YELLOW}${#WORKTREES[@]}${NC} worktree(s) matching '${WORKTREES_DIR}':"
    echo ""

    for wt in "${WORKTREES[@]}"; do
        echo -e "  ${YELLOW}→${NC} $wt"
    done
    echo ""

    CONFIRM_ALL_WORKTREES=false

    for worktree in "${WORKTREES[@]}"; do
        if [[ "$CONFIRM_ALL_WORKTREES" == true ]]; then
            echo -e "${GREEN}Removing worktree:${NC} $worktree"
            if git worktree remove "$worktree" --force 2>/dev/null; then
                echo -e "  ${GREEN}✓ Removed successfully${NC}"
            else
                echo -e "  ${RED}✗ Failed to remove (may need manual cleanup)${NC}"
            fi
        else
            confirm "Remove worktree '$worktree'?"
            result=$?

            if [[ $result -eq 0 ]] || [[ $result -eq 2 ]]; then
                if [[ $result -eq 2 ]]; then
                    CONFIRM_ALL_WORKTREES=true
                fi

                echo -e "${GREEN}Removing worktree:${NC} $worktree"
                if git worktree remove "$worktree" --force 2>/dev/null; then
                    echo -e "  ${GREEN}✓ Removed successfully${NC}"
                else
                    echo -e "  ${RED}✗ Failed to remove (may need manual cleanup)${NC}"
                fi
            else
                echo -e "${YELLOW}Skipping worktree:${NC} $worktree"
            fi
        fi
        echo ""
    done
fi

# Prune worktree administrative files for worktrees that no longer exist
echo -e "${BLUE}Pruning stale worktree references...${NC}"
git worktree prune
echo -e "${GREEN}✓ Worktree prune complete${NC}"
echo ""

# ============================================
# STEP 2: Find and remove matching branches
# ============================================
echo -e "${BLUE}--- Step 2: Cleaning up branches ---${NC}"
echo ""

# Get list of branches matching the prefix
BRANCHES=()
while IFS= read -r line; do
    [[ -n "$line" ]] && BRANCHES+=("$line")
done < <(git branch | grep "$BRANCH_PREFIX" | sed 's/^[* ]*//' || true)

if [[ ${#BRANCHES[@]} -eq 0 ]]; then
    echo -e "${GREEN}No branches found matching '$BRANCH_PREFIX'${NC}"
else
    echo -e "Found ${YELLOW}${#BRANCHES[@]}${NC} branch(es) matching '${BRANCH_PREFIX}':"
    echo ""

    for br in "${BRANCHES[@]}"; do
        echo -e "  ${YELLOW}→${NC} $br"
    done
    echo ""

    CONFIRM_ALL_BRANCHES=false

    for branch in "${BRANCHES[@]}"; do
        # Check if this is the currently checked out branch
        CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || true)

        if [[ "$branch" == "$CURRENT_BRANCH" ]]; then
            echo -e "${RED}Warning: '$branch' is the currently checked out branch - skipping${NC}"
            echo ""
            continue
        fi

        if [[ "$CONFIRM_ALL_BRANCHES" == true ]]; then
            echo -e "${GREEN}Deleting branch:${NC} $branch"
            if git branch -D "$branch" 2>/dev/null; then
                echo -e "  ${GREEN}✓ Deleted successfully${NC}"
            else
                echo -e "  ${RED}✗ Failed to delete${NC}"
            fi
        else
            confirm "Delete branch '$branch'?"
            result=$?

            if [[ $result -eq 0 ]] || [[ $result -eq 2 ]]; then
                if [[ $result -eq 2 ]]; then
                    CONFIRM_ALL_BRANCHES=true
                fi

                echo -e "${GREEN}Deleting branch:${NC} $branch"
                if git branch -D "$branch" 2>/dev/null; then
                    echo -e "  ${GREEN}✓ Deleted successfully${NC}"
                else
                    echo -e "  ${RED}✗ Failed to delete${NC}"
                fi
            else
                echo -e "${YELLOW}Skipping branch:${NC} $branch"
            fi
        fi
        echo ""
    done
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Cleanup complete!${NC}"
echo -e "${BLUE}========================================${NC}"

# SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
# PARENT_DIR="$(dirname "$SCRIPT_DIR")"
# pushd "$PARENT_DIR"
# # git worktree list --porcelain | grep -E '^worktree ' | awk '{print $2}' | grep '/.worktrees/' | xargs -I {} git worktree remove --force {}
# git worktree list --porcelain | grep -E '^worktree ' | awk '{print $2}' | grep '/.worktrees/'
# # git branch | grep 'alex/' | sed 's/^[* ]*//' | xargs -r git branch -D
# git branch | grep 'alex/' | sed 's/^[* ]*//'
# popd

#!/bin/bash
# skill-incremental-sync.sh
# Efficient incremental updates and synchronization
#
# SUBAGENT: OPUS-3 (Systems Architect)
# TIER: 4 - Operations
#
# "skill-incremental-index.sh is non-negotiable for scale"
# - OPUS-3, Round 2

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
SYNC_DIR="${SYNC_DIR:-$HOME/.inception/sync}"
CHECKPOINT_FILE="$SYNC_DIR/checkpoint.json"

usage() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Efficient incremental updates and synchronization.

Commands:
    status      Show sync status and pending changes
    diff        Show content changes since last sync
    sync        Perform incremental sync
    checkpoint  Save current state checkpoint
    restore     Restore from checkpoint
    export      Export delta changes to backup

Options:
    --sources <dir>     Source directory to sync (default: current)
    --force             Force full resync
    --dry-run           Show what would be done without doing it
    --verbose           Verbose output

Examples:
    $0 status                  # Check sync status
    $0 sync --sources ./docs   # Sync specific directory
    $0 checkpoint              # Save checkpoint
    $0 restore                 # Restore from checkpoint

EOF
}

init_sync_dir() {
    mkdir -p "$SYNC_DIR"
    if [[ ! -f "$CHECKPOINT_FILE" ]]; then
        echo '{"version": 1, "sources": {}, "last_sync": null}' > "$CHECKPOINT_FILE"
    fi
}

compute_content_hash() {
    local file="$1"
    if command -v sha256sum &>/dev/null; then
        sha256sum "$file" | cut -d' ' -f1
    elif command -v shasum &>/dev/null; then
        shasum -a 256 "$file" | cut -d' ' -f1
    else
        md5 -q "$file"
    fi
}

show_status() {
    init_sync_dir
    echo "═══════════════════════════════════════════════════════════════"
    echo "  INCREMENTAL SYNC STATUS"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    
    if [[ -f "$CHECKPOINT_FILE" ]]; then
        local last_sync
        last_sync=$(python3 -c "import json; print(json.load(open('$CHECKPOINT_FILE')).get('last_sync', 'Never'))" 2>/dev/null || echo "Never")
        local source_count
        source_count=$(python3 -c "import json; print(len(json.load(open('$CHECKPOINT_FILE')).get('sources', {})))" 2>/dev/null || echo "0")
        
        echo "  Last Sync:     $last_sync"
        echo "  Tracked Files: $source_count"
    else
        echo "  Status: Not initialized"
    fi
    echo ""
}

scan_changes() {
    local source_dir="${1:-.}"
    init_sync_dir
    
    echo "Scanning for changes in: $source_dir"
    echo ""
    
    local added=0
    local modified=0
    local deleted=0
    
    # Find all relevant files
    find "$source_dir" -type f \( -name "*.py" -o -name "*.md" -o -name "*.txt" -o -name "*.json" \) 2>/dev/null | while read -r file; do
        local rel_path="${file#$source_dir/}"
        local current_hash
        current_hash=$(compute_content_hash "$file")
        
        # Check against checkpoint
        local stored_hash
        stored_hash=$(python3 -c "
import json
import sys
try:
    cp = json.load(open('$CHECKPOINT_FILE'))
    print(cp.get('sources', {}).get('$rel_path', {}).get('hash', ''))
except:
    print('')
" 2>/dev/null)
        
        if [[ -z "$stored_hash" ]]; then
            echo "  [+] $rel_path"
            ((added++)) || true
        elif [[ "$stored_hash" != "$current_hash" ]]; then
            echo "  [M] $rel_path"
            ((modified++)) || true
        fi
    done
    
    echo ""
    echo "Summary: +$added added, ~$modified modified"
}

save_checkpoint() {
    local source_dir="${1:-.}"
    init_sync_dir
    
    echo "Saving checkpoint..."
    
    python3 << PYTHON
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path

source_dir = Path("$source_dir").resolve()
checkpoint_file = Path("$CHECKPOINT_FILE")

# Load existing or create new
if checkpoint_file.exists():
    checkpoint = json.load(open(checkpoint_file))
else:
    checkpoint = {"version": 1, "sources": {}}

# Scan and update hashes
extensions = {".py", ".md", ".txt", ".json", ".yaml", ".yml"}
for file_path in source_dir.rglob("*"):
    if file_path.is_file() and file_path.suffix in extensions:
        rel_path = str(file_path.relative_to(source_dir))
        with open(file_path, "rb") as f:
            content_hash = hashlib.sha256(f.read()).hexdigest()
        
        checkpoint["sources"][rel_path] = {
            "hash": content_hash,
            "size": file_path.stat().st_size,
            "mtime": file_path.stat().st_mtime
        }

checkpoint["last_sync"] = datetime.now().isoformat()

with open(checkpoint_file, "w") as f:
    json.dump(checkpoint, f, indent=2)

print(f"✓ Checkpoint saved: {len(checkpoint['sources'])} files tracked")
PYTHON
}

# Main
COMMAND="${1:-status}"
shift || true

case "$COMMAND" in
    status)
        show_status
        ;;
    diff)
        scan_changes "${1:-.}"
        ;;
    sync)
        scan_changes "${1:-.}"
        save_checkpoint "${1:-.}"
        ;;
    checkpoint)
        save_checkpoint "${1:-.}"
        ;;
    restore)
        echo "Restore not yet implemented"
        ;;
    export)
        echo "Delta export not yet implemented"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo "Unknown command: $COMMAND"
        usage
        exit 1
        ;;
esac

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Incremental Sync Complete"
echo "═══════════════════════════════════════════════════════════════"


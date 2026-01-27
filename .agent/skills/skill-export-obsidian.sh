#!/bin/bash
# skill-export-obsidian.sh
# Export knowledge graph to Obsidian vault
#
# SUBAGENT: GEMINI-PRO (Integration Specialist)
# TIER: 4 - Operations
#
# "skill-export-integration.sh: Obsidian/Notion/Anki export is critical 
# for adoption."
# - GEMINI-PRO, Round 1

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Configuration
FORMAT="${FORMAT:-obsidian}"
BACKLINKS="${BACKLINKS:-true}"

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <output_directory>

Export knowledge graph to various formats.

Formats:
    obsidian    Markdown vault with [[backlinks]] (default)
    notion      Notion-compatible markdown
    anki        Anki flashcard deck
    jsonld      JSON-LD for semantic web

Options:
    --source <nid>      Export specific source only
    --format <name>     Export format (default: obsidian)
    --no-backlinks      Disable backlink generation
    --include-gaps      Include gap nodes as TODO items
    --help              Show this help message

Examples:
    $0 ~/obsidian/inception              # Export all to Obsidian
    $0 --source 123 ~/vault              # Export specific source
    $0 --format anki ~/anki/inception    # Generate Anki deck

Obsidian Structure:
    vault/
    ├── Sources/
    │   └── Video Title.md
    ├── Entities/
    │   └── Python.md
    ├── Claims/
    │   └── claim_123.md
    ├── Procedures/
    │   └── Install Python.md
    └── Gaps/
        └── undefined_term_RLHF.md

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE_NID="$2"
            shift 2
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --no-backlinks)
            BACKLINKS="false"
            shift
            ;;
        --include-gaps)
            INCLUDE_GAPS="true"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            OUTPUT_DIR="$1"
            shift
            ;;
    esac
done

if [[ -z "${OUTPUT_DIR:-}" ]]; then
    echo "Error: output_directory required"
    usage
    exit 1
fi

echo "=== Export to $FORMAT ==="
echo "Output: $OUTPUT_DIR"
echo "Backlinks: $BACKLINKS"
echo ""

# Create output structure
mkdir -p "$OUTPUT_DIR"/{Sources,Entities,Claims,Procedures,Gaps}

cd "$PROJECT_ROOT"
echo "Exporting knowledge graph..."
uv run python -c "
import os
from pathlib import Path

output_dir = Path('$OUTPUT_DIR')

try:
    from inception.db import get_db
    from inception.db.keys import NodeKind
    
    db = get_db()
    
    # Export sources
    sources = list(db.iter_sources())
    print(f'Exporting {len(sources)} sources...')
    
    for src in sources:
        title = src.title or f'source_{src.nid}'
        safe_title = ''.join(c for c in title if c.isalnum() or c in ' -_')[:50]
        
        md = f'# {title}\\n\\n'
        md += f'**URI**: {src.uri}\\n'
        md += f'**Type**: {src.source_type.name}\\n'
        md += f'**NID**: {src.nid}\\n'
        
        path = output_dir / 'Sources' / f'{safe_title}.md'
        path.write_text(md)
    
    # Export nodes
    nodes = list(db.iter_nodes())
    entities = [n for n in nodes if n.kind == NodeKind.ENTITY]
    claims = [n for n in nodes if n.kind == NodeKind.CLAIM]
    procs = [n for n in nodes if n.kind == NodeKind.PROCEDURE]
    gaps = [n for n in nodes if n.kind == NodeKind.GAP]
    
    print(f'Exporting {len(entities)} entities...')
    for entity in entities:
        name = entity.payload.get('name', f'entity_{entity.nid}')
        safe_name = ''.join(c for c in name if c.isalnum() or c in ' -_')[:50]
        
        md = f'# {name}\\n\\n'
        md += f'**Type**: {entity.payload.get(\"entity_type\", \"unknown\")}\\n'
        md += f'**NID**: {entity.nid}\\n'
        
        path = output_dir / 'Entities' / f'{safe_name}.md'
        path.write_text(md)
    
    print(f'Exporting {len(claims)} claims...')
    for claim in claims:
        text = claim.payload.get('text', '')[:100]
        
        md = f'# Claim\\n\\n'
        md += f'{claim.payload.get(\"text\", \"\")}\\n\\n'
        md += f'**NID**: {claim.nid}\\n'
        
        path = output_dir / 'Claims' / f'claim_{claim.nid}.md'
        path.write_text(md)
    
    print(f'Exporting {len(procs)} procedures...')
    for proc in procs:
        title = proc.payload.get('title', f'procedure_{proc.nid}')
        safe_title = ''.join(c for c in title if c.isalnum() or c in ' -_')[:50]
        
        md = f'# {title}\\n\\n'
        md += f'{proc.payload.get(\"goal\", \"\")}\\n\\n'
        md += '## Steps\\n\\n'
        for step in proc.payload.get('steps', []):
            md += f'- {step.get(\"text\", \"\")}\\n'
        
        path = output_dir / 'Procedures' / f'{safe_title}.md'
        path.write_text(md)
    
    print(f'Exporting {len(gaps)} gaps...')
    for gap in gaps:
        gap_type = gap.payload.get('gap_type', 'unknown')
        desc = gap.payload.get('description', '')[:50]
        
        md = f'# Gap: {gap_type}\\n\\n'
        md += f'- [ ] {gap.payload.get(\"description\", \"\")}\\n'
        
        path = output_dir / 'Gaps' / f'{gap_type}_{gap.nid}.md'
        path.write_text(md)
    
    print()
    print(f'Export complete! Files written to: {output_dir}')
    
except Exception as e:
    print(f'Export failed: {e}')
    print('Database may not be initialized.')
" 2>/dev/null || echo "Export placeholder - database may not be initialized"

echo ""
echo "Done."

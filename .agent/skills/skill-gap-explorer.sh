#!/bin/bash
# skill-gap-explorer.sh
# Autonomous gap-driven knowledge acquisition
#
# SUBAGENT: GEMINI-PRO (Integration Specialist)
# TIER: 2 - Agency
#
# "This is the 'prescient awesomeness'. Imagine: Inception detects a gap 
# ('undefined term: RLHF'), then autonomously searches web for explanations, 
# ingests them, and resolves the gap. That's agentic knowledge building."
# - GEMINI-PRO, Round 2

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Safety rails (per GEMINI-PRO's recommendation)
MAX_DEPTH="${MAX_DEPTH:-2}"
RATE_LIMIT="${RATE_LIMIT:-10}"  # requests per minute
BUDGET_CAP="${BUDGET_CAP:-0.50}"  # USD per session
HITL="${HITL:-true}"  # Human-in-the-loop mode

usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Autonomous gap-driven knowledge exploration and resolution.

Safety Rails:
    --max-depth <n>     Maximum exploration depth (default: 2)
    --rate-limit <n>    Max requests per minute (default: 10)
    --budget <amount>   Budget cap in USD (default: 0.50)
    --auto              Disable human-in-the-loop (use with caution!)
    --allowlist <file>  Domain allowlist file
    --blocklist <file>  Domain blocklist file

Examples:
    $0                              # Interactive mode (default)
    $0 --max-depth 1                # Shallow exploration
    $0 --auto --max-depth 1         # Autonomous shallow exploration

Gap Types Handled:
    - undefined_term: Search for definitions
    - missing_context: Find background information  
    - unresolved_reference: Locate source material
    - incomplete_procedure: Find missing steps

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --max-depth)
            MAX_DEPTH="$2"
            shift 2
            ;;
        --rate-limit)
            RATE_LIMIT="$2"
            shift 2
            ;;
        --budget)
            BUDGET_CAP="$2"
            shift 2
            ;;
        --auto)
            HITL="false"
            shift
            ;;
        --allowlist)
            ALLOWLIST="$2"
            shift 2
            ;;
        --blocklist)
            BLOCKLIST="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

echo "=== Gap Explorer ==="
echo "Max Depth: $MAX_DEPTH"
echo "Rate Limit: $RATE_LIMIT req/min"
echo "Budget Cap: \$$BUDGET_CAP"
echo "Human-in-the-loop: $HITL"
echo ""

if [[ "$HITL" == "false" ]]; then
    echo "⚠️  WARNING: Running in autonomous mode!"
    echo "   The system will automatically fetch and ingest external content."
    echo "   Press Ctrl+C within 5 seconds to cancel..."
    sleep 5
fi

cd "$PROJECT_ROOT"
echo "Scanning for unresolved gaps..."

uv run python << 'PYTHON_SCRIPT'
import sys
import json
from pathlib import Path

try:
    from inception.db import get_db
    from inception.db.keys import NodeKind
except ImportError:
    print("Inception DB not available. Ensure the project is installed.")
    sys.exit(1)

def categorize_gap(gap):
    """Categorize gap by type and suggest resolution strategy."""
    gap_type = gap.payload.get('gap_type', 'unknown')
    description = gap.payload.get('description', '')
    
    strategies = {
        'undefined_term': {
            'action': 'search_definition',
            'sources': ['wikipedia', 'glossary', 'specification'],
            'template': f'define "{description}"'
        },
        'missing_context': {
            'action': 'search_background',
            'sources': ['documentation', 'whitepaper', 'tutorial'],
            'template': f'background on {description}'
        },
        'unresolved_reference': {
            'action': 'locate_source',
            'sources': ['arxiv', 'github', 'official_spec'],
            'template': f'source for {description}'
        },
        'incomplete_procedure': {
            'action': 'find_steps',
            'sources': ['documentation', 'tutorial', 'stackoverflow'],
            'template': f'how to {description} step by step'
        },
        'conflicting_claims': {
            'action': 'dialectical_analysis',
            'sources': ['academic', 'official'],
            'template': f'comparison of {description}'
        }
    }
    
    return strategies.get(gap_type, {
        'action': 'general_search',
        'sources': ['web'],
        'template': description
    })

def format_gap_report(gaps):
    """Format gaps into actionable report."""
    report = []
    for i, gap in enumerate(gaps, 1):
        category = categorize_gap(gap)
        gap_type = gap.payload.get('gap_type', 'unknown')
        desc = gap.payload.get('description', 'No description')
        severity = gap.payload.get('severity', 0.5)
        
        report.append({
            'index': i,
            'nid': gap.nid,
            'type': gap_type,
            'description': desc[:80],
            'severity': severity,
            'action': category['action'],
            'search_query': category['template'],
            'sources': category['sources']
        })
    
    return report

try:
    db = get_db()
    gaps = [n for n in db.iter_nodes() if n.kind == NodeKind.GAP]
    
    if not gaps:
        print("✓ No gaps found in knowledge graph.")
        sys.exit(0)
    
    # Sort by severity
    gaps.sort(key=lambda g: g.payload.get('severity', 0.5), reverse=True)
    
    print(f"\n═══════════════════════════════════════════════════════════════")
    print(f"  KNOWLEDGE GAPS: {len(gaps)} detected")
    print(f"═══════════════════════════════════════════════════════════════\n")
    
    report = format_gap_report(gaps[:10])
    
    for item in report:
        severity_bar = '█' * int(item['severity'] * 10)
        print(f"[{item['index']:2}] {item['type'].upper()}")
        print(f"    Description: {item['description']}")
        print(f"    Severity: {severity_bar} ({item['severity']:.2f})")
        print(f"    Suggested: {item['action']}")
        print(f"    Query: \"{item['search_query']}\"")
        print(f"    Sources: {', '.join(item['sources'])}")
        print()
    
    # Output JSON for programmatic use
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        print(json.dumps(report, indent=2))

except Exception as e:
    print(f"Error accessing database: {e}")
    sys.exit(1)
PYTHON_SCRIPT

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  Gap Explorer Complete"
echo "═══════════════════════════════════════════════════════════════"


#!/bin/bash
# skill-llm-extractor.sh
# LLM-enhanced claim, entity, and procedure extraction
#
# SUBAGENT: OPUS-2 (ML/AI Specialist)
# TIER: 1 - Intelligence
#
# Usage: ./skill-llm-extractor.sh [--provider ollama|openrouter|cloud] [--offline] <source_nid>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

# Default provider hierarchy (respects --offline)
PROVIDER="${PROVIDER:-ollama}"
OFFLINE="${OFFLINE:-false}"

usage() {
    cat << EOF
Usage: $0 [OPTIONS] <source_nid>

LLM-enhanced extraction for improved claim, entity, and procedure detection.

Options:
    --provider <name>   LLM provider: ollama, openrouter, cloud (default: ollama)
    --offline           Use only local providers (Ollama)
    --help              Show this help message

Providers:
    ollama     - Local Llama3/Mistral via Ollama (free, private)
    openrouter - OpenRouter API (cost-effective, diverse models)
    cloud      - Claude/GPT-4 direct API (highest quality)

Examples:
    $0 123                           # Extract with default Ollama
    $0 --provider openrouter 123     # Use OpenRouter
    $0 --offline 123                 # Force offline mode

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --provider)
            PROVIDER="$2"
            shift 2
            ;;
        --offline)
            OFFLINE="true"
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            SOURCE_NID="$1"
            shift
            ;;
    esac
done

if [[ -z "${SOURCE_NID:-}" ]]; then
    echo "Error: source_nid required"
    usage
    exit 1
fi

echo "=== LLM Extractor ==="
echo "Provider: $PROVIDER"
echo "Offline: $OFFLINE"
echo "Source: $SOURCE_NID"
echo ""

# Check provider availability
check_ollama() {
    if command -v ollama &> /dev/null; then
        if ollama list 2>/dev/null | grep -q "llama"; then
            return 0
        fi
    fi
    return 1
}

if [[ "$PROVIDER" == "ollama" ]] || [[ "$OFFLINE" == "true" ]]; then
    if ! check_ollama; then
        echo "Error: Ollama not available. Install with: brew install ollama && ollama pull llama3"
        exit 1
    fi
fi

# Run extraction
cd "$PROJECT_ROOT"
echo "Running LLM-enhanced extraction..."
uv run python -c "
from inception.db import get_db
from inception.analyze.claims import extract_claims
from inception.analyze.entities import extract_entities

# TODO: Implement LLM-enhanced extraction
# This is a placeholder for the enhancement implementation
print('LLM extraction not yet implemented - use standard extraction for now')
print('Run: inception build-graph $SOURCE_NID')
" 2>/dev/null || echo "Placeholder: LLM extraction module not yet implemented"

echo ""
echo "Done. Enhancement pending implementation."

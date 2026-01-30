#!/usr/bin/env bash
# =============================================================================
# skill-rheomode-transform.sh — Bohm's Flowing Language Transformation
# =============================================================================
# PURPOSE: Transform static language into flowing meaning per Rheomode
# SWARM: entelecheia-plus-2026-01-28-alpha
# PERSONAS: DIALECTICA, HARMONIST, ALCHEMIST
# =============================================================================

set -euo pipefail

SKILL_NAME="rheomode-transform"
SKILL_VERSION="1.0.0"

# -----------------------------------------------------------------------------
# Noun → Gerund Transformations
# -----------------------------------------------------------------------------

declare -A GERUNDS=(
    ["thought"]="thinking"
    ["knowledge"]="knowing"
    ["understanding"]="understanding"
    ["explanation"]="explaining"
    ["analysis"]="analyzing"
    ["creation"]="creating"
    ["decision"]="deciding"
    ["observation"]="observing"
    ["perception"]="perceiving"
    ["belief"]="believing"
    ["definition"]="defining"
    ["concept"]="conceiving"
    ["memory"]="remembering"
    ["attention"]="attending"
    ["intention"]="intending"
    ["abstraction"]="abstracting"
    ["reflection"]="reflecting"
    ["comprehension"]="comprehending"
    ["recognition"]="recognizing"
    ["assumption"]="assuming"
    ["conclusion"]="concluding"
    ["inference"]="inferring"
    ["judgment"]="judging"
    ["evaluation"]="evaluating"
    ["interpretation"]="interpreting"
)

# -----------------------------------------------------------------------------
# Static → Flowing Transform
# -----------------------------------------------------------------------------

static_to_flowing() {
    local text="$1"
    local result="$text"
    
    echo "[RHEOMODE] Transforming static → flowing"
    
    for noun in "${!GERUNDS[@]}"; do
        local gerund="${GERUNDS[$noun]}"
        # Replace "the [noun]" with "the act of [gerund]"
        result=$(echo "$result" | sed -E "s/\bthe $noun\b/the act of $gerund/gi")
        # Replace "[noun]" alone with "[gerund]"
        result=$(echo "$result" | sed -E "s/\b$noun\b/$gerund/gi")
    done
    
    echo "$result"
}

# -----------------------------------------------------------------------------
# Object → Process Transform
# -----------------------------------------------------------------------------

object_to_process() {
    local text="$1"
    local result="$text"
    
    echo "[RHEOMODE] Transforming object → process"
    
    # Common object→process patterns
    result=$(echo "$result" | sed -E 's/\bthis is a ([a-z]+)\b/this is the process of \1ing/gi')
    result=$(echo "$result" | sed -E 's/\bthe ([a-z]+) is\b/the \1ing process is/gi')
    result=$(echo "$result" | sed -E 's/\bhave a ([a-z]+)\b/engage in \1ing/gi')
    
    echo "$result"
}

# -----------------------------------------------------------------------------
# Fragment → Whole Transform
# -----------------------------------------------------------------------------

fragment_to_whole() {
    local text="$1"
    
    echo "[RHEOMODE] Transforming fragment → whole"
    
    # Add wholeness framing
    cat << EOF
Viewing this holistically, with attention to implicit connections:

$text

In this movement of thought, the fragments above participate in a larger coherent whole.
EOF
}

# -----------------------------------------------------------------------------
# Frozen → Alive Transform  
# -----------------------------------------------------------------------------

frozen_to_alive() {
    local text="$1"
    
    echo "[RHEOMODE] Transforming frozen → alive"
    
    # Add dynamic framing
    cat << EOF
Consider this not as fixed truth, but as an ongoing movement:

$text

This meaning continues to flow and evolve with new understanding.
EOF
}

# -----------------------------------------------------------------------------
# Co-Object Inference
# -----------------------------------------------------------------------------

coobject_infer() {
    local primary="$1"
    
    echo "[RHEOMODE] Inferring co-objects for: $primary"
    
    # Check for related gerunds
    local primary_lower=$(echo "$primary" | tr '[:upper:]' '[:lower:]')
    local related=()
    
    # Semantic neighbors based on common domains
    case "$primary_lower" in
        *think*|*thought*|*reason*)
            related=("knowing" "understanding" "reflecting" "concluding")
            ;;
        *know*|*learn*)
            related=("understanding" "remembering" "recognizing" "applying")
            ;;
        *create*|*build*|*make*)
            related=("designing" "planning" "implementing" "testing")
            ;;
        *analyze*|*evaluat*)
            related=("measuring" "comparing" "judging" "interpreting")
            ;;
        *decide*|*choose*)
            related=("evaluating" "weighing" "committing" "acting")
            ;;
        *)
            related=("understanding" "relating" "contextualizing" "applying")
            ;;
    esac
    
    echo "[RHEOMODE] Co-objects found:"
    printf ' - %s\n' "${related[@]}"
    
    # Output as JSON
    printf '%s\n' "${related[@]}" | jq -R . | jq -s .
}

# -----------------------------------------------------------------------------
# Full Rheomode Analysis
# -----------------------------------------------------------------------------

full_analysis() {
    local text="$1"
    
    echo "[RHEOMODE] Full analysis"
    echo "========================"
    echo ""
    echo "ORIGINAL:"
    echo "$text"
    echo ""
    echo "STATIC → FLOWING:"
    static_to_flowing "$text"
    echo ""
    echo "WITH WHOLENESS:"
    fragment_to_whole "$text"
    echo ""
    
    # Extract key nouns and find co-objects
    local nouns=$(echo "$text" | grep -oE '\b[a-z]+tion\b|\b[a-z]+ment\b|\b[a-z]+ness\b' | head -3)
    if [[ -n "$nouns" ]]; then
        echo "CO-OBJECTS FOR KEY CONCEPTS:"
        while IFS= read -r noun; do
            [[ -z "$noun" ]] && continue
            echo "  $noun:"
            coobject_infer "$noun" 2>/dev/null | jq -r '.[] | "    - " + .'
        done <<< "$nouns"
    fi
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    local cmd="${1:-help}"
    shift || true
    
    case "$cmd" in
        static-to-flowing)
            static_to_flowing "$@"
            ;;
        object-to-process)
            object_to_process "$@"
            ;;
        fragment-to-whole)
            fragment_to_whole "$@"
            ;;
        frozen-to-alive)
            frozen_to_alive "$@"
            ;;
        coobject)
            coobject_infer "$@"
            ;;
        analyze)
            full_analysis "$@"
            ;;
        help|*)
            echo "skill-rheomode-transform.sh — Bohm's Flowing Language"
            echo ""
            echo "Commands:"
            echo "  static-to-flowing <text>  — Noun → Gerund"
            echo "  object-to-process <text>  — Thing → Action"
            echo "  fragment-to-whole <text>  — Parts → Coherent"
            echo "  frozen-to-alive <text>    — Static → Dynamic"
            echo "  coobject <concept>        — Infer related concepts"
            echo "  analyze <text>            — Full rheomode analysis"
            ;;
    esac
}

main "$@"

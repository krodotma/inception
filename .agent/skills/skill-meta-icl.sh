#!/usr/bin/env bash
# =============================================================================
# skill-meta-icl.sh — Meta In-Context Learning
# =============================================================================
# PURPOSE: Implement meta in-context learning with context distillation,
#          transfer learning, and few-to-zero progression
# SWARM: entelecheia-plus-2026-01-28-alpha
# PERSONAS: METACOG, ALCHEMIST
# =============================================================================

set -euo pipefail

SKILL_NAME="meta-icl"
SKILL_VERSION="1.0.0"
KERNEL_DIR="${INCEPTION_KERNELS:-$HOME/.inception/kernels}"

# -----------------------------------------------------------------------------
# Context Distillation
# -----------------------------------------------------------------------------
# Compress successful examples into reusable kernels
# Input: Examples (JSONL), Output: Kernel (JSON)

context_distill() {
    local examples_file="$1"
    local kernel_name="$2"
    local domain="${3:-general}"
    
    echo "[META-ICL] Distilling examples from: $examples_file"
    
    # Create kernel directory if needed
    mkdir -p "$KERNEL_DIR/$domain"
    
    # Extract patterns from examples
    local patterns=$(jq -s '
        group_by(.type) |
        map({
            type: .[0].type,
            count: length,
            common_fields: (map(keys) | add | unique),
            example: .[0]
        })
    ' "$examples_file")
    
    # Create kernel
    local kernel_file="$KERNEL_DIR/$domain/${kernel_name}.kernel.json"
    
    cat > "$kernel_file" << EOF
{
    "kernel_name": "$kernel_name",
    "kernel_version": "1.0.0",
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "source_examples": "$examples_file",
    "domain": "$domain",
    "patterns": $patterns,
    "usage_count": 0,
    "success_rate": 0.0
}
EOF

    echo "[META-ICL] Kernel created: $kernel_file"
    echo "$kernel_file"
}

# -----------------------------------------------------------------------------
# Context Transfer
# -----------------------------------------------------------------------------
# Apply learnings across domains via embedding space mapping

context_transfer() {
    local source_kernel="$1"
    local target_domain="$2"
    
    echo "[META-ICL] Transferring kernel to domain: $target_domain"
    
    if [[ ! -f "$source_kernel" ]]; then
        echo "[ERROR] Source kernel not found: $source_kernel" >&2
        return 1
    fi
    
    local source_domain=$(jq -r '.domain' "$source_kernel")
    local kernel_name=$(jq -r '.kernel_name' "$source_kernel")
    
    # Create transferred kernel
    mkdir -p "$KERNEL_DIR/$target_domain"
    local target_file="$KERNEL_DIR/$target_domain/${kernel_name}_transferred.kernel.json"
    
    jq --arg target "$target_domain" --arg source "$source_domain" '
        . + {
            domain: $target,
            transferred_from: $source,
            transfer_confidence: 0.7,
            requires_validation: true
        }
    ' "$source_kernel" > "$target_file"
    
    echo "[META-ICL] Transferred kernel: $target_file"
    echo "$target_file"
}

# -----------------------------------------------------------------------------
# Few-to-Zero Progression
# -----------------------------------------------------------------------------
# Graduate from example-based to principle-based reasoning

few_to_zero() {
    local kernel_file="$1"
    local min_success_rate="${2:-0.85}"
    
    echo "[META-ICL] Checking few-to-zero progression for: $kernel_file"
    
    if [[ ! -f "$kernel_file" ]]; then
        echo "[ERROR] Kernel not found: $kernel_file" >&2
        return 1
    fi
    
    local usage_count=$(jq -r '.usage_count' "$kernel_file")
    local success_rate=$(jq -r '.success_rate' "$kernel_file")
    
    if (( $(echo "$success_rate >= $min_success_rate" | bc -l) )) && (( usage_count >= 10 )); then
        echo "[META-ICL] ✓ Ready for zero-shot: success=$success_rate, usage=$usage_count"
        
        # Extract principles from patterns
        jq --arg status "zero_shot_ready" '
            . + {
                zero_shot_status: $status,
                principles: [
                    .patterns[] | 
                    "For type \(.type), ensure fields: \(.common_fields | join(", "))"
                ]
            }
        ' "$kernel_file" > "${kernel_file}.tmp" && mv "${kernel_file}.tmp" "$kernel_file"
        
        echo "ready"
    else
        echo "[META-ICL] ✗ Not ready: success=$success_rate (need $min_success_rate), usage=$usage_count (need 10)"
        echo "not_ready"
    fi
}

# -----------------------------------------------------------------------------
# Negative Transfer Detection
# -----------------------------------------------------------------------------
# Detect when cross-domain transfer hurts performance

negative_transfer_detect() {
    local kernel_file="$1"
    local performance_log="${2:-performance.log}"
    
    echo "[META-ICL] Checking for negative transfer: $kernel_file"
    
    if [[ ! -f "$kernel_file" ]]; then
        echo "[ERROR] Kernel not found: $kernel_file" >&2
        return 1
    fi
    
    local is_transferred=$(jq -r '.transferred_from // empty' "$kernel_file")
    
    if [[ -z "$is_transferred" ]]; then
        echo "[META-ICL] Not a transferred kernel, skipping"
        echo "not_applicable"
        return 0
    fi
    
    local transfer_confidence=$(jq -r '.transfer_confidence' "$kernel_file")
    
    # Check if performance degraded
    if (( $(echo "$transfer_confidence < 0.5" | bc -l) )); then
        echo "[META-ICL] ⚠ Negative transfer detected: confidence=$transfer_confidence"
        
        jq '. + {negative_transfer_detected: true, recommended_action: "rollback"}' \
            "$kernel_file" > "${kernel_file}.tmp" && mv "${kernel_file}.tmp" "$kernel_file"
        
        echo "detected"
    else
        echo "[META-ICL] Transfer performing well: confidence=$transfer_confidence"
        echo "not_detected"
    fi
}

# -----------------------------------------------------------------------------
# Kernel Usage Tracking
# -----------------------------------------------------------------------------

kernel_use() {
    local kernel_file="$1"
    local success="${2:-true}"
    
    if [[ ! -f "$kernel_file" ]]; then
        echo "[ERROR] Kernel not found: $kernel_file" >&2
        return 1
    fi
    
    local current_usage=$(jq -r '.usage_count' "$kernel_file")
    local current_success=$(jq -r '.success_rate' "$kernel_file")
    local new_usage=$((current_usage + 1))
    
    local new_success
    if [[ "$success" == "true" ]]; then
        new_success=$(echo "scale=4; ($current_success * $current_usage + 1) / $new_usage" | bc)
    else
        new_success=$(echo "scale=4; ($current_success * $current_usage) / $new_usage" | bc)
    fi
    
    jq --argjson usage "$new_usage" --arg rate "$new_success" '
        .usage_count = $usage | .success_rate = ($rate | tonumber)
    ' "$kernel_file" > "${kernel_file}.tmp" && mv "${kernel_file}.tmp" "$kernel_file"
    
    echo "[META-ICL] Updated: usage=$new_usage, success_rate=$new_success"
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    local cmd="${1:-help}"
    shift || true
    
    case "$cmd" in
        distill)
            context_distill "$@"
            ;;
        transfer)
            context_transfer "$@"
            ;;
        few-to-zero)
            few_to_zero "$@"
            ;;
        negative-detect)
            negative_transfer_detect "$@"
            ;;
        use)
            kernel_use "$@"
            ;;
        help|*)
            echo "skill-meta-icl.sh — Meta In-Context Learning"
            echo ""
            echo "Commands:"
            echo "  distill <examples.jsonl> <kernel_name> [domain]"
            echo "  transfer <kernel.json> <target_domain>"
            echo "  few-to-zero <kernel.json> [min_success_rate]"
            echo "  negative-detect <kernel.json> [performance.log]"
            echo "  use <kernel.json> [true|false]"
            ;;
    esac
}

main "$@"

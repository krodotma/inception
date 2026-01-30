#!/usr/bin/env bash
# =============================================================================
# skill-stigmergic-trace.sh — Trace-Based Agent Coordination
# =============================================================================
# PURPOSE: Implement stigmergic coordination via pheromone-like traces
#          for emergent multi-agent collaboration
# SWARM: entelecheia-plus-2026-01-28-alpha
# PERSONAS: METACOG, PRESCIENT, KINESIS
# =============================================================================

set -euo pipefail

SKILL_NAME="stigmergic-trace"
SKILL_VERSION="1.0.0"
TRACE_DIR="${INCEPTION_TRACES:-$HOME/.inception/traces}"
EVAPORATION_RATE="${TRACE_EVAPORATION:-0.05}"  # Decay per hour
REINFORCE_FACTOR="${TRACE_REINFORCE:-1.5}"     # Multiplier on revisit

# -----------------------------------------------------------------------------
# Trace Deposit
# -----------------------------------------------------------------------------
# Leave a coordination mark at a location

trace_deposit() {
    local trace_type="$1"      # task, discovery, warning, success, failure
    local location="$2"        # file path, concept ID, or URI
    local agent_id="$3"        # depositing agent
    local strength="${4:-1.0}" # initial strength
    local metadata="${5:-{}}"  # additional context
    
    echo "[STIGMERGIC] Depositing trace: type=$trace_type, location=$location"
    
    mkdir -p "$TRACE_DIR"
    
    local trace_id=$(echo "$trace_type:$location:$agent_id:$(date +%s)" | md5sum | cut -c1-16)
    local trace_file="$TRACE_DIR/${trace_id}.trace.json"
    
    cat > "$trace_file" << EOF
{
    "trace_id": "$trace_id",
    "trace_type": "$trace_type",
    "location": "$location",
    "agent_id": "$agent_id",
    "strength": $strength,
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "visit_count": 1,
    "metadata": $metadata
}
EOF

    echo "[STIGMERGIC] Trace deposited: $trace_id"
    echo "$trace_id"
}

# -----------------------------------------------------------------------------
# Trace Follow
# -----------------------------------------------------------------------------
# Navigate by following traces

trace_follow() {
    local location="$1"
    local trace_type="${2:-}"  # optional filter
    local min_strength="${3:-0.1}"
    
    echo "[STIGMERGIC] Following traces at: $location"
    
    local traces=()
    
    for trace_file in "$TRACE_DIR"/*.trace.json; do
        [[ -f "$trace_file" ]] || continue
        
        local t_location=$(jq -r '.location' "$trace_file")
        local t_type=$(jq -r '.trace_type' "$trace_file")
        local t_strength=$(jq -r '.strength' "$trace_file")
        
        # Match location (exact or prefix)
        if [[ "$t_location" == "$location"* ]] || [[ "$location" == "$t_location"* ]]; then
            # Filter by type if specified
            if [[ -z "$trace_type" ]] || [[ "$t_type" == "$trace_type" ]]; then
                # Filter by strength
                if (( $(echo "$t_strength >= $min_strength" | bc -l) )); then
                    traces+=("$trace_file")
                fi
            fi
        fi
    done
    
    if [[ ${#traces[@]} -eq 0 ]]; then
        echo "[STIGMERGIC] No traces found at location"
        echo "[]"
        return 0
    fi
    
    # Sort by strength (descending) and output
    jq -s 'sort_by(-.strength)' "${traces[@]}"
}

# -----------------------------------------------------------------------------
# Trace Reinforce
# -----------------------------------------------------------------------------
# Strengthen traces on revisit

trace_reinforce() {
    local trace_id="$1"
    local agent_id="$2"
    
    echo "[STIGMERGIC] Reinforcing trace: $trace_id"
    
    local trace_file="$TRACE_DIR/${trace_id}.trace.json"
    
    if [[ ! -f "$trace_file" ]]; then
        echo "[ERROR] Trace not found: $trace_id" >&2
        return 1
    fi
    
    local current_strength=$(jq -r '.strength' "$trace_file")
    local new_strength=$(echo "scale=4; $current_strength * $REINFORCE_FACTOR" | bc)
    
    # Cap at 10.0
    if (( $(echo "$new_strength > 10.0" | bc -l) )); then
        new_strength="10.0"
    fi
    
    jq --arg strength "$new_strength" --arg time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --arg agent "$agent_id" '
        .strength = ($strength | tonumber) |
        .last_updated = $time |
        .visit_count += 1 |
        .visitors += [$agent]
    ' "$trace_file" > "${trace_file}.tmp" && mv "${trace_file}.tmp" "$trace_file"
    
    echo "[STIGMERGIC] Reinforced: strength=$current_strength → $new_strength"
    echo "$new_strength"
}

# -----------------------------------------------------------------------------
# Trace Evaporate
# -----------------------------------------------------------------------------
# Decay traces over time

trace_evaporate() {
    local hours="${1:-1}"  # hours since last update
    
    echo "[STIGMERGIC] Evaporating traces (rate=$EVAPORATION_RATE per hour)"
    
    local now=$(date +%s)
    local evaporated=0
    local removed=0
    
    for trace_file in "$TRACE_DIR"/*.trace.json; do
        [[ -f "$trace_file" ]] || continue
        
        local last_updated=$(jq -r '.last_updated' "$trace_file")
        local last_epoch=$(date -d "$last_updated" +%s 2>/dev/null || echo "$now")
        local hours_since=$(( (now - last_epoch) / 3600 ))
        
        if (( hours_since > 0 )); then
            local current_strength=$(jq -r '.strength' "$trace_file")
            local decay=$(echo "scale=4; $EVAPORATION_RATE * $hours_since" | bc)
            local new_strength=$(echo "scale=4; $current_strength - $decay" | bc)
            
            if (( $(echo "$new_strength <= 0" | bc -l) )); then
                # Remove trace
                rm "$trace_file"
                ((removed++))
            else
                jq --arg strength "$new_strength" '
                    .strength = ($strength | tonumber)
                ' "$trace_file" > "${trace_file}.tmp" && mv "${trace_file}.tmp" "$trace_file"
                ((evaporated++))
            fi
        fi
    done
    
    echo "[STIGMERGIC] Evaporated: $evaporated, Removed: $removed"
}

# -----------------------------------------------------------------------------
# Trace Topology
# -----------------------------------------------------------------------------
# Detect emergent topology from traces

trace_topology() {
    echo "[STIGMERGIC] Analyzing trace topology"
    
    local nodes=()
    local edges=()
    
    for trace_file in "$TRACE_DIR"/*.trace.json; do
        [[ -f "$trace_file" ]] || continue
        
        local location=$(jq -r '.location' "$trace_file")
        local strength=$(jq -r '.strength' "$trace_file")
        local visit_count=$(jq -r '.visit_count' "$trace_file")
        
        nodes+=("{\"id\": \"$location\", \"strength\": $strength, \"visits\": $visit_count}")
    done
    
    if [[ ${#nodes[@]} -eq 0 ]]; then
        echo "{\"nodes\": [], \"edges\": [], \"hubs\": [], \"bridges\": []}"
        return 0
    fi
    
    # Build topology JSON
    local nodes_json=$(printf '%s\n' "${nodes[@]}" | jq -s '
        group_by(.id) | map({
            id: .[0].id,
            total_strength: (map(.strength) | add),
            total_visits: (map(.visits) | add),
            trace_count: length
        }) | sort_by(-.total_strength)
    ')
    
    # Identify hubs (high connectivity)
    local hubs=$(echo "$nodes_json" | jq '[.[] | select(.trace_count >= 3)]')
    
    # Identify bridges (connect different clusters - simplified)
    local bridges=$(echo "$nodes_json" | jq '[.[] | select(.total_visits >= 5 and .trace_count >= 2)]')
    
    cat << EOF
{
    "nodes": $nodes_json,
    "edges": [],
    "hubs": $hubs,
    "bridges": $bridges,
    "total_traces": $(ls -1 "$TRACE_DIR"/*.trace.json 2>/dev/null | wc -l || echo 0)
}
EOF
}

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

main() {
    local cmd="${1:-help}"
    shift || true
    
    case "$cmd" in
        deposit)
            trace_deposit "$@"
            ;;
        follow)
            trace_follow "$@"
            ;;
        reinforce)
            trace_reinforce "$@"
            ;;
        evaporate)
            trace_evaporate "$@"
            ;;
        topology)
            trace_topology
            ;;
        help|*)
            echo "skill-stigmergic-trace.sh — Trace-Based Agent Coordination"
            echo ""
            echo "Commands:"
            echo "  deposit <type> <location> <agent_id> [strength] [metadata_json]"
            echo "  follow <location> [trace_type] [min_strength]"
            echo "  reinforce <trace_id> <agent_id>"
            echo "  evaporate [hours]"
            echo "  topology"
            echo ""
            echo "Trace Types: task, discovery, warning, success, failure"
            ;;
    esac
}

main "$@"

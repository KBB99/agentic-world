#!/usr/bin/env bash
# Test AI Agent system by simulating game state and requesting decisions

set -euo pipefail

err() { echo "ERROR: $*" 1>&2; }
info() { echo "INFO: $*"; }

# Configuration
REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
AGENT_ID="${AGENT_ID:-npc_001}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --agent-id) AGENT_ID="$2"; shift 2;;
    --help)
      echo "Usage: $0 [--region REGION] [--project PROJECT] [--agent-id ID]"
      echo "  Tests AI agent decision-making with sample game states"
      exit 0
      ;;
    *) err "Unknown arg: $1"; exit 1;;
  esac
done

OUT_DIR="aws/out"

# Load WebSocket endpoint
if [[ ! -f "$OUT_DIR/telemetry.outputs.json" ]]; then
  err "Telemetry outputs not found. Deploy telemetry stack first."
  exit 2
fi

WS_ENDPOINT=$(jq -r '.WebSocketUrl // empty' "$OUT_DIR/telemetry.outputs.json")
if [[ -z "$WS_ENDPOINT" ]]; then
  err "WebSocket endpoint not found in outputs"
  exit 2
fi

# Load agent function ARN
if [[ ! -f "$OUT_DIR/agent-ai.outputs.json" ]]; then
  err "Agent AI outputs not found. Deploy agent stack first."
  exit 2
fi

AGENT_FUNCTION=$(jq -r '.AgentOrchestratorFunctionArn // empty' "$OUT_DIR/agent-ai.outputs.json")

info "=== Testing AI Agent System ==="
info "Agent ID:   $AGENT_ID"
info "WebSocket:  $WS_ENDPOINT"
info "Function:   $AGENT_FUNCTION"
echo

# Test 1: Basic movement decision
info "Test 1: Requesting basic movement decision..."
GAME_STATE_1='{
  "location": "town_square",
  "timeOfDay": "morning",
  "weather": "sunny",
  "nearbyObjects": ["fountain", "bench", "merchant_stall"],
  "visibleCharacters": ["player_001", "merchant_npc"],
  "interactableItems": ["quest_board", "fountain"]
}'

CHARACTER_STATE_1='{
  "position": {"x": 100, "y": 0, "z": 50},
  "health": 100,
  "inventory": ["bread", "water"],
  "currentAnimation": "idle",
  "isMoving": false,
  "energy": 80
}'

PAYLOAD_1=$(jq -n \
  --arg agentId "$AGENT_ID" \
  --argjson gameState "$GAME_STATE_1" \
  --argjson characterState "$CHARACTER_STATE_1" \
  '{
    action: "agent_request",
    data: {
      agentId: $agentId,
      gameState: $gameState,
      characterState: $characterState,
      requestType: "explore"
    }
  }')

info "Invoking Lambda function directly..."
RESPONSE_1=$(aws lambda invoke \
  --function-name "$AGENT_FUNCTION" \
  --payload "$(echo "$PAYLOAD_1" | base64)" \
  --region "$REGION" \
  /dev/stdout 2>/dev/null | tail -n 1)

echo "Response 1:"
echo "$RESPONSE_1" | jq '.'
echo

# Test 2: Urgent reaction
info "Test 2: Testing urgent reaction to event..."
GAME_STATE_2='{
  "location": "forest_path",
  "timeOfDay": "night",
  "weather": "stormy",
  "nearbyObjects": ["fallen_tree", "glowing_mushroom"],
  "visibleCharacters": ["wolf_enemy"],
  "threats": ["wolf_enemy"],
  "dangerLevel": "high"
}'

CHARACTER_STATE_2='{
  "position": {"x": 500, "y": 0, "z": 200},
  "health": 60,
  "inventory": ["sword", "health_potion"],
  "currentAnimation": "combat_ready",
  "isMoving": false,
  "energy": 40,
  "inCombat": true
}'

PAYLOAD_2=$(jq -n \
  --arg agentId "$AGENT_ID" \
  --argjson gameState "$GAME_STATE_2" \
  --argjson characterState "$CHARACTER_STATE_2" \
  '{
    action: "agent_request",
    data: {
      agentId: $agentId,
      gameState: $gameState,
      characterState: $characterState,
      requestType: "react_to_threat",
      urgency: "high"
    }
  }')

RESPONSE_2=$(aws lambda invoke \
  --function-name "$AGENT_FUNCTION" \
  --payload "$(echo "$PAYLOAD_2" | base64)" \
  --region "$REGION" \
  /dev/stdout 2>/dev/null | tail -n 1)

echo "Response 2:"
echo "$RESPONSE_2" | jq '.'
echo

# Test 3: Social interaction
info "Test 3: Testing social interaction decision..."
GAME_STATE_3='{
  "location": "tavern",
  "timeOfDay": "evening",
  "weather": "clear",
  "nearbyObjects": ["bar", "fireplace", "table", "chair"],
  "visibleCharacters": ["bartender", "bard", "mysterious_stranger"],
  "socialContext": "friendly_gathering",
  "ambientSound": "music_playing"
}'

CHARACTER_STATE_3='{
  "position": {"x": 50, "y": 0, "z": 25},
  "health": 100,
  "inventory": ["gold_coins", "letter"],
  "currentAnimation": "idle",
  "isMoving": false,
  "energy": 90,
  "mood": "curious"
}'

PAYLOAD_3=$(jq -n \
  --arg agentId "$AGENT_ID" \
  --argjson gameState "$GAME_STATE_3" \
  --argjson characterState "$CHARACTER_STATE_3" \
  '{
    action: "agent_request",
    data: {
      agentId: $agentId,
      gameState: $gameState,
      characterState: $characterState,
      requestType: "social_interaction"
    }
  }')

RESPONSE_3=$(aws lambda invoke \
  --function-name "$AGENT_FUNCTION" \
  --payload "$(echo "$PAYLOAD_3" | base64)" \
  --region "$REGION" \
  /dev/stdout 2>/dev/null | tail -n 1)

echo "Response 3:"
echo "$RESPONSE_3" | jq '.'
echo

# Test WebSocket connection (requires wscat or similar)
if command -v wscat >/dev/null 2>&1; then
  info "Test 4: Testing WebSocket connection..."
  
  # Create test message
  WS_TEST_MSG=$(jq -n \
    --arg agentId "$AGENT_ID" \
    '{
      action: "agent_request",
      data: {
        agentId: $agentId,
        gameState: {
          location: "test_area",
          nearbyObjects: ["test_object"]
        },
        characterState: {
          position: {x: 0, y: 0, z: 0},
          health: 100
        },
        requestType: "test"
      }
    }')
  
  info "Sending test message via WebSocket..."
  echo "$WS_TEST_MSG" | wscat -c "$WS_ENDPOINT" -x - --wait 2 || true
else
  info "wscat not found, skipping WebSocket test"
  info "Install with: npm install -g wscat"
fi

# Check agent history
info "Checking agent decision history..."
aws dynamodb query \
  --table-name "${PROJECT}-agent-state" \
  --key-condition-expression "agentId = :aid" \
  --expression-attribute-values "{\":aid\": {\"S\": \"$AGENT_ID\"}}" \
  --limit 5 \
  --scan-index-forward false \
  --region "$REGION" \
  --output json | jq '.Items[] | {
    timestamp: .timestamp.N,
    decision: (.decision.M | {
      goal: .goal.S,
      action: .action.S,
      rationale: .rationale.S
    })
  }'

echo
info "=== AI Agent System Test Complete ==="
info "The AI agent responded to:"
info "  1. Basic exploration request"
info "  2. Urgent threat reaction"
info "  3. Social interaction scenario"
echo
info "To monitor agent decisions in real-time:"
info "  1. Start the enhanced MCP bridge"
info "  2. Connect Unreal Engine"
info "  3. View telemetry at: https://[cloudfront-domain]/index.html?ws=$WS_ENDPOINT"
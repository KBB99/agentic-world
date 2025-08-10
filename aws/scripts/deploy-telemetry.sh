#!/usr/bin/env bash
# Deploys Telemetry WebSocket stack (API Gateway WebSocket + Lambda + DynamoDB)
# Produces: aws/out/telemetry.outputs.json with:
#   - WebSocketWssUrl (e.g., wss://abc123.execute-api.us-east-1.amazonaws.com/prod)
#   - ConnectionTableName
#
# Usage:
#   REGION=us-east-1 PROJECT=agentic-demo STAGE=prod bash aws/scripts/deploy-telemetry.sh
#
# Requirements: awscli v2, jq

set -euo pipefail

# --- deps ---
if ! command -v aws >/dev/null; then
  echo "ERROR: aws CLI not found" 1>&2; exit 1
fi
if ! command -v jq >/dev/null; then
  echo "ERROR: jq not found" 1>&2; exit 1
fi

REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
STAGE="${STAGE:-prod}"

STACK_NAME="${STACK_NAME:-${PROJECT}-telemetry-${STAGE}}"
TEMPLATE="aws/templates/cfn/telemetry-websocket.yaml"

OUT_DIR="aws/out"
OUT_FILE="$OUT_DIR/telemetry.outputs.json"
mkdir -p "$OUT_DIR"

echo "Deploying Telemetry WebSocket stack: $STACK_NAME (region=$REGION, project=$PROJECT, stage=$STAGE)"
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --parameter-overrides \
    ProjectName="$PROJECT" \
    StageName="$STAGE" \
  --capabilities CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset

# Collect outputs → key:value JSON
tmp="$OUT_DIR/.telemetry-raw.json"
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output json > "$tmp"

jq 'map({(.OutputKey): .OutputValue}) | add' "$tmp" > "$OUT_FILE"
rm -f "$tmp"

echo "Telemetry outputs -> $OUT_FILE"
cat "$OUT_FILE"

echo
echo "To connect the viewer overlay, open:"
echo "  https://<cloudfrontDomain>/index.html?ws=$(jq -r '.WebSocketWssUrl' "$OUT_FILE")"
echo
echo "To publish a test telemetry message to all connections, use:"
echo "  bash aws/scripts/post-telemetry.sh --ws \"$(jq -r '.WebSocketWssUrl' "$OUT_FILE")\" --table \"$(jq -r '.ConnectionTableName' "$OUT_FILE")\" --goal \"Explore\" --action \"MoveForward\" --rationale \"Scanning area\" --result \"Started\""
#!/usr/bin/env bash
# Deploy AI Agent Orchestrator infrastructure
# Creates Lambda functions, DynamoDB tables, and WebSocket routes for AI-powered NPCs

set -euo pipefail

err() { echo "ERROR: $*" 1>&2; }
info() { echo "INFO: $*"; }
need() { command -v "$1" >/dev/null || { err "Missing dependency: $1"; exit 1; } }

need aws
need jq

# Configuration
REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
BEDROCK_MODEL="${BEDROCK_MODEL:-anthropic.claude-3-sonnet-20240229-v1:0}"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --bedrock-model) BEDROCK_MODEL="$2"; shift 2;;
    --help) 
      echo "Usage: $0 [--region REGION] [--project PROJECT] [--bedrock-model MODEL]"
      echo "  Deploys AI agent orchestrator infrastructure for Unreal Engine NPCs"
      echo "  Requires: Telemetry WebSocket stack must be deployed first"
      exit 0
      ;;
    *) err "Unknown arg: $1"; exit 1;;
  esac
done

STACK_NAME="${PROJECT}-agent-orchestrator"
OUT_DIR="aws/out"
mkdir -p "$OUT_DIR"

info "=== Deploying AI Agent Orchestrator ==="
info "Region:        $REGION"
info "Project:       $PROJECT"
info "Stack:         $STACK_NAME"
info "Bedrock Model: $BEDROCK_MODEL"
echo

# Check for telemetry stack outputs
TELEMETRY_OUTPUTS="$OUT_DIR/telemetry.outputs.json"
if [[ ! -f "$TELEMETRY_OUTPUTS" ]]; then
  err "Telemetry stack outputs not found at $TELEMETRY_OUTPUTS"
  err "Please deploy telemetry stack first: bash aws/scripts/deploy-telemetry.sh"
  exit 2
fi

# Get WebSocket API ID from telemetry outputs
WS_API_ID=$(jq -r '.WebSocketApiId // empty' "$TELEMETRY_OUTPUTS")
if [[ -z "$WS_API_ID" ]]; then
  err "WebSocket API ID not found in telemetry outputs"
  exit 2
fi

info "Using WebSocket API: $WS_API_ID"

# Package Lambda function
info "Packaging Lambda function..."
LAMBDA_DIR="aws/lambdas/agent-orchestrator"
if [[ ! -f "$LAMBDA_DIR/index.js" ]]; then
  err "Lambda function not found at $LAMBDA_DIR/index.js"
  exit 2
fi

# Create deployment package
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

cp "$LAMBDA_DIR/index.js" "$TEMP_DIR/"
cd "$TEMP_DIR"

# Create minimal package.json for dependencies
cat > package.json <<EOF
{
  "name": "agent-orchestrator",
  "version": "1.0.0",
  "dependencies": {
    "@aws-sdk/client-bedrock-runtime": "^3.0.0",
    "@aws-sdk/client-dynamodb": "^3.0.0",
    "@aws-sdk/client-apigatewaymanagementapi": "^3.0.0",
    "@aws-sdk/util-dynamodb": "^3.0.0"
  }
}
EOF

# Install dependencies
info "Installing Lambda dependencies..."
npm install --production --silent

# Create zip file
LAMBDA_ZIP="$OLDPWD/$OUT_DIR/agent-orchestrator.zip"
zip -qr "$LAMBDA_ZIP" .
cd "$OLDPWD"

info "Lambda package created: $LAMBDA_ZIP"

# Upload Lambda package to S3
LAMBDA_BUCKET="${PROJECT}-lambda-${REGION}-$(aws sts get-caller-identity --query Account --output text)"
LAMBDA_KEY="agent-orchestrator/function.zip"

info "Creating S3 bucket for Lambda code..."
aws s3api create-bucket \
  --bucket "$LAMBDA_BUCKET" \
  --region "$REGION" \
  $(if [ "$REGION" != "us-east-1" ]; then echo "--create-bucket-configuration LocationConstraint=$REGION"; fi) \
  2>/dev/null || true

info "Uploading Lambda package to S3..."
aws s3 cp "$LAMBDA_ZIP" "s3://$LAMBDA_BUCKET/$LAMBDA_KEY" \
  --region "$REGION"

# Deploy CloudFormation stack
info "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file aws/templates/cfn/agent-orchestrator.yaml \
  --stack-name "$STACK_NAME" \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Project="$PROJECT" \
    BedrockModel="$BEDROCK_MODEL" \
    WebSocketApiId="$WS_API_ID" \
  --region "$REGION" \
  --no-fail-on-empty-changeset

info "Waiting for stack to complete..."
aws cloudformation wait stack-create-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION" 2>/dev/null || \
aws cloudformation wait stack-update-complete \
  --stack-name "$STACK_NAME" \
  --region "$REGION" 2>/dev/null || true

# Get stack outputs
info "Retrieving stack outputs..."
OUTPUTS=$(aws cloudformation describe-stacks \
  --stack-name "$STACK_NAME" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs' \
  --output json)

# Parse outputs
AGENT_FUNCTION_ARN=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="AgentOrchestratorFunctionArn") | .OutputValue')
AGENT_STATE_TABLE=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="AgentStateTableName") | .OutputValue')
AGENT_CONTEXT_TABLE=$(echo "$OUTPUTS" | jq -r '.[] | select(.OutputKey=="AgentContextTableName") | .OutputValue')

# Save outputs
AGENT_OUTPUTS="$OUT_DIR/agent-ai.outputs.json"
cat > "$AGENT_OUTPUTS" <<EOF
{
  "AgentOrchestratorFunctionArn": "$AGENT_FUNCTION_ARN",
  "AgentStateTable": "$AGENT_STATE_TABLE",
  "AgentContextTable": "$AGENT_CONTEXT_TABLE",
  "WebSocketApiId": "$WS_API_ID",
  "BedrockModel": "$BEDROCK_MODEL",
  "Region": "$REGION",
  "StackName": "$STACK_NAME"
}
EOF

info "Outputs saved to: $AGENT_OUTPUTS"

# Update aggregated outputs
if [[ -f "$OUT_DIR/stack-outputs.json" ]]; then
  info "Updating aggregated outputs..."
  jq --slurpfile agent "$AGENT_OUTPUTS" \
    '. + {agentAI: $agent[0]}' \
    "$OUT_DIR/stack-outputs.json" > "$OUT_DIR/stack-outputs.tmp.json" && \
  mv "$OUT_DIR/stack-outputs.tmp.json" "$OUT_DIR/stack-outputs.json"
fi

# Initialize sample agent context
info "Initializing sample agent context..."
aws dynamodb put-item \
  --table-name "$AGENT_CONTEXT_TABLE" \
  --item '{
    "agentId": {"S": "npc_001"},
    "context": {"M": {
      "personality": {"S": "curious and friendly"},
      "goals": {"L": [
        {"S": "explore the environment"},
        {"S": "interact with players"}
      ]},
      "emotional_state": {"S": "happy"},
      "knowledge": {"M": {}},
      "relationships": {"M": {}},
      "memory_summary": {"S": ""}
    }}
  }' \
  --region "$REGION" 2>/dev/null || true

echo
info "=== AI Agent Orchestrator Deployment Complete ==="
info "Agent Function ARN: $AGENT_FUNCTION_ARN"
info "State Table:        $AGENT_STATE_TABLE"
info "Context Table:      $AGENT_CONTEXT_TABLE"
echo
info "Next steps:"
info "1. Start the AI-enhanced MCP bridge:"
info "   node mcp-bridge/index-ai.js --wss wss://$WS_API_ID.execute-api.$REGION.amazonaws.com/prod --agent-id npc_001"
info "2. Configure Unreal Engine MCP server to connect on 127.0.0.1:32123"
info "3. Test AI agent with: bash aws/scripts/test-agent-ai.sh"
echo
info "To remove this stack later:"
info "   aws cloudformation delete-stack --stack-name $STACK_NAME --region $REGION"
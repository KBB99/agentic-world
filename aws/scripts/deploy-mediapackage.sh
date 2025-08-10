#!/usr/bin/env bash
# Deploys AWS Elemental MediaPackage (Channel + HLS OriginEndpoint) via CloudFormation
set -euo pipefail

# Requirements: awscli v2, jq
if ! command -v aws >/dev/null; then
  echo "ERROR: aws CLI not found" 1>&2; exit 1
fi
if ! command -v jq >/dev/null; then
  echo "ERROR: jq not found" 1>&2; exit 1
fi

REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
STACK_NAME="${STACK_NAME:-${PROJECT}-mp}"
TEMPLATE="aws/templates/cfn/mediapackage.yaml"
OUT_DIR="aws/out"
OUT_FILE="$OUT_DIR/mediapackage.outputs.json"

mkdir -p "$OUT_DIR"

echo "Deploying MediaPackage stack: $STACK_NAME (region=$REGION, project=$PROJECT)"
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --parameter-overrides \
    ProjectName="$PROJECT" \
    HlsManifestName="index" \
    SegmentDurationSeconds="2" \
    PlaylistWindowSeconds="6" \
  --no-fail-on-empty-changeset

# Collect outputs as key:value JSON
tmp="$OUT_DIR/.mp-raw.json"
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output json > "$tmp"

jq 'map({(.OutputKey): .OutputValue}) | add' "$tmp" > "$OUT_FILE"
rm -f "$tmp"

echo "MediaPackage outputs -> $OUT_FILE"
cat "$OUT_FILE"
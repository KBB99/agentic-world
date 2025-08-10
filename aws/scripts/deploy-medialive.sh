#!/usr/bin/env bash
# Deploys AWS Elemental MediaLive (RTMP push Input + Channel to MediaPackage) via CloudFormation
# - Requires MediaPackage to be deployed first (aws/out/mediapackage.outputs.json)
# - Produces:
#   - aws/out/medialive.outputs.json (CFN outputs)
#   - aws/out/medialive.ingest.json (RTMP ingest URLs for OBS/ffmpeg)

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
STACK_NAME="${STACK_NAME:-${PROJECT}-ml}"

TEMPLATE="aws/templates/cfn/medialive.yaml"
OUT_DIR="aws/out"
MP_OUT="$OUT_DIR/mediapackage.outputs.json"
ML_OUT="$OUT_DIR/medialive.outputs.json"
ML_INGEST="$OUT_DIR/medialive.ingest.json"

if [ ! -f "$MP_OUT" ]; then
  echo "ERROR: Missing $MP_OUT. Run aws/scripts/deploy-mediapackage.sh first." 1>&2
  exit 2
fi

MEDIA_PACKAGE_CHANNEL_ID="$(jq -r '.MediaPackageChannelId // empty' "$MP_OUT")"
if [ -z "$MEDIA_PACKAGE_CHANNEL_ID" ] || [ "$MEDIA_PACKAGE_CHANNEL_ID" = "null" ]; then
  echo "ERROR: Could not read MediaPackageChannelId from $MP_OUT" 1>&2
  exit 2
fi

mkdir -p "$OUT_DIR"

# Preflight: if a previous attempt left the stack in a terminal failed state (e.g., ROLLBACK_COMPLETE),
# delete it before re-deploying, otherwise 'cloudformation deploy' cannot update it.
STATUS="$(aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK_NAME" --query 'Stacks[0].StackStatus' --output text 2>/dev/null || true)"
if [[ "$STATUS" == "ROLLBACK_COMPLETE" || "$STATUS" == "ROLLBACK_FAILED" || "$STATUS" == "DELETE_FAILED" || "$STATUS" == "CREATE_FAILED" ]]; then
  echo "Existing stack $STACK_NAME is in status $STATUS; deleting before redeploy..."
  aws cloudformation delete-stack --region "$REGION" --stack-name "$STACK_NAME"
  echo "Waiting for stack deletion to complete..."
  aws cloudformation wait stack-delete-complete --region "$REGION" --stack-name "$STACK_NAME"
fi

echo "Deploying MediaLive stack: $STACK_NAME (region=$REGION, project=$PROJECT)"
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$TEMPLATE" \
  --parameter-overrides \
    ProjectName="$PROJECT" \
    MediaPackageChannelId="$MEDIA_PACKAGE_CHANNEL_ID" \
  --capabilities CAPABILITY_IAM \
  --no-fail-on-empty-changeset

# Collect CFN outputs
tmp="$OUT_DIR/.ml-raw.json"
aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs" \
  --output json > "$tmp"

jq 'map({(.OutputKey): .OutputValue}) | add' "$tmp" > "$ML_OUT"
rm -f "$tmp"

echo "MediaLive CFN outputs -> $ML_OUT"
cat "$ML_OUT"

# Retrieve RTMP ingest endpoints for the created Input
ML_INPUT_ID="$(jq -r '.MediaLiveInputId // empty' "$ML_OUT")"
if [ -z "$ML_INPUT_ID" ] || [ "$ML_INPUT_ID" = "null" ]; then
  echo "WARN: MediaLiveInputId not present in outputs, skipping ingest endpoint retrieval." 1>&2
  exit 0
fi

echo "Describing MediaLive Input: $ML_INPUT_ID"
# This returns one or two destinations depending on SINGLE_PIPELINE vs STANDARD
aws medialive describe-input \
  --region "$REGION" \
  --input-id "$ML_INPUT_ID" \
  --output json > "$OUT_DIR/.ml-input.json"

# Extract up to two destination URLs
PRIMARY_URL="$(jq -r '.Destinations[0].Url // empty' "$OUT_DIR/.ml-input.json")"
BACKUP_URL="$(jq -r '.Destinations[1].Url // empty' "$OUT_DIR/.ml-input.json")"

jq -n --arg primary "$PRIMARY_URL" --arg backup "$BACKUP_URL" '{
  primaryUrl: ($primary // ""),
  backupUrl: ($backup // "")
}' > "$ML_INGEST"

rm -f "$OUT_DIR/.ml-input.json"

echo "MediaLive ingest endpoints -> $ML_INGEST"
cat "$ML_INGEST"

echo
echo "Next:"
echo "  - Configure OBS/ffmpeg to stream to the 'primaryUrl' in $ML_INGEST."
echo "  - Start the MediaLive Channel (can be started from AWS Console or via CLI):"
echo "      aws medialive start-channel --region $REGION --channel-id \"$(jq -r '.MediaLiveChannelId' "$ML_OUT")\""
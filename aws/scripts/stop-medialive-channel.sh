#!/usr/bin/env bash
# Stop the MediaLive Channel using outputs from aws/out/medialive.outputs.json
set -euo pipefail

if ! command -v aws >/dev/null; then
  echo "ERROR: aws CLI not found" 1>&2; exit 1
fi
if ! command -v jq >/dev/null; then
  echo "ERROR: jq not found" 1>&2; exit 1
fi

REGION="${REGION:-us-east-1}"
OUT_DIR="aws/out"
ML_OUT="$OUT_DIR/medialive.outputs.json"

if [[ ! -f "$ML_OUT" ]]; then
  echo "ERROR: Missing $ML_OUT. Deploy MediaLive first." 1>&2
  exit 2
fi

CHANNEL_ID="$(jq -r '.MediaLiveChannelId // empty' "$ML_OUT")"
if [[ -z "$CHANNEL_ID" || "$CHANNEL_ID" == "null" ]]; then
  echo "ERROR: MediaLiveChannelId missing in $ML_OUT" 1>&2
  exit 2
fi

echo "Stopping MediaLive Channel: $CHANNEL_ID (region=$REGION)"
aws medialive stop-channel --region "$REGION" --channel-id "$CHANNEL_ID" >/dev/null || true

echo "Stop requested. Current state:"
aws medialive describe-channel --region "$REGION" --channel-id "$CHANNEL_ID" --query 'State' --output text
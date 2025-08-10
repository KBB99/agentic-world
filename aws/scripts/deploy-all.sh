#!/usr/bin/env bash
# Orchestrate end-to-end deploy:
# - MediaPackage (Channel + HLS)
# - MediaLive (RTMP Input + Channel to MediaPackage)
# - CloudFront + viewer upload (dual origins + /live/* behavior)
# - Aggregate outputs
#
# Safety: This does NOT start the MediaLive Channel automatically (to avoid unexpected cost).
# You can start it later with: bash aws/scripts/start-medialive-channel.sh
#
# Requirements: awscli v2, jq, node

set -euo pipefail

err() { echo "ERROR: $*" 1>&2; }
need() { command -v "$1" >/dev/null || { err "Missing dependency: $1"; exit 1; } }

need aws
need jq
need node

REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
BUCKET="${BUCKET:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --region) REGION="$2"; shift 2;;
    --project) PROJECT="$2"; shift 2;;
    --bucket) BUCKET="$2"; shift 2;;
    *) err "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$BUCKET" ]]; then
  err "BUCKET is required (use --bucket or set env BUCKET)"
  exit 2
fi

echo "=== Deploy All ==="
echo "Region:  $REGION"
echo "Project: $PROJECT"
echo "Bucket:  $BUCKET"
echo

# 1) MediaPackage
echo "Step 1/4: Deploy MediaPackage"
REGION="$REGION" PROJECT="$PROJECT" bash aws/scripts/deploy-mediapackage.sh
echo

# 2) MediaLive
echo "Step 2/4: Deploy MediaLive"
REGION="$REGION" PROJECT="$PROJECT" bash aws/scripts/deploy-medialive.sh
echo

# 3) CloudFront + viewer
echo "Step 3/4: Deploy CloudFront and upload viewer"
REGION="$REGION" PROJECT="$PROJECT" BUCKET="$BUCKET" bash aws/scripts/deploy-cloudfront-and-viewer.sh --bucket "$BUCKET"
echo

# 4) Aggregate outputs
echo "Step 4/4: Aggregate outputs"
bash aws/scripts/aggregate-outputs.sh
echo

echo "=== Deploy Complete ==="
if [[ -f aws/out/stack-outputs.json ]]; then
  echo "Outputs (aws/out/stack-outputs.json):"
  cat aws/out/stack-outputs.json | jq .
fi
echo
echo "Next steps:"
echo "  1) Start MediaLive Channel when ready to stream:"
echo "       bash aws/scripts/start-medialive-channel.sh"
echo "  2) Push a test RTMP stream with ffmpeg (optional):"
echo "       bash aws/scripts/test-ffmpeg-push.sh"
echo "  3) Open the viewer (replace domain):"
echo "       https://<cloudfrontDomainName>/index.html"
echo
echo "Reference runbook: docs/RUNBOOK.md"
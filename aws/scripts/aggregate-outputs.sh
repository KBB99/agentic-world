#!/usr/bin/env bash
# Aggregate deploy outputs into aws/out/stack-outputs.json (matches schema: aws/out/stack-outputs.schema.json)
# Requires: jq, node (for URL parsing portability)

set -euo pipefail

err() { echo "ERROR: $*" 1>&2; }
need() { command -v "$1" >/dev/null || { err "Missing dependency: $1"; exit 1; } }

need jq
need node

OUT_DIR="aws/out"
SCHEMA_PATH="aws/out/stack-outputs.schema.json"
CF_OUT="$OUT_DIR/cloudfront.outputs.json"
MP_OUT="$OUT_DIR/mediapackage.outputs.json"
ML_OUT="$OUT_DIR/medialive.outputs.json"
DST="$OUT_DIR/stack-outputs.json"

# Basic checks
[[ -f "$CF_OUT" ]] || { err "Missing $CF_OUT. Run CloudFront+viewer deployment first."; exit 2; }
[[ -f "$MP_OUT" ]] || { err "Missing $MP_OUT. Run MediaPackage deployment first."; exit 2; }
[[ -f "$ML_OUT" ]] || { err "Missing $ML_OUT. Run MediaLive deployment first."; exit 2; }
[[ -f "$SCHEMA_PATH" ]] || { err "Missing schema $SCHEMA_PATH (should ship in repo)."; exit 2; }

# Read CF values
projectName="$(jq -r '.projectName // empty' "$CF_OUT")"
region="$(jq -r '.region // empty' "$CF_OUT")"
viewerBucketName="$(jq -r '.viewerBucketName // empty' "$CF_OUT")"
viewerBucketDomain="$(jq -r '.viewerBucketDomain // empty' "$CF_OUT")"
cloudfrontDistributionId="$(jq -r '.cloudfrontDistributionId // empty' "$CF_OUT")"
cloudfrontDomainName="$(jq -r '.cloudfrontDomainName // empty' "$CF_OUT")"
liveFunctionName="$(jq -r '.liveFunctionName // empty' "$CF_OUT")"
liveFunctionArn="$(jq -r '.liveFunctionArn // empty' "$CF_OUT")"

# Fallbacks for project/region if not in CF_OUT
projectName="${projectName:-${PROJECT:-agentic-demo}}"
region="${region:-${REGION:-us-east-1}}"

# Read MP values
mediaPackageChannelId="$(jq -r '.MediaPackageChannelId // empty' "$MP_OUT")"
mediaPackageChannelArn="$(jq -r '.MediaPackageChannelArn // empty' "$MP_OUT")"
mediaPackageHlsEndpointId="$(jq -r '.HlsEndpointId // empty' "$MP_OUT")"
mediaPackageHlsEndpointUrl="$(jq -r '.HlsEndpointUrl // empty' "$MP_OUT")"

# Derive MP host + path (origin path = parent dir of manifest)
if [[ -z "$mediaPackageHlsEndpointUrl" || "$mediaPackageHlsEndpointUrl" == "null" ]]; then
  err "HlsEndpointUrl not present in $MP_OUT"
  exit 2
fi
mediaPackageOriginDomain="$(node -e 'const u=new URL(process.argv[1]);console.log(u.host)' "$mediaPackageHlsEndpointUrl")"
mediaPackageOriginPath="$(echo "$mediaPackageHlsEndpointUrl" | sed -E 's#https?://[^/]+(/.*)/[^/]+$#\1#')"

# Read ML values
mediaLiveInputId="$(jq -r '.MediaLiveInputId // empty' "$ML_OUT")"
mediaLiveChannelId="$(jq -r '.MediaLiveChannelId // empty' "$ML_OUT")"
mediaLiveChannelArn="$(jq -r '.MediaLiveChannelArn // empty' "$ML_OUT")"

# Validate required fields (as per schema)
required_missing=()
for kv in \
  "projectName:$projectName" \
  "region:$region" \
  "viewerBucketName:$viewerBucketName" \
  "viewerBucketDomain:$viewerBucketDomain" \
  "cloudfrontDistributionId:$cloudfrontDistributionId" \
  "cloudfrontDomainName:$cloudfrontDomainName" \
  "liveFunctionName:$liveFunctionName" \
  "liveFunctionArn:$liveFunctionArn" \
  "mediaPackageChannelId:$mediaPackageChannelId" \
  "mediaPackageChannelArn:$mediaPackageChannelArn" \
  "mediaPackageHlsEndpointId:$mediaPackageHlsEndpointId" \
  "mediaPackageHlsEndpointUrl:$mediaPackageHlsEndpointUrl" \
  "mediaPackageOriginDomain:$mediaPackageOriginDomain" \
  "mediaPackageOriginPath:$mediaPackageOriginPath" \
  "mediaLiveInputId:$mediaLiveInputId" \
  "mediaLiveChannelId:$mediaLiveChannelId" \
  "mediaLiveChannelArn:$mediaLiveChannelArn"
do
  key="${kv%%:*}"
  val="${kv#*:}"
  if [[ -z "$val" || "$val" == "null" ]]; then
    required_missing+=("$key")
  fi
done

if (( ${#required_missing[@]} > 0 )); then
  err "Missing required fields: ${required_missing[*]}"
  err "Ensure prior deploy steps completed successfully."
  exit 3
fi

# Write outputs JSON
tmp="$OUT_DIR/.stack-outputs.tmp.json"
jq -n \
  --arg projectName "$projectName" \
  --arg region "$region" \
  --arg viewerBucketName "$viewerBucketName" \
  --arg viewerBucketDomain "$viewerBucketDomain" \
  --arg cloudfrontDistributionId "$cloudfrontDistributionId" \
  --arg cloudfrontDomainName "$cloudfrontDomainName" \
  --arg liveFunctionName "$liveFunctionName" \
  --arg liveFunctionArn "$liveFunctionArn" \
  --arg mediaPackageChannelId "$mediaPackageChannelId" \
  --arg mediaPackageChannelArn "$mediaPackageChannelArn" \
  --arg mediaPackageHlsEndpointId "$mediaPackageHlsEndpointId" \
  --arg mediaPackageHlsEndpointUrl "$mediaPackageHlsEndpointUrl" \
  --arg mediaPackageOriginDomain "$mediaPackageOriginDomain" \
  --arg mediaPackageOriginPath "$mediaPackageOriginPath" \
  --arg mediaLiveInputId "$mediaLiveInputId" \
  --arg mediaLiveChannelId "$mediaLiveChannelId" \
  --arg mediaLiveChannelArn "$mediaLiveChannelArn" \
  '{
    projectName: $projectName,
    region: $region,
    viewerBucketName: $viewerBucketName,
    viewerBucketDomain: $viewerBucketDomain,
    cloudfrontDistributionId: $cloudfrontDistributionId,
    cloudfrontDomainName: $cloudfrontDomainName,
    liveFunctionName: $liveFunctionName,
    liveFunctionArn: $liveFunctionArn,
    mediaPackageChannelId: $mediaPackageChannelId,
    mediaPackageChannelArn: $mediaPackageChannelArn,
    mediaPackageHlsEndpointId: $mediaPackageHlsEndpointId,
    mediaPackageHlsEndpointUrl: $mediaPackageHlsEndpointUrl,
    mediaPackageOriginDomain: $mediaPackageOriginDomain,
    mediaPackageOriginPath: $mediaPackageOriginPath,
    mediaLiveInputId: $mediaLiveInputId,
    mediaLiveChannelId: $mediaLiveChannelId,
    mediaLiveChannelArn: $mediaLiveChannelArn
  }' > "$tmp"

mv "$tmp" "$DST"
echo "Wrote $DST"
#!/usr/bin/env bash
# Deploy S3 viewer site and CloudFront distribution with dual origins (S3 + MediaPackage)
# - Requires: awscli v2, jq, node
# - Inputs (env or flags):
#     REGION         (default: us-east-1)
#     PROJECT        (default: agentic-demo)
#     BUCKET         (required; S3 bucket for viewer site)
# - Requires MediaPackage stack outputs at aws/out/mediapackage.outputs.json
# - Produces:
#     aws/out/cloudfront.config.json
#     aws/out/cloudfront.outputs.json
#     aws/out/viewer.bucket.policy.json
# - Associates CloudFront Function [strip-live-uri.js](aws/functions/strip-live-uri.js:1) to handle /live/* path

set -euo pipefail

# --- Helpers ---
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

if [[ -z "${BUCKET}" ]]; then
  err "BUCKET is required (use --bucket or set env BUCKET)"
  exit 2
fi

OUT_DIR="aws/out"
TEMPLATE_CF="aws/templates/cloudfront-viewer-and-live.json.tpl"
TEMPLATE_POLICY="aws/templates/s3-bucket-policy-oac.json.tpl"
RENDER="aws/tools/render-template.js"
FN_CODE="aws/functions/strip-live-uri.js"
MP_OUT="$OUT_DIR/mediapackage.outputs.json"

mkdir -p "$OUT_DIR"

if [[ ! -f "$MP_OUT" ]]; then
  err "Missing $MP_OUT. Run [aws/scripts/deploy-mediapackage.sh](aws/scripts/deploy-mediapackage.sh:1) first."
  exit 2
fi

# --- Parse MediaPackage HLS endpoint URL into domain + origin path ---
MP_URL="$(jq -r '.HlsEndpointUrl // empty' "$MP_OUT")"
if [[ -z "$MP_URL" || "$MP_URL" == "null" ]]; then
  err "HlsEndpointUrl not found in $MP_OUT"
  exit 2
fi

MP_DOMAIN="$(node -e 'const u=new URL(process.argv[1]);console.log(u.host)' "$MP_URL")"
# OriginPath is the parent directory of the manifest (strip trailing filename)
MP_ORIGIN_PATH="$(node -e 'const u=new URL(process.argv[1]);const p=u.pathname;const i=p.lastIndexOf("/");console.log(i>0?p.slice(0,i):"/");' "$MP_URL")"
if [[ -z "$MP_DOMAIN" || -z "$MP_ORIGIN_PATH" ]]; then
  err "Failed to parse MediaPackage URL: $MP_URL"
  exit 2
fi

# --- Create or ensure S3 bucket exists ---
echo "Ensuring S3 bucket exists: $BUCKET (region=$REGION)"
if aws s3api head-bucket --bucket "$BUCKET" 2>/dev/null; then
  echo "Bucket exists: $BUCKET"
else
  if [[ "$REGION" == "us-east-1" ]]; then
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"
  else
    aws s3api create-bucket --bucket "$BUCKET" --region "$REGION" \
      --create-bucket-configuration LocationConstraint="$REGION"
  fi
  echo "Created bucket: $BUCKET"
fi

# Bucket policy will be applied after the CloudFront distribution is created (requires distribution ARN)

# --- Upload viewer files ---
echo "Syncing viewer/ -> s3://$BUCKET/"
aws s3 sync viewer/ "s3://$BUCKET/" --delete --cache-control "max-age=60"

# --- Ensure CloudFront Origin Access Control (OAC) for S3 origin ---
OAC_NAME="${PROJECT}-viewer-oac"
echo "Ensuring CloudFront Origin Access Control: $OAC_NAME"
OAC_ID="$(aws cloudfront list-origin-access-controls --query 'OriginAccessControlList.Items[?Name==`'"$OAC_NAME"'`].Id' --output text 2>/dev/null || true)"
if [[ -z "$OAC_ID" || "$OAC_ID" == "None" ]]; then
  OAC_CFG="$OUT_DIR/.oac.json"
  cat > "$OAC_CFG" << 'JSON'
{
  "Name": "__OAC_NAME__",
  "Description": "S3 OAC for agentic viewer",
  "OriginAccessControlOriginType": "s3",
  "SigningBehavior": "always",
  "SigningProtocol": "sigv4"
}
JSON
  # inject name
  sed -i '' -e "s|__OAC_NAME__|$OAC_NAME|g" "$OAC_CFG" 2>/dev/null || sed -i -e "s|__OAC_NAME__|$OAC_NAME|g" "$OAC_CFG"
  OAC_CREATE_JSON="$OUT_DIR/.oac-create.json"
  aws cloudfront create-origin-access-control \
    --origin-access-control-config "file://$OAC_CFG" \
    --output json > "$OAC_CREATE_JSON"
  OAC_ID="$(jq -r '.OriginAccessControl.Id' "$OAC_CREATE_JSON")"
fi
if [[ -z "$OAC_ID" || "$OAC_ID" == "None" ]]; then
  err "Failed to create or locate CloudFront OAC"
  exit 2
fi
echo "CloudFront OAC Id: $OAC_ID"

# --- Create/Update CloudFront Function for /live prefix stripping ---
FN_NAME="${PROJECT}-strip-live"
echo "Publishing CloudFront Function: $FN_NAME"

# Try create; if exists, update
CREATE_JSON="$OUT_DIR/.cf-fn-create.json"
UPDATE_JSON="$OUT_DIR/.cf-fn-update.json"
PUB_JSON="$OUT_DIR/.cf-fn-publish.json"

set +e
aws cloudfront create-function \
  --name "$FN_NAME" \
  --function-config Comment="Strip /live prefix",Runtime="cloudfront-js-1.0" \
  --function-code "fileb://$FN_CODE" \
  --output json > "$CREATE_JSON" 2>"$OUT_DIR/.cf-fn-create.err"
rc=$?
set -e

if [[ $rc -ne 0 ]]; then
  # Update existing
  echo "Function exists; updating: $FN_NAME"
  ETag="$(aws cloudfront describe-function --name "$FN_NAME" --output json | jq -r '.ETag')"
  aws cloudfront update-function \
    --name "$FN_NAME" \
    --if-match "$ETag" \
    --function-config Comment="Strip /live prefix",Runtime="cloudfront-js-1.0" \
    --function-code "fileb://$FN_CODE" \
    --output json > "$UPDATE_JSON"
  ETag="$(jq -r '.ETag' "$UPDATE_JSON")"
else
  ETag="$(jq -r '.ETag' "$CREATE_JSON")"
fi

aws cloudfront publish-function --name "$FN_NAME" --if-match "$ETag" --output json > "$PUB_JSON"
FN_ARN="$(jq -r '.FunctionSummary.FunctionMetadata.FunctionARN' "$PUB_JSON")"
if [[ -z "$FN_ARN" || "$FN_ARN" == "null" ]]; then
  err "Failed to resolve Function ARN for $FN_NAME"
  exit 2
fi
echo "CloudFront Function ARN: $FN_ARN"

# --- Render CloudFront distribution config ---
CALLER_REF="$(date +%s)-$RANDOM"
# Use regional S3 REST endpoint for origin
BUCKET_DOMAIN="${BUCKET}.s3.${REGION}.amazonaws.com"
CF_CONF="$OUT_DIR/cloudfront.config.json"

echo "Rendering CloudFront distribution config -> $CF_CONF"
node "$RENDER" "$TEMPLATE_CF" "$CF_CONF" \
  "{\"BUCKET_DOMAIN\":\"$BUCKET_DOMAIN\",\"MP_DOMAIN\":\"$MP_DOMAIN\",\"MP_ORIGIN_PATH\":\"$MP_ORIGIN_PATH\",\"LIVE_FN_ARN\":\"$FN_ARN\",\"CALLER_REF\":\"$CALLER_REF\",\"OAC_ID\":\"$OAC_ID\"}"

# --- Create CloudFront distribution ---
CF_CREATE_JSON="$OUT_DIR/.cf-create.json"
echo "Creating CloudFront distribution"
aws cloudfront create-distribution \
  --distribution-config "file://$CF_CONF" \
  --output json > "$CF_CREATE_JSON"

CF_ID="$(jq -r '.Distribution.Id' "$CF_CREATE_JSON")"
CF_DOMAIN="$(jq -r '.Distribution.DomainName' "$CF_CREATE_JSON")"
CF_ARN="$(jq -r '.Distribution.ARN // .Distribution.Arn // empty' "$CF_CREATE_JSON")"
if [[ -z "$CF_ID" || -z "$CF_DOMAIN" ]]; then
  err "Failed to create CloudFront distribution; see $CF_CREATE_JSON"
  exit 2
fi
if [[ -z "$CF_ARN" || "$CF_ARN" == "null" ]]; then
  ACCT="$(aws sts get-caller-identity --query Account --output text)"
  CF_ARN="arn:aws:cloudfront::${ACCT}:distribution/${CF_ID}"
fi

CF_OUT="$OUT_DIR/cloudfront.outputs.json"
jq -n \
  --arg project "$PROJECT" \
  --arg region "$REGION" \
  --arg bucket "$BUCKET" \
  --arg bucketDomain "$BUCKET_DOMAIN" \
  --arg distId "$CF_ID" \
  --arg distDomain "$CF_DOMAIN" \
  --arg fnName "$FN_NAME" \
  --arg fnArn "$FN_ARN" \
  '{
    projectName: $project,
    region: $region,
    viewerBucketName: $bucket,
    viewerBucketDomain: $bucketDomain,
    cloudfrontDistributionId: $distId,
    cloudfrontDomainName: $distDomain,
    liveFunctionName: $fnName,
    liveFunctionArn: $fnArn
  }' > "$CF_OUT"

echo "CloudFront outputs -> $CF_OUT"
cat "$CF_OUT"

# --- Apply S3 bucket policy for OAC access (after distribution creation to get ARN) ---
POL_OUT="$OUT_DIR/viewer.bucket.policy.json"
echo "Rendering bucket policy -> $POL_OUT (OAC-based)"
node "$RENDER" "$TEMPLATE_POLICY" "$POL_OUT" "{\"BUCKET_NAME\":\"$BUCKET\",\"CF_DISTRIBUTION_ARN\":\"$CF_ARN\"}"

echo "Applying bucket policy (OAC)"
aws s3api put-bucket-policy --bucket "$BUCKET" --policy "file://$POL_OUT"

echo
echo "Viewer URL (static):     https://$CF_DOMAIN/index.html"
echo "Live manifest (expected): https://$CF_DOMAIN/live/index.m3u8"
echo
echo "Note: Distribution status will be InProgress for a few minutes while propagating."
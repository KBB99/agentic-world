#!/usr/bin/env bash
# Broadcast a telemetry message to all connected WebSocket clients
# Uses DynamoDB table of connectionIds and API Gateway Management API to post the payload.
#
# Requirements: awscli v2, jq, node (for robust URL parsing)
#
# Usage:
#   bash aws/scripts/post-telemetry.sh \
#     --ws wss://abc123.execute-api.us-east-1.amazonaws.com/prod \
#     --table agentic-demo-telemetry-connections \
#     --goal "Explore the room" \
#     --action "MoveForward" \
#     --rationale "Scanning area" \
#     --result "Started"
#
# Notes:
# - REGION may be inferred from --ws, or override with env REGION=... or --region ...
# - Payload fields are optional; only provided fields are sent.

set -euo pipefail

err() { echo "ERROR: $*" 1>&2; }
need() { command -v "$1" >/dev/null || { err "Missing dependency: $1"; exit 1; } }
need aws
need jq
need node

WS_URL=""
TABLE=""
GOAL=""
ACT=""
RATIONALE=""
RESULT=""
REGION="${REGION:-}"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ws) WS_URL="$2"; shift 2;;
    --table) TABLE="$2"; shift 2;;
    --goal) GOAL="$2"; shift 2;;
    --action) ACT="$2"; shift 2;;
    --rationale) RATIONALE="$2"; shift 2;;
    --result) RESULT="$2"; shift 2;;
    --region) REGION="$2"; shift 2;;
    *) err "Unknown arg: $1"; exit 1;;
  esac
done

[[ -n "$WS_URL" ]] || { err "--ws is required (WebSocket WSS URL)"; exit 2; }
[[ -n "$TABLE" ]] || { err "--table is required (DynamoDB connections table)"; exit 2; }

# Derive endpoint-url for API Gateway Management API (https://host/stage)
ENDPOINT_URL="$(node -e 'const u=new URL(process.argv[1]); console.log(`https://${u.host}${u.pathname}`)' "$WS_URL" 2>/dev/null || true)"
[[ -n "$ENDPOINT_URL" ]] || { err "Failed to parse endpoint-url from --ws '$WS_URL'"; exit 2; }

# Infer region from host if not provided
if [[ -z "$REGION" ]]; then
  REGION="$(node -e 'const h=new URL(process.argv[1]).host; const m=h.match(/execute-api\.([a-z0-9-]+)\.amazonaws\.com$/); if(!m){process.exit(2)} console.log(m[1])' "$WS_URL" 2>/dev/null || true)"
fi
[[ -n "$REGION" ]] || { err "Failed to infer region; provide --region or set REGION=..."; exit 2; }

# Build compact JSON payload (only include provided fields)
PAYLOAD="$(jq -c -n \
  --arg goal "$GOAL" \
  --arg action "$ACT" \
  --arg rationale "$RATIONALE" \
  --arg result "$RESULT" \
  '{
     goal:       ( ($goal       | select(length>0)) // empty ),
     action:     ( ($action     | select(length>0)) // empty ),
     rationale:  ( ($rationale  | select(length>0)) // empty ),
     result:     ( ($result     | select(length>0)) // empty )
   } | with_entries(select(.value != null))')"

if [[ "$PAYLOAD" == "{}" ]]; then
  err "No telemetry fields provided; set at least one of --goal/--action/--rationale/--result"
  exit 2
fi

echo "Region:        $REGION"
echo "Endpoint URL:  $ENDPOINT_URL"
echo "Table:         $TABLE"
echo "Payload:       $PAYLOAD"
echo

# Scan all connectionIds (demo scale)
TMP_SCAN="$(mktemp)"
aws dynamodb scan \
  --region "$REGION" \
  --table-name "$TABLE" \
  --projection-expression "connectionId" \
  --output json > "$TMP_SCAN"

CONNECTIONS=( $(jq -r '.Items[].connectionId.S // empty' "$TMP_SCAN") )
rm -f "$TMP_SCAN"

if (( ${#CONNECTIONS[@]} == 0 )); then
  err "No active connections found in table '$TABLE'"
  exit 3
fi

# Write payload to a temp file for fileb:// posting
TMP_DATA="$(mktemp)"
printf '%s' "$PAYLOAD" > "$TMP_DATA"

SENT=0
CLEANED=0
for CID in "${CONNECTIONS[@]}"; do
  set +e
  aws apigatewaymanagementapi post-to-connection \
    --region "$REGION" \
    --endpoint-url "$ENDPOINT_URL" \
    --connection-id "$CID" \
    --data "fileb://$TMP_DATA" >/dev/null 2> >(tee /tmp/post-err.$$ >&2)
  rc=$?
  set -e
  if [[ $rc -ne 0 ]]; then
    # If Gone (410), clean up the stale connection
    if grep -qi "GoneException" /tmp/post-err.$$; then
      aws dynamodb delete-item \
        --region "$REGION" \
        --table-name "$TABLE" \
        --key "{\"connectionId\":{\"S\":\"$CID\"}}" >/dev/null || true
      ((CLEANED++))
    else
      echo "WARN: post-to-connection failed for $CID (rc=$rc)"
    fi
  else
    ((SENT++))
  fi
  rm -f /tmp/post-err.$$ || true
done

rm -f "$TMP_DATA"

echo
echo "Broadcast complete: sent=$SENT cleaned=$CLEANED stale connections"
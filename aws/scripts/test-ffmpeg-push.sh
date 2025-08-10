#!/usr/bin/env bash
# Push a synthetic test stream to MediaLive RTMP input (primaryUrl) using ffmpeg
# Reads the ingest URL from aws/out/medialive.ingest.json (produced by deploy-medialive.sh)
#
# Environment overrides:
#   RES=1280x720       # frame size
#   FPS=30             # frames per second
#   VB=2500k           # video bitrate
#   GOP_SECONDS=2      # GOP duration in seconds
#   URL=<rtmp-url>      # override ingest URL instead of reading from file
#
# Usage:
#   bash aws/scripts/test-ffmpeg-push.sh

set -euo pipefail

# --- deps ---
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg is required" 1>&2
  exit 1
fi
if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required" 1>&2
  exit 1
fi

OUT_DIR="aws/out"
INGEST="$OUT_DIR/medialive.ingest.json"

# --- resolve ingest URL ---
PRIMARY_URL="${URL:-}"
if [[ -z "$PRIMARY_URL" ]]; then
  if [[ ! -f "$INGEST" ]]; then
    echo "ERROR: Missing $INGEST. Run [aws/scripts/deploy-medialive.sh](aws/scripts/deploy-medialive.sh:1) first." 1>&2
    exit 2
  fi
  PRIMARY_URL="$(jq -r '.primaryUrl // empty' "$INGEST")"
fi

if [[ -z "$PRIMARY_URL" || "$PRIMARY_URL" == "null" ]]; then
  echo "ERROR: primaryUrl is empty. Check $INGEST or set URL=rtmp://..." 1>&2
  exit 2
fi

# --- encoding params (override via env) ---
RES="${RES:-1280x720}"
FPS="${FPS:-30}"
VB="${VB:-2500k}"
GOP_SECONDS="${GOP_SECONDS:-2}"

# Integer math for GOP frames (FPS * GOP_SECONDS)
if ! [[ "$FPS" =~ ^[0-9]+$ && "$GOP_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "ERROR: FPS and GOP_SECONDS must be integers (got FPS=$FPS, GOP_SECONDS=$GOP_SECONDS)" 1>&2
  exit 2
fi
GOP="$(( FPS * GOP_SECONDS ))"

echo "Pushing test stream to: $PRIMARY_URL"
echo "  RES=$RES FPS=$FPS VB=$VB GOP_SECONDS=$GOP_SECONDS (GOP=$GOP)"
echo "Press Ctrl+C to stop."

# -re: read input at native frame rate (simulate live)
# testsrc + sine generate video/audio; libx264 + aac typical for HLS pipelines
ffmpeg -re \
  -f lavfi -i "testsrc=size=${RES}:rate=${FPS}" \
  -f lavfi -i "sine=frequency=1000:sample_rate=48000" \
  -c:v libx264 -pix_fmt yuv420p -preset veryfast -b:v "${VB}" -g "${GOP}" \
  -c:a aac -b:a 128k -ar 48000 -ac 2 \
  -f flv "${PRIMARY_URL}"
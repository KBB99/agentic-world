#!/bin/bash
# Start streaming AI character decisions to telemetry overlay

echo "======================================"
echo "  AI TELEMETRY STREAMING SYSTEM"
echo "======================================"
echo
echo "📺 VIEWER URL:"
echo "   https://d1u690gz6k82jo.cloudfront.net/index.html"
echo
echo "🔌 WEBSOCKET:"
echo "   wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"
echo
echo "To see the AI decisions:"
echo "1. Open the viewer URL in a browser"
echo "2. Click 'Connect WebSocket' if needed"
echo "3. Watch the telemetry overlay update with character decisions"
echo
echo "Starting AI stream..."
echo "======================================"

# Run the streaming script
python3 stream-ai-to-telemetry.py 2>&1 | while read line; do
    echo "[$(date '+%H:%M:%S')] $line"
done
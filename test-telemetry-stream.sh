#!/bin/bash
# Quick test to show AI decisions in telemetry overlay

echo "=== AI TELEMETRY STREAMING TEST ==="
echo "This will stream realistic character decisions to the live viewer"
echo
echo "1. Open the viewer with telemetry:"
echo "   https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss%3A%2F%2Funk0zycq5d.execute-api.us-east-1.amazonaws.com%2Fprod"
echo
echo "2. Watch the overlay update with AI decisions..."
echo

# Quick test with curl/wscat
WS_URL="wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"

# Test message 1: Alex facing eviction
echo "Sending: Alex gets eviction notice..."
echo '{
  "action": "telemetry",
  "data": {
    "goal": "[Alex Chen] Find somewhere to crash tonight",
    "action": "Texting everyone I know, crafting sob story",
    "rationale": "Pride is a luxury I cant afford",
    "result": "3 people left on read, 1 maybe"
  }
}' | wscat -c "$WS_URL" -x - --wait 1 2>/dev/null || echo "Install wscat: npm install -g wscat"

sleep 3

# Test message 2: Jamie at networking event
echo "Sending: Jamie at film networking..."
echo '{
  "action": "telemetry", 
  "data": {
    "goal": "[Jamie Rodriguez] Make connection without seeming desperate",
    "action": "Eating enough appetizers to skip dinner tomorrow",
    "rationale": "Parking was $20, I have $27 until Friday",
    "result": "Got a maybe, worth the hunger"
  }
}' | wscat -c "$WS_URL" -x - --wait 1 2>/dev/null

sleep 3

# Test message 3: Marcus gets LinkedIn message
echo "Sending: Marcus hiding Uber driving..."
echo '{
  "action": "telemetry",
  "data": {
    "goal": "[Marcus Williams] Maintain professional image",
    "action": "Reply vaguely about exploring opportunities",
    "rationale": "Cant let them know Im driving drunk people at 2am",
    "result": "Scheduled lunch I cant afford"
  }
}' | wscat -c "$WS_URL" -x - --wait 1 2>/dev/null

echo
echo "Check the viewer overlay - it should show these realistic struggles!"
echo "The AI agent appears to be making decisions based on economic survival."
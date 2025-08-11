#!/bin/bash
# Pause all AI operations to prevent costs

echo "======================================"
echo "  🛑 PAUSING AI SYSTEM"
echo "======================================"

python3 cost-control.py pause

echo ""
echo "AI operations are now PAUSED:"
echo "- No Bedrock API calls will be made"
echo "- No costs will be incurred from AI"
echo "- WebSocket and DynamoDB still active (minimal cost)"
echo ""
echo "To resume: ./resume-ai.sh"
echo "To check status: ./cost-status.sh"
#!/bin/bash
# Resume AI operations

echo "======================================"
echo "  ▶️  RESUMING AI SYSTEM"
echo "======================================"

python3 cost-control.py resume

echo ""
echo "AI operations are now ACTIVE:"
echo "- Bedrock API calls enabled"
echo "- Cost tracking active"
echo "- Daily limit: $10.00"
echo ""
echo "To pause: ./pause-ai.sh"
echo "To check costs: ./cost-status.sh"
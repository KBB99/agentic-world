#!/bin/bash
# Open the Agentic World web interface in browser

URL="http://localhost:3001"

echo "🌍 Opening Agentic World Web Interface..."
echo "   URL: $URL"
echo ""

# Check if server is running
if curl -s -o /dev/null -w "%{http_code}" $URL | grep -q "200"; then
    echo "✅ Server is running"
else
    echo "⚠️  Server not running. Starting it now..."
    ./start-web-interface.sh &
    sleep 3
fi

# Open in browser (macOS)
if [[ "$OSTYPE" == "darwin"* ]]; then
    open $URL
# Open in browser (Linux)
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open $URL 2>/dev/null || echo "Please open $URL in your browser"
# Open in browser (Windows/WSL)
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    start $URL
else
    echo "Please open $URL in your browser"
fi

echo ""
echo "Web Interface Controls:"
echo "  ▶️  Run Turn      - Execute one simulation turn"
echo "  ⏩  Run 5 Turns   - Execute multiple turns"
echo "  🤖  Run with AI   - Use AWS Bedrock for decisions"
echo "  🔄  Refresh       - Update display"
echo "  🔄  Reset World   - Start over (requires confirmation)"
echo ""
echo "Keyboard Shortcuts:"
echo "  Space - Run a turn"
echo "  R     - Refresh state"
echo ""
echo "Current Statistics:"
curl -s $URL/stats | python3 -m json.tool
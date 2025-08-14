#!/bin/bash
# Start the web interface for Agentic World simulation

echo "🌍 Starting Agentic World Web Interface..."
echo ""

# Check if we're in the right directory
if [ ! -f "execute-simulation-turn.py" ]; then
    echo "❌ Error: Must run from agentic directory"
    echo "   Please cd to the agentic directory and try again"
    exit 1
fi

# Check for Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Error: Node.js is not installed"
    echo "   Please install Node.js first"
    exit 1
fi

# Install dependencies if needed
if [ ! -d "web-interface/node_modules" ]; then
    echo "📦 Installing dependencies..."
    cd web-interface
    npm install
    cd ..
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "⚠️  Warning: AWS credentials not configured"
    echo "   The simulation will work but with limited functionality"
    echo "   Run 'aws configure' to set up credentials"
    echo ""
fi

# Start the server
echo "🚀 Starting server on http://localhost:3001"
echo ""
echo "📊 Open your browser to http://localhost:3001"
echo "   Press Ctrl+C to stop the server"
echo ""
echo "Keyboard shortcuts in the web interface:"
echo "  Space - Run a turn"
echo "  R     - Refresh state"
echo ""

cd web-interface
node server.js
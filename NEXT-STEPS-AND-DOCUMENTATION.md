# Next Steps and Documentation Guide

## Current System Status

You have a fully functional economic inequality simulation with:
- ✅ AI characters with personalities and memories (DynamoDB)
- ✅ Web interface for controlling simulation
- ✅ Bidirectional messaging (viewers ↔ characters)
- ✅ Character-to-character interactions
- ✅ MCP tools for digital presence (streaming, social media)
- ✅ AWS infrastructure for streaming and telemetry
- ✅ Cost control system

## Essential Documentation to Read

### 1. **CLAUDE.md** 
- Main project documentation
- All commands and workflows
- Cost management ($10/day limit)
- Character profiles and economic tiers

### 2. **UNREAL-CHARACTER-CONTROL-PLAN.md**
- Complete architecture for Unreal integration
- MCP command protocol
- Animation state machines
- Location system design

### 3. **METAHUMAN-AI-INTEGRATION.md**
- MetaHuman setup for economic classes
- Facial expression mapping
- Clothing degradation system
- Performance optimization

### 4. **WORLD-PROCESSING-DETAILED.md**
- 5-layer perception pipeline
- How characters see and interpret the world
- MCP bridge architecture

## Key Files and Their Purpose

### Web Interface
- `web-interface/index.html` - Frontend with messaging and interactions
- `web-interface/server.js` - Express server connecting to simulation
- `execute-simulation-turn-with-mcp.py` - Main simulation engine with MCP tools
- `character-interactions.py` - Character-to-character interaction system

### MCP Bridge Components
- `mcp-bridge/index.js` - Basic MCP to WebSocket bridge
- `mcp-viewer-communication-server.js` - MCP server for viewer interactions

### AWS Infrastructure
- `aws/scripts/deploy-all.sh` - Deploy entire AWS stack
- `aws/scripts/start-medialive-channel.sh` - Start streaming
- `aws/scripts/stop-medialive-channel.sh` - Stop streaming (IMPORTANT: saves money)
- `cost-status.sh` - Check current AWS costs

### Character Management
- `create-characters.py` - Add new characters to DynamoDB
- `execute-simulation-turn.py` - Basic simulation without MCP
- `create-messages-table.sh` - Setup messaging database

## What to Do Next

### Phase 1: Setup on Unreal Machine (Week 1)

1. **Clone Repository**
```bash
git clone https://github.com/[your-username]/agentic.git
cd agentic
```

2. **Install Dependencies**
```bash
# Node.js for MCP bridge
cd mcp-bridge && npm install
cd ../web-interface && npm install

# Python for simulation
pip install boto3
```

3. **Configure AWS**
```bash
aws configure
# Enter your AWS credentials
# Region: us-east-1
```

4. **Test Current System**
```bash
# Start web interface
cd web-interface
node server.js

# Open browser to http://localhost:3001
# Run a turn to verify everything works
```

### Phase 2: Unreal Engine Setup (Week 2)

1. **Create New Unreal Project**
   - Unreal Engine 5.3+
   - Enable plugins: LiveLink, WebSocket, JSON Blueprint
   - Import MetaHuman samples

2. **Build Test Level**
   - Create simple scene with library, coffee shop, street
   - Add nav mesh for character movement
   - Place spawn points for characters

3. **Implement MCP Server in Unreal**
   - Create TCP server listening on port 32123
   - Parse JSON-RPC messages
   - Map commands to character actions

4. **Test Basic Communication**
```bash
# From agentic directory
node mcp-bridge/index.js --tcp localhost:32123

# Send test command
curl -X POST http://localhost:3001/run-turn \
  -H "Content-Type: application/json" \
  -d '{"useAI": true, "turns": 1}'
```

### Phase 3: MetaHuman Integration (Week 3)

1. **Create Character Presets**
   - Poor: Alex Chen, Maria Gonzalez
   - Middle: Ashley Kim
   - Wealthy: Victoria Sterling

2. **Setup Appearance by Class**
   - Poor: Tired eyes, unkempt hair, worn clothes
   - Wealthy: Perfect grooming, designer clothes

3. **Implement Emotion System**
   - Map AI emotions to facial expressions
   - Add body language based on needs

4. **Test Character Embodiment**
   - Verify movement commands work
   - Check facial expressions
   - Test character interactions

### Phase 4: Streaming Integration (Week 4)

1. **Setup OBS**
   - Capture Unreal viewport
   - Configure RTMP output

2. **Start AWS MediaLive**
```bash
bash aws/scripts/start-medialive-channel.sh
# Get RTMP URL from aws/out/medialive.ingest.json
```

3. **Stream to CloudFront**
   - Configure OBS with RTMP URL
   - View stream at CloudFront domain

4. **Add Telemetry Overlay**
   - Connect MCP bridge to WebSocket
   - Show character thoughts on stream

### Phase 5: Full Integration (Week 5)

1. **Connect Everything**
   - Web interface → AI decisions
   - AI → MCP commands
   - MCP → Unreal characters
   - Unreal → Stream
   - Stream → Viewers

2. **Test Complete Pipeline**
   - Run simulation turns
   - Watch characters move in Unreal
   - See stream with overlay
   - Message characters and get responses

## Critical Commands to Remember

### Daily Workflow
```bash
# Start everything
./start-web-interface.sh
./cost-status.sh  # Check costs first!

# Run simulation
open http://localhost:3001
# Click "Run Turn (AI + MCP)"

# Stop expensive services when done
./stop-expensive-services.sh
```

### Cost Control
```bash
# ALWAYS check costs
./cost-status.sh

# Pause AI if needed
./pause-ai.sh

# Resume when ready
./resume-ai.sh
```

### Troubleshooting
```bash
# Check server logs
tail -f web-interface/server.log

# Test AWS connection
aws dynamodb list-tables

# Test character data
curl http://localhost:3001/characters/alex_chen
```

## Environment Variables Needed

Create `.env` file:
```bash
AWS_REGION=us-east-1
AWS_PROFILE=default
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
MCP_TCP_HOST=localhost
MCP_TCP_PORT=32123
WEBSOCKET_URL=wss://your-api-gateway.execute-api.us-east-1.amazonaws.com/prod
```

## Key Architecture Decisions Made

1. **DynamoDB** for persistent character state
2. **AWS Bedrock** for AI decisions (Claude)
3. **MCP Protocol** for tool access and Unreal communication
4. **WebSocket** for real-time telemetry
5. **Express.js** for web API
6. **MetaHuman** for photorealistic characters
7. **CloudFront** for global stream distribution

## What Makes This System Unique

- **Real AI personalities** with memories and relationships
- **Economic inequality visible** in character appearance
- **Viewer interaction** through messaging
- **Character autonomy** with MCP tool access
- **Social dynamics** through character interactions
- **Persistent world** that evolves over time

## Support Resources

- MCP Protocol: https://github.com/modelcontextprotocol/servers
- MetaHuman Docs: https://docs.metahuman.unrealengine.com/
- AWS Bedrock: https://docs.aws.amazon.com/bedrock/
- Unreal LiveLink: https://docs.unrealengine.com/5.3/en-US/live-link

## Ready for Handoff

This system is ready to be developed on a machine with:
- Unreal Engine 5.3+
- OBS Studio
- GPU for MetaHuman rendering
- AWS credentials configured
- Node.js 18+ and Python 3.9+

The simulation will create a visceral experience of economic inequality through photorealistic characters whose appearance, behavior, and interactions reflect their economic reality.

**Remember**: Always run `./cost-status.sh` before starting work to avoid unexpected AWS charges!
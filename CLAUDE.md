# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AWS-based live streaming and telemetry demonstration project that integrates Unreal Engine with AWS media services. The architecture includes:

- **Live Streaming Pipeline**: Unreal Engine → OBS → MediaLive → MediaPackage → CloudFront → Web viewer
- **Telemetry Bridge**: MCP (Model Context Protocol) TCP server → WebSocket API Gateway for real-time telemetry overlay
- **Infrastructure**: CloudFormation templates for AWS services deployment

## Key Commands

### MCP Bridge Service
```bash
# Install dependencies (first time only)
cd mcp-bridge && npm install

# Start the MCP bridge (connects Unreal to WebSocket telemetry)
node mcp-bridge/index.js --wss wss://your-api-gateway.execute-api.region.amazonaws.com/prod
```

### AWS Infrastructure Deployment
```bash
# Deploy entire stack (MediaPackage, MediaLive, CloudFront, viewer)
REGION=us-east-1 PROJECT=agentic-demo BUCKET=your-unique-bucket bash aws/scripts/deploy-all.sh

# Deploy individual components
bash aws/scripts/deploy-mediapackage.sh
bash aws/scripts/deploy-medialive.sh
bash aws/scripts/deploy-cloudfront-and-viewer.sh
bash aws/scripts/deploy-telemetry.sh

# MediaLive channel control (start/stop to manage costs)
bash aws/scripts/start-medialive-channel.sh
bash aws/scripts/stop-medialive-channel.sh

# Test RTMP streaming with ffmpeg
bash aws/scripts/test-ffmpeg-push.sh

# Send test telemetry message
bash aws/scripts/post-telemetry.sh --ws "$WS" --table "$TABLE" \
  --goal "Test goal" --action "Test action" \
  --rationale "Test rationale" --result "Test result"

# Aggregate all stack outputs for reference
bash aws/scripts/aggregate-outputs.sh
```

## Architecture Components

### AWS Infrastructure (`aws/`)
- **CloudFormation Templates** (`aws/templates/cfn/`):
  - `mediapackage.yaml` - HLS packaging and origin
  - `medialive.yaml` - RTMP input and channel encoding
  - `telemetry-websocket.yaml` - WebSocket API for telemetry
  - `ec2-windows-gpu.yaml` - GPU instance for Unreal/OBS

- **Deployment Scripts** (`aws/scripts/`):
  - Orchestrated deployment via `deploy-all.sh`
  - Individual service deployments
  - Channel lifecycle management
  - Output aggregation into `aws/out/stack-outputs.json`

- **CloudFront Configuration**:
  - Dual-origin setup: S3 for viewer assets, MediaPackage for HLS
  - CloudFront Function (`aws/functions/strip-live-uri.js`) rewrites `/live/*` paths
  - Template rendering via `aws/tools/render-template.js`

### MCP Bridge (`mcp-bridge/`)
- TCP JSON-RPC client connects to Unreal MCP server (default: 127.0.0.1:32123)
- WebSocket client publishes to API Gateway
- Intelligent message mapping: JSON-RPC → telemetry fields (goal, action, rationale, result)
- Supports both NDJSON and LSP-style Content-Length framing
- Automatic reconnection with exponential backoff

### Viewer Application (`viewer/`)
- Single-page HLS player with telemetry overlay
- Fallback chain: live HLS → VOD sample
- WebSocket integration for real-time telemetry updates
- Animated agent avatar with talk/blink animations
- Query parameters:
  - `?src=` - Override HLS source
  - `?ws=` or `?telemetry=` - WebSocket endpoint for telemetry

## Cost Management & Control System

**⚠️ CRITICAL**: This project can incur significant AWS costs. Use the cost control system:

### Quick Commands
```bash
# Check costs and running services
./cost-status.sh

# Pause all AI operations (prevents Bedrock costs)
./pause-ai.sh

# Resume AI operations
./resume-ai.sh

# Stop ALL expensive services immediately
./stop-expensive-services.sh
```

### Cost Breakdown
- **MediaLive**: ~$0.59-$2.30/hour per channel (STOP WHEN NOT STREAMING)
- **EC2 GPU (g4dn)**: ~$0.53/hour for Unreal Engine
- **Bedrock Claude**: ~$0.003/1K input tokens, $0.015/1K output tokens
- **DynamoDB & WebSocket**: <$0.01/hour (minimal)

### Safety Features
- **Auto-pause** at $10 daily limit
- **Pause switch** blocks all AI calls when activated
- **Cost tracking** in `costs.json` file
- **Service checker** identifies running expensive services

### Typical Costs
- AI narrative session (100 turns): ~$0.50-$1.00
- Live streaming (1 hour): ~$1.50-$3.00
- Full demo (streaming + AI): ~$5.00/hour

**ALWAYS** run `./cost-status.sh` before and after sessions to verify services are stopped!

## Output Files

All deployment outputs are stored in `aws/out/`:
- `stack-outputs.json` - Aggregated endpoints and IDs
- `mediapackage.outputs.json` - MediaPackage channel details
- `medialive.outputs.json` - MediaLive channel IDs
- `medialive.ingest.json` - RTMP ingest URLs
- `cloudfront.outputs.json` - CloudFront distribution domain
- `telemetry.outputs.json` - WebSocket endpoint and DynamoDB table

## Common Workflows

### Starting a Live Stream
1. Start EC2 instance (if using cloud GPU)
2. Start MediaLive channel: `bash aws/scripts/start-medialive-channel.sh`
3. Configure OBS with RTMP URL from `aws/out/medialive.ingest.json`
4. Start streaming in OBS
5. View stream at CloudFront domain from `aws/out/cloudfront.outputs.json`

### Testing Telemetry
1. Start MCP bridge with WebSocket URL from `aws/out/telemetry.outputs.json`
2. Open viewer with `?ws=wss://...` parameter
3. Send test messages via `post-telemetry.sh` or connect Unreal MCP server

### Troubleshooting Stream Issues
- Verify MediaLive channel is RUNNING: check `aws/out/medialive.outputs.json`
- Confirm RTMP push is active: monitor OBS streaming status
- Check CloudFront Function association for `/live/*` behavior
- Review MediaPackage endpoint URL in outputs
- For fallback testing, viewer automatically tries `/assets/sample.mp4` if live fails

## AI Agent System (LLM-Powered NPCs)

The system simulates realistic characters with persistent memories, economic struggles, spatial awareness, and digital presence using Claude via AWS Bedrock.

### Architecture
```
Character Memories (DynamoDB) → Claude AI → Decision with Context
     ↓                                           ↓
World State → Affects Others → WebSocket → Viewer Telemetry
     ↓                                           ↓
MCP Tools → Digital Interactions → Viewer Messages → AI Responses
```

### Web Interface & Interactive Simulation

#### Starting the Web Interface
```bash
# Start the web server
cd web-interface
node server.js

# Or use the helper script
bash start-web-interface.sh

# Open in browser
open http://localhost:3001
```

#### Web Interface Features

**Character Cards Display:**
- 💰 Current money and survival days
- 📺 Stream follower count  
- 📱 Social media followers
- 🔴 LIVE badge when streaming
- 📍 Current location
- 🔋 Needs meters (hunger, exhaustion, stress)
- 💬 Message button for direct interaction

**Expandable Details:**
- Personality description
- Background story
- Current situation
- Goals list
- Recent memories (last 5)
- Last MCP action taken
- Recent viewer interactions

**Controls:**
- **Run Turn (AI + MCP)**: Execute simulation with Bedrock and MCP tools
- **Run Multiple Turns**: Batch execution
- **Refresh**: Update display
- **Reset World**: Start fresh simulation

**Keyboard Shortcuts:**
- `Space` - Run a turn
- `R` - Refresh state
- `Escape` - Close message modal

### Interactive Messaging System

#### Features
- **💬 Direct Messaging**: Click "Message" button on any character card
- **AI-Powered Responses**: Characters respond based on personality and situation
- **Persistent Chat History**: Messages stored in DynamoDB
- **Emotional States**: Characters express feelings in responses
- **Context-Aware**: Responses reflect economic status and current needs

#### Message API Endpoints
```bash
# Send message to character
POST /send-message
{
  "characterId": "alex_chen",
  "message": "How are you doing?",
  "senderName": "Viewer"
}

# Get message history
GET /messages/:characterId
```

#### Example Interactions
- Message **Alex Chen** (struggling writer): "How are you holding up?"
  - Response: "Thanks for reaching out. Every bit of support helps when you're struggling like I am." *[Feeling: grateful but exhausted]*

- Message **Victoria Sterling** (SVP): "What do you think about housing costs?"
  - Response: "The market is performing exceptionally well. Our portfolio continues to deliver strong returns." *[Feeling: satisfied]*

### MCP Tools for Digital Presence

Characters can use these Model Context Protocol tools:

- **read_viewer_messages** - Read messages from stream viewers
- **respond_to_viewer** - Reply to specific viewers  
- **check_viewer_sentiment** - Gauge audience mood
- **read_donations** - Check donation messages
- **thank_donor** - Acknowledge supporters
- **ask_viewers_for_help** - Request assistance when desperate
- **post_to_social** - Share on social media platforms
- **check_crowdfunding** - Monitor crowdfunding campaigns
- **stream_performance** - Stream content for followers

#### Running MCP-Enabled Simulation
```bash
# Run with MCP tools enabled (streaming, social media, viewer interactions)
python3 execute-simulation-turn-with-mcp.py --use-bedrock --turns 1

# Standard simulation without MCP
python3 execute-simulation-turn.py --use-bedrock --turns 1
```

#### Example MCP Actions
```python
# Poor character asking for help
{
  "action": "stream_for_donations",
  "mcp_tool": "ask_viewers_for_help",
  "tool_params": {
    "problem": "need money for food",
    "urgency": "high"
  },
  "reasoning": "Desperate for money, asking viewers for help",
  "emotion": "desperate",
  "urgency": "immediate"
}

# Wealthy character posting
{
  "action": "post_to_social",
  "mcp_tool": "post_to_social",
  "tool_params": {
    "platform": "LinkedIn",
    "message": "MegaProperty REIT celebrates record quarterly earnings"
  },
  "reasoning": "Promoting company success",
  "emotion": "proud",
  "urgency": "low"
}
```

### Creating New Characters

```python
# Example: Create a new character in create-characters.py
new_character = {
    'character_id': {
        'personality': 'Core traits, worldview, blind spots',
        'background': 'Age, education, income, family situation',
        'current_situation': 'What crisis/opportunity they face now',
        'stress_response': 'How they cope (cry, drink, shop, etc)',
        'goals': ['Immediate need', 'Dream', 'Fear to avoid'],
        'current_state': 'emotional_state',
        'initial_memories': [
            'Foundational memory that shapes them',
            'Recent event that drives current behavior',
            'Relationship or loss that matters'
        ],
        'resources': {'money': amount, 'other': value},
        'location': 'starting_location'
    }
}
```

Run: `python3 create-characters.py` to add characters to DynamoDB.

### Running Narrative Turns

```bash
# Quick test - run a few turns with existing characters
python3 run-narrative-turns.py

# Run interconnected narrative showing class dynamics  
python3 intersecting-lives.py

# Run spatial narrative with movement
python3 spatial-world-system.py

# Safe mode with cost tracking (auto-pauses at $10 daily limit)
python3 safe-ai-narrative.py
```

### How AI Decisions Work

1. **Load Character Context**: Fetch memories from DynamoDB
2. **Build Prompt**: Combine situation + memories + world state
3. **AI Decision**: Claude generates response based on economic position
4. **Update World**: Save new memory, affect other characters
5. **Stream to Viewer**: Send to WebSocket telemetry overlay

### Character Types & Detachment Levels

- **Level 0**: Direct exploiters (Tyler - tech bro landlord)
- **Level 1**: Processors (Brandon - property manager)  
- **Level 2**: Abstractors (Victoria - REIT executive)
- **Level 3**: Algorithms (Quantum AI - trading system)
- **Level 4**: Destroyers (Richard - private equity)
- **Level 5**: Oblivious heirs (Madison - trust fund)

### Memory System

Characters accumulate memories that shape future decisions:
```python
# Memories persist across sessions
alex_memories = [
    "Got eviction notice",
    "Down to $47", 
    "Jamie helped me",
    "Joined rent strike"
]
# Each new decision adds to memories
# Next decision uses recent memories as context
```

### Spatial Awareness

Characters navigate physical spaces:
```python
locations = {
    'library': {'wifi': True, 'cost': 0},
    'coffee_shop': {'wifi': True, 'cost': 5},
    'luxury_apartment': {'wifi': True, 'cost': 0}
}
# Characters choose movement based on needs vs resources
```

### Character Profiles & Economic Tiers

#### Struggling Characters (< $100)
- **Alex Chen**: Writer, couchsurfing, $53
- **Jamie Rodriguez**: Film PA/barista, $43
- Access to streaming, crowdfunding, viewer donations
- Desperate actions trigger sympathy from viewers
- High hunger, exhaustion, and stress levels

#### Middle Class ($1K - $10K)
- Tech workers, nurses
- Moderate follower counts
- Balanced viewer sentiment
- Professional tools access

#### Wealthy (> $100K)
- **Victoria Sterling**: SVP at MegaProperty REIT, $500K
- **Madison Worthington**: Trust fund, $25M
- Negative viewer sentiment when streaming
- Post about profits and luxury
- All needs automatically met

### DynamoDB Tables

```bash
# Agent contexts and personalities
agentic-demo-agent-contexts

# World state and locations  
agentic-demo-world-state

# Character memories
agentic-demo-character-memories

# Message history (viewer-character interactions)
agentic-demo-messages
```

#### Creating Tables
```bash
# Create messages table for chat history
bash create-messages-table.sh
```

### Simulation Statistics

The `/stats` endpoint provides:
- Total characters
- Current turn number
- Wealth gap and ratio
- Richest/poorest characters
- Average needs (hunger, exhaustion, stress)

### Testing Commands

```bash
# Test messaging system
curl -X POST http://localhost:3001/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "characterId": "alex_chen",
    "message": "How are you holding up?",
    "senderName": "SupportiveViewer"
  }'

# Check simulation statistics
curl http://localhost:3001/stats | python3 -m json.tool

# Get character details with memories
curl http://localhost:3001/characters/alex_chen | python3 -m json.tool

# Run a simulation turn via API
curl -X POST http://localhost:3001/run-turn \
  -H "Content-Type: application/json" \
  -d '{"useAI": true, "turns": 1}'
```

### Cost Control

```bash
# Check costs and pause/resume AI
./cost-status.sh   # View current costs
./pause-ai.sh      # Stop AI operations
./resume-ai.sh     # Resume AI operations
```

Daily limit: $10 (auto-pauses)
Typical costs: ~$0.002 per decision

## Dependencies

- AWS CLI v2 with valid credentials
- Node.js ≥18 (for mcp-bridge)
- jq (for JSON processing in scripts)
- ffmpeg (optional, for test streaming)
- OBS Studio (for production streaming)
- AWS Bedrock access (for Claude AI agents)
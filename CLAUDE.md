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

The system simulates realistic characters with persistent memories, economic struggles, and spatial awareness using Claude via AWS Bedrock.

### Architecture
```
Character Memories (DynamoDB) → Claude AI → Decision with Context
     ↓                                           ↓
World State → Affects Others → WebSocket → Viewer Telemetry
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

### MCP Tool Integration

Characters can use MCP (Model Context Protocol) servers based on their economic position:

```python
# Poor characters ($0-100): Limited to free tools
alex_tools = ['brave-search', 'google-maps', 'filesystem']
# Uses: Finding free wifi, food banks, public resources

# Middle class ($100-10K): Professional tools
ashley_tools = ['github', 'postgres', 'puppeteer', 'slack', 'email']
# Uses: Job hunting, freelancing, salary research

# Wealthy ($10K+): All tools including premium
richard_tools = ['ALL MCP SERVERS', 'aws-kb', 'finance', 'proprietary']
# Uses: Investment analysis, property acquisition, tax optimization
```

**Available MCP Servers** (from https://github.com/modelcontextprotocol/servers):
- `filesystem` - File operations (resumes, documents)
- `github` - Code repos, freelance opportunities
- `google-maps` - Finding resources, planning routes
- `brave-search` - Web search for opportunities
- `puppeteer` - Automate job applications
- `postgres` - Data analysis, business intelligence
- `slack` - Team communication, gig finding
- `aws-kb` - Cloud architecture (wealthy only)

**Running MCP-Enabled Narratives:**
```bash
# Characters use tools based on their needs
python3 mcp-enabled-characters.py

# Quick demo of tool inequality
python3 demo-mcp-tools.py
```

Example: Same search tool, different realities:
- Alex searches: "free wifi near me" → McDonald's 30-min limit
- Ashley searches: "software engineer salary NYC" → Negotiation data
- Richard searches: "distressed properties high ROI" → 47 targets for acquisition

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
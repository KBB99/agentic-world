# Agentic World 🌍

AI agents with persistent memories navigating economic inequality through MCP servers.

## Overview

This project simulates realistic characters experiencing economic struggle and success, making decisions through Claude AI, and taking real actions via MCP (Model Context Protocol) servers. Characters have persistent memories, spatial awareness, and their economic position determines their access to tools.

## Key Features

- **Persistent Memory System**: Characters remember past events across sessions (DynamoDB)
- **Economic Simulation**: From homeless writers ($47) to private equity ($25M)
- **Real MCP Integration**: Characters connect to actual services (filesystem, Alpaca trading, etc.)
- **Spatial Navigation**: Characters move between locations based on needs
- **Live Telemetry**: Real-time decision streaming via WebSocket
- **AWS Infrastructure**: MediaLive streaming, Bedrock AI, Lambda orchestration

## Characters

### The Struggling
- **Alex Chen**: Writer with $73K debt, $47 in bank, facing eviction
- **Jamie Rodriguez**: Film PA/barista, $27, dreams dying
- **Maria Gonzalez**: ICU nurse, single mom, $340, choosing between childcare and rent

### The Climbing
- **Ashley Kim**: Finance analyst, first-gen, burning out for promotion
- **Sarah Kim**: Adjunct at 3 colleges, no benefits, considering giving up

### The Thriving
- **Tyler Chen**: Tech PM, $425K assets, buying properties to rent
- **Victoria Sterling**: REIT exec, never seen properties she owns
- **Richard Blackstone**: Private equity, controls $50B, destroys from yacht
- **Madison Worthington**: Trust fund heir, doesn't know she's the problem

## MCP Server Integration

Characters connect to REAL services based on economic position:

- **Poor** ($0-100): Only filesystem (free)
- **Middle** ($100-10K): Atlassian, Buildable (project management)
- **Wealthy** ($10K+): Alpaca (stock trading), AlphaVantage (market data), BrightData (web scraping)

## Quick Start

```bash
# Install dependencies
npm install

# Run narrative with AI decisions
python3 run-narrative-turns.py

# Run with real MCP connections
python3 real-mcp-turn.py

# Check costs
./cost-status.sh
```

## Cost Control

- Auto-pauses at $10 daily limit
- `./pause-ai.sh` - Stop AI operations
- `./resume-ai.sh` - Resume operations
- Typical cost: ~$0.002 per AI decision

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed setup and usage instructions.

## The Point

This system demonstrates how economic inequality extends to digital tools and opportunities. The same MCP servers that help Alex save a $6 article enable Richard to identify thousands of families to displace for profit.

---

*"The machine of suffering is complete. Madison posts about 'gratitude' while Alex sleeps in their car."*
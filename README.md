# Agentic World: Unreal Engine + MCP Servers + Strands Agents

Operate and observe Unreal Engine Strands agents through Model Context Protocol (MCP) servers, with a front-end that can trigger actions and stream telemetry.

This repository focuses on:
- Strands agents inside Unreal Engine that expose capabilities
- MCP servers (local services/tools) that agents and the front-end can invoke
- A WebSocket bridge that streams agent intent/telemetry to the UI overlay
- A simple web interface for issuing commands and viewing state

## Architecture

```
[Browser UI]
   ├─ Issues actions (button clicks, form inputs)
   ├─ Subscribes to telemetry overlay via WebSocket (API Gateway)
   ▼
[Web Interface (Express, :3001)]
   ├─ Serves static pages (dashboard.html, index.html)
   ├─ Hosts REST endpoints for future command execution and content viewing
   ▼
[MCP Clients / Tools (local scripts)]
   ├─ Connect to MCP servers (filesystem, custom Unreal tools, etc.)
   └─ Translate front-end actions → MCP commands

[Unreal Engine + Strands Agents]
   ├─ Listens for JSON-RPC (TCP) commands (e.g., 127.0.0.1:32123)
   ├─ Executes movement, interaction, expression, and need-based behaviors
   └─ Emits JSON-RPC messages (decisions/results/events)

[mcp-bridge]
   ├─ TCP JSON-RPC ←→ API Gateway WebSocket
   └─ Heuristically maps JSON-RPC to overlay fields {goal, action, rationale, result}
```

- Strands agents: autonomous NPCs/services in Unreal that can be addressed with structured commands.
- MCP servers: capability providers (filesystem, custom tools, “editor” functions) available to agents and/or UI via a standard protocol.
- Bridge: a resilient connector that streams agent intent/state to an overlay via an API Gateway WebSocket.

## Quick Start

Requirements:
- Node.js 18+ (see `.nvmrc`)
- Unreal Engine with a JSON-RPC TCP listener (e.g., 127.0.0.1:32123)
- Optional: An API Gateway WebSocket endpoint for telemetry overlay

1) Install dependencies
```bash
nvm use || true
npm install
```

2) Launch Unreal Engine with MCP TCP JSON-RPC
- Ensure Unreal is listening on a TCP socket (default example: 127.0.0.1:32123).
- See UNREAL-AVATAR-MCP.md for command schemas and integration tips.

3) Start the Web Telemetry Bridge
```bash
# Publish agent telemetry to your API Gateway WebSocket
node mcp-bridge/index.js \
  --wss wss://YOUR_API_GATEWAY.execute-api.us-east-1.amazonaws.com/prod \
  --mcp-host 127.0.0.1 \
  --mcp-port 32123 \
  --verbose
```
Environment variables are also supported:
- TELEMETRY_WSS
- MCP_HOST (default 127.0.0.1)
- MCP_PORT (default 32123)

4) Start the Web Interface (serves UI and endpoints)
```bash
npm -w web-interface run start
# Opens on http://localhost:3001

# Useful pages:
# - http://localhost:3001/index.html
# - http://localhost:3001/dashboard.html
# - http://localhost:3001/content-hub.html (if present)
```

The web interface currently provides endpoints and UI scaffolding for interacting with backend services and content; you can integrate specific MCP command routes as needed for your use case.

## Sending Commands to Strands Agents (JSON-RPC)

Unreal’s MCP endpoint accepts JSON-RPC over TCP. Example payloads (see UNREAL-AVATAR-MCP.md for more):

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "unreal.avatar.control",
  "params": {
    "character_id": "agent_01",
    "action": "walk_to",
    "parameters": {
      "location": "training_area",
      "speed": "normal"
    }
  }
}
```

Additional common actions:
- Movement: `walk_to`, `run_to`, `turn_to`, `look_at`, `sit_on`, `stand_up`
- Interaction: `pickup`, `drop`, `use`, `open`, `talk_to`, `gesture`
- Expression: `set_facial_expression`, `play_animation`, `set_posture`
- Need-based: `eat`, `drink`, `sleep`, `work`

The bridge maps inbound/outbound JSON-RPC messages to an overlay-friendly telemetry schema:
```json
{
  "action": "telemetry",
  "data": {
    "goal": "Explore training area",
    "actionText": "unreal.avatar.control walk_to location=training_area",
    "rationale": "Patrol routine",
    "result": "Initiated"
  }
}
```

## Front-end → MCP Execution

This repository includes:
- Web UI (Express, `web-interface/`) for hosting dashboards and future control panels
- MCP tooling and examples (`demo-mcp-tools.py`, `mcp-real-client.js`) to script MCP interactions
- A bridge (`mcp-bridge/`) that publishes agent intent/state for overlays

You can wire up a route in the web interface to:
1) Accept a front-end action
2) Invoke a local MCP client/script
3) Forward a JSON-RPC command to Unreal
4) Stream telemetry back to the UI via your WebSocket overlay

This keeps the UI thin while leveraging MCP servers and local tools.

## Configuration

- Node/Tooling
  - Node 18+ required (see `.nvmrc`)
  - Linting/formatting: `npm run check` (ESLint + Prettier)
  - Python tooling: `npm run py:check` (Ruff + Black)

- Bridge
  - CLI: `node mcp-bridge/index.js --wss ... [--mcp-host ...] [--mcp-port ...] [--verbose]`
  - Env: `TELEMETRY_WSS`, `MCP_HOST`, `MCP_PORT`, `VERBOSE=1`

- Web Interface
  - Starts on `:3001`
  - Serves static files from `web-interface/`
  - You can add REST routes to translate UI actions → MCP commands

## Documentation

- Unreal avatar control via MCP: [docs/UNREAL-AVATAR-MCP.md](docs/UNREAL-AVATAR-MCP.md)
- Strands agents + A2A (Agent-to-Agent) guide: [docs/A2A-Guide-for-Unreal-Strands.md](docs/A2A-Guide-for-Unreal-Strands.md)
- MCP runbook and ops notes: [docs/MCP-RUNBOOK.md](docs/MCP-RUNBOOK.md)
- Viewer/UI communication: [docs/VIEWER-COMMUNICATION-SYSTEM.md](docs/VIEWER-COMMUNICATION-SYSTEM.md)
- MetaHuman integration notes: [docs/METAHUMAN-AI-INTEGRATION.md](docs/METAHUMAN-AI-INTEGRATION.md)

## Development

Install and validate:
```bash
nvm use || true
npm install
npm run check      # ESLint + Prettier (check)
npm run py:check   # Ruff + Black (check)
```

Workspace commands:
```bash
# Web interface
npm -w web-interface run start

# Bridge
node mcp-bridge/index.js --wss wss://YOUR_API
```

## Contributing & Security

- See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, workflow, and conventions.
- Please report vulnerabilities responsibly as described in [SECURITY.md](SECURITY.md).

## License

MIT — see [LICENSE](LICENSE).

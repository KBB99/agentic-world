# Unreal MCP Integration — Runbook (TCP JSON-RPC → WebSocket overlay)

Goal
- Connect an Unreal MCP Server (JSON-RPC over TCP at 127.0.0.1:32123) to the existing overlay via the deployed API Gateway WebSocket.
- Bridge process: Unreal MCP (TCP) → Node bridge → WSS → Viewer overlay.
- No new AWS services; minimal cost; reversible.

Key components
- Viewer overlay (HLS + telemetry): [viewer/index.html](viewer/index.html)
- WebSocket API (broadcast): [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml)
- Bridge code (local, Node.js): [mcp-bridge/index.js](mcp-bridge/index.js:1-409)

Prerequisites
- WSS: wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
- DynamoDB connections table: agentic-demo-telemetry-connections
- Node.js 18+ on the Windows GPU instance
- Unreal Engine project with Python remote execution enabled

0) Update the Telemetry WebSocket stack (one-time for envelope support)
- We adjusted the message Lambda to support an envelope payload so the top‑level "action" can remain "telemetry" for API route selection.
- Redeploy (safe, negligible cost):
  - REGION=us-east-1 PROJECT=agentic-demo bash [aws/scripts/deploy-telemetry.sh](aws/scripts/deploy-telemetry.sh:1)
- Expected (unchanged):
  - WebSocket WSS remains: wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod

1) Configure Unreal for Python remote execution (Windows GPU instance via RDP)
- In Unreal Editor:
  - Edit → Plugins → enable "Python Editor Script Plugin"
  - Edit → Project Settings → search "Python" → enable "Enable Remote Execution"
- Restart the editor if prompted, then open your project.

2) Start an Unreal MCP Server (TCP JSON-RPC at 127.0.0.1:32123)
- Choose an Unreal MCP server implementation that can listen on a TCP socket and speak JSON‑RPC.
- Example reference: https://github.com/runreal/unreal-mcp (commonly run via npx; adjust or select a TCP‑capable variant).
- Ensure the server binds to 127.0.0.1:32123 (loopback) to avoid exposing control surface to LAN.
- Verify the server logs indicate it is listening on 127.0.0.1:32123 and connected to the Unreal Editor (Python remote exec must be enabled).

3) Install and run the bridge on the Windows GPU instance
- Copy or clone this repo onto the instance and open PowerShell in the repo root.
- Install dependencies:
  - cd .\mcp-bridge
  - npm install
- Start the bridge (option A: CLI flags)
  - node [mcp-bridge/index.js](mcp-bridge/index.js:1-409) --wss wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod --mcp-host 127.0.0.1 --mcp-port 32123 --verbose
- Start the bridge (option B: PowerShell helper)
  - A helper script is provided at [mcp-bridge/start-bridge.ps1](mcp-bridge/start-bridge.ps1)
  - Example:
    - PowerShell: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process -Force
    - PowerShell: .\start-bridge.ps1 -Wss "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod" -Host "127.0.0.1" -Port 32123 -Verbose
- Expected logs:
  - [mcp] Connected to 127.0.0.1:32123
  - [telemetry] Connected to API Gateway WebSocket
  - When MCP tools run, the bridge will coalesce and publish succinct overlay updates.

Bridge behavior (mapping)
- The bridge accepts JSON‑RPC requests/responses/notifications from the MCP server and heuristically maps them to:
  - goal: high‑level objective text (e.g., set_goal, plan)
  - action: concise description of the current operation (editor_* tools, create_/update_/delete_, console commands, screenshots, etc.)
  - rationale: optional brief explanation if included in parameters
  - result: success/error derived from JSON‑RPC results or errors
- The bridge publishes an envelope to the WebSocket to avoid API route collisions:
  - {"action":"telemetry","data":{"goal","actionText","rationale","result"}}
- The WebSocket message Lambda rebroadcasts a flattened payload to clients as:
  - {"goal","action","rationale","result"}
- Viewer overlay picks these up in [handleTelemetry()](viewer/index.html:154-166).

4) Validate the overlay end‑to‑end
- Open the viewer with the ws param:
  - https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss%3A%2F%2Funk0zycq5d.execute-api.us-east-1.amazonaws.com%2Fprod
- "Status" should show "Agent Running" once a WebSocket client is connected.
- Trigger an MCP tool (e.g., editor_console_command, editor_take_screenshot, editor_create_object) and observe:
  - Action, Goal, Rationale, Result fields update
  - Brief mouth "talk" animation on updates

5) Optional: validate video path (keep costs low)
- Only when ready to test video:
  - Start MediaLive: bash [aws/scripts/start-medialive-channel.sh](aws/scripts/start-medialive-channel.sh:1)
  - In OBS, Start Streaming to the MediaLive endpoint
  - Viewer should play /live/index.m3u8 (fallback to /assets/sample.mp4 when idle)
- Stop when done to control costs:
  - Stop Streaming in OBS
  - Stop MediaLive: bash [aws/scripts/stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)

Troubleshooting
- Viewer shows "Disconnected":
  - Ensure the viewer URL includes ?ws=wss://... and that the bridge has connected to WSS.
  - Verify that the WebSocket API is deployed and reachable (no corporate proxy blocks).
- Action shows "telemetry" or stays blank:
  - Redeploy the telemetry stack so the message Lambda maps data.actionText → action; see step 0 above.
  - Ensure bridge logs show outbound publishes on tool invocations.
- Bridge cannot connect to MCP:
  - Verify the MCP server is listening on 127.0.0.1:32123 and Unreal Editor has Python remote execution enabled.
  - Check Windows Firewall: allow local loopback on the chosen port.
- No overlay updates after MCP actions:
  - Run the broadcaster script to sanity‑check overlay:
    - WS=wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
    - TABLE=agentic-demo-telemetry-connections
    - bash [aws/scripts/post-telemetry.sh](aws/scripts/post-telemetry.sh:1-138) --ws "$WS" --table "$TABLE" --goal "Smoke test" --action "editor_console_command stat fps" --rationale "Validate overlay link" --result "Initiated"

Security notes
- Keep the MCP server bound to 127.0.0.1 to avoid LAN exposure. If using 0.0.0.0, harden Windows Firewall rules to your RDP IP only.
- The overlay carries non‑sensitive text. Do not transmit secrets or code through these fields.

Cost control reminders
- Keep the GPU EC2 instance stopped when idle.
- Keep MediaLive Channel stopped except during active tests.
- Viewer/CloudFront and WebSocket/DynamoDB idle costs are minimal.

Reference files
- Viewer: [viewer/index.html](viewer/index.html:90-199)
- WebSocket template: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml:152-171)
- Bridge: [mcp-bridge/index.js](mcp-bridge/index.js:1-409)
- Broadcaster: [aws/scripts/post-telemetry.sh](aws/scripts/post-telemetry.sh:1-138)
- MediaLive start/stop: [aws/scripts/start-medialive-channel.sh](aws/scripts/start-medialive-channel.sh:1), [aws/scripts/stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)
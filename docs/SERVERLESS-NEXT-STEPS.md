# Serverless Control Plane and CloudFront Integration — Next Steps (Investigation Plan)

Purpose
- Replace any EC2-based control plane with a fully serverless architecture that leverages what’s already in this repo for realistic characters and telemetry.
- Keep the viewer hosted on CloudFront (S3 origin) and connect it to serverless APIs and WebSocket telemetry.
- Preserve the NVIDIA-configured Unreal Engine streamer (GPU instance) for video capture/encode only (NVENC/OBS/Unreal headless), streaming RTMP to MediaLive → MediaPackage → CloudFront. Only the “control plane” moves to serverless.
- Ensure safe, reversible, low-cost deployment.

Leverage Existing Assets (built previously)
- CloudFront viewer and live HLS:
  - Template: [aws/templates/cloudfront-viewer-and-live.json.tpl](aws/templates/cloudfront-viewer-and-live.json.tpl)
  - Deployer: [aws/scripts/deploy-cloudfront-and-viewer.sh](aws/scripts/deploy-cloudfront-and-viewer.sh)
  - Viewer: [viewer/index.html](viewer/index.html)
- Telemetry WebSocket Stack:
  - CFN: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml)
  - Deployer: [aws/scripts/deploy-telemetry.sh](aws/scripts/deploy-telemetry.sh)
  - Posting script (example): [aws/scripts/post-telemetry.sh](aws/scripts/post-telemetry.sh)
- AI Orchestrator and DynamoDB patterns (for decisions/memory):
  - CFN: [aws/templates/cfn/agent-orchestrator.yaml](aws/templates/cfn/agent-orchestrator.yaml)
  - Lambda scaffold: [aws/lambdas/agent-orchestrator/index.js](aws/lambdas/agent-orchestrator/index.js)
  - Design docs: [CLAUDE.md](CLAUDE.md), [docs/AI-AGENT-PERSONALITIES.md](docs/AI-AGENT-PERSONALITIES.md), [docs/REALISTIC-AGENT-PROFILES.md](docs/REALISTIC-AGENT-PROFILES.md), [realistic-everyday-characters.md](realistic-everyday-characters.md)
- MCP bridge and Unreal link:
  - Bridge: [mcp-bridge/index.js](mcp-bridge/index.js)
  - Viewer comms concept: [VIEWER-COMMUNICATION-SYSTEM.md](VIEWER-COMMUNICATION-SYSTEM.md)

Important Notes
- The NVIDIA Unreal Engine streamer on a GPU instance remains part of the architecture for video and audio. This instance pushes RTMP to MediaLive, packaged by MediaPackage, served by CloudFront under /live/*. No change there.
- The local Node control servers ([server/control-server.js](server/control-server.js), [server/control-server-ec2.js](server/control-server-ec2.js)) were created for rapid prototyping. The serverless design below replaces them in production (for control APIs and telemetry), while keeping the GPU streamer.

Target Serverless Architecture (High-level)
- Video path (unchanged):
  - NVIDIA-configured Unreal/OBS → MediaLive (RTMP) → MediaPackage (HLS) → CloudFront (/live/* behavior)
- Viewer/UI:
  - S3 + CloudFront for static hosting (index.html, assets)
  - HLS playback via hls.js
  - Telemetry overlay via WebSocket and/or SSE (WS preferred in serverless)
  - “Run Turn” and Character interactions via HTTP API
- Control Plane (serverless):
  - API Gateway (HTTP API) + AWS Lambda + DynamoDB
  - Endpoints:
    - GET /api/characters → Lambda: listCharacters
    - POST /api/interact → Lambda: interactCharacter
    - POST /api/run-turn → Lambda or Step Functions: runTurns
  - Telemetry:
    - API Gateway WebSocket + Lambda (connection tracking in DynamoDB; broadcast via execute-api:ManageConnections)
- Viewer runtime config:
  - Provide ws and api endpoints via S3-served config.json or via query params (?api, ?ws). Viewer already supports overrides.

Next Steps to Investigate (Prioritized)

0) NVIDIA Unreal Engine streamer alignment (video remains on GPU)
- Confirm Windows GPU EC2 stack: [aws/templates/cfn/ec2-windows-gpu.yaml](aws/templates/cfn/ec2-windows-gpu.yaml) or your existing GPU host.
- Ensure Unreal/OBS/NVENC pipeline continues pushing RTMP to MediaLive (URIs from [aws/out/medialive.ingest.json] if present).
- Verify MediaLive → MediaPackage endpoints (HLS) used in CloudFront “/live/*” behavior.
- Consider synchronizing visual feedback with control-plane telemetry:
  - Option: Unreal subscribes (client) to WebSocket telemetry to react to interactions (animations). See “Unreal command path” below.

1) Telemetry WebSocket (reuse existing stack)
- Confirm/Deploy the telemetry WebSocket:
  - Template: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml)
  - Script: [aws/scripts/deploy-telemetry.sh](aws/scripts/deploy-telemetry.sh)
- Investigation actions:
  - Verify connect/disconnect handlers store connectionIds (DynamoDB).
  - Capture outputs (wss endpoint) to aws/out.
  - Ensure execute-api:ManageConnections permission for any publisher Lambda.
- Acceptance:
  - A wss://… endpoint suitable for viewer (?ws=) and serverless broadcast.

2) Serverless Control Plane (HTTP API + Lambda + DynamoDB)
- Author CFN (serverless-control-plane.yaml) or extend [aws/templates/cfn/agent-orchestrator.yaml](aws/templates/cfn/agent-orchestrator.yaml) with:
  - HTTP routes:
    - GET /api/characters → listCharacters Lambda
    - POST /api/interact → interactCharacter Lambda
    - POST /api/run-turn → runTurnsEntry Lambda (capped loop) or Step Functions
  - DynamoDB tables:
    - Characters/world state table (PAY_PER_REQUEST)
    - WS connections table (if not in telemetry stack)
  - Environment:
    - WS_API_ENDPOINT for broadcasting telemetry
- Investigation actions:
  - JSON schemas for requests/responses matching viewer expectations.
  - Minimal world-tick logic consistent with realism docs (needs/stress drift, animation nudges).
- Acceptance:
  - Deployed API base URL (+ outputs) and working curl tests; viewer can read list/update state; WS broadcasts received.

3) Unreal command path (optional but recommended for in-engine reactions)
- Two integration patterns:
  - WebSocket subscriber inside Unreal (Blueprint/C++ or plugin) that listens to telemetry/commands and applies animations/RC commands.
  - Use existing bridge: [mcp-bridge/index.js](mcp-bridge/index.js) or [mcp-to-unreal-bridge.js](mcp-to-unreal-bridge.js) to relay serverless events into Unreal via Unreal Remote Control API.
- Investigation actions:
  - Validate feasibility of Unreal Remote Control or MCP within the GPU streamer host.
  - If using bridge on the GPU host, point it at the WS endpoint and translate messages to Unreal.
- Acceptance:
  - On viewer “nudge_action” or “set_goal,” Unreal avatar visibly reacts (e.g., animation, pose, or UI callout).

4) N-turn execution strategy (Step Functions vs. Lambda loop)
- Option A: Lambda loop with cap (<= 100 turns), single request.
- Option B: Step Functions for high counts or pacing; optionally slow-sends telemetry for “live” feel.
- Decision/Acceptance:
  - Choose based on latency/cost; document caps and implement accordingly.

5) Viewer runtime configuration
- Option A: config.json published to S3 (api + ws endpoints), loaded by viewer at start; params still override.
- Option B: Use query params (?api, ?ws).
- Acceptance:
  - Viewer works out-of-the-box from CloudFront; no hard-coded endpoints needed.

6) CloudFront patterns for serverless endpoints
- Preferred: viewer calls API Gateway and WebSocket directly (no CloudFront proxy), minimizing complexity.
- Optional: add CloudFront origins/behaviors for “/api/*” if you need same-domain routing.
- Acceptance:
  - Documented decision; implement only if it simplifies ops.

7) Security, Safety, Limits
- IAM least-privilege for Lambdas (DynamoDB ARNs, execute-api for WS API only).
- API throttling and CORS restricted to viewer domain.
- Input validation: length caps, sanitization for goal/action/message.
- Cost guardrails: continue using [cost-status.sh](cost-status.sh) and budget alarms.
- Acceptance:
  - Checklist documented and controls applied.

8) Observability
- CloudWatch Logs retention; basic alarms for Lambda errors and API 5XX.
- (Optional) Custom metrics: turnsProcessed, interactions, activeWSConnections.
- Acceptance:
  - Logs present; at least one alarm configured.

9) Data Model & Seeding
- DynamoDB “characters” items:
  - id, name, economicTier, location, state: { animation, needs:{…}, money, inventory, goal, messages[] }
- World item (optional): id=world, tick counter.
- Seed initial data from [multi-character-orchestrator.js](multi-character-orchestrator.js) and realism docs.
- Acceptance:
  - listCharacters returns a schema matching viewer needs.

10) End-to-End Demo Acceptance (CloudFront viewer)
- With NVIDIA Unreal streamer sending HLS, viewer shows:
  - Live HLS video.
  - Telemetry overlay connected to WS.
  - Left panel tabs:
    - Telemetry (connection + fields)
    - Characters (live state)
    - Controls (run turns)
  - Interactions update state + telemetry; optional Unreal reaction if bridge integrated.
- Acceptance Script:
  - Open CloudFront viewer, connect WS.
  - Run 5 turns; observe needs/stress + telemetry.
  - Set goal for alex_chen; observe update and optional avatar reaction.

Phased Execution Plan

Phase 0: Prep (Video)
- Keep NVIDIA Unreal GPU streaming to MediaLive; confirm MediaPackage endpoint and CloudFront /live/*.

Phase 1: Telemetry WS
- Deploy telemetry WebSocket stack; capture ws endpoint outputs.

Phase 2: Serverless Control Plane
- CFN for HTTP API + Lambdas + DynamoDB; implement Lambdas and caps; broadcast via WS.

Phase 3: Viewer Config
- Add config.json or use query params to point viewer to serverless endpoints.

Phase 4: Unreal Command Path (optional)
- Bridge serverless commands to Unreal (WS client in Unreal or Node bridge → Unreal RC).

Phase 5: Security/Observability
- Throttling, CORS, IAM, logs, alarms.

Phase 6: UAT
- Validate controls end-to-end alongside live video.

Risk & Mitigations
- WS proxy through CloudFront: avoid initially; use direct ws endpoint.
- Lambda timeouts for N-turn: cap and/or Step Functions for larger sequences.
- Unreal integration complexity: start with visual-only (video + overlay), phase-in in-engine reactions as a follow-up.

Cost Notes
- Control plane is serverless (API Gateway + Lambda + DynamoDB).
- NVIDIA Unreal GPU instance remains only for video encode/stream; start/stop it per session to manage cost.

Definition of Done (Serverless + NVIDIA Streamer)
- CloudFront viewer URL shows live HLS from the NVIDIA streaming instance.
- Serverless control plane provides Characters tab, controls, and real-time telemetry via WS.
- Optional: in-engine reactions via Unreal bridge to demonstrate loop-closure from web → serverless → Unreal.

Action Items (Checklist)
- [ ] Confirm/deploy telemetry WS: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml)
- [ ] Author serverless-control-plane.yaml (HTTP API + Lambdas + DynamoDB)
- [ ] Implement Lambdas:
  - [ ] listCharacters
  - [ ] interactCharacter
  - [ ] runTurnsEntry (cap 100 turns)
  - [ ] WS broadcast utility
- [ ] Seed DynamoDB with initial characters (aligned with realism docs)
- [ ] Publish viewer config.json; optionally auto-fetch in [viewer/index.html](viewer/index.html)
- [ ] Validate viewer with CloudFront (?api, ?ws or config.json)
- [ ] Apply throttling, CORS, IAM least-privilege; add logs retention + alarms
- [ ] Optional: implement Unreal bridge (WS subscriber or [mcp-bridge/index.js](mcp-bridge/index.js)) for in-engine reactions
- [ ] Update runbooks: [docs/MCP-RUNBOOK.md](docs/MCP-RUNBOOK.md), [VIEWER-COMMUNICATION-SYSTEM.md](VIEWER-COMMUNICATION-SYSTEM.md)

References (for context)
- Viewer: [viewer/index.html](viewer/index.html)
- CloudFront + Viewer deploy: [aws/scripts/deploy-cloudfront-and-viewer.sh](aws/scripts/deploy-cloudfront-and-viewer.sh)
- Telemetry WS: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml), [aws/scripts/deploy-telemetry.sh](aws/scripts/deploy-telemetry.sh)
- Orchestrator scaffold: [aws/templates/cfn/agent-orchestrator.yaml](aws/templates/cfn/agent-orchestrator.yaml)
- NVIDIA Unreal GPU (video): [aws/templates/cfn/ec2-windows-gpu.yaml](aws/templates/cfn/ec2-windows-gpu.yaml)
- Realistic character guidance: [CLAUDE.md](CLAUDE.md), [docs/AI-AGENT-PERSONALITIES.md](docs/AI-AGENT-PERSONALITIES.md), [docs/REALISTIC-AGENT-PROFILES.md](docs/REALISTIC-AGENT-PROFILES.md)

Notes on Reversibility
- No EC2 for control plane. NVIDIA GPU instance remains solely for streaming. All control flows are serverless and can be rolled back by deleting the API/Lambda/WS stacks without impacting the video pipeline.

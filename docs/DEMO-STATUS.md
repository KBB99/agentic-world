# Agentic Demo — Status, Endpoints, Costs, and Next Steps

Generated: 2025-08-09 UTC

This document captures the current state of the live demo stack (Unreal → OBS → MediaLive → MediaPackage → CloudFront, with telemetry overlay), plus exact next steps to complete validation while controlling costs.

## Summary

- Region: us-east-1
- Project: agentic-demo
- Viewer (CloudFront): https://d1u690gz6k82jo.cloudfront.net/index.html
- HLS master (via CloudFront path): https://d1u690gz6k82jo.cloudfront.net/live/index.m3u8
- HLS master (direct MediaPackage): https://ccf3786b925ee51c.mediapackage.us-east-1.amazonaws.com/out/v1/f7dd6e8b0ee74ff4954fcc90c4e138b8/index.m3u8
- MediaLive RTMP ingest (primary): rtmp://54.174.84.192:1935/agentic-demo/primary
- MediaLive RTMP ingest (backup): rtmp://54.210.126.20:1935/agentic-demo/backup
- Telemetry WebSocket (WSS): wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
- Windows GPU EC2: i-04bcee1a80b8c7839 (g5.xlarge, Windows Server 2022) — STOPPED

## Current stack status

- CloudFront distribution is deployed; viewer page at the domain above (code: [viewer/index.html](viewer/index.html:1)).
- MediaPackage Channel + HLS endpoint is active (template: [aws/templates/cfn/mediapackage.yaml](aws/templates/cfn/mediapackage.yaml:1)).
- MediaLive Channel is provisioned and currently IDLE (stopped) (template: [aws/templates/cfn/medialive.yaml](aws/templates/cfn/medialive.yaml:1)).
- Telemetry WebSocket is deployed and functional (fixed to Node.js 16 runtime) (template: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml:1-312)).
- Windows GPU instance is STOPPED. OBS is installed; audio services are enabled; NVIDIA driver not yet installed; Unreal/MetaHuman not yet installed.

Validation performed so far

- HLS master playlist resolves via CloudFront and directly via MediaPackage.
- Telemetry overlay verified end-to-end: viewer connected via ?ws=..., and [aws/scripts/post-telemetry.sh](aws/scripts/post-telemetry.sh:1-138) broadcast reached the overlay (Goal/Action/Rationale/Result updated and avatar animated).

## MCP integration (Unreal)

- Unreal MCP transport: JSON-RPC over TCP at 127.0.0.1:32123 (loopback).
- Bridge service (local, no new AWS spend): connects to MCP TCP and forwards succinct telemetry to the existing WebSocket:
  - Code: [mcp-bridge/index.js](mcp-bridge/index.js:1), [mcp-bridge/start-bridge.ps1](mcp-bridge/start-bridge.ps1:1), [mcp-bridge/package.json](mcp-bridge/package.json:1)
  - Runbook: [docs/MCP-RUNBOOK.md](docs/MCP-RUNBOOK.md:1)
- Telemetry WebSocket Lambda accepts envelope payloads to avoid route-selection collisions:
  - Path: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml:152)
  - Redeploy: REGION=us-east-1 PROJECT=agentic-demo bash [aws/scripts/deploy-telemetry.sh](aws/scripts/deploy-telemetry.sh:1)
## Endpoints and IDs (source: [aws/out/stack-outputs.json](aws/out/stack-outputs.json:1-19), [aws/out/medialive.ingest.json](aws/out/medialive.ingest.json:1-4), [aws/out/telemetry.outputs.json](aws/out/telemetry.outputs.json:1-5))

- CloudFront domain: d1u690gz6k82jo.cloudfront.net
- MediaPackage:
  - ChannelId: agentic-demo
  - HLS endpoint URL: https://ccf3786b925ee51c.mediapackage.us-east-1.amazonaws.com/out/v1/f7dd6e8b0ee74ff4954fcc90c4e138b8/index.m3u8
- MediaLive:
  - InputId: 7798988
  - ChannelId: 3407016
  - RTMP ingest:
    - primary: rtmp://54.174.84.192:1935/agentic-demo/primary
    - backup:  rtmp://54.210.126.20:1935/agentic-demo/backup
- Telemetry:
  - WebSocket WSS: wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
  - Connections table: agentic-demo-telemetry-connections

## Cost overview (observed via Cost Explorer; CE may lag by hours)

Daily (demo-related services) — 2025-08-07 → 2025-08-08, estimated=True
- EC2 - Other: 4.584516 USD
- Amazon EC2 - Compute: 0.777600 USD
- S3: 0.008939 USD
- DynamoDB: 0.003341 USD
- API Gateway: 0.002465 USD
- Lambda: 0.000067 USD
- CloudFront / CloudWatch: 0

Month-to-date (demo-related services) — 2025-08-01 → 2025-08-08, estimated=True
- EC2 - Other: 32.091615 USD
- Amazon EC2 - Compute: 5.443200 USD
- S3: 0.057838 USD
- DynamoDB: 0.018896 USD
- API Gateway: 0.017030 USD
- Lambda: 0.000468 USD
- CloudFront / CloudWatch: 0

Practical cost control

- Keep MediaLive stopped except when actively streaming (scripts: [aws/scripts/start-medialive-channel.sh](aws/scripts/start-medialive-channel.sh:1), [aws/scripts/stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)).
- Stop the GPU EC2 instance between work sessions.
- Viewer/Telemetry stacks have negligible idle costs.

## RDP access (Windows GUI)

- RDP = Remote Desktop Protocol (Microsoft GUI remote access).
- macOS: install “Microsoft Remote Desktop” (App Store). Windows: run mstsc.
- Host: EC2 public IP of i-04bcee1a80b8c7839.
- User: Administrator
- Password: retrieve if needed:
  ```bash
  aws ec2 get-password-data --region us-east-1 \
    --instance-id i-04bcee1a80b8c7839 \
    --priv-launch-key /path/to/your-key.pem > aws/out/win-admin-password.json
  ```
  Then open [aws/out/win-admin-password.json](aws/out/win-admin-password.json:1).
- Security group must allow inbound TCP 3389 from your IP.

## EC2 instance state and prework done

- Instance: i-04bcee1a80b8c7839 (g5.xlarge, Windows Server 2022) — STOPPED.
- OBS installed via SSM (path: C:\Program Files\obs-studio\bin\64bit\obs64.exe) using [aws/out/ssm-install-obs.json](aws/out/ssm-install-obs.json:1-11).
- Audio services enabled via SSM using [aws/out/ssm-enable-audio.json](aws/out/ssm-enable-audio.json:1-14).
- GPU driver not yet installed (nvidia-smi was not present in the last check via [aws/out/ssm-check-gpu-audio.json](aws/out/ssm-check-gpu-audio.json:1)).
- Unreal Engine 5 and MetaHuman sample not yet installed.

## Next steps (operator checklist — cost-aware)

1) Start the EC2 GPU instance
   ```bash
   aws ec2 start-instances --region us-east-1 --instance-ids i-04bcee1a80b8c7839
   aws ec2 wait instance-running --region us-east-1 --instance-ids i-04bcee1a80b8c7839
   aws ec2 describe-instances --region us-east-1 --instance-ids i-04bcee1a80b8c7839 \
     --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
   ```

2) RDP into the instance and install NVIDIA GPU driver (G5 A10G)
   - On the instance, open the AWS doc “Install NVIDIA drivers on Windows instances”.
   - Download the Windows Server 2022 driver for G5 (A10G); run Express install; reboot.
   - Validate after reboot:
     - Device Manager → Display adapters shows NVIDIA.
     - dxdiag → Display tab shows NVIDIA + feature levels.
     - Optional: run nvidia-smi.

3) Install Unreal Engine 5 + MetaHuman sample
   - Install Epic Games Launcher; sign in.
   - Install Unreal Engine 5.x (latest stable).
   - In Launcher Library, install a MetaHuman-capable sample (e.g., “MetaHuman Sample”).
   - Open the sample; Play-In-Editor in a window (1080p) and ensure audio plays to default device.

4) Configure OBS
   - Settings → Output:
     - Output Mode: Advanced (or Simple equivalent)
     - Encoder: NVIDIA NVENC H.264 (new)
     - Bitrate: 4000 Kbps (start), Keyframe: 2 s, Profile: high, Preset: Performance
   - Settings → Video:
     - Base (Canvas): 1920x1080 (or 1280x720); Output (Scaled): 1920x1080 (or 1280x720); FPS: 30
   - Settings → Audio:
     - Desktop Audio: Default (meters should move when UE plays sound)
   - Settings → Stream (Service: Custom)
     - Server: rtmp://54.174.84.192:1935/agentic-demo
     - Stream Key: primary
     - Or full URL: rtmp://54.174.84.192:1935/agentic-demo/primary
   - Scene setup:
     - Scene “Unreal”; Source “Game Capture” → Capture specific window → Unreal editor viewport.
     - If black capture, try “Capture any fullscreen application” or temporarily “Display Capture”.

5) Start MediaLive (only when ready to stream)
   ```bash
   bash aws/scripts/start-medialive-channel.sh
   ```
   - Wait for Channel state RUNNING; then click “Start Streaming” in OBS.

6) Validate viewer playback and overlay
   - Open viewer: https://d1u690gz6k82jo.cloudfront.net/index.html and click Play.
   - The page first tries /live/index.m3u8 (rewritten to MediaPackage by CloudFront Function).
   - Expected latency: standard HLS (~10–20+ seconds).
   - Telemetry overlay: open with ws param to confirm live updates:
     https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss%3A%2F%2Funk0zycq5d.execute-api.us-east-1.amazonaws.com%2Fprod
   - Optional: push a test overlay message from your workstation:
     ```bash
     WS=wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
     TABLE=agentic-demo-telemetry-connections
     bash aws/scripts/post-telemetry.sh --ws "$WS" --table "$TABLE" \
       --goal "Explore foyer" --action "MoveForward 1m" \
       --rationale "Move to entry to begin path planning and spatial mapping" \
       --result "Initiated"
     ```

7) Stop streaming and control costs
   - In OBS, Stop Streaming.
   - Stop MediaLive:
     ```bash
     bash aws/scripts/stop-medialive-channel.sh
     ```
   - Stop the EC2 instance:
     ```bash
     aws ec2 stop-instances --region us-east-1 --instance-ids i-04bcee1a80b8c7839
     aws ec2 wait instance-stopped --region us-east-1 --instance-ids i-04bcee1a80b8c7839
     ```

## Troubleshooting

- Viewer shows fallback video (sample.mp4) instead of live:
  - MediaLive Channel must be RUNNING and ingesting from OBS.
  - Verify OBS uses the correct RTMP server/stream key.
  - Confirm MediaPackage endpoint URL and CloudFront Function association.
- Black screen in OBS Game Capture:
  - Use “Capture any fullscreen application” or “Display Capture”.
- No audio in the viewer:
  - Ensure Windows audio services are running (we enabled them via SSM).
  - Ensure Unreal audio routes to the default device; OBS Desktop Audio meters should move.
- Telemetry overlay not updating:
  - Ensure the viewer is opened with the ws parameter and that the WebSocket shows “Agent Running”.
  - Use the broadcaster script to send a test event (see step 6).

## References

- MediaPackage CFN: [aws/templates/cfn/mediapackage.yaml](aws/templates/cfn/mediapackage.yaml:1)
- MediaLive CFN: [aws/templates/cfn/medialive.yaml](aws/templates/cfn/medialive.yaml:1)
- Telemetry CFN: [aws/templates/cfn/telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml:1-312)
- Deploy MediaPackage: [aws/scripts/deploy-mediapackage.sh](aws/scripts/deploy-mediapackage.sh:1)
- Deploy MediaLive: [aws/scripts/deploy-medialive.sh](aws/scripts/deploy-medialive.sh:1)
- Deploy CloudFront + viewer: [aws/scripts/deploy-cloudfront-and-viewer.sh](aws/scripts/deploy-cloudfront-and-viewer.sh:1)
- Aggregate outputs: [aws/scripts/aggregate-outputs.sh](aws/scripts/aggregate-outputs.sh:1)
- Start MediaLive: [aws/scripts/start-medialive-channel.sh](aws/scripts/start-medialive-channel.sh:1)
- Stop MediaLive: [aws/scripts/stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)
- Telemetry broadcaster: [aws/scripts/post-telemetry.sh](aws/scripts/post-telemetry.sh:1-138)
- Viewer page: [viewer/index.html](viewer/index.html:1)

---

For an at-a-glance checklist, see “Next steps (operator checklist)” above. Keep MediaLive and the EC2 GPU instance stopped when idle to minimize cost.
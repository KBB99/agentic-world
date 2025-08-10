# Windows Unreal Streaming — Login and Setup Guide

This guide shows exactly how to log into the Windows GPU instance, install what’s needed, and stream a real Unreal Engine scene to your CloudFront viewer with the live telemetry overlay. It assumes the AWS-side pipeline is already deployed.

Quick links
- Viewer (click Play): https://d1u690gz6k82jo.cloudfront.net/index.html
- Viewer + overlay: https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss%3A%2F%2Funk0zycq5d.execute-api.us-east-1.amazonaws.com%2Fprod
- RTMP ingest (OBS):
  - Primary: rtmp://54.174.84.192:1935/agentic-demo/primary
  - Backup:  rtmp://54.210.126.20:1935/agentic-demo/backup

References (repo)
- OBS profile setup: [ssm-configure-obs.json](aws/out/ssm-configure-obs.json:1)
- OBS scene + shortcuts: [ssm-configure-obs-scenes.json](aws/out/ssm-configure-obs-scenes.json:1)
- Temporary Autologon + auto‑OBS: [ssm-autologon.json](aws/out/ssm-autologon.json:1)
- Viewer telemetry handler: [index.html](viewer/index.html:154)
- WebSocket Lambda (envelope mapping): [telemetry-websocket.yaml](aws/templates/cfn/telemetry-websocket.yaml:152)
- MCP bridge helper: [start-bridge.ps1](mcp-bridge/start-bridge.ps1:1), code: [index.js](mcp-bridge/index.js:1)

1) Log into the Windows GPU instance (RDP)

a) Find public IP
- AWS Console → EC2 → Instances → select i-04bcee1a80b8c7839 (Name: agentic-demo-gpu) → copy “Public IPv4 address”.

b) Get Administrator password (choose ONE)
- Parameter Store SecureString (we set this for temporary Autologon):
  aws ssm get-parameter --region us-east-1 --name /agentic-demo/win/admin-password --with-decryption --query Parameter.Value --output text
- Or standard EC2 method (requires your PEM for KeyName agentic-demo-ue5-20250809):
  aws ec2 get-password-data --region us-east-1 --instance-id i-04bcee1a80b8c7839 --priv-launch-key /path/to/agentic-demo-ue5-20250809.pem --query PasswordData --output text

c) RDP
- macOS: Microsoft Remote Desktop (App Store); Windows: Start → mstsc
- Host: the Public IP from (a)
- User: Administrator; Password: from (b)
- If RDP fails: confirm the instance Security Group allows inbound TCP 3389 from your IP.

2) Install NVIDIA GPU driver (G5 A10G, Windows Server 2022)
- On the instance, open the AWS guide “Install NVIDIA drivers on Windows instances”.
- Download the Windows Server 2022 driver for G5 (A10G), run Express install; reboot if prompted.
- Verify after reboot:
  - Device Manager → Display adapters shows NVIDIA.
  - dxdiag → Display tab shows NVIDIA + feature levels.

3) Install Epic Games Launcher and Unreal Engine 5.x
- Download Epic Games Launcher (Interactive):
  - https://store.epicgames.com/en-US/download (sign in interactively, handle 2FA if prompted)
- Or MSI (silent) method:
  - Download: https://launcher-public-service-prod06.ol.epicgames.com/launcher/api/installer/download/EpicGamesLauncherInstaller.msi
  - Install (PowerShell as Administrator):
    Start-Process msiexec.exe -ArgumentList "/i `"$env:USERPROFILE\Downloads\EpicGamesLauncherInstaller.msi`" /qn /norestart" -Wait -NoNewWindow
- Launch “Epic Games Launcher” and sign in.
- Install Unreal Engine 5.x (latest stable) from the Launcher → Unreal Engine → Library.

4) Create/open a sample project and enable Python remote execution
- Launch UE 5.x from Epic Launcher.
- Create a “Third Person” (or any) sample project and open it.
- Enable MCP compatibility in the Editor:
  - Edit → Plugins → enable “Python Editor Script Plugin”
  - Edit → Project Settings → search “Python” → enable “Enable Remote Execution”
  - Restart the Editor if prompted and reopen the project.

5) Start streaming with OBS (already preconfigured)
- Desktop shortcuts:
  - “OBS Agentic Live.lnk” (profile only)
  - “OBS Agentic Live + Display.lnk” (profile + Display Capture; auto-starts streaming)
- If OBS isn’t running, double-click “OBS Agentic Live + Display.lnk”. It loads:
  - Profile: AgenticLive (RTMP server/key already set)
  - Scene Collection: AgenticUnreal (Display Capture on monitor 0)
  - It is configured to start streaming automatically. If not, click Start Streaming.
- Optional (cleaner capture): add “Game Capture” → Capture specific window → UnrealEditor.exe (viewport), then place it above or disable Display Capture.

6) Validate playback and overlay
- Video (click Play): https://d1u690gz6k82jo.cloudfront.net/index.html
- Overlay (WebSocket): https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss%3A%2F%2Funk0zycq5d.execute-api.us-east-1.amazonaws.com%2Fprod
- Expected:
  - HLS plays with ~10–20 s latency.
  - Overlay “Status” shows “Agent Running”; the text fields update when telemetry arrives.

7) Optional: Live MCP overlay from Unreal
- Run your Unreal MCP Server (TCP JSON‑RPC) on Windows listening at 127.0.0.1:32123.
- Start the bridge on Windows:
  - PowerShell: cd to your repo → cd .\mcp-bridge → npm install
  - .\ [start-bridge.ps1](mcp-bridge/start-bridge.ps1:1) -Wss "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod" -Host "127.0.0.1" -Port 32123 -Verbose
- The overlay maps to {goal, action, rationale, result}; viewer handler is in [index.html](viewer/index.html:154).

8) Security cleanup (disable temporary Autologon after validation)
- Remove the Startup shortcut:
  - C:\Users\Administrator\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\Start OBS Agentic Live + Display.lnk
- Clear Autologon registry values (PowerShell as Administrator):
  Remove-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name 'DefaultPassword' -ErrorAction SilentlyContinue
  Set-ItemProperty -Path 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon' -Name 'AutoAdminLogon' -Value '0'
- Rotate Administrator password; optionally delete the Parameter Store secret /agentic-demo/win/admin-password.

9) Cost control (important)
- In OBS, Stop Streaming when done.
- Stop MediaLive: bash [stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)
- Stop the EC2 GPU instance (compute charges end; EBS storage charges remain).

Troubleshooting
- Viewer shows fallback sample.mp4:
  - Ensure MediaLive Channel is RUNNING and OBS is streaming to rtmp://54.174.84.192:1935/agentic-demo (key: primary).
- OBS “Game Capture” black:
  - Try “Capture any fullscreen application”, or use Display Capture temporarily.
- No audio:
  - Verify Windows default playback device and that OBS “Desktop Audio” meters move when UE plays sound.
- Overlay not updating:
  - Open the viewer with the ws parameter (see step 6).
  - Send a quick test from your workstation using [post-telemetry.sh](aws/scripts/post-telemetry.sh:1-138).

Appendix — useful one‑liners (from your workstation)
- Start MediaLive: bash [start-medialive-channel.sh](aws/scripts/start-medialive-channel.sh:1)
- Stop MediaLive: bash [stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1)
- Show MediaLive state: aws medialive describe-channel --region us-east-1 --channel-id 3407016 --query State --output text
- Aggregate outputs: bash [deploy-all.sh](aws/scripts/deploy-all.sh:1)
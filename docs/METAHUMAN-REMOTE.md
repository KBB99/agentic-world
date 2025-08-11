# MetaHuman Remote Control — Add, Drive, and Stream

Goal: Add a MetaHuman to your UE5 project on the Windows GPU instance and control it remotely (move-to, play animations), while streaming via OBS → MediaLive → MediaPackage → CloudFront.

This guide uses Unreal’s Remote Control API (HTTP/WebSocket) so you can trigger Blueprint functions and tweak properties over the network. It works in the Editor (PIE/Standalone) and in packaged builds when the plugin is enabled.

Prerequisites
- Windows GPU instance with NVIDIA driver installed (see [docs/WINDOWS-UNREAL-STREAM.md](docs/WINDOWS-UNREAL-STREAM.md:37)).
- Unreal Engine 5.x installed (see [docs/WINDOWS-UNREAL-STREAM.md](docs/WINDOWS-UNREAL-STREAM.md:44)).
- OBS streaming to MediaLive (see [docs/WINDOWS-UNREAL-STREAM.md](docs/WINDOWS-UNREAL-STREAM.md:62)).

Plugin setup (once per project)
1) Enable these plugins in Edit → Plugins:
   - MetaHuman
   - Quixel Bridge
   - Remote Control API
   - Remote Control Web Interface
   - Web Remote Control
   - Control Rig (usually enabled by MetaHuman)
   - Optional: Live Link & Live Link Face (for facial capture later)
2) Project Settings:
   - Search “Remote Control” and ensure the HTTP server is enabled.
   - Default ports (UE5): HTTP 30010, WebSocket 30011. You can change them if needed.
   - For packaged builds, keep the Remote Control API enabled in your Packaging settings.

Add a MetaHuman to your project
1) Open the Quixel Bridge panel inside UE (Add → Quixel Bridge).
2) Click the MetaHumans tab, pick or create a MetaHuman, then Add to Project. Wait for assets to download/import.
3) In the Content Browser, locate the blueprint BP_<Name> (for example, BP_Ada) and drag it into your level.
4) With the actor selected:
   - Auto Possess Player: Disabled
   - Auto Possess AI: Placed in World or Spawned
   - Ensure the Character Movement component exists (MetaHuman blueprints are Characters by default).

Navigation (for MoveTo)
1) Place a Nav Mesh Bounds Volume covering the floor where you want the character to move.
2) Press P to visualize the green nav area. If you don’t see it, ensure the level has a NavMesh and the volume covers the area.

Create remote-callable functions on the MetaHuman
You can add functions to the existing BP_<Name> or create a child blueprint (recommended) so you don’t modify vendor assets:
1) Right-click BP_<Name> → Create Child Blueprint Class; name it BP_RemoteMetaHuman.
2) Open BP_RemoteMetaHuman and implement:
   A) Function RemoteMoveTo (Destination: Vector)
      - Get Controller → AI Move To
      - Pawn: Self
      - Destination: the input vector
      - Acceptance Radius: e.g., 50.0
      - Ensure there is an AIController. If none, on BeginPlay do “Spawn Default Controller”.

   B) Function RemotePlayMontage (Montage: AnimMontage asset reference)
      - Use “Play Anim Montage” on the Mesh. The MetaHuman AnimBP must support the montage slot.

   C) Function RemoteLookAt (Target: Vector)
      - Compute LookAt rotation: Find Look At Rotation (Actor Location → Target)
      - Set Actor Rotation (Z/Yaw only) or use a yaw-only interp.

3) Compile and Save. Replace your placed BP_<Name> with BP_RemoteMetaHuman (or add BP_RemoteMetaHuman to the level).

Expose the functions via Remote Control
1) Window → Remote Control. Create a new Preset (name it RemoteMetaHuman).
2) Click Add → Actor → pick your BP_RemoteMetaHuman actor in the level.
3) In the Preset, expand the actor, select Functions, and add:
   - RemoteMoveTo
   - RemotePlayMontage
   - RemoteLookAt
4) Optionally, expose properties like CharacterMovement.MaxWalkSpeed or Transform location/rotation.
5) Click Save on the Preset.

Find the object path you’ll call
- In World Outliner, right-click your BP_RemoteMetaHuman actor → Copy Reference.
- You’ll get something like: /Game/Maps/DemoMap.DemoMap:PersistentLevel.BP_RemoteMetaHuman_C_1

Test locally from the instance (HTTP)
From PowerShell or CMD on the Windows instance:
curl -s -X POST http://127.0.0.1:30010/remote/object/call -H "Content-Type: application/json" -d "{\"objectPath\":\"/Game/Maps/DemoMap.DemoMap:PersistentLevel.BP_RemoteMetaHuman_C_1\",\"functionName\":\"RemoteMoveTo\",\"parameters\":{\"Destination\":{\"X\":0,\"Y\":600,\"Z\":0}}}"

If successful, the character should walk ~600 units on Y (assuming there is nav coverage).

List presets (useful for discovery)
curl -s http://127.0.0.1:30010/remote/presets

WebSocket alternative
- The WebSocket endpoint is ws://127.0.0.1:30011.
- You can use a WS client (e.g., wscat) to send Remote Control API messages. HTTP is simpler for the initial tests.

Secure remote access from your workstation
Do not open these ports to the internet. Use AWS Systems Manager Session Manager for port forwarding:
aws ssm start-session --region us-east-1 --target i-INSTANCEID --document-name AWS-StartPortForwardingSession --parameters "portNumber=['30010'],localPortNumber=['30010']"

Then call http://127.0.0.1:30010 from your local machine (the session forwards to the instance). Replace i-INSTANCEID with your EC2 instance ID.

Drive from Node.js (example)
If you prefer Node, run this on the instance or through the SSM tunnel:
node -e "const http=require('http');const data=JSON.stringify({objectPath:'/Game/Maps/DemoMap.DemoMap:PersistentLevel.BP_RemoteMetaHuman_C_1',functionName:'RemoteMoveTo',parameters:{Destination:{X:300,Y:0,Z:0}}});const req=http.request({hostname:'127.0.0.1',port:30010,path:'/remote/object/call',method:'POST',headers:{'Content-Type':'application/json','Content-Length':Buffer.byteLength(data)}},res=>{res.on('data',d=>process.stdout.write(d));});req.on('error',e=>console.error(e));req.write(data);req.end();"

Integrate with this repo’s MCP overlay (optional)
- The overlay is independent; it just shows {goal, action, rationale, result}. See [mcp-bridge/index.js](mcp-bridge/index.js:391) and [viewer/index.html](viewer/index.html:154).
- You can have your remote controller send telemetry lines to the WebSocket alongside calling Unreal, e.g., {action:'MoveTo', result:'Initiated'} to keep the on‑screen status in sync.

Recommended defaults for sharp visuals
- In-game console: r.SetRes 1920x1080f, t.MaxFPS 60, r.VSync 0
- OBS: 1080p60, NVENC H.264, 8 Mbps CBR, keyframe 2s, Lanczos scaler (see [aws/templates/cfn/medialive.yaml](aws/templates/cfn/medialive.yaml:24) for bitrate).

Packaging notes
- Ensure Remote Control API and any required Blueprints are included in the packaged build.
- If using HTTP in a packaged game, confirm ports are allowed by Windows Firewall on the instance (or continue to use SSM port forwarding).

Extending control (facial, speech, gaze)
- Facial capture: Enable Live Link and use the iOS Live Link Face app; the MetaHuman head will receive ARKit curves. Combine with your movement control.
- Speech: Trigger in-game audio playback, or stream TTS output as a sound cue. For overlay text only, send the text via the telemetry bridge.
- Gaze/head aim: Expose a function that rotates a head aim target and drive it from your remote client.

Troubleshooting
- Character doesn’t move:
  - Make sure a Nav Mesh Bounds Volume covers the area and is built (green overlay). Ensure an AIController is spawned (“Spawn Default Controller” on BeginPlay).
- HTTP call returns 404/400:
  - Verify Remote Control API plugin is enabled and running, and check the objectPath. Use Copy Reference to get the exact path. Check that the function is exposed in the Preset.
- OBS shows a blurry stream:
  - Raise OBS bitrate and match MediaLive params (see [aws/templates/cfn/medialive.yaml](aws/templates/cfn/medialive.yaml:24)).
- No NVENC in OBS:
  - Install NVIDIA driver and reconnect using NICE DCV/Parsec if RDP blocks GPU (see [docs/WINDOWS-UNREAL-STREAM.md](docs/WINDOWS-UNREAL-STREAM.md:37)).

Alternative: Pixel Streaming (interactive input)
- If you need remote keyboard/mouse control with sub-second interactivity, consider Unreal Pixel Streaming instead of OBS. It adds cost/complexity and replaces the video pipeline with WebRTC; not necessary for this broadcast pipeline, but it’s an option.

Checklist (minimal working path)
- Plugins enabled (Remote Control + MetaHuman + Bridge)
- MetaHuman placed as BP_RemoteMetaHuman (Character)
- Nav Mesh placed; AI Controller spawns
- RemoteMoveTo exposed in a Remote Control Preset
- curl POST to /remote/object/call succeeds; actor moves
- OBS streaming 1080p60 NVENC to MediaLive; viewer plays via CloudFront
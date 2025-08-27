# Notes — Sunday August 17, 2025

Status summary (paused to control costs)
- MediaLive channel 3407016: IDLE (stopped)
- Windows GPU EC2 i-04bcee1a80b8c7839: stopped, type g5.4xlarge (64 GiB)
- Last known EC2 Public IP before stop: 100.26.181.155
- Viewer/CloudFront domain: d1u690gz6k82jo.cloudfront.net (see [aws/out/cloudfront.outputs.json](aws/out/cloudfront.outputs.json:1))

Context
We now have a MetaHuman in Unreal. The immediate need is remote WASD-like control without MCP. We will:
- Use Unreal’s Remote Control API for a quick, direct control channel (HTTP/WebSocket on the Unreal host).
- Optionally, follow up with a lightweight plugin for a purpose-built input server.

Approach A (fast): Unreal Remote Control API (no custom plugin required)
1) In Unreal, enable plugins: Remote Control API and Remote Control.
2) Add an Actor “RemoteWASDController” to the level that forwards remote calls to the possessed Character:
   - Functions: MoveForward(Value, DurationOptional), MoveRight(Value, DurationOptional), TurnYawRate(Value, DurationOptional), LookPitchRate(Value, DurationOptional), Jump(), StopJumping(), SetSprint(Enabled).
   - Implementation: For movement, call AddMovementInput(GetActorForwardVector(), Value) and AddMovementInput(GetActorRightVector(), Value); for turn/look call AddControllerYawInput/ AddControllerPitchInput; for jump call Character->Jump()/StopJumping().
3) Expose the above functions in a Remote Control Preset so they can be invoked via HTTP or WebSocket.
4) Start the Remote Control API server (default HTTP 30010, WS 30020). Bind to 127.0.0.1 and use an SSM port forward or SSH tunnel for secure remote control.

Example HTTP call (invoke a BlueprintCallable function)
POST http://127.0.0.1:30010/remote/object/call
Body (JSON):
{
  "objectPath": "/Game/YourMap.YourMap:PersistentLevel.RemoteWASDController_C_0",
  "functionName": "MoveForward",
  "parameters": { "Value": 1.0, "Duration": 0.25 }
}

Holding movement
- To “hold W”, send MoveForward with Value 1.0 every 100–200 ms or include a small Duration parameter and re-issue while held.
- For “turn right” (mouse X), repeatedly call TurnYawRate with a small rate over the desired duration.

Security notes
- Keep the API bound to localhost. Use AWS SSM Session Manager port forwarding to reach it remotely.
- Do not expose these ports publicly in the Security Group.

Approach B (robust): Lightweight plugin “StrandsInputServer”
Goal: provide a minimal JSON command server inside Unreal that maps to Character movement and actions. No editor windows required; works in PIE and packaged builds.
Transport: TCP or WebSocket server running in-game on localhost; secure via tunnel.
Command schema (JSON lines):
{ "cmd": "move", "forward": 1.0, "right": 0.0, "duration": 0.25 }
{ "cmd": "look", "yawRate": 0.5, "pitchRate": 0.0, "duration": 0.2 }
{ "cmd": "jump" }
{ "cmd": "sprint", "enabled": true }

Server responsibilities
- Parse JSON, schedule commands on the game thread, and drive the possessed Pawn:
  - Move → AddMovementInput(forward/right)
  - Look → AddControllerYawInput/AddControllerPitchInput
  - Jump/Stop → Character->Jump()/StopJumping()
- Optional: cap rates and normalize inputs for safety.

Why not fake keyboard keys?
- OS-level key injection depends on window focus, breaks in background/headless, and is non-deterministic. Direct gameplay function calls are reliable and net-friendly.

Streaming and control separation
- Keep video/audio via OBS → MediaLive. Use Remote Control API (or the plugin) purely for control messages.
- References: [docs/WINDOWS-UNREAL-STREAM.md](docs/WINDOWS-UNREAL-STREAM.md:1), [aws/scripts/stop-medialive-channel.sh](aws/scripts/stop-medialive-channel.sh:1).

Next actions (when resuming)
- In Unreal: enable Remote Control API, add RemoteWASDController functions, create Preset, start HTTP/WS server.
- On a controller host: send HTTP/WS calls to invoke Move/Turn/Jump periodically.
- If needed, proceed to implement “StrandsInputServer” plugin for a first-class control channel.

Cost/state log
- 23:02–00:44 ET: MediaLive started and EC2 resized to g5.4xlarge.
- 23:52 ET: MediaLive confirmed RUNNING; ingest endpoints retrieved.
- 00:43 ET: EC2 running at 100.26.181.155 after resize.
- 03:02 ET: MediaLive stopped; EC2 stopped for cost control.
- Files/refs: [aws/out/cloudfront.outputs.json](aws/out/cloudfront.outputs.json:1), [CLAUDE.md](CLAUDE.md:87), [WINDOWS-SETUP.md](WINDOWS-SETUP.md:1), [docs/METAHUMAN-REMOTE.md](docs/METAHUMAN-REMOTE.md:1).

Decision
- Short term: use Unreal Remote Control API (no MCP).
- Medium term: implement StrandsInputServer plugin to accept JSON commands and map to Character movement.
- Long term: optionally unify with MCP so the same control path can be driven by agents with telemetry.

— End —
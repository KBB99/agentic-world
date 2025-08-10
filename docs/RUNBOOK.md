# Agentic Demo — Live Streaming Runbook (Unreal → OBS → MediaLive → MediaPackage → CloudFront)

This runbook brings up a minimal, cost‑aware live pipeline to stream Unreal (or any video via OBS/ffmpeg) into AWS and play it through the viewer.

Architecture (baseline)
```
Unreal/OBS (EC2 GPU or local) 
   └── RTMP push ──> MediaLive (Input + Channel)
                         └── HLS out ──> MediaPackage (Channel + HLS endpoint)
                                              └── CloudFront (dual origins)
                                                     • S3 origin: viewer/ + assets
                                                     • MediaPackage origin: /live/* routed to HLS
                                                     • CloudFront Function: strips /live prefix
Viewer page (CloudFront) 
   └── plays /live/index.m3u8 (fallback to /assets/sample.mp4)
```

Safety and cost notes
- AWS costs: MediaLive, MediaPackage, and GPU EC2 incur charges. Use small Regions/time windows for dev. Stop the MediaLive Channel and your EC2 instance when idle. Delete stacks when finished.
- This setup defaults to standard HLS (not LL‑HLS) to reduce complexity and cost. You can enable LL‑HLS later.

Prerequisites
- AWS CLI v2 authenticated (`aws sts get-caller-identity` should succeed)
- jq, node
- ffmpeg (for quick test) or OBS Studio (for production ingestion)
- An S3 bucket name you control for the viewer site, globally unique (e.g., your‑name‑agentic‑viewer)

Repository overview (key files/scripts)
- CloudFormation templates:
  - MediaPackage: aws/templates/cfn/mediapackage.yaml
  - MediaLive: aws/templates/cfn/medialive.yaml
- CloudFront:
  - Distribution template for rendering: aws/templates/cloudfront-viewer-and-live.json.tpl
  - CloudFront Function (JS): aws/functions/strip-live-uri.js
  - Template renderer: aws/tools/render-template.js
- Scripts:
  - Deploy MediaPackage: aws/scripts/deploy-mediapackage.sh
  - Deploy MediaLive: aws/scripts/deploy-medialive.sh
  - Deploy CloudFront + upload viewer: aws/scripts/deploy-cloudfront-and-viewer.sh
  - Aggregate outputs: aws/scripts/aggregate-outputs.sh
  - Start MediaLive Channel: aws/scripts/start-medialive-channel.sh
  - Stop MediaLive Channel: aws/scripts/stop-medialive-channel.sh
  - Test RTMP ingest with ffmpeg: aws/scripts/test-ffmpeg-push.sh (optional, created below if absent)
- Viewer:
  - viewer/index.html (expects /live/index.m3u8 or ?src=)

Outputs directory (created by scripts)
- aws/out/mediapackage.outputs.json
- aws/out/medialive.outputs.json
- aws/out/medialive.ingest.json
- aws/out/cloudfront.config.json
- aws/out/cloudfront.outputs.json
- aws/out/stack-outputs.json (aggregated, for quick reference)

1) Deploy MediaPackage (Channel + HLS)
- Defaults:
  - Region: us-east-1
  - Project: agentic-demo
  - HLS manifest name: index

Command
```bash
REGION=us-east-1 PROJECT=agentic-demo bash aws/scripts/deploy-mediapackage.sh
```

Result
- Outputs written to aws/out/mediapackage.outputs.json, including:
  - MediaPackageChannelId
  - HlsEndpointUrl (format: https://{mp-domain}/out/v1/{uuid}/index.m3u8)

2) Deploy MediaLive (RTMP Input + Channel to MediaPackage)
- Requires MediaPackage outputs from step 1.

Command
```bash
REGION=us-east-1 PROJECT=agentic-demo bash aws/scripts/deploy-medialive.sh
```

Result
- CFN outputs in aws/out/medialive.outputs.json
- RTMP ingest endpoints in aws/out/medialive.ingest.json, e.g.:
```json
{ "primaryUrl":"rtmp://.../primary/streamKey", "backupUrl":"rtmp://.../backup/streamKey" }
```

3) Deploy CloudFront and upload viewer site
- Provide an S3 bucket to host the viewer. Bucket is created if it doesn’t exist.

Command
```bash
REGION=us-east-1 PROJECT=agentic-demo BUCKET=your-unique-viewer-bucket \
bash aws/scripts/deploy-cloudfront-and-viewer.sh
```

What it does
- Renders a CloudFront distribution config with:
  - S3 origin (viewer and assets)
  - MediaPackage origin for /live/*
  - Associates a CloudFront Function to rewrite /live/* to MP endpoint path
- Uploads viewer/ to that S3 bucket
- Writes CloudFront outputs to aws/out/cloudfront.outputs.json

4) Aggregate outputs for quick reference
```bash
bash aws/scripts/aggregate-outputs.sh
```

Result
- Combined file at aws/out/stack-outputs.json containing CloudFront domain, MediaPackage details, and MediaLive IDs.

5) Start the MediaLive Channel
- Starting the channel incurs cost; keep test windows short.

Command
```bash
bash aws/scripts/start-medialive-channel.sh
```

6) Test ingest with ffmpeg (optional)
- This pushes a synthetic test pattern + sine tone to the MediaLive RTMP input.

One‑liner example
```bash
PRIMARY="$(jq -r '.primaryUrl' aws/out/medialive.ingest.json)"
ffmpeg -re \
 -f lavfi -i "testsrc=size=1280x720:rate=30" \
 -f lavfi -i "sine=frequency=1000:sample_rate=48000" \
 -c:v libx264 -pix_fmt yuv420p -preset veryfast -b:v 2500k -g 60 \
 -c:a aac -b:a 128k \
 -f flv "$PRIMARY"
```

Script (if provided)
```bash
bash aws/scripts/test-ffmpeg-push.sh
```

7) View the stream
- Open the CloudFront viewer domain from aws/out/cloudfront.outputs.json:
  - https://{cloudfrontDomain}/index.html
- Click Play
- The viewer attempts /live/index.m3u8 first, then falls back to /assets/sample.mp4 if live is not available.
- You can force a specific source: https://{cloudfrontDomain}/index.html?src=https://.../index.m3u8

8) OBS configuration (for Windows GPU EC2 or local)
- Server: For MediaLive “RTMP push” Input, you will typically have a URL that includes both server and stream key together.
- Two options:
  1) If OBS requires separate fields:
     - Server: the part up to but not including the final path segment
     - Stream Key: the final path segment
  2) If OBS allows a full URL:
     - Paste the full primaryUrl (from aws/out/medialive.ingest.json)
- Encoder: Use NVENC (on NVIDIA GPU instances) for better performance and quality.
- Bitrate: 2.5–6 Mbps for 720p–1080p; match MediaLive template defaults or update MediaLive CFN params as needed.

Recommended EC2 GPU configuration (Windows)
- Instance: g4dn.xlarge or g5.xlarge, Windows Server 2019/2022
- Security group: RDP only from your IP; allow outbound (HTTPS/RTMP)
- Install NVIDIA drivers and OBS Studio
- Install Unreal Engine (via Epic Games Launcher or pre‑baked AMI)
- Run Unreal in windowed mode; capture via OBS and Start Streaming
- On finish: Stop OBS, shut down EC2 instance to control costs

9) Troubleshooting
- CloudFront distribution “InProgress”: wait until “Deployed” before testing
- Playlist loads but no video:
  - Verify MediaLive Channel is started
  - Verify ffmpeg/OBS is pushing to the MediaLive Input primaryUrl
  - Check MediaPackage endpoint URL in aws/out/mediapackage.outputs.json
  - CloudFront path rewrite: ensure CloudFront Function is published and associated to the /live/* behavior
- Viewer won’t autoplay: click Play (user gesture often required by browsers)
- Slow or jittery playback: reduce ffmpeg bitrate or choose a faster x264 preset; ensure EC2 instance has GPU drivers and OBS uses NVENC

10) Stop streaming and control costs
- Stop MediaLive Channel:
```bash
bash aws/scripts/stop-medialive-channel.sh
```
- Stop your EC2 instance (if used)
- Consider deleting stacks if done

11) Tear‑down (manual outline)
- CloudFront distribution: disable, wait to deploy, then delete
- S3: delete objects then delete the bucket
- CloudFormation stacks: delete MediaLive and MediaPackage stacks
- IAM roles/policies created for the stacks are removed with CFN deletion

Next steps (optional)
- Enable low‑latency HLS in MediaPackage + viewer tweaks (hls.js lowLatencyMode)
- Add an SSE or WebSocket telemetry service and route /telemetry/* via CloudFront
- Harden security (limit RTMP input CIDR, Origin Access Control for S3, WAF, scoped IAM, etc.)
#!/bin/bash

# Stream Recording Setup for MediaLive
# Creates S3 bucket for recordings and provides OBS recording setup

set -e

PROJECT=${PROJECT:-"agentic-demo"}
REGION=${REGION:-"us-east-1"}
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
BUCKET_NAME="${PROJECT}-stream-recordings-${ACCOUNT_ID}"

echo "Setting up stream recording for project: $PROJECT"
echo "Region: $REGION"
echo "Bucket: $BUCKET_NAME"

# Create S3 bucket for recordings
echo "Creating S3 bucket for stream recordings..."
aws s3api create-bucket \
  --bucket "$BUCKET_NAME" \
  --region "$REGION" \
  --create-bucket-configuration LocationConstraint="$REGION" \
  || echo "Bucket might already exist"

# Set bucket lifecycle to auto-delete old recordings (optional)
cat > /tmp/lifecycle.json <<EOF
{
    "Rules": [
        {
            "ID": "DeleteOldRecordings",
            "Status": "Enabled",
            "Filter": {},
            "Expiration": {
                "Days": 30
            }
        }
    ]
}
EOF

aws s3api put-bucket-lifecycle-configuration \
  --bucket "$BUCKET_NAME" \
  --lifecycle-configuration file:///tmp/lifecycle.json

rm /tmp/lifecycle.json

echo ""
echo "✅ S3 bucket created: $BUCKET_NAME"
echo ""

# Option 1: OBS Local Recording + S3 Upload
echo "📹 OPTION 1: OBS Local Recording + S3 Upload"
echo "==========================================="
echo "1. In OBS, go to Settings → Output"
echo "2. Set Recording Path to a local folder"
echo "3. Set Recording Format to MP4"
echo "4. Start your stream AND recording simultaneously"
echo "5. Use this script to upload recordings to S3:"
echo ""
echo "   # Upload single file"
echo "   aws s3 cp /path/to/recording.mp4 s3://$BUCKET_NAME/recordings/"
echo ""
echo "   # Upload entire folder (sync)"
echo "   aws s3 sync /path/to/recordings/ s3://$BUCKET_NAME/recordings/"
echo ""

# Option 2: FFmpeg Stream Tee
echo "📡 OPTION 2: FFmpeg Stream Tee (Advanced)"
echo "========================================="

# Get MediaLive RTMP endpoints
MEDIALIVE_INPUT_ID=$(aws cloudformation describe-stacks \
  --stack-name "${PROJECT}-ml" \
  --region "$REGION" \
  --query 'Stacks[0].Outputs[?OutputKey==`MediaLiveInputId`].OutputValue' \
  --output text 2>/dev/null || echo "")

if [[ -n "$MEDIALIVE_INPUT_ID" ]]; then
  echo "Found MediaLive Input ID: $MEDIALIVE_INPUT_ID"
  
  # Get RTMP endpoints
  RTMP_ENDPOINTS=$(aws medialive describe-input \
    --input-id "$MEDIALIVE_INPUT_ID" \
    --region "$REGION" \
    --query 'Destinations[].Url' \
    --output text 2>/dev/null || echo "")
  
  if [[ -n "$RTMP_ENDPOINTS" ]]; then
    PRIMARY_RTMP=$(echo "$RTMP_ENDPOINTS" | head -1)
    echo ""
    echo "Use FFmpeg to stream AND record simultaneously:"
    echo ""
    echo "ffmpeg -f avfoundation -i \"0:0\" \\"
    echo "  -c:v libx264 -preset veryfast -b:v 2500k \\"
    echo "  -c:a aac -b:a 128k -ar 44100 \\"
    echo "  -f flv \"$PRIMARY_RTMP/$PROJECT/primary\" \\"
    echo "  -c copy -f mp4 \"recording-\$(date +%Y%m%d_%H%M%S).mp4\""
    echo ""
  fi
fi

# Option 3: S3 sync script for automated uploads
echo "🔄 OPTION 3: Automated Upload Script"
echo "===================================="
cat > /tmp/upload-recordings.sh <<EOF
#!/bin/bash
# Automated upload script for OBS recordings
# Usage: ./upload-recordings.sh /path/to/obs/recordings

RECORDING_DIR="\$1"
S3_BUCKET="$BUCKET_NAME"

if [[ -z "\$RECORDING_DIR" ]]; then
  echo "Usage: \$0 /path/to/obs/recordings"
  exit 1
fi

if [[ ! -d "\$RECORDING_DIR" ]]; then
  echo "Directory \$RECORDING_DIR does not exist"
  exit 1
fi

echo "Uploading recordings from \$RECORDING_DIR to s3://\$S3_BUCKET/recordings/"

# Upload all MP4 files
find "\$RECORDING_DIR" -name "*.mp4" -type f | while read -r file; do
  filename=\$(basename "\$file")
  echo "Uploading \$filename..."
  aws s3 cp "\$file" "s3://\$S3_BUCKET/recordings/\$filename"
done

echo "Upload complete!"
EOF

chmod +x /tmp/upload-recordings.sh
cp /tmp/upload-recordings.sh .
rm /tmp/upload-recordings.sh

echo ""
echo "Created ./upload-recordings.sh script"
echo ""

# Show current bucket contents
echo "📂 Current S3 bucket contents:"
aws s3 ls s3://$BUCKET_NAME/ --recursive || echo "(empty)"

echo ""
echo "✅ Setup complete!"
echo ""
echo "S3 Bucket: $BUCKET_NAME" 
echo "Region: $REGION"
echo ""
echo "💡 Quick commands:"
echo "  # List recordings"
echo "  aws s3 ls s3://$BUCKET_NAME/recordings/"
echo ""
echo "  # Download a recording"  
echo "  aws s3 cp s3://$BUCKET_NAME/recordings/video.mp4 ./video.mp4"
echo ""
echo "  # Set up folder sync (auto-upload new recordings)"
echo "  # Add this to your crontab:"
echo "  # */5 * * * * aws s3 sync /path/to/obs/recordings s3://$BUCKET_NAME/recordings/"
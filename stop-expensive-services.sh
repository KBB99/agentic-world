#!/bin/bash
# Stop expensive AWS services to prevent costs

echo "======================================"
echo "  💸 STOPPING EXPENSIVE SERVICES"
echo "======================================"

# Stop MediaLive channels
echo ""
echo "Checking MediaLive channels..."
CHANNEL_IDS=$(aws medialive list-channels --region us-east-1 --query "Channels[?State=='RUNNING'].Id" --output text 2>/dev/null)

if [ ! -z "$CHANNEL_IDS" ]; then
    echo "Found running MediaLive channels: $CHANNEL_IDS"
    for CHANNEL_ID in $CHANNEL_IDS; do
        echo "Stopping channel $CHANNEL_ID..."
        aws medialive stop-channel --channel-id "$CHANNEL_ID" --region us-east-1 2>/dev/null && \
            echo "✅ Stopped $CHANNEL_ID" || \
            echo "❌ Failed to stop $CHANNEL_ID"
    done
else
    echo "✅ No MediaLive channels running"
fi

# Stop EC2 instances (excluding critical ones)
echo ""
echo "Checking EC2 instances..."
INSTANCE_IDS=$(aws ec2 describe-instances \
    --region us-east-1 \
    --filters "Name=instance-state-name,Values=running" \
    --query "Reservations[].Instances[?!Tags[?Key=='KeepRunning' && Value=='true']].InstanceId" \
    --output text 2>/dev/null)

if [ ! -z "$INSTANCE_IDS" ]; then
    echo "Found running EC2 instances: $INSTANCE_IDS"
    read -p "Stop these instances? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        aws ec2 stop-instances --instance-ids $INSTANCE_IDS --region us-east-1 2>/dev/null && \
            echo "✅ Stopped EC2 instances" || \
            echo "❌ Failed to stop instances"
    fi
else
    echo "✅ No EC2 instances to stop"
fi

echo ""
echo "======================================"
echo "Cost-saving measures applied!"
echo "Run ./cost-status.sh to verify"
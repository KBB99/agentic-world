# AWS Resources Paused - Cost Savings Active

## Stopped Resources (as of now)

### MediaLive Channel
- **Channel ID**: 3407016
- **Status**: STOPPED
- **Hourly Cost When Running**: ~$0.75/hour
- **Daily Savings**: ~$18/day

### EC2 Instances

#### GPU Instance (g5.xlarge)
- **Instance ID**: i-04bcee1a80b8c7839
- **Name**: agentic-demo-gpu
- **Status**: STOPPED
- **Hourly Cost When Running**: ~$1.00/hour
- **Daily Savings**: ~$24/day

#### t2.micro Instance  
- **Instance ID**: i-0e6d5f9440f430a0f
- **Status**: STOPPED
- **Hourly Cost When Running**: ~$0.012/hour
- **Daily Savings**: ~$0.29/day

## Total Savings

**Combined Daily Savings**: ~$42.29/day
**Combined Monthly Savings**: ~$1,268.70/month

## Still Running (Low/No Cost)

- S3 Buckets (pay per GB stored)
- CloudFront Distribution (pay per request)
- API Gateway WebSocket (pay per message)
- Lambda Functions (pay per invocation)
- DynamoDB Tables (pay per request mode)

## To Restart Services

```bash
# Start MediaLive channel
bash aws/scripts/start-medialive-channel.sh

# Start GPU instance
aws ec2 start-instances --region us-east-1 --instance-ids i-04bcee1a80b8c7839

# Start t2.micro instance
aws ec2 start-instances --region us-east-1 --instance-ids i-0e6d5f9440f430a0f
```

## Cost Management Best Practices

1. **Always stop MediaLive when not streaming** - This is the most expensive service
2. **Stop GPU instances between sessions** - Only needed for Unreal Engine rendering
3. **Use Lambda/DynamoDB for AI agents** - Pay only when actively simulating
4. **Monitor AWS Cost Explorer daily** - Set up billing alerts at $10/day

## Current Status
✅ All expensive services stopped
✅ Simulation can still run using Lambda/DynamoDB
✅ Ready to restart when needed for streaming
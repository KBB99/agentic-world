#!/bin/bash

# Deploy S3 and CloudFront for AI character content

set -e

# Configuration
REGION=${REGION:-us-east-1}
PROJECT=${PROJECT:-agentic-demo}
STACK_NAME="${PROJECT}-content-cdn"
TEMPLATE_FILE="../templates/cfn/content-s3-cdn.yaml"
OUTPUT_FILE="../out/content-cdn.outputs.json"

echo "🚀 Deploying Content CDN Stack"
echo "================================"
echo "Region: $REGION"
echo "Project: $PROJECT"
echo "Stack: $STACK_NAME"
echo ""

# Create output directory
mkdir -p ../out

# Deploy CloudFormation stack
echo "📦 Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file "$TEMPLATE_FILE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        ProjectName="$PROJECT" \
    --capabilities CAPABILITY_NAMED_IAM \
    --region "$REGION" \
    --no-fail-on-empty-changeset

# Get stack outputs
echo "📝 Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json > "$OUTPUT_FILE"

# Extract key values
BUCKET_NAME=$(cat "$OUTPUT_FILE" | jq -r '.[] | select(.OutputKey=="BucketName") | .OutputValue')
CDN_URL=$(cat "$OUTPUT_FILE" | jq -r '.[] | select(.OutputKey=="CloudFrontURL") | .OutputValue')
BUCKET_URL=$(cat "$OUTPUT_FILE" | jq -r '.[] | select(.OutputKey=="BucketURL") | .OutputValue')

echo ""
echo "✅ Content CDN Deployed Successfully!"
echo "======================================"
echo "📁 S3 Bucket: $BUCKET_NAME"
echo "🌐 CloudFront URL: $CDN_URL"
echo "🔗 S3 Website URL: $BUCKET_URL"
echo ""
echo "Characters can now publish content to S3!"
echo ""
echo "To test publishing:"
echo "  python3 mcp-s3-publisher.py --character alex_chen --type blog --file test.html"
echo ""
echo "To create content hub:"
echo "  python3 mcp-s3-publisher.py --create-hub"
echo ""
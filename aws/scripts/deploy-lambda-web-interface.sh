#!/bin/bash

# Deploy Lambda-based web interface for Agentic Demo
# This deploys the Express server as a serverless Lambda function

set -e

# Configuration
REGION=${REGION:-us-east-1}
PROJECT=${PROJECT:-agentic-demo}
STACK_NAME="${PROJECT}-web-interface-lambda"

echo "============================================"
echo "Deploying Lambda Web Interface"
echo "============================================"
echo "Region: $REGION"
echo "Project: $PROJECT"
echo "Stack: $STACK_NAME"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "Error: AWS CLI not found. Please install AWS CLI."
    exit 1
fi

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "Note: SAM CLI not found. Installing dependencies manually..."
    USE_SAM=false
else
    USE_SAM=true
fi

# Navigate to web-interface directory
cd "$(dirname "$0")/../../web-interface"

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

# Create deployment package
echo "Creating deployment package..."
mkdir -p ../aws/out/lambda-deployment

# Copy all necessary files
cp -r . ../aws/out/lambda-deployment/
cd ../aws/out/lambda-deployment

# Remove unnecessary files
rm -rf node_modules/.cache
rm -rf .git
rm -rf tests
rm -rf *.log

# Create a zip file
echo "Creating deployment zip..."
zip -r ../web-interface-lambda.zip . -q

cd ../../../

# If SAM is available, use it for deployment
if [ "$USE_SAM" = true ]; then
    echo "Deploying with SAM CLI..."
    cd aws/templates/cfn
    
    sam deploy \
        --template-file web-interface-lambda.yaml \
        --stack-name "$STACK_NAME" \
        --s3-bucket "${PROJECT}-deployment-${REGION}" \
        --capabilities CAPABILITY_IAM \
        --region "$REGION" \
        --parameter-overrides ProjectName="$PROJECT" \
        --no-fail-on-empty-changeset
        
    cd ../../../
else
    echo "Deploying with CloudFormation directly..."
    
    # First, we need to create an S3 bucket for the Lambda code
    DEPLOYMENT_BUCKET="${PROJECT}-lambda-deployment-${REGION}"
    
    # Create bucket if it doesn't exist
    if ! aws s3 ls "s3://${DEPLOYMENT_BUCKET}" --region "$REGION" 2>/dev/null; then
        echo "Creating deployment bucket: $DEPLOYMENT_BUCKET"
        aws s3 mb "s3://${DEPLOYMENT_BUCKET}" --region "$REGION"
    fi
    
    # Upload Lambda code to S3
    echo "Uploading Lambda code to S3..."
    aws s3 cp aws/out/web-interface-lambda.zip "s3://${DEPLOYMENT_BUCKET}/lambda/web-interface.zip" --region "$REGION"
    
    # Deploy CloudFormation stack
    echo "Deploying CloudFormation stack..."
    aws cloudformation deploy \
        --template-file aws/templates/cfn/web-interface-lambda.yaml \
        --stack-name "$STACK_NAME" \
        --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
        --region "$REGION" \
        --parameter-overrides ProjectName="$PROJECT"
fi

# Get stack outputs
echo ""
echo "Getting stack outputs..."
aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs' \
    --output json > aws/out/lambda-web-interface.outputs.json

# Extract API Gateway URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --region "$REGION" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text)

echo ""
echo "============================================"
echo "Lambda Web Interface Deployed Successfully!"
echo "============================================"
echo ""
echo "API Gateway URL: $API_URL"
echo ""
echo "You can access the web interface at:"
echo "  Dashboard: ${API_URL}/dashboard"
echo "  Content Hub: ${API_URL}/content-hub.html"
echo "  S3 Viewer: ${API_URL}/s3-content-viewer.html"
echo ""
echo "Outputs saved to: aws/out/lambda-web-interface.outputs.json"
echo ""

# Update stack-outputs.json with Lambda API URL
if [ -f "aws/out/stack-outputs.json" ]; then
    echo "Updating stack-outputs.json..."
    jq --arg url "$API_URL" '. + {lambdaApiUrl: $url}' aws/out/stack-outputs.json > aws/out/stack-outputs.tmp.json
    mv aws/out/stack-outputs.tmp.json aws/out/stack-outputs.json
fi

echo "Deployment complete!"
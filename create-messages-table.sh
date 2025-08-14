#!/bin/bash
# Create DynamoDB table for storing character messages

TABLE_NAME="agentic-demo-messages"
REGION="us-east-1"

echo "Creating DynamoDB table for messages..."

aws dynamodb create-table \
    --table-name $TABLE_NAME \
    --attribute-definitions \
        AttributeName=characterId,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=characterId,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST \
    --region $REGION

if [ $? -eq 0 ]; then
    echo "✅ Messages table created successfully"
    
    echo "Waiting for table to become active..."
    aws dynamodb wait table-exists --table-name $TABLE_NAME --region $REGION
    
    echo "✅ Table is ready"
else
    echo "Table might already exist or there was an error"
fi

echo ""
echo "Table details:"
aws dynamodb describe-table --table-name $TABLE_NAME --region $REGION --query 'Table.{Name:TableName,Status:TableStatus,Items:ItemCount}' --output json
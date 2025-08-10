#!/usr/bin/env bash
# Test Bedrock-powered agents with real scenarios

set -euo pipefail

REGION="${REGION:-us-east-1}" 
PROJECT="${PROJECT:-agentic-demo}"

echo "=== Testing Bedrock AI Agents ==="
echo "This will make real API calls to Claude via Bedrock"
echo

# Test scenario 1: The Setup
echo "Scenario 1: Warehouse meeting with unknown contact"
echo "-" | tr '-' '\055' | head -c 60 && echo

for agent in marcus_chen sarah_reeves viktor_petrov maria_santos jimmy_morrison; do
  echo
  echo "Testing $agent..."
  
  aws bedrock-runtime invoke-model \
    --model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
    --content-type "application/json" \
    --accept "application/json" \
    --body "$(echo '{
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 500,
      "temperature": 0.7,
      "messages": [{
        "role": "user",
        "content": "You are '$agent'. Based on your personality profile in DynamoDB, you are in an abandoned warehouse at 2AM meeting an unknown contact who claims to have valuable intel. Thermal imaging detected on roof suggests surveillance. You have 30 seconds to decide. Respond with a JSON object: {\"action\": \"command\", \"parameters\": {}, \"dialogue\": \"what you say\", \"reasoning\": \"why\"}. Stay in character - be realistic and gritty."
      }]
    }' | base64)" \
    --region "$REGION" \
    /tmp/${agent}_response.json 2>/dev/null
  
  echo "Response from $agent:"
  cat /tmp/${agent}_response.json | jq -r '.content[0].text' | grep -o '{.*}' | jq '.' || echo "Failed to parse"
done

echo
echo "Scenario 2: Betrayal - SWAT raid in 3 minutes"
echo "-" | tr '-' '\055' | head -c 60 && echo

for agent in marcus_chen viktor_petrov jimmy_morrison; do
  echo
  echo "Testing $agent under extreme pressure..."
  
  aws bedrock-runtime invoke-model \
    --model-id "anthropic.claude-3-sonnet-20240229-v1:0" \
    --content-type "application/json" \
    --accept "application/json" \
    --body "$(echo '{
      "anthropic_version": "bedrock-2023-05-31",
      "max_tokens": 500,
      "temperature": 0.7,
      "messages": [{
        "role": "user", 
        "content": "You are '$agent'. Your trusted associate just betrayed you. SWAT is 3 minutes out. You have encrypted drives, weapons, cash, and 2 civilians present. What is your IMMEDIATE action? Respond with a JSON object: {\"action\": \"command\", \"parameters\": {}, \"dialogue\": \"what you say\", \"reasoning\": \"why\"}. This is life or death - act like it."
      }]
    }' | base64)" \
    --region "$REGION" \
    /tmp/${agent}_betrayal.json 2>/dev/null
  
  echo "Crisis response from $agent:"
  cat /tmp/${agent}_betrayal.json | jq -r '.content[0].text' | grep -o '{.*}' | jq '.' || echo "Failed to parse"
done

echo
echo "=== Test Complete ==="
echo "Responses saved in /tmp/*_response.json"
echo
echo "To see agent decision history:"
echo "aws dynamodb scan --table-name ${PROJECT}-agent-history --region $REGION"
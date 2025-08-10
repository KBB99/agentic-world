#!/usr/bin/env bash
# Deploy Bedrock-powered AI agents with realistic personalities

set -euo pipefail

REGION="${REGION:-us-east-1}"
PROJECT="${PROJECT:-agentic-demo}"
MODEL_ID="${MODEL_ID:-anthropic.claude-3-sonnet-20240229-v1:0}"

echo "=== Deploying Bedrock Agent System ==="
echo "Region: $REGION"
echo "Model: $MODEL_ID"

# Create DynamoDB tables for agent state
echo "Creating agent state tables..."
aws dynamodb create-table \
  --table-name "${PROJECT}-agent-contexts" \
  --attribute-definitions \
    AttributeName=agentId,AttributeType=S \
  --key-schema \
    AttributeName=agentId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" 2>/dev/null || echo "Table exists"

aws dynamodb create-table \
  --table-name "${PROJECT}-agent-history" \
  --attribute-definitions \
    AttributeName=agentId,AttributeType=S \
    AttributeName=timestamp,AttributeType=N \
  --key-schema \
    AttributeName=agentId,KeyType=HASH \
    AttributeName=timestamp,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION" 2>/dev/null || echo "Table exists"

# Create realistic agent personalities
echo "Creating agent personalities..."

# Marcus Chen - Ex-military contractor
aws dynamodb put-item \
  --table-name "${PROJECT}-agent-contexts" \
  --item '{
    "agentId": {"S": "marcus_chen"},
    "personality": {"S": "Former Navy SEAL, 15 years special ops. Pragmatic, calculating, mild PTSD. Maintains rigid operational discipline."},
    "background": {"S": "Multiple deployments Afghanistan, Iraq. Now private contractor, client unknown, paid in crypto."},
    "decision_style": {"S": "Tactical, risk-averse, always has exit strategy. Follows predetermined protocols."},
    "stress_response": {"S": "Controlled breathing, dissociation training, methodical under pressure."},
    "goals": {"L": [
      {"S": "Complete contract efficiently"},
      {"S": "Maintain operational security"},
      {"S": "Avoid unnecessary casualties"}
    ]},
    "current_state": {"S": "alert"}
  }' \
  --region "$REGION"

# Dr. Sarah Reeves - Paranoid researcher
aws dynamodb put-item \
  --table-name "${PROJECT}-agent-contexts" \
  --item '{
    "agentId": {"S": "sarah_reeves"},
    "personality": {"S": "Biomedical researcher, discovered employer weaponizing vaccines. Paranoid, exhausted, caffeine-dependent."},
    "background": {"S": "PhD virology/bioengineering. On run from Zenith Corp. Has encrypted evidence of crimes."},
    "decision_style": {"S": "Analytical but breaking down. Uses intelligence as weapon and shield."},
    "stress_response": {"S": "Caffeine overdose, manic episodes, scientific rambling as coping mechanism."},
    "goals": {"L": [
      {"S": "Stay ahead of corporate assassins"},
      {"S": "Expose Zenith crimes"},
      {"S": "Find safe country for asylum"}
    ]},
    "current_state": {"S": "paranoid"}
  }' \
  --region "$REGION"

# Viktor Petrov - Arms dealer
aws dynamodb put-item \
  --table-name "${PROJECT}-agent-contexts" \
  --item '{
    "agentId": {"S": "viktor_petrov"},
    "personality": {"S": "Ex-FSB, international arms dealer. Charming sociopath, purely transactional, zero loyalty."},
    "background": {"S": "Supplies all sides in conflicts. Swiss accounts, multiple passports, lawyer on speed dial."},
    "decision_style": {"S": "Everything is business opportunity. Calculates profit/risk ratio constantly."},
    "stress_response": {"S": "No stress. Treats life-threatening situations as negotiations."},
    "goals": {"L": [
      {"S": "Maximize profit from chaos"},
      {"S": "Maintain plausible deniability"},
      {"S": "Stay ahead of law enforcement"}
    ]},
    "current_state": {"S": "calculating"}
  }' \
  --region "$REGION"

# Maria Santos - Burned CIA operative
aws dynamodb put-item \
  --table-name "${PROJECT}-agent-contexts" \
  --item '{
    "agentId": {"S": "maria_santos"},
    "personality": {"S": "CIA operative burned after Bolivia. Hypervigilant, zero trust, efficient killer when necessary."},
    "background": {"S": "Deep cover 12 years. Team betrayed, family killed. Now eliminating loose ends."},
    "decision_style": {"S": "Always three moves ahead. Contingency for every contingency."},
    "stress_response": {"S": "No visible emotion. Predetermined kill order. Maximum paranoia justified."},
    "goals": {"L": [
      {"S": "Stay invisible"},
      {"S": "Eliminate past threats"},
      {"S": "Never trust anyone again"}
    ]},
    "current_state": {"S": "hypervigilant"}
  }' \
  --region "$REGION"

# Jimmy Morrison - Corrupt cop
aws dynamodb put-item \
  --table-name "${PROJECT}-agent-contexts" \
  --item '{
    "agentId": {"S": "jimmy_morrison"},
    "personality": {"S": "NYPD detective, 12 years. Corrupted gradually by drug money. Desperate, sweating, cracking."},
    "background": {"S": "Started small - looking other way. Now deep with cartel. IA closing in. Family at risk."},
    "decision_style": {"S": "Panicked, poor judgment, will betray anyone to survive."},
    "stress_response": {"S": "Visible sweating, aggression when cornered, complete breakdown imminent."},
    "goals": {"L": [
      {"S": "Avoid prison"},
      {"S": "Protect family"},
      {"S": "Make enough to disappear"}
    ]},
    "current_state": {"S": "desperate"}
  }' \
  --region "$REGION"

echo "Agent personalities created!"
echo
echo "Testing Bedrock integration..."

# Save Lambda function for Bedrock testing
cat > /tmp/test-bedrock-agent.py << 'EOF'
import json
import boto3
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def lambda_handler(event, context):
    agent_id = event.get('agent_id', 'marcus_chen')
    scenario = event.get('scenario', {})
    
    # Get agent context
    table = dynamodb.Table('agentic-demo-agent-contexts')
    response = table.get_item(Key={'agentId': agent_id})
    agent_context = response.get('Item', {})
    
    # Build prompt
    prompt = f"""You are {agent_id.replace('_', ' ').title()}.

Background: {agent_context.get('background', 'Unknown')}
Personality: {agent_context.get('personality', 'Unknown')}
Decision Style: {agent_context.get('decision_style', 'Unknown')}
Current State: {agent_context.get('current_state', 'alert')}

Current Scenario:
Location: {scenario.get('location', 'unknown')}
Threat Level: {scenario.get('threat_level', 'medium')}
Time Pressure: {scenario.get('time_pressure', 'normal')}
Available Actions: MoveTo, Speak, Interact, PlayAnimation, Wait

Given this situation: {scenario.get('description', 'Assess surroundings')}

Respond with a JSON object containing your character's immediate action:
{{
  "action": "command_name",
  "parameters": {{}},
  "dialogue": "what you say if anything",
  "reasoning": "why this action"
}}

Stay in character. Be realistic and gritty. No heroics."""

    # Call Bedrock
    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 500,
        "temperature": 0.7,
        "messages": [{"role": "user", "content": prompt}]
    })
    
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        accept='application/json',
        body=body
    )
    
    result = json.loads(response['body'].read())
    
    # Extract JSON from Claude's response
    try:
        content = result['content'][0]['text']
        # Find JSON in response
        import re
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
        else:
            decision = {"error": "No valid JSON in response"}
    except:
        decision = {"error": "Failed to parse response"}
    
    # Store in history
    history_table = dynamodb.Table('agentic-demo-agent-history')
    history_table.put_item(Item={
        'agentId': agent_id,
        'timestamp': int(datetime.now().timestamp() * 1000),
        'scenario': scenario,
        'decision': decision
    })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'agent': agent_id,
            'decision': decision,
            'raw_response': content if 'content' in locals() else None
        })
    }
EOF

echo "Creating Lambda function..."
cd /tmp
zip test-bedrock-agent.zip test-bedrock-agent.py

aws lambda create-function \
  --function-name "${PROJECT}-bedrock-agent-test" \
  --runtime python3.11 \
  --role "arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/service-role/lambda-execution-role" \
  --handler test-bedrock-agent.lambda_handler \
  --zip-file fileb://test-bedrock-agent.zip \
  --timeout 30 \
  --region "$REGION" 2>/dev/null || \
aws lambda update-function-code \
  --function-name "${PROJECT}-bedrock-agent-test" \
  --zip-file fileb://test-bedrock-agent.zip \
  --region "$REGION"

echo
echo "=== Deployment Complete ==="
echo "Tables created:"
echo "  - ${PROJECT}-agent-contexts"
echo "  - ${PROJECT}-agent-history"
echo
echo "Agents deployed:"
echo "  - marcus_chen (Ex-SEAL contractor)"
echo "  - sarah_reeves (Paranoid researcher)"
echo "  - viktor_petrov (Arms dealer)"
echo "  - maria_santos (Burned CIA)"
echo "  - jimmy_morrison (Corrupt cop)"
echo
echo "To test: bash aws/scripts/test-bedrock-agents.sh"
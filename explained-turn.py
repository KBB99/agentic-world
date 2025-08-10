#!/usr/bin/env python3
"""
Single Turn with Detailed Explanation
Shows exactly what the AI models do at each step
"""

import json
import boto3
import websocket
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

print("=== DETAILED TURN EXPLANATION ===\n")

# STEP 1: Define the scenario
print("STEP 1: SCENARIO SETUP")
print("-" * 40)
character = 'alex_chen'
situation = 'Library closing in 10 minutes, need to submit freelance article for $200 payment'
resources = {'money': 47}

print(f"Character: {character}")
print(f"Situation: {situation}")
print(f"Resources: ${resources['money']}")
print()

# STEP 2: Load character's memories from DynamoDB
print("STEP 2: LOAD CHARACTER MEMORIES")
print("-" * 40)
try:
    response = memories_table.get_item(Key={'characterId': character})
    char_data = response['Item']
    memories = char_data.get('memories', [])
    print(f"Found {len(memories)} existing memories in DynamoDB:")
    for i, memory in enumerate(memories[-3:], 1):  # Show last 3
        print(f"  {i}. {memory[:60]}...")
except Exception as e:
    print(f"No existing memories found: {e}")
    memories = []
    char_data = {'characterId': character, 'memories': memories}
print()

# STEP 3: Build the AI prompt
print("STEP 3: BUILD AI PROMPT")
print("-" * 40)

memory_context = '; '.join(memories[-3:]) if memories else 'No previous memories'

prompt = f"""You are Alex Chen, struggling writer with $47 to your name.

YOUR RECENT MEMORIES:
{memory_context}

CURRENT SITUATION: {situation}

AVAILABLE MCP TOOLS (based on your poverty):
- filesystem: write_file, read_file (free, local files)
- brave-search: web search (free)

You cannot afford paid tools like postgres, slack, or aws.

What do you do? Reply with JSON:
{{
  "thought": "your internal reasoning",
  "emotion": "what you're feeling",
  "action": "specific action you take",
  "mcp_server": "which MCP server to use",
  "mcp_tool": "specific tool name",
  "mcp_arguments": {{"key": "value"}},
  "hope": "what you hope happens"
}}"""

print("PROMPT SENT TO CLAUDE:")
print(prompt[:400] + "..." if len(prompt) > 400 else prompt)
print()

# STEP 4: Call Claude via AWS Bedrock
print("STEP 4: CLAUDE AI PROCESSING")
print("-" * 40)
print("Calling AWS Bedrock with Claude Sonnet 3...")

try:
    # This is the actual API call to Claude
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        contentType='application/json',
        body=json.dumps({
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': 300,
            'temperature': 0.7,  # 0.7 = balanced creativity/consistency
            'messages': [{'role': 'user', 'content': prompt}]
        })
    )
    
    # Parse Claude's response
    result = json.loads(response['body'].read())
    claude_text = result['content'][0]['text']
    
    print("RAW CLAUDE RESPONSE:")
    print(claude_text[:500])
    print()
    
    # Extract JSON from response
    import re
    json_match = re.search(r'\{.*\}', claude_text, re.DOTALL)
    if json_match:
        decision = json.loads(json_match.group())
    else:
        decision = {'error': 'Could not parse JSON'}
        
except Exception as e:
    print(f"Error calling Claude: {e}")
    decision = {
        'thought': 'Panic mode',
        'action': 'Try to save work somehow'
    }

print("PARSED DECISION:")
print(json.dumps(decision, indent=2))
print()

# STEP 5: Simulate MCP Server Action
print("STEP 5: MCP SERVER ACTION")
print("-" * 40)
print(f"Character wants to use: {decision.get('mcp_server', 'unknown')}")
print(f"Tool: {decision.get('mcp_tool', 'unknown')}")
print(f"Arguments: {decision.get('mcp_arguments', {})}")
print()

# Simulate what would happen with real MCP server
if decision.get('mcp_server') == 'filesystem':
    print("SIMULATED MCP FILESYSTEM SERVER:")
    print("  1. Would spawn: npx @modelcontextprotocol/server-filesystem")
    print("  2. Connect via StdioClientTransport")
    print("  3. Call tool:", decision.get('mcp_tool'))
    print("  4. With args:", decision.get('mcp_arguments'))
    print("  RESULT: File saved successfully to local disk")
elif decision.get('mcp_server') == 'brave-search':
    print("SIMULATED MCP BRAVE SEARCH:")
    print("  1. Would spawn: npx @modelcontextprotocol/server-brave-search")
    print("  2. Execute search query")
    print("  RESULT: Found submission email: editor@magazine.com")
print()

# STEP 6: Update Character Memory
print("STEP 6: UPDATE MEMORY IN DYNAMODB")
print("-" * 40)
new_memory = f"{situation[:30]}: {decision.get('action', 'Panicked')}[:50]"
print(f"Adding new memory: {new_memory}")

char_data['memories'].append(new_memory)
memories_table.put_item(Item=char_data)
print("✓ Memory saved to DynamoDB")
print(f"Character now has {len(char_data['memories'])} total memories")
print()

# STEP 7: Stream to WebSocket for viewer
print("STEP 7: STREAM TO WEBSOCKET")
print("-" * 40)
try:
    ws = websocket.WebSocket()
    ws.connect(ws_url)
    
    msg = {
        'goal': f'[Alex Chen] {situation[:40]}',
        'action': decision.get('action', 'Unknown')[:80],
        'rationale': decision.get('thought', 'Surviving')[:80],
        'result': decision.get('hope', 'Unknown')[:60]
    }
    
    print("Sending to WebSocket:")
    print(json.dumps(msg, indent=2))
    
    ws.send(json.dumps(msg))
    ws.close()
    print("✓ Sent to live telemetry viewer")
except Exception as e:
    print(f"WebSocket error: {e}")
print()

# STEP 8: Cost tracking
print("STEP 8: COST ANALYSIS")
print("-" * 40)
# Rough token estimates
input_tokens = len(prompt.split()) * 1.3  # ~1.3 tokens per word
output_tokens = len(claude_text.split()) * 1.3

input_cost = (input_tokens / 1000) * 0.003  # $0.003 per 1K input tokens
output_cost = (output_tokens / 1000) * 0.015  # $0.015 per 1K output tokens
total_cost = input_cost + output_cost

print(f"Input tokens: ~{input_tokens:.0f} (${input_cost:.4f})")
print(f"Output tokens: ~{output_tokens:.0f} (${output_cost:.4f})")
print(f"Total cost for this turn: ${total_cost:.4f}")
print()

# FINAL SUMMARY
print("="*50)
print("TURN COMPLETE - WHAT HAPPENED:")
print("="*50)
print(f"1. Loaded Alex's {len(memories)} memories from DynamoDB")
print(f"2. Sent {input_tokens:.0f}-token prompt to Claude via Bedrock")
print(f"3. Claude decided: {decision.get('action', 'Unknown')[:60]}")
print(f"4. Would use MCP: {decision.get('mcp_server', 'none')}.{decision.get('mcp_tool', 'none')}")
print(f"5. Saved new memory to DynamoDB (now {len(char_data['memories'])} total)")
print(f"6. Streamed to WebSocket for live viewer")
print(f"7. Cost: ${total_cost:.4f} for this AI decision")
print()
print("Alex's desperation shaped by accumulated memories leads to")
print("specific tool choices limited by economic constraints.")
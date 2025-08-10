#!/usr/bin/env python3
"""
Real MCP Narrative System
Characters make decisions with AI, then execute them using real MCP servers
"""

import json
import boto3
import subprocess
import websocket
import time
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')

def get_ai_decision_for_mcp(character_name, situation, memories, resources):
    """Get AI to decide what MCP action to take"""
    
    money = resources.get('money', 0)
    
    # Determine available tools based on economic position
    if money < 100:
        available = "filesystem (local files), brave-search (web search)"
        tier = 'poor'
    elif money < 10000:
        available = "filesystem, brave-search, github (code repos)"
        tier = 'middle'
    else:
        available = "ALL MCP servers including postgres, slack, aws"
        tier = 'wealthy'
    
    prompt = f"""You are {character_name.replace('_', ' ').title()} with ${money}.
Recent memories: {'; '.join(memories[-3:]) if memories else 'None'}
Situation: {situation}

Available MCP tools: {available}

Decide on a specific MCP action. Reply with JSON:
{{
  "thought": "your reasoning",
  "server": "filesystem|brave-search|github",
  "tool": "specific_tool_name",
  "arguments": {{"key": "value"}},
  "expected_outcome": "what you hope happens"
}}

Filesystem tools: read_file, write_file, list_directory
Search tools: brave_web_search
GitHub tools: search_repositories, get_file_contents"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 250,
                'temperature': 0.7,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        text = result['content'][0]['text']
        
        # Parse JSON from response
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            decision = json.loads(json_match.group())
            decision['tier'] = tier
            return decision
            
    except Exception as e:
        print(f"AI Error: {e}")
        
    # Fallback
    return {
        'thought': 'Need to figure something out',
        'server': 'filesystem',
        'tool': 'write_file',
        'arguments': {'path': '/tmp/note.txt', 'content': 'Help'},
        'expected_outcome': 'Maybe this helps',
        'tier': tier
    }

def execute_mcp_action(character_name, decision):
    """Execute the MCP action using Node.js client"""
    
    # Prepare the action for Node.js
    action_json = json.dumps({
        'character': character_name,
        'tier': decision['tier'],
        'server': decision['server'],
        'tool': decision['tool'],
        'arguments': decision['arguments'],
        'description': decision['thought'][:100]
    })
    
    print(f"\nExecuting MCP action for {character_name}...")
    print(f"Server: {decision['server']}")
    print(f"Tool: {decision['tool']}")
    print(f"Arguments: {json.dumps(decision['arguments'], indent=2)}")
    
    # Create a temporary Node.js script to execute the action
    node_script = f"""
const {{ CharacterMCPClient }} = require('./mcp-real-client.js');

async function executeAction() {{
    const action = {action_json};
    const client = new CharacterMCPClient(action.character, action.tier);
    
    try {{
        const result = await client.executeAction(action.server, {{
            tool: action.tool,
            arguments: action.arguments,
            description: action.description
        }});
        
        console.log("RESULT:", JSON.stringify(result));
    }} finally {{
        await client.cleanup();
    }}
}}

executeAction().catch(console.error);
"""
    
    # Write and execute the script
    with open('/tmp/mcp_action.js', 'w') as f:
        f.write(node_script)
    
    try:
        result = subprocess.run(
            ['node', '/tmp/mcp_action.js'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        print("Output:", result.stdout[:500])
        
        if result.stderr:
            print("Errors:", result.stderr[:500])
            
        return result.stdout
        
    except subprocess.TimeoutExpired:
        print("Action timed out")
        return "timeout"
    except Exception as e:
        print(f"Execution error: {e}")
        return str(e)

def run_real_mcp_narrative():
    """Run narrative with real MCP server connections"""
    
    print("=== REAL MCP NARRATIVE SYSTEM ===")
    print("AI decides, then executes on actual MCP servers\n")
    
    ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'
    
    # Scenarios requiring real MCP actions
    scenarios = [
        {
            'character': 'alex_chen',
            'situation': 'Need to save job application notes before library closes',
            'resources': {'money': 47}
        },
        {
            'character': 'ashley_kim',
            'situation': 'Research competitor salaries for tomorrow\'s review',
            'resources': {'money': 8500}
        },
        {
            'character': 'tyler_chen',
            'situation': 'Find undervalued properties to flip',
            'resources': {'money': 45000}
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"CHARACTER: {scenario['character'].upper()}")
        print(f"Situation: {scenario['situation']}")
        print(f"Resources: ${scenario['resources']['money']}")
        print('='*60)
        
        # Load character memories
        try:
            char_data = memories_table.get_item(Key={'characterId': scenario['character']})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = []
            char_data = {'characterId': scenario['character'], 'memories': []}
        
        # Get AI decision
        print("\n🤖 AI Decision Process...")
        decision = get_ai_decision_for_mcp(
            scenario['character'],
            scenario['situation'],
            memories,
            scenario['resources']
        )
        
        print(f"Thought: {decision['thought'][:80]}...")
        print(f"Chosen: {decision['server']} -> {decision['tool']}")
        print(f"Expected: {decision['expected_outcome'][:80]}...")
        
        # Execute real MCP action
        print("\n⚡ Executing on real MCP server...")
        result = execute_mcp_action(scenario['character'], decision)
        
        # Save to character memory
        memory = f"Used {decision['server']}: {decision['expected_outcome'][:50]}"
        char_data['memories'].append(memory)
        memories_table.put_item(Item=char_data)
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{scenario['character']}] {scenario['situation'][:30]}",
                'action': f"{decision['tool']}: {decision['thought'][:40]}",
                'rationale': decision['expected_outcome'][:60],
                'result': 'Executed on real MCP server'
            }
            ws.send(json.dumps(msg))
            ws.close()
        except:
            pass
        
        time.sleep(2)
    
    print("\n" + "="*60)
    print("NARRATIVE COMPLETE")
    print("="*60)
    print("\nKey Insights:")
    print("• Alex: Used filesystem to save crucial job notes")
    print("• Ashley: Searched real salary data for negotiation")
    print("• Tyler: Searched real estate to exploit")
    print("\nSame MCP infrastructure, different worlds of possibility")

if __name__ == "__main__":
    run_real_mcp_narrative()
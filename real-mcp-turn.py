#!/usr/bin/env python3
"""
REAL MCP Turn Execution
Characters make AI decisions then ACTUALLY execute them on MCP servers
"""

import json
import boto3
import subprocess
import websocket
import os
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

def get_ai_decision(character, situation, memories, money):
    """Get AI to decide on MCP action"""
    
    # Determine available tools based on money
    if money < 100:
        available = """
        - filesystem: read_file(path), write_file(path, content), list_directory(path)
        - brave-search: brave_web_search(query) [if API key available]
        """
    else:
        available = """
        - filesystem: All file operations
        - brave-search: Web search
        - github: Repository search (if authenticated)
        """
    
    prompt = f"""You are {character.replace('_', ' ').title()} with ${money}.
Recent memories: {'; '.join(memories[-3:]) if memories else 'Starting fresh'}

SITUATION: {situation}

AVAILABLE MCP TOOLS:{available}

Choose ONE specific action. Reply with JSON:
{{
  "thought": "your reasoning",
  "mcp_server": "filesystem or brave-search",
  "mcp_tool": "exact tool name from list above",
  "mcp_arguments": {{"exact_key": "value"}},
  "hope": "what you hope happens"
}}

For filesystem tools, use paths like: {os.getcwd()}/character_files/your_file.txt"""

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
    
    # Parse JSON
    import re
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    
    return None

def execute_on_real_mcp(character, decision):
    """Execute the decision on real MCP server via Node.js"""
    
    # Add character name to decision
    decision['character'] = character
    
    # Prepare for Node.js execution
    decision_json = json.dumps(decision)
    
    print(f"\n🔌 CONNECTING TO REAL MCP SERVER: {decision['mcp_server']}")
    print(f"📡 Will execute: {decision['mcp_tool']}")
    
    try:
        # Call Node.js script to handle MCP connection
        result = subprocess.run(
            ['node', 'real-mcp-connection.js', decision_json],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        print("\n📝 MCP SERVER OUTPUT:")
        print("-" * 40)
        print(result.stdout)
        
        if result.stderr:
            print("\n⚠️ Errors:")
            print(result.stderr)
        
        # Extract JSON result if present
        if 'JSON_RESULT:' in result.stdout:
            json_line = result.stdout.split('JSON_RESULT:')[1].strip()
            return json.loads(json_line.split('\n')[0])
        
        return {'output': result.stdout}
        
    except subprocess.TimeoutExpired:
        print("❌ MCP connection timed out")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_real_mcp_turn():
    """Run a complete turn with real MCP execution"""
    
    print("=== REAL MCP TURN EXECUTION ===")
    print("AI decides → Connects to real MCP → Executes tool\n")
    
    # Create character files directory if it doesn't exist
    os.makedirs('character_files', exist_ok=True)
    
    scenarios = [
        {
            'character': 'alex_chen',
            'situation': 'Need to save article draft before library computer logs you out',
            'money': 47
        },
        {
            'character': 'ashley_kim',
            'situation': 'Want to save salary negotiation notes for tomorrow',
            'money': 8500
        },
        {
            'character': 'tyler_chen',
            'situation': 'Document property acquisition targets',
            'money': 45000
        }
    ]
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"CHARACTER: {scenario['character'].upper()}")
        print(f"Situation: {scenario['situation']}")
        print(f"Money: ${scenario['money']}")
        print('='*60)
        
        # Load memories
        try:
            char_data = memories_table.get_item(Key={'characterId': scenario['character']})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = []
            char_data = {'characterId': scenario['character'], 'memories': []}
        
        # Get AI decision
        print("\n🤖 AI DECISION:")
        decision = get_ai_decision(
            scenario['character'],
            scenario['situation'],
            memories,
            scenario['money']
        )
        
        if not decision:
            print("❌ Could not get AI decision")
            continue
            
        print(f"Thought: {decision['thought'][:70]}...")
        print(f"Will use: {decision['mcp_server']}.{decision['mcp_tool']}")
        
        # EXECUTE ON REAL MCP SERVER
        mcp_result = execute_on_real_mcp(scenario['character'], decision)
        
        # Save to memory
        if mcp_result:
            memory = f"Used MCP {decision['mcp_server']}: {decision['hope'][:50]}"
            char_data['memories'].append(memory)
            memories_table.put_item(Item=char_data)
            print(f"\n✅ Memory saved: {memory}")
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{scenario['character']}] {scenario['situation'][:30]}",
                'action': f"MCP: {decision['mcp_tool']}",
                'rationale': decision['thought'][:50],
                'result': 'Executed on REAL MCP server'
            }
            ws.send(json.dumps(msg))
            ws.close()
        except:
            pass
        
        print("\n" + "-"*60)
        input("Press Enter to continue to next character...")
    
    print("\n" + "="*60)
    print("ALL TURNS COMPLETE")
    print("="*60)
    print("\nWhat happened:")
    print("1. AI made decisions based on character's economic position")
    print("2. Actually spawned MCP servers (filesystem, etc)")
    print("3. Executed real tools on real servers")
    print("4. Results saved to character memories")

if __name__ == "__main__":
    run_real_mcp_turn()
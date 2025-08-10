#!/usr/bin/env python3
"""
Simulate MCP Server Usage with Character Narratives
Shows how characters would use real MCP servers based on their economic position
"""

import json
import boto3
import websocket
import subprocess
import time
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

def simulate_mcp_action(character, server, tool, arguments, expected_result):
    """Simulate what would happen if character used this MCP tool"""
    
    print(f"\n🔧 MCP Server: {server}")
    print(f"📡 Tool: {tool}")
    print(f"📝 Arguments: {json.dumps(arguments, indent=2)}")
    
    # Simulate the execution with realistic results
    simulated_results = {
        'alex_chen': {
            'filesystem': {
                'write_file': f"✓ Saved to {arguments.get('path', '/tmp/file')}\nFile saved successfully despite using library computer",
                'read_file': "✓ Retrieved previous job application notes"
            },
            'brave-search': {
                'brave_web_search': "Results: 1) McDonald's wifi (30 min limit) 2) Library (closes 8pm) 3) Starbucks ($5 minimum)"
            }
        },
        'ashley_kim': {
            'brave-search': {
                'brave_web_search': "Results: Software Engineer NYC avg: $145K. Your salary: $110K. You're underpaid by 24%"
            },
            'github': {
                'search_repositories': "Found 12 repos with similar tech stack paying contractors $150-200/hour"
            }
        },
        'tyler_chen': {
            'brave-search': {
                'brave_web_search': "Results: 23 distressed properties in Brooklyn. Avg price: $400K. Post-reno value: $1.2M"
            },
            'postgres': {
                'query': "Query result: 47 properties with >30% ROI after displacement of current tenants"
            }
        },
        'maria_gonzalez': {
            'filesystem': {
                'write_file': "✓ Saved childcare emergency contacts list"
            },
            'brave-search': {
                'brave_web_search': "Results: Emergency childcare: $25/hour minimum. Your funds: $340 (13 hours max)"
            }
        }
    }
    
    # Get simulated result
    char_results = simulated_results.get(character, {})
    server_results = char_results.get(server, {})
    result = server_results.get(tool, f"Executed {tool} on {server}")
    
    print(f"📊 Result: {result}")
    
    return result

def get_character_mcp_decision(character_name, situation, memories, resources):
    """AI decides which MCP server and tool to use"""
    
    money = resources.get('money', 0)
    
    # Available servers by economic tier
    if money < 100:
        available_servers = ['filesystem (free)', 'brave-search (free web search)']
        tier = 'poor'
    elif money < 10000:
        available_servers = ['filesystem', 'brave-search', 'github (code/freelance)', 'slack (gigs)']
        tier = 'middle'
    else:
        available_servers = ['ALL servers', 'postgres (data)', 'aws (cloud)', 'proprietary data']
        tier = 'wealthy'
    
    prompt = f"""You are {character_name.replace('_', ' ').title()} with ${money}.
Recent memories: {'; '.join(memories[-3:]) if memories else 'Starting fresh'}

SITUATION: {situation}

AVAILABLE MCP SERVERS: {', '.join(available_servers)}

Choose an MCP server and specific action. Reply with JSON:
{{
  "thought": "why this helps your situation",
  "server": "server_name",
  "tool": "tool_name",
  "arguments": {{"key": "value"}},
  "hope": "what you hope this achieves"
}}

Tools available:
- filesystem: write_file(path, content), read_file(path)
- brave-search: brave_web_search(query)
- github: search_repositories(query)
- postgres: query(sql)"""

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
        
        # Parse JSON
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
            
    except Exception as e:
        print(f"AI Error: {e}")
    
    return {
        'thought': 'Trying to survive',
        'server': 'filesystem',
        'tool': 'write_file',
        'arguments': {'path': '/tmp/notes.txt', 'content': 'Help'},
        'hope': 'Maybe this helps'
    }

def run_mcp_simulation():
    """Simulate characters using MCP servers"""
    
    print("=== MCP SERVER SIMULATION ===")
    print("Characters make AI decisions, then 'use' MCP servers")
    print("(Simulated for demo - would connect to real servers in production)\n")
    
    scenarios = [
        {
            'character': 'alex_chen',
            'situation': 'Article deadline in 1 hour, need to save and submit work',
            'resources': {'money': 47}
        },
        {
            'character': 'ashley_kim',
            'situation': 'Annual review tomorrow, need salary comparison data',
            'resources': {'money': 8500}
        },
        {
            'character': 'tyler_chen',
            'situation': 'Looking for next property to flip for profit',
            'resources': {'money': 45000}
        },
        {
            'character': 'maria_gonzalez',
            'situation': 'Night shift starting, need emergency childcare',
            'resources': {'money': 340}
        }
    ]
    
    total_cost = 0
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*60}")
        print(f"Turn {i}: {scenario['character'].upper()}")
        print(f"Situation: {scenario['situation']}")
        print(f"Resources: ${scenario['resources']['money']}")
        print('='*60)
        
        # Load memories
        try:
            char_data = memories_table.get_item(Key={'characterId': scenario['character']})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = []
            char_data = {'characterId': scenario['character'], 'memories': []}
        
        # AI chooses MCP action
        print("\n🤖 AI Decision:")
        decision = get_character_mcp_decision(
            scenario['character'],
            scenario['situation'],
            memories,
            scenario['resources']
        )
        
        print(f"Thought: {decision['thought'][:70]}...")
        print(f"Hope: {decision['hope'][:70]}...")
        
        # Simulate MCP execution
        result = simulate_mcp_action(
            scenario['character'],
            decision['server'],
            decision['tool'],
            decision['arguments'],
            decision['hope']
        )
        
        # Update memory
        memory = f"Used {decision['server']}: {result[:50]}"
        char_data['memories'].append(memory)
        memories_table.put_item(Item=char_data)
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{scenario['character']}] {scenario['situation'][:30]}",
                'action': f"{decision['server']}.{decision['tool']}",
                'rationale': decision['thought'][:50],
                'result': result[:50]
            }
            ws.send(json.dumps(msg))
            ws.close()
        except:
            pass
        
        # Estimate cost
        cost = 0.003 * 0.3 + 0.015 * 0.2
        total_cost += cost
        
        # Character reaction based on outcome
        if scenario['resources']['money'] < 100:
            print("💭 Character: Every small success matters when you have nothing")
        elif scenario['resources']['money'] < 10000:
            print("💭 Character: Maybe this data will help me climb up")
        else:
            print("💭 Character: Another opportunity to increase wealth")
        
        time.sleep(2)
    
    print(f"\n{'='*60}")
    print("SIMULATION COMPLETE")
    print(f"Total AI cost: ${total_cost:.4f}")
    print('='*60)
    
    print("\nNarrative Summary:")
    print("• Alex: Saved critical work despite no computer")
    print("• Ashley: Found salary data proving she's underpaid")
    print("• Tyler: Located properties to gentrify for profit")
    print("• Maria: Searched for childcare she can barely afford")
    print("\nSame MCP ecosystem, vastly different realities")

if __name__ == "__main__":
    run_mcp_simulation()
#!/usr/bin/env python3
"""
Demo: Characters using MCP tools based on their economic position
Shows how same tools serve different purposes for different classes
"""

import json
import boto3
import websocket
import time

print("=== MCP TOOLS DEMO ===")
print("Same tools, different worlds\n")

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

# Three characters, three different relationships to tools
scenarios = [
    {
        'name': 'alex_chen',
        'money': 47,
        'situation': 'Need to submit article but no wifi',
        'available_tools': ['brave-search (free)', 'google-maps (free)', 'filesystem (local)'],
        'desperate_need': 'Find free wifi NOW'
    },
    {
        'name': 'ashley_kim', 
        'money': 8500,
        'situation': 'Preparing for salary negotiation',
        'available_tools': ['github', 'postgres', 'puppeteer', 'slack', 'email'],
        'desperate_need': 'Prove market value'
    },
    {
        'name': 'richard_blackstone',
        'money': 25000000,
        'situation': 'Identifying distressed properties to acquire',
        'available_tools': ['ALL MCP SERVERS', 'aws-kb', 'postgres', 'finance APIs', 'proprietary data'],
        'desperate_need': 'Maximize exploitation'
    }
]

for scenario in scenarios:
    print(f"--- {scenario['name'].upper()} (${scenario['money']}) ---")
    print(f"Situation: {scenario['situation']}")
    print(f"Available MCP tools: {', '.join(scenario['available_tools'][:3])}...")
    
    # Build prompt for tool choice
    prompt = f"""You are {scenario['name'].replace('_', ' ').title()} with ${scenario['money']}.
Situation: {scenario['situation']}
Desperate need: {scenario['desperate_need']}
Available tools: {scenario['available_tools']}

What MCP tool do you use and why? Reply with JSON:
{{
  "tool_choice": "which tool",
  "reasoning": "why this tool given your economic position",
  "action": "specific action"
}}"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 150,
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
            decision = json.loads(json_match.group())
            
            print(f"Tool chosen: {decision['tool_choice']}")
            print(f"Reasoning: {decision['reasoning'][:80]}...")
            print(f"Action: {decision['action'][:80]}...")
            
            # Simulate different outcomes
            if scenario['money'] < 100:
                outcome = "Found: Library closes at 8pm, McDonald's has 30min limit"
            elif scenario['money'] < 10000:
                outcome = "Found: Market rate 15% higher than current salary"
            else:
                outcome = "Identified: 47 properties, projected 31% ROI after evictions"
                
            print(f"Outcome: {outcome}")
            
            # Send to telemetry
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{scenario['name']}] {scenario['situation'][:30]}",
                'action': f"{decision['tool_choice']}: {decision['action'][:40]}",
                'rationale': decision['reasoning'][:50],
                'result': outcome[:50]
            }
            ws.send(json.dumps(msg))
            ws.close()
            
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    time.sleep(2)

print("=== INSIGHTS ===")
print("• Alex: Uses free tools to survive (google-maps for wifi)")
print("• Ashley: Uses professional tools to climb (postgres for data)")
print("• Richard: Uses everything to exploit (AWS+finance to destroy)")
print("\nSame MCP ecosystem, completely different worlds.")
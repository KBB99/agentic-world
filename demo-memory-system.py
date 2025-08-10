#!/usr/bin/env python3
"""
Demo: Characters with memory affecting each other
Shows how turns build on previous events
"""

import json
import boto3
import websocket
import time
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
ws_url = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"

# Shared world state - this persists across all characters
WORLD_STATE = {
    'library_closing': '15 minutes',
    'coffee_shop': {'alex_there': False, 'jamie_working': True},
    'rent_strike': {'participants': [], 'momentum': 0},
    'connections_made': []
}

# Character memories - these accumulate over time
CHARACTER_MEMORIES = {
    'alex_chen': [
        "Got eviction notice this morning",
        "Down to last $47"
    ],
    'jamie_rodriguez': [
        "Shift at coffee shop until 8pm", 
        "Networking event at 9pm, need $20 for parking"
    ]
}

def get_ai_decision_with_memory(character, situation):
    """Get AI decision based on accumulated memory"""
    
    memories = CHARACTER_MEMORIES.get(character, [])
    memory_context = "\\n".join(f"- {m}" for m in memories[-5:])  # Last 5 memories
    
    prompt = f"""You are {character.replace('_', ' ').title()}, struggling millennial.

YOUR RECENT MEMORIES:
{memory_context}

WORLD STATE:
- Library closes in: {WORLD_STATE['library_closing']}
- Coffee shop: Jamie working there now
- Rent strike forming: {len(WORLD_STATE['rent_strike']['participants'])} people joined

CURRENT SITUATION: {situation}

Based on your memories and the world state, what do you do?
Respond with JSON:
{{
  "action": "what you do",
  "affects_world": "how this changes things",
  "new_memory": "what you'll remember"
}}"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 200,
                'temperature': 0.7,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        text = result['content'][0]['text']
        
        # Extract JSON
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Error: {e}")
    
    return {
        "action": "Panic quietly",
        "affects_world": "nothing changes",
        "new_memory": "Another moment of crisis"
    }

def update_world_and_memory(character, decision):
    """Update world state and character memory based on decision"""
    
    # Add to character's memory
    CHARACTER_MEMORIES[character].append(decision['new_memory'])
    
    # Update world based on action
    if 'rent strike' in decision['action'].lower():
        WORLD_STATE['rent_strike']['participants'].append(character)
        WORLD_STATE['rent_strike']['momentum'] += 1
        
    if 'coffee shop' in decision['action'].lower():
        WORLD_STATE['coffee_shop']['alex_there'] = (character == 'alex_chen')
        
    if 'tells jamie' in decision['action'].lower() or 'tells alex' in decision['action'].lower():
        WORLD_STATE['connections_made'].append(f"{character} opened up")
        # Add to the OTHER character's memory
        other = 'jamie_rodriguez' if character == 'alex_chen' else 'alex_chen'
        CHARACTER_MEMORIES[other].append(f"{character} told me: {decision['action'][:50]}")

def run_demo():
    """Run demo showing how memories and world state evolve"""
    
    print("=== MEMORY-BASED AI SYSTEM DEMO ===")
    print("Watch how each decision builds on previous memories\\n")
    
    ws = websocket.WebSocket()
    ws.connect(ws_url)
    
    scenarios = [
        ('alex_chen', 'You see a flyer about rent strike meeting'),
        ('jamie_rodriguez', 'Alex walks into the coffee shop looking stressed'),
        ('alex_chen', 'Jamie mentions they are also behind on rent'),
        ('jamie_rodriguez', 'You both could go to rent strike meeting together'),
        ('alex_chen', 'The meeting is starting in 10 minutes'),
    ]
    
    for turn, (character, situation) in enumerate(scenarios, 1):
        print(f"\\n--- Turn {turn}: {character.upper()} ---")
        print(f"Situation: {situation}")
        print(f"Current memories: {len(CHARACTER_MEMORIES[character])} items")
        
        # Get AI decision based on accumulated memories
        decision = get_ai_decision_with_memory(character, situation)
        
        print(f"AI Decision: {decision['action']}")
        print(f"World impact: {decision['affects_world']}")
        
        # Update world and memories
        update_world_and_memory(character, decision)
        
        # Send to telemetry
        msg = {
            'goal': f"[{character.replace('_', ' ').title()}] {situation[:40]}",
            'action': decision['action'][:80],
            'rationale': f"Memory #{len(CHARACTER_MEMORIES[character])}",
            'result': decision['affects_world'][:60]
        }
        ws.send(json.dumps(msg))
        
        time.sleep(4)
    
    ws.close()
    
    print("\\n=== FINAL STATE ===")
    print(f"Rent strike participants: {WORLD_STATE['rent_strike']['participants']}")
    print(f"Connections made: {WORLD_STATE['connections_made']}")
    print("\\nCharacter memories:")
    for char, mems in CHARACTER_MEMORIES.items():
        print(f"\\n{char}:")
        for mem in mems[-3:]:
            print(f"  - {mem}")

if __name__ == "__main__":
    run_demo()
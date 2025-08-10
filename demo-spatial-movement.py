#!/usr/bin/env python3
"""
Demo: Characters navigating spaces based on needs
Shows movement decisions and location-based interactions
"""

import json
import boto3
import websocket
import time

print("=== SPATIAL MOVEMENT DEMO ===")
print("Watch characters navigate based on their needs\n")

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

# Simplified location tracking
character_locations = {
    'alex_chen': 'apartment',
    'jamie_rodriguez': 'coffee_shop',
    'tyler_chen': 'luxury_apartment'
}

# Location properties
locations = {
    'apartment': {'wifi': False, 'cost': 0, 'eviction': True},
    'library': {'wifi': True, 'cost': 0, 'closing': '8pm'},
    'coffee_shop': {'wifi': True, 'cost': 5, 'jamie_works': True},
    'mcdonalds': {'wifi': True, 'cost': 2, 'always_open': True},
    'luxury_apartment': {'wifi': True, 'cost': 0, 'private': True},
    'street': {'wifi': False, 'cost': 0, 'public': True}
}

# Movement scenarios with clear spatial needs
scenarios = [
    {
        'character': 'alex_chen',
        'situation': 'Need wifi to submit article for $200 payment, deadline 2 hours',
        'current_location': 'apartment',
        'nearby': ['library (10min walk)', 'coffee_shop (5min)', 'mcdonalds (15min)'],
        'constraints': 'Have $47 total'
    },
    {
        'character': 'jamie_rodriguez',  
        'situation': 'See Alex walk in looking desperate for wifi',
        'current_location': 'coffee_shop',
        'nearby': ['can offer free wifi password', 'can comp a coffee'],
        'constraints': 'Manager watching'
    },
    {
        'character': 'tyler_chen',
        'situation': 'Want to visit your new investment property (Alex\'s building)',
        'current_location': 'luxury_apartment',
        'nearby': ['alex_apartment (20min drive)', 'office (10min)', 'coffee_shop (15min)'],
        'constraints': 'Have meeting at 3pm'
    }
]

for i, scenario in enumerate(scenarios, 1):
    print(f"--- Scenario {i}: {scenario['character'].upper()} ---")
    print(f"Currently at: {scenario['current_location']}")
    print(f"Situation: {scenario['situation']}")
    print(f"Can go to: {', '.join(scenario['nearby'])}")
    
    # Load character memories
    try:
        char_data = memories_table.get_item(Key={'characterId': scenario['character']})['Item']
        memories = char_data.get('memories', [])[-3:]
    except:
        memories = []
    
    # Build spatial decision prompt
    prompt = f"""You are {scenario['character'].replace('_', ' ').title()}.
Recent memories: {'; '.join(memories) if memories else 'None'}

CURRENT LOCATION: {scenario['current_location']}
Location properties: {json.dumps(locations.get(scenario['current_location'], {}))}

SITUATION: {scenario['situation']}

NEARBY LOCATIONS: {', '.join(scenario['nearby'])}

CONSTRAINTS: {scenario['constraints']}

Make a spatial decision. Reply with JSON:
{{
  "thinking": "your reasoning about where to go and why",
  "decision": "where you go or what you do",
  "movement": "location you move to (or 'stay')"
}}"""

    try:
        # Get AI decision
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
            decision = json.loads(json_match.group())
            
            print(f"Thinking: {decision.get('thinking', '')[:80]}...")
            print(f"Decision: {decision.get('decision', '')[:80]}...")
            print(f"Movement: {decision.get('movement', 'stay')}")
            
            # Update location
            if decision.get('movement') and decision['movement'] != 'stay':
                old_loc = character_locations[scenario['character']]
                new_loc = decision['movement'].split('(')[0].strip()
                character_locations[scenario['character']] = new_loc
                print(f"→ Moved from {old_loc} to {new_loc}")
                
                # Save movement to memory
                memory = f"Moved to {new_loc}: {decision['decision'][:50]}"
                char_data['memories'].append(memory)
                memories_table.put_item(Item=char_data)
            
            # Send to telemetry
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{scenario['character']}] {scenario['situation'][:30]}",
                'action': decision.get('decision', '')[:80],
                'rationale': decision.get('thinking', '')[:60],
                'result': f"→ {decision.get('movement', 'stayed')}"
            }
            ws.send(json.dumps(msg))
            ws.close()
            
    except Exception as e:
        print(f"Error: {e}")
    
    print()
    time.sleep(2)

print("=== MOVEMENT COMPLETE ===")
print("\nFinal locations:")
for char, loc in character_locations.items():
    print(f"  {char}: {loc}")
print("\nKey insights:")
print("• Alex had to choose between expensive coffee shop or far McDonalds for wifi")
print("• Jamie could help Alex but risks manager's anger")
print("• Tyler visits his 'investment' (Alex's soon-to-be-former home)")
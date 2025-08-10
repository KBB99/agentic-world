#!/usr/bin/env python3
"""
Run narrative showing how different economic classes interact
Tyler's success directly impacts others' struggles
"""

import json
import boto3
import websocket
import time
from datetime import datetime

print('=== INTERSECTING LIVES NARRATIVE ===')
print('See how success and struggle are connected...\n')

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')

ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

# Interconnected scenarios
scenarios = [
    ('tyler_chen', 'Your property manager texts: "Evictions complete, units ready for renovation"'),
    ('alex_chen', 'You see construction crew arriving at your building with "Luxury Renovations" truck'),
    ('maria_gonzalez', 'Hospital announces "partnership" with Tyler\'s company for "wellness suites" - cutting ICU beds'),
    ('dorothy_jackson', 'Letter arrives: your property has been rezoned, taxes will triple next year'),
    ('brittany_torres', 'Delivery ping: $200 champagne to Tyler Chen penthouse, estimated tip: $0-2'),
    ('ashley_kim', 'Tyler posts LinkedIn humble-brag about "giving back" while you eat cup noodles at desk'),
    ('tyler_chen', 'You consider which charity to donate to for tax write-off')
]

total_cost = 0

for turn, (character, situation) in enumerate(scenarios, 1):
    print(f'--- Turn {turn}: {character.upper()} ---')
    print(f'Situation: {situation}\n')
    
    # Load character context
    try:
        char_data = memories_table.get_item(Key={'characterId': character})['Item']
        memories = char_data.get('memories', [])
    except:
        memories = ['New to this situation']
        char_data = {'characterId': character, 'memories': memories}
    
    # Build prompt with character's full context
    memory_context = '; '.join(memories[-5:]) if memories else 'No context'
    
    # Get AI decision based on character's position
    prompt = f'''You are {character.replace("_", " ").title()}.
Your recent context: {memory_context}
Current situation: {situation}
Respond with ONE realistic action/thought based on your economic position. One sentence.'''
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 100,
                'temperature': 0.7,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        action = result['content'][0]['text'].strip()
        
        # Track cost
        cost = 0.003 * 0.15 + 0.015 * 0.08
        total_cost += cost
        
        print(f'Response: {action[:100]}...')
        
        # Save memory
        new_memory = f'{situation[:40]}: {action[:60]}'
        char_data['memories'].append(new_memory)
        memories_table.put_item(Item=char_data)
        
        # Determine impact
        if character == 'tyler_chen':
            impact = 'Profit increases, others displaced'
        elif character in ['alex_chen', 'dorothy_jackson']:
            impact = 'Housing insecurity deepens'
        elif character == 'maria_gonzalez':
            impact = 'Healthcare access reduced'
        elif character == 'brittany_torres':
            impact = 'Gig exploitation continues'
        elif character == 'ashley_kim':
            impact = 'Pressure to become Tyler intensifies'
        else:
            impact = 'Struggle continues'
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f'[{character.replace("_", " ").title()}] {situation[:35]}',
                'action': action[:80],
                'rationale': impact,
                'result': f'Class position: {char_data.get("resources", {}).get("money", "unknown")}'
            }
            ws.send(json.dumps(msg))
            ws.close()
            print(f'Impact: {impact}')
        except Exception as ws_error:
            print(f'WebSocket error: {ws_error}')
        
        print()  # Spacing
        time.sleep(2)
        
    except Exception as e:
        print(f'Error: {e}\n')
        continue

print('=== NARRATIVE COMPLETE ===')
print(f'Total cost: ${total_cost:.4f}')
print('\nKey Insights:')
print('• Tyler\'s "success" directly creates housing crisis for others')
print('• Maria saves lives of people who profit from her struggle')
print('• Ashley burns out trying to become Tyler')
print('• Dorothy\'s lifetime of service rewarded with displacement')
print('• Brittany serves luxury to those who see her as app, not person')
print('• Alex & Jamie face homelessness from Tyler\'s "investments"')
print('\nThe system working perfectly for some IS the crisis for others.')
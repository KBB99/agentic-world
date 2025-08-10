#!/usr/bin/env python3
"""
Run a few narrative turns to demonstrate the AI system
"""

import json
import boto3
import websocket
import time
from datetime import datetime

print('=== RUNNING AI NARRATIVE TURNS ===')
print('Starting world simulation...\n')

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')

# WebSocket for telemetry
ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'

# Run 3 narrative turns
scenarios = [
    ('alex_chen', 'Your phone buzzes - landlord says you have 24 hours'),
    ('jamie_rodriguez', 'Manager asks why you gave away tip money'),
    ('alex_chen', 'Jamie texts you about a rent strike meeting tonight'),
]

total_cost = 0

for turn, (character, situation) in enumerate(scenarios, 1):
    print(f'--- Turn {turn} ---')
    print(f'{character.upper()}: {situation}')
    
    # Load character memories
    try:
        char_data = memories_table.get_item(Key={'characterId': character})['Item']
        memories = char_data.get('memories', [])
    except:
        memories = ['Starting fresh']
        char_data = {'characterId': character, 'memories': memories}
    
    # Build context from memories
    memory_context = '; '.join(memories[-5:]) if memories else 'No memories yet'
    
    # Get AI decision
    prompt = f'''You are {character.replace("_", " ").title()}, struggling to survive.
Recent memories: {memory_context}
Situation: {situation}
What do you do? One realistic action in one sentence.'''
    
    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 100,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        action = result['content'][0]['text'].strip()
        
        # Estimate cost (rough)
        cost = 0.003 * 0.2 + 0.015 * 0.1  # ~200 input tokens, ~100 output tokens
        total_cost += cost
        
        print(f'Decision: {action[:80]}...')
        print(f'Cost: ${cost:.4f}')
        
        # Save new memory
        new_memory = f'{situation[:30]}: {action[:50]}'
        char_data['memories'].append(new_memory)
        memories_table.put_item(Item=char_data)
        print(f'Memory saved: "{new_memory[:50]}..."')
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f'[{character.replace("_", " ").title()}] {situation[:40]}',
                'action': action[:80],
                'rationale': f'Memory #{len(char_data["memories"])}',
                'result': 'Ongoing struggle'
            }
            ws.send(json.dumps(msg))
            ws.close()
            print('✓ Sent to telemetry overlay')
        except Exception as ws_error:
            print(f'WebSocket error: {ws_error}')
        
        print()  # Blank line between turns
        time.sleep(2)  # Brief pause between turns
        
    except Exception as e:
        print(f'Error calling AI: {e}')
        break

print(f'=== NARRATIVE COMPLETE ===')
print(f'Total cost: ${total_cost:.4f}')
print(f'Characters now have updated memories in DynamoDB')
print('\nTo view in browser:')
print('https://d1u690gz6k82jo.cloudfront.net/index.html?ws=wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod')
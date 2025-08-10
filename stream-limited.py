#!/usr/bin/env python3
"""
Limited streaming demo - sends 5 AI character decisions to telemetry
"""

import json
import boto3
import websocket
import time
import random
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# WebSocket endpoint
WS_URL = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"

# Quick scenarios
scenarios = [
    ('alex_chen', 'Eviction notice', '$47 in account, rent is $1100'),
    ('jamie_rodriguez', 'Producer wants coffee meeting', 'Have $3.50, coffee is $6'),
    ('sarah_kim', 'Gas light on', 'Have $20, need gas for week'),
    ('marcus_williams', 'Ex-coworker asks about new role', 'Cannot say driving Uber'),
    ('emma_thompson', '47th gallery rejection', 'Need this barista job')
]

def get_ai_response(character, situation, context):
    """Get realistic response from Claude"""
    
    prompt = f"""You are {character.replace('_', ' ').title()}, struggling millennial.
Situation: {situation}
Context: {context}
What do you actually do? One realistic sentence."""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 100,
                'temperature': 0.8,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        return result['content'][0]['text'].strip()
    except:
        return "Panic internally while appearing calm"

def main():
    print("=== STREAMING AI TO TELEMETRY ===")
    print("Viewer URL: https://d1u690gz6k82jo.cloudfront.net/index.html")
    print(f"WebSocket: {WS_URL}\n")
    
    # Connect to WebSocket
    ws = websocket.WebSocket()
    ws.connect(WS_URL)
    print("Connected to telemetry!")
    
    # Send 5 decisions
    for i, (character, situation, context) in enumerate(scenarios):
        print(f"\n[{i+1}/5] {character}: {situation}")
        
        # Get AI decision
        action = get_ai_response(character, situation, context)
        print(f"AI: {action[:80]}...")
        
        # Send to telemetry
        msg = {
            "action": "telemetry",
            "data": {
                "goal": f"[{character.replace('_', ' ').title()}] {situation}",
                "action": action[:100],
                "rationale": context,
                "result": "Ongoing struggle"
            }
        }
        
        ws.send(json.dumps(msg))
        print("✓ Sent to viewer overlay")
        
        time.sleep(5)  # Wait 5 seconds between messages
    
    ws.close()
    print("\n✅ Successfully streamed 5 AI decisions to telemetry!")
    print("Viewers can see character struggles at the URL above")

if __name__ == "__main__":
    main()
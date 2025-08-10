#!/usr/bin/env python3
"""
Stream AI character decisions to live telemetry overlay
This connects Bedrock AI responses to the WebSocket telemetry that appears on the viewer
"""

import json
import boto3
import websocket
import time
import random
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# WebSocket endpoint from telemetry stack
WS_URL = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"

# Realistic everyday scenarios
scenarios = [
    {
        'name': 'Rent Due',
        'description': 'Landlord texts: "Rent was due 3 days ago. Pay today or eviction process starts."',
        'context': 'You have $247 in your account. Rent is $1,100.'
    },
    {
        'name': 'Job Interview',
        'description': 'Finally got interview at creative agency. They ask: "Why the gap in employment?"',
        'context': 'You\'ve been freelancing (barely surviving) for 8 months.'
    },
    {
        'name': 'Family Call',
        'description': 'Mom calls: "How\'s everything going? Your cousin just bought a house!"',
        'context': 'You\'re eating ramen for the third day straight.'
    },
    {
        'name': 'Car Breaks',
        'description': 'Check engine light comes on. Mechanic quotes $1,200.',
        'context': 'This is your only way to get to work/gigs.'
    },
    {
        'name': 'Old Friend Success',
        'description': 'Instagram: College friend posts about their promotion to Creative Director.',
        'context': 'You\'re 31 and still have roommates.'
    }
]

def get_ai_response(character, scenario):
    """Get realistic response from Claude via Bedrock"""
    
    character_profiles = {
        'alex_chen': 'Alex Chen, 28, struggling writer with MFA and $73K debt, couchsurfing, making $200/week on CBD copy',
        'jamie_rodriguez': 'Jamie Rodriguez, 26, film school dropout, PA and barista, dreams of directing, $1200/month income',
        'sarah_kim': 'Sarah Kim, 34, PhD adjunct professor at 3 colleges, no benefits, 1997 Honda with 230K miles',
        'marcus_williams': 'Marcus Williams, 31, laid-off tech worker, now Uber/DoorDash driver, hiding situation from friends',
        'emma_thompson': 'Emma Thompson, 25, BFA in painting, barista making latte art she hates, $20 Etsy sales'
    }
    
    prompt = f"""You are {character_profiles.get(character, 'a struggling millennial')}.

Situation: {scenario['description']}
Context: {scenario['context']}

How do you respond? Be painfully realistic. Reply with JSON:
{{
  "goal": "what you're trying to achieve",
  "action": "what you actually do",
  "rationale": "why (be honest about money/survival)",
  "result": "immediate outcome"
}}"""

    try:
        response = bedrock.invoke_model(
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            contentType='application/json',
            accept='application/json',
            body=json.dumps({
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 300,
                'temperature': 0.8,
                'messages': [{'role': 'user', 'content': prompt}]
            })
        )
        
        result = json.loads(response['body'].read())
        text = result['content'][0]['text']
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except Exception as e:
        print(f"Bedrock error: {e}")
    
    # Fallback response
    return {
        "goal": "Survive another day",
        "action": "Panic internally while appearing calm",
        "rationale": "Can't afford to lose any opportunity",
        "result": "Anxiety increases"
    }

def send_to_telemetry(ws, character, decision, scenario):
    """Send AI decision to WebSocket for live viewer overlay"""
    
    telemetry_msg = {
        "action": "telemetry",
        "data": {
            "goal": f"[{character}] {decision.get('goal', 'Survive')}",
            "action": decision.get('action', 'Coping'),
            "rationale": decision.get('rationale', 'Money is tight'),
            "result": f"{scenario['name']}: {decision.get('result', 'Ongoing')}"
        }
    }
    
    try:
        ws.send(json.dumps(telemetry_msg))
        print(f"Sent to overlay: {character} - {scenario['name']}")
        return True
    except Exception as e:
        print(f"WebSocket error: {e}")
        return False

def main():
    """Stream AI character decisions to live telemetry"""
    
    print("=== AI TO TELEMETRY STREAMING ===")
    print(f"WebSocket: {WS_URL}")
    print(f"Starting at {datetime.now()}\n")
    
    # Connect to WebSocket
    ws = websocket.WebSocket()
    try:
        ws.connect(WS_URL)
        print("Connected to telemetry WebSocket!")
    except Exception as e:
        print(f"Failed to connect: {e}")
        return
    
    # Characters to simulate
    characters = ['alex_chen', 'jamie_rodriguez', 'sarah_kim', 'marcus_williams', 'emma_thompson']
    
    # Stream decisions
    try:
        while True:
            # Pick random character and scenario
            character = random.choice(characters)
            scenario = random.choice(scenarios)
            
            print(f"\n{character.upper()} faces: {scenario['name']}")
            
            # Get AI decision
            decision = get_ai_response(character, scenario)
            print(f"AI Response: {json.dumps(decision, indent=2)}")
            
            # Send to telemetry overlay
            if send_to_telemetry(ws, character, decision, scenario):
                print("✓ Streamed to viewer overlay")
            
            # Wait before next update (simulate real-time decisions)
            time.sleep(10)  # Update every 10 seconds
            
    except KeyboardInterrupt:
        print("\nStopping stream...")
    finally:
        ws.close()
        print("Disconnected from telemetry")

if __name__ == "__main__":
    main()
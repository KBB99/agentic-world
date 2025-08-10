#!/usr/bin/env python3
"""
Demo: Stream realistic AI decisions that WOULD go to telemetry
Shows what viewers would see in the overlay
"""

import json
import boto3
import time
import random
from datetime import datetime

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Realistic character situations
character_scenarios = {
    'alex_chen': [
        ('Eviction notice on door', '$47 in account, rent is $1100', 'Text everyone I know asking to crash'),
        ('Parents calling again', 'They think book deal is close', 'Let it go to voicemail, text "in meeting"'),
        ('Library closing', 'Nowhere else with free wifi', 'Pack up, walk to 24hr McDonalds'),
    ],
    'jamie_rodriguez': [
        ('Producer wants coffee meeting', 'Have $3.50, coffee is $6', 'Suggest meeting at their office instead'),
        ('Film gig tomorrow 6am', 'Barista shift starts at 5am', 'Call in sick to coffee shop, lose $120'),
        ('Roommate eating your food again', 'That was dinner for 2 days', 'Leave passive aggressive note'),
    ],
    'sarah_kim': [
        ('Department wants free guest lecture', 'They pay real professors for this', 'Agree anyway, need the connection'),
        ('Student crying in office hours', 'You have 10 mins before driving to next campus', 'Give them your personal email'),
        ('Gas light on', 'Have $20, need gas for week', 'Put in $10, pray'),
    ],
    'marcus_williams': [
        ('Ex-coworker LinkedIn message', 'Asks about new role', 'Vague response about "consulting"'),
        ('Uber passenger is old boss', 'Recognized you immediately', 'Pretend this is temporary side thing'),
        ('Date asks what you do', 'Cannot say Uber driver', 'Say "in transition between tech roles"'),
    ],
    'emma_thompson': [
        ('Customer wants you to smile more', 'You worked till 3am on art', 'Dead-eye smile, add extra foam passive aggressively'),
        ('Gallery reject email', '47th rejection this year', 'Screenshot for motivation board, cry in bathroom'),
        ('Mom asks about "real job"', 'This IS real job', 'Send her Instagram follower count as proof'),
    ]
}

def get_ai_decision(character, situation, context):
    """Get realistic AI response via Bedrock"""
    
    prompt = f"""You are {character.replace('_', ' ').title()}, struggling millennial/gen-z.
Situation: {situation}
Context: {context}
What do you ACTUALLY do? One sentence, be painfully real."""

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

def format_telemetry(character, situation, context, action):
    """Format as it would appear in viewer overlay"""
    
    return {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "character": character.replace('_', ' ').title(),
        "telemetry": {
            "Goal": f"Handle: {situation}",
            "Action": action[:80] + "..." if len(action) > 80 else action,
            "Rationale": context,
            "Result": "Anxiety +10"
        }
    }

def main():
    print("=== BEDROCK AI STREAMING DEMO ===")
    print("Showing what would appear in viewer telemetry overlay")
    print("URL: https://d1u690gz6k82jo.cloudfront.net/index.html")
    print("="*70 + "\n")
    
    # Run for 10 iterations
    for i in range(10):
        # Pick random character and scenario
        character = random.choice(list(character_scenarios.keys()))
        situation, context, _ = random.choice(character_scenarios[character])
        
        # Get AI decision
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Getting AI response for {character}...")
        action = get_ai_decision(character, situation, context)
        
        # Format as telemetry
        telemetry = format_telemetry(character, situation, context, action)
        
        # Display
        print("\n" + "─"*60)
        print(f"CHARACTER: {telemetry['character']}")
        print(f"SITUATION: {situation}")
        print("\nTELEMETRY OVERLAY:")
        for key, value in telemetry['telemetry'].items():
            print(f"  {key}: {value}")
        print("─"*60 + "\n")
        
        # Wait before next
        time.sleep(5)
    
    print("\n" + "="*70)
    print("In production, this would stream to the live viewer overlay")
    print("Viewers would see these internal character struggles in real-time")
    print("Creating empathy and narrative engagement with 'NPCs' who feel human")

if __name__ == "__main__":
    main()
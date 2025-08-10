#!/usr/bin/env python3
"""
Safe AI Narrative System with Cost Control
Only makes AI calls if system is not paused and under budget
"""

import json
import sys
from datetime import datetime
from cost_control import SafeAIClient, PauseControl, CostTracker
import boto3
import websocket

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class SafeNarrative:
    """Narrative system with cost controls"""
    
    def __init__(self):
        self.ai = SafeAIClient()
        self.tracker = CostTracker()
        self.memories_table = dynamodb.Table('agentic-demo-character-memories')
        self.ws_url = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"
        
    def run_turn(self, character, situation):
        """Run one narrative turn with cost tracking"""
        
        # Check if paused
        if PauseControl.is_paused():
            print("⏸️  System is paused - no AI calls will be made")
            print("   Use ./resume-ai.sh to enable AI operations")
            return None
            
        # Get character memories
        try:
            char_data = self.memories_table.get_item(Key={'characterId': character})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = ["No previous memories"]
            
        # Build prompt
        prompt = f"""You are {character.replace('_', ' ').title()}, struggling millennial.
Memories: {'; '.join(memories[-5:])}
Situation: {situation}
What do you do? Reply with one realistic action."""

        # Make safe AI call with cost tracking
        print(f"\n[{character}] {situation}")
        result = self.ai.invoke_model_safe(prompt, max_tokens=80)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
            if result.get('cost'):
                print(f"   Today's cost: ${result['cost']:.2f}")
            return None
            
        action = result['content'].strip()
        
        # Track DynamoDB operations
        self.tracker.track_dynamodb_operation(reads=1, writes=1)
        
        # Save new memory
        memories.append(f"{situation}: {action[:50]}")
        char_data['memories'] = memories
        self.memories_table.put_item(Item=char_data)
        
        # Send to telemetry (track WebSocket cost)
        try:
            ws = websocket.WebSocket()
            ws.connect(self.ws_url)
            msg = {
                'goal': f'[{character}] {situation[:30]}',
                'action': action[:80],
                'rationale': f'Cost: ${result["cost"]:.4f}',
                'result': f'Memory #{len(memories)}'
            }
            ws.send(json.dumps(msg))
            ws.close()
            self.tracker.track_websocket_message()
        except:
            pass
            
        print(f"✓ Action: {action[:60]}...")
        
        return action
        
    def run_demo(self, max_turns=5):
        """Run demo with cost limits"""
        
        print("\n=== SAFE AI NARRATIVE DEMO ===")
        print(f"Daily limit: $10.00")
        print(f"Current today: ${self.tracker.get_today_cost():.2f}")
        
        if PauseControl.is_paused():
            status = PauseControl.get_status()
            print(f"\n⏸️  PAUSED since {status['since']}")
            print("Run ./resume-ai.sh to enable AI")
            return
            
        scenarios = [
            ('alex_chen', 'Landlord knocking on door'),
            ('jamie_rodriguez', 'Customer asks about your dreams'),
            ('sarah_kim', 'Another adjunct position email'),
            ('marcus_williams', 'Picking up ex-colleague in Uber'),
            ('alex_chen', 'Found $20 on ground')
        ]
        
        for i, (character, situation) in enumerate(scenarios[:max_turns]):
            print(f"\n--- Turn {i+1}/{max_turns} ---")
            
            action = self.run_turn(character, situation)
            
            if not action:
                print("\n⚠️  Stopping due to pause or limit")
                break
                
            # Check if we should auto-pause
            if self.tracker.get_today_cost() > 5.0:
                print(f"\n⚠️  Approaching daily limit (${self.tracker.get_today_cost():.2f})")
                
        summary = self.tracker.get_summary()
        print(f"\n=== SESSION COMPLETE ===")
        print(f"Session cost: ~${summary['today']:.4f}")
        print(f"Total all-time: ${summary['total']:.4f}")

def main():
    """Main entry point"""
    
    if len(sys.argv) > 1 and sys.argv[1] == 'pause':
        PauseControl.pause()
    elif len(sys.argv) > 1 and sys.argv[1] == 'resume':
        PauseControl.resume()
    else:
        narrative = SafeNarrative()
        narrative.run_demo()

if __name__ == "__main__":
    main()
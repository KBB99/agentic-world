#!/usr/bin/env python3
"""
Persistent World State System
Characters have memories stored in DynamoDB that persist across sessions
Their actions affect the shared world and each other
"""

import json
import boto3
import websocket
import time
from datetime import datetime
from decimal import Decimal

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# DynamoDB tables
WORLD_TABLE = 'agentic-demo-world-state'
MEMORIES_TABLE = 'agentic-demo-character-memories'

class PersistentWorld:
    """World state that persists in DynamoDB"""
    
    def __init__(self):
        self.table = dynamodb.Table(WORLD_TABLE)
        self.load_or_create()
        
    def load_or_create(self):
        """Load world state from DynamoDB or create new"""
        try:
            response = self.table.get_item(Key={'worldId': 'main'})
            if 'Item' in response:
                self.state = response['Item']['state']
                print("Loaded existing world state")
            else:
                self.create_new_world()
        except:
            self.create_new_world()
            
    def create_new_world(self):
        """Initialize new world state"""
        self.state = {
            'day': 1,
            'time': 'evening',
            'locations': {
                'library': {'closing_soon': True, 'occupants': []},
                'coffee_shop': {'hiring': False, 'occupants': []},
                'mcdonalds': {'always_open': True, 'occupants': []},
                'apartment': {'eviction_notices': ['alex_chen'], 'occupants': []}
            },
            'events': {
                'rent_strike': {'active': True, 'participants': [], 'day': 'tomorrow'},
                'networking_event': {'tonight': True, 'cost': 20}
            },
            'relationships': {},  # who knows who
            'shared_resources': {'community_fund': 0}  # collective resources
        }
        self.save()
        print("Created new world state")
        
    def save(self):
        """Save world state to DynamoDB"""
        try:
            self.table.put_item(Item={
                'worldId': 'main',
                'state': self.state,
                'lastUpdated': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error saving world: {e}")
            
    def update_location(self, character, from_loc, to_loc):
        """Move character between locations"""
        if from_loc and from_loc in self.state['locations']:
            occupants = self.state['locations'][from_loc]['occupants']
            if character in occupants:
                occupants.remove(character)
                
        if to_loc and to_loc in self.state['locations']:
            self.state['locations'][to_loc]['occupants'].append(character)
            
        self.save()
        
    def add_relationship(self, char1, char2, relationship_type):
        """Record relationship between characters"""
        if char1 not in self.state['relationships']:
            self.state['relationships'][char1] = {}
        self.state['relationships'][char1][char2] = relationship_type
        self.save()

class PersistentCharacter:
    """Character with memories that persist in DynamoDB"""
    
    def __init__(self, name):
        self.name = name
        self.table = dynamodb.Table(MEMORIES_TABLE)
        self.load_or_create()
        
    def load_or_create(self):
        """Load character from DynamoDB or create new"""
        try:
            response = self.table.get_item(Key={'characterId': self.name})
            if 'Item' in response:
                self.memories = response['Item']['memories']
                self.resources = response['Item']['resources']
                self.location = response['Item']['location']
                print(f"Loaded {self.name} with {len(self.memories)} memories")
            else:
                self.create_new_character()
        except:
            self.create_new_character()
            
    def create_new_character(self):
        """Initialize new character"""
        profiles = {
            'alex_chen': {
                'memories': ["Got MFA, now $73K in debt", "Eviction notice posted today"],
                'resources': {'money': 47, 'energy': 'low', 'hope': 'fading'},
                'location': 'library'
            },
            'jamie_rodriguez': {
                'memories': ["Film degree was a mistake", "Barista job barely covers rent"],
                'resources': {'money': 27, 'energy': 'exhausted', 'hope': 'stubborn'},
                'location': 'coffee_shop'
            },
            'sarah_kim': {
                'memories': ["PhD doesn't pay bills", "Teaching at 3 colleges"],
                'resources': {'money': 120, 'gas': 'quarter_tank', 'patience': 'gone'},
                'location': 'car'
            }
        }
        
        profile = profiles.get(self.name, {
            'memories': ["Just trying to survive"],
            'resources': {'money': 50},
            'location': 'unknown'
        })
        
        self.memories = profile['memories']
        self.resources = profile['resources']
        self.location = profile['location']
        self.save()
        print(f"Created new character: {self.name}")
        
    def save(self):
        """Save character to DynamoDB"""
        try:
            # Convert to DynamoDB-safe format
            safe_resources = {k: Decimal(str(v)) if isinstance(v, (int, float)) else v 
                            for k, v in self.resources.items()}
            
            self.table.put_item(Item={
                'characterId': self.name,
                'memories': self.memories,
                'resources': safe_resources,
                'location': self.location,
                'lastUpdated': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Error saving {self.name}: {e}")
            
    def remember(self, memory):
        """Add memory and save"""
        timestamp = datetime.now().strftime("%H:%M")
        self.memories.append(f"[{timestamp}] {memory}")
        # Keep last 30 memories
        if len(self.memories) > 30:
            self.memories.pop(0)
        self.save()
        
    def get_memory_prompt(self):
        """Format memories for AI prompt"""
        recent = self.memories[-10:] if len(self.memories) > 10 else self.memories
        return "\\n".join(recent)

class StatefulNarrative:
    """Manages persistent narrative with memory"""
    
    def __init__(self):
        self.world = PersistentWorld()
        self.characters = {}
        self.ws_url = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"
        
    def get_character(self, name):
        """Get or create character"""
        if name not in self.characters:
            self.characters[name] = PersistentCharacter(name)
        return self.characters[name]
        
    def get_ai_decision(self, character_name, situation):
        """Get AI decision based on persistent memory and world state"""
        
        char = self.get_character(character_name)
        
        # Who else is at this location?
        others_here = [c for c in self.world.state['locations'].get(char.location, {}).get('occupants', []) 
                      if c != character_name]
        
        prompt = f"""You are {character_name.replace('_', ' ').title()}, struggling to survive.

YOUR MEMORIES (persistent from previous sessions):
{char.get_memory_prompt()}

YOUR RESOURCES:
{json.dumps(char.resources)}

CURRENT LOCATION: {char.location}
OTHERS HERE: {others_here if others_here else 'nobody'}

WORLD STATE:
- Day {self.world.state['day']}, {self.world.state['time']}
- Rent strike: {len(self.world.state['events']['rent_strike']['participants'])} people committed
- Community fund: ${self.world.state['shared_resources']['community_fund']}

RELATIONSHIPS:
{json.dumps(self.world.state['relationships'].get(character_name, {}))}

SITUATION: {situation}

Respond based on your memories and relationships. Format as JSON:
{{
  "action": "what you do (one sentence)",
  "internal": "your real thoughts",
  "memory": "what you'll remember from this",
  "affects": "impact on world/others",
  "move_to": "location to go to, or null to stay"
}}"""

        try:
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                contentType='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 300,
                    'temperature': 0.7,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            text = result['content'][0]['text']
            
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            print(f"AI error: {e}")
            
        return {
            "action": "Freeze, overwhelmed",
            "internal": "Can't process this",
            "memory": "Another crisis",
            "affects": "nothing",
            "move_to": None
        }
        
    def process_action(self, character_name, situation):
        """Process character action and update persistent state"""
        
        char = self.get_character(character_name)
        decision = self.get_ai_decision(character_name, situation)
        
        # Update memory (persists to DynamoDB)
        char.remember(decision['memory'])
        
        # Update location if moving
        if decision.get('move_to'):
            self.world.update_location(character_name, char.location, decision['move_to'])
            char.location = decision['move_to']
            char.save()
            
        # Process effects on world
        if 'rent strike' in decision['affects'].lower():
            self.world.state['events']['rent_strike']['participants'].append(character_name)
            self.world.save()
            
        if 'tells' in decision['affects'].lower():
            # Create relationships
            for other_name in self.characters:
                if other_name != character_name and other_name.replace('_', ' ') in decision['affects']:
                    self.world.add_relationship(character_name, other_name, 'confided_in')
                    other_char = self.get_character(other_name)
                    other_char.remember(f"{character_name} told me: {decision['action'][:50]}")
                    
        # Send to telemetry
        self.send_telemetry(character_name, decision, situation)
        
        return decision
        
    def send_telemetry(self, character_name, decision, situation):
        """Send to WebSocket for viewer"""
        try:
            ws = websocket.WebSocket()
            ws.connect(self.ws_url)
            
            char = self.get_character(character_name)
            
            msg = {
                'goal': f"[{character_name.replace('_', ' ').title()}] {situation[:40]}",
                'action': decision['action'][:80],
                'rationale': decision['internal'][:80],
                'result': f"Day {self.world.state['day']}, Memory #{len(char.memories)}"
            }
            
            ws.send(json.dumps(msg))
            ws.close()
            
            print(f"✓ Telemetry: {character_name}")
            
        except Exception as e:
            print(f"WebSocket error: {e}")

def main():
    """Run persistent narrative system"""
    
    print("=== PERSISTENT WORLD SYSTEM ===")
    print("Characters have memories that persist across sessions")
    print("Their actions permanently affect the world\\n")
    
    narrative = StatefulNarrative()
    
    # Run some turns
    events = [
        ('alex_chen', 'Library closing announcement plays'),
        ('jamie_rodriguez', 'Alex walks into coffee shop looking desperate'),
        ('alex_chen', 'You recognize Jamie from the coffee shop'),
        ('jamie_rodriguez', 'Alex mentions being evicted'),
        ('alex_chen', 'Jamie suggests the rent strike meeting'),
    ]
    
    for character, situation in events:
        print(f"\\n{character.upper()}: {situation}")
        
        decision = narrative.process_action(character, situation)
        
        print(f"Action: {decision['action']}")
        print(f"Thinks: {decision['internal'][:60]}...")
        
        time.sleep(3)
        
    print("\\n=== PERSISTENT STATE SAVED ===")
    print("Run this script again and characters will remember everything!")
    print("Their memories and relationships persist in DynamoDB")

if __name__ == "__main__":
    main()
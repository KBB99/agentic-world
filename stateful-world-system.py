#!/usr/bin/env python3
"""
Stateful World System - Characters with memory and interconnected lives
Each character's actions affect the world and other characters
"""

import json
import boto3
import websocket
import time
from datetime import datetime
from typing import Dict, List, Any

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class SharedWorld:
    """Maintains global state that all characters exist within"""
    
    def __init__(self):
        self.state = {
            'time_of_day': 'evening',
            'day_of_week': 'Thursday',
            'rent_due_days': 2,
            'weather': 'raining',
            'locations': {
                'library': {'closes_in': '30 minutes', 'wifi': True, 'people': []},
                'mcdonalds': {'open_24hr': True, 'wifi': True, 'people': []},
                'coffee_shop': {'hiring': False, 'people': []},
                'alex_apartment': {'eviction_notice': True, 'days_left': 3},
                'shared_studio': {'roommates': 4, 'drama_level': 'high'},
            },
            'events': {
                'networking_event': {'tonight': True, 'location': 'downtown', 'cost': '$20 parking'},
                'rent_strike': {'participants': [], 'momentum': 'growing'},
            },
            'connections': {}  # Who knows who
        }
        
        # Recent events that affect everyone
        self.recent_events = []
        
    def update(self, event: Dict[str, Any]):
        """Update world based on character action"""
        self.recent_events.append(event)
        # Keep last 10 events
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)
            
        # Update locations
        if 'leaves' in event:
            location = event['leaves']
            if location in self.state['locations'] and event['character'] in self.state['locations'][location]['people']:
                self.state['locations'][location]['people'].remove(event['character'])
                
        if 'arrives' in event:
            location = event['arrives']
            if location in self.state['locations']:
                self.state['locations'][location]['people'].append(event['character'])
                
        # Update connections
        if 'meets' in event:
            char1 = event['character']
            char2 = event['meets']
            if char1 not in self.state['connections']:
                self.state['connections'][char1] = []
            if char2 not in self.state['connections']:
                self.state['connections'][char2] = []
            self.state['connections'][char1].append(char2)
            self.state['connections'][char2].append(char1)
            
        return self.state

class Character:
    """A character with persistent memory and relationships"""
    
    def __init__(self, name: str, profile: Dict[str, Any]):
        self.name = name
        self.profile = profile
        self.memory = []  # List of all past events/decisions
        self.relationships = {}  # Feelings about other characters
        self.current_location = profile.get('location', 'unknown')
        self.resources = profile.get('resources', {'money': 50, 'energy': 'low'})
        
    def remember(self, event: str):
        """Add to character's memory"""
        timestamp = datetime.now().strftime("%H:%M")
        self.memory.append(f"[{timestamp}] {event}")
        # Keep last 20 memories to avoid prompt getting too long
        if len(self.memory) > 20:
            self.memory.pop(0)
            
    def get_memory_context(self) -> str:
        """Get memory as context string"""
        if not self.memory:
            return "This is your first conscious moment today."
        return "Your recent memories:\n" + "\n".join(self.memory[-10:])  # Last 10 memories
        
    def update_relationship(self, other_character: str, feeling: str):
        """Update feelings about another character"""
        self.relationships[other_character] = feeling

class StatefulAISystem:
    """Manages characters with memory in a shared world"""
    
    def __init__(self):
        self.world = SharedWorld()
        self.characters = {}
        self.ws_url = "wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod"
        self.ws = None
        
        # Initialize characters
        self._init_characters()
        
    def _init_characters(self):
        """Create characters with initial state"""
        
        self.characters['alex_chen'] = Character('Alex Chen', {
            'profile': 'Writer, MFA, $73K debt, couchsurfing',
            'location': 'library',
            'resources': {'money': 47, 'energy': 'exhausted'},
            'personality': 'Anxious, talented, desperate but hiding it'
        })
        
        self.characters['jamie_rodriguez'] = Character('Jamie Rodriguez', {
            'profile': 'Film PA, barista, dreams of directing',
            'location': 'coffee_shop',
            'resources': {'money': 27, 'energy': 'running_on_fumes'},
            'personality': 'Optimistic wearing thin, networking desperately'
        })
        
        self.characters['sarah_kim'] = Character('Sarah Kim', {
            'profile': 'Adjunct professor, 3 colleges, no benefits',
            'location': 'car',
            'resources': {'money': 120, 'gas': 'quarter_tank'},
            'personality': 'Brilliant, overworked, considering giving up'
        })
        
        self.characters['marcus_williams'] = Character('Marcus Williams', {
            'profile': 'Ex-tech, now Uber driver, hiding from friends',
            'location': 'car',
            'resources': {'money': 89, 'dignity': 'declining'},
            'personality': 'Maintaining facade, deeply ashamed'
        })
        
        # Set initial memories
        self.characters['alex_chen'].remember("Landlord posted eviction notice this morning")
        self.characters['alex_chen'].remember("Haven't eaten since yesterday's ramen")
        
        self.characters['jamie_rodriguez'].remember("Manager cut my hours again")
        self.characters['jamie_rodriguez'].remember("Networking event tonight but parking is $20")
        
        # Set initial relationships
        self.characters['alex_chen'].relationships['jamie_rodriguez'] = 'met at coffee shop, seems nice but also struggling'
        self.characters['jamie_rodriguez'].relationships['alex_chen'] = 'writer who comes in, always on laptop, orders just water'
        
    def get_ai_decision(self, character_name: str, situation: str) -> Dict[str, Any]:
        """Get AI decision with full context of memory and world state"""
        
        char = self.characters[character_name]
        
        # Build comprehensive prompt with memory and world state
        prompt = f"""You are {char.name}: {char.profile['profile']}
Personality: {char.profile['personality']}

CURRENT WORLD STATE:
- Time: {self.world.state['time_of_day']}, {self.world.state['day_of_week']}
- Weather: {self.world.state['weather']}
- Rent due in: {self.world.state['rent_due_days']} days
- Your location: {char.current_location}
- Your resources: {json.dumps(char.resources)}

YOUR MEMORIES:
{char.get_memory_context()}

YOUR RELATIONSHIPS:
{json.dumps(char.relationships) if char.relationships else "You don't know anyone well yet"}

OTHERS CURRENTLY AT {char.current_location}:
{self.world.state['locations'].get(char.current_location, {}).get('people', [])}

RECENT EVENTS IN THE WORLD:
{self._format_recent_events()}

CURRENT SITUATION:
{situation}

Respond with a realistic action considering your memories, relationships, and the world state.
Format as JSON:
{{
  "action": "what you do (one sentence)",
  "internal_thought": "what you're really thinking",
  "affects": "how this impacts others or the world",
  "goes_to": "location you move to (or 'stays')",
  "remembers": "what you'll remember from this"
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
            
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                return decision
                
        except Exception as e:
            print(f"AI error: {e}")
            
        # Fallback
        return {
            "action": "Stare blankly, paralyzed by options",
            "internal_thought": "I can't afford any mistakes",
            "affects": "nothing changes",
            "goes_to": "stays",
            "remembers": "Another moment of paralysis"
        }
        
    def _format_recent_events(self) -> str:
        """Format recent world events for context"""
        if not self.world.recent_events:
            return "Nothing notable has happened yet"
        
        events_str = []
        for event in self.world.recent_events[-5:]:  # Last 5 events
            events_str.append(f"- {event.get('character', 'Someone')}: {event.get('action', 'did something')}")
        return "\n".join(events_str)
        
    def process_turn(self, character_name: str, situation: str):
        """Process one character's turn with memory and world updates"""
        
        char = self.characters[character_name]
        
        # Get AI decision with full context
        decision = self.get_ai_decision(character_name, situation)
        
        # Update character's memory
        char.remember(f"{situation} -> {decision['action']}")
        if 'remembers' in decision:
            char.remember(decision['remembers'])
            
        # Update character location
        if decision.get('goes_to') and decision['goes_to'] != 'stays':
            old_location = char.current_location
            char.current_location = decision['goes_to']
            
            # Update world state
            self.world.update({
                'character': character_name,
                'leaves': old_location,
                'arrives': decision['goes_to'],
                'action': decision['action']
            })
            
        # Check for character interactions
        if 'affects' in decision and 'tells' in decision['affects'].lower():
            # Parse who they're telling
            for other_name, other_char in self.characters.items():
                if other_name != character_name and other_name.replace('_', ' ') in decision['affects']:
                    other_char.remember(f"{char.name} told me: {decision['action']}")
                    
        # Send to telemetry
        self.send_to_telemetry(character_name, decision, situation)
        
        return decision
        
    def send_to_telemetry(self, character_name: str, decision: Dict, situation: str):
        """Send decision to WebSocket for viewer overlay"""
        
        if not self.ws:
            self.ws = websocket.WebSocket()
            self.ws.connect(self.ws_url)
            
        char = self.characters[character_name]
        
        msg = {
            'goal': f"[{char.name}] {situation[:50]}",
            'action': decision['action'][:100],
            'rationale': decision.get('internal_thought', 'Surviving')[:100],
            'result': f"Memory#{len(char.memory)}: {decision.get('affects', 'Continues')}[:50]"
        }
        
        try:
            self.ws.send(json.dumps(msg))
            print(f"✓ {char.name}: {decision['action'][:60]}...")
        except Exception as e:
            print(f"WebSocket error: {e}")
            self.ws = None
            
    def run_narrative_sequence(self, turns: int = 10):
        """Run a sequence where characters take turns, building on previous events"""
        
        print("=== STATEFUL NARRATIVE SYSTEM ===")
        print("Characters have memory and affect each other's world\n")
        
        # Situations that evolve based on world state
        situations_pool = [
            ("alex_chen", "Library announcement: 'Closing in 10 minutes'"),
            ("jamie_rodriguez", "Text from roommate: 'Where's your half of utilities?'"),
            ("sarah_kim", "Email: 'Can you cover another class tomorrow?'"),
            ("marcus_williams", "Uber ping: Pickup at your old office building"),
            ("alex_chen", "Jamie walks by in the coffee shop"),
            ("jamie_rodriguez", "See Alex at library, looking stressed"),
            ("sarah_kim", "Student emails: 'Is there extra credit?'"),
            ("marcus_williams", "LinkedIn notification from former colleague"),
        ]
        
        for turn in range(turns):
            print(f"\n--- Turn {turn + 1} ---")
            
            # Pick situation based on world state
            char_name, base_situation = situations_pool[turn % len(situations_pool)]
            
            # Enhance situation with world context
            char = self.characters[char_name]
            location_info = self.world.state['locations'].get(char.current_location, {})
            others_here = location_info.get('people', [])
            
            enhanced_situation = base_situation
            if others_here and len(others_here) > 1:
                enhanced_situation += f" (Others here: {', '.join(others_here)})"
                
            # Process turn
            decision = self.process_turn(char_name, enhanced_situation)
            
            print(f"Location: {char.current_location}")
            print(f"Thought: {decision.get('internal_thought', 'Surviving')[:80]}")
            print(f"Impact: {decision.get('affects', 'None')[:80]}")
            
            time.sleep(3)  # Pause between turns
            
        print("\n=== FINAL MEMORY STATES ===")
        for name, char in self.characters.items():
            print(f"\n{name} remembers:")
            for memory in char.memory[-3:]:
                print(f"  {memory}")

def main():
    """Run the stateful world system"""
    
    system = StatefulAISystem()
    
    # Run a narrative sequence where characters affect each other
    system.run_narrative_sequence(turns=8)
    
    print("\n✅ Stateful narrative complete!")
    print("Characters now have persistent memories and relationships")
    print("Their actions affected the shared world and each other")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Spatial World System - Characters navigate real spaces and take location-based actions
Characters have spatial awareness and can move between connected locations
"""

import json
import boto3
import websocket
import time
from datetime import datetime
from typing import Dict, List, Set, Tuple

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

class SpatialWorld:
    """World with connected locations and spatial properties"""
    
    def __init__(self):
        # Define locations with properties and what's available there
        self.locations = {
            'library': {
                'type': 'public',
                'resources': ['free_wifi', 'computers', 'quiet_space', 'books'],
                'cost': 0,
                'hours': '9am-8pm',
                'description': 'Public library with free wifi and resources',
                'capacity': 50,
                'current_occupants': []
            },
            'coffee_shop': {
                'type': 'commercial',
                'resources': ['wifi', 'coffee', 'food', 'seating'],
                'cost': 5,  # Minimum purchase
                'hours': '6am-10pm',
                'description': 'Local coffee shop where Jamie works',
                'capacity': 30,
                'current_occupants': []
            },
            'luxury_apartment': {
                'type': 'private',
                'resources': ['high_speed_internet', 'gym', 'pool', 'security'],
                'cost': 5000,  # Monthly rent
                'hours': '24/7',
                'description': 'Tyler\'s penthouse with city views',
                'capacity': 5,
                'current_occupants': []
            },
            'alex_apartment': {
                'type': 'private',
                'resources': ['basic_utilities'],
                'cost': 1100,  # Monthly rent (unpaid)
                'hours': '24/7',
                'description': 'Alex\'s soon-to-be-evicted apartment',
                'capacity': 2,
                'current_occupants': [],
                'status': 'eviction_pending'
            },
            'hospital': {
                'type': 'workplace',
                'resources': ['medical_care', 'cafeteria', 'vending_machines'],
                'cost': 0,  # For employees
                'hours': '24/7',
                'description': 'Hospital where Maria works ICU',
                'capacity': 500,
                'current_occupants': []
            },
            'downtown_office': {
                'type': 'workplace',
                'resources': ['meeting_rooms', 'kitchen', 'gym'],
                'cost': 0,  # For employees
                'hours': '7am-9pm',
                'description': 'Financial district office where Ashley works',
                'capacity': 200,
                'current_occupants': []
            },
            'street': {
                'type': 'public',
                'resources': ['transit_access', 'shops'],
                'cost': 0,
                'hours': '24/7',
                'description': 'City streets connecting locations',
                'capacity': 1000,
                'current_occupants': []
            },
            'car': {
                'type': 'mobile',
                'resources': ['transportation', 'shelter', 'storage'],
                'cost': 4,  # Gas per trip
                'hours': '24/7',
                'description': 'Vehicle for transportation or gig work',
                'capacity': 4,
                'current_occupants': []
            },
            'mcdonalds': {
                'type': 'commercial',
                'resources': ['wifi', 'cheap_food', 'restroom', '24hr_access'],
                'cost': 2,  # Minimum purchase
                'hours': '24/7',
                'description': '24-hour McDonald\'s with wifi',
                'capacity': 40,
                'current_occupants': []
            },
            'old_house': {
                'type': 'private',
                'resources': ['garden', 'memories', 'space'],
                'cost': 800,  # Property tax/month
                'hours': '24/7',
                'description': 'Dorothy\'s house of 40 years',
                'capacity': 6,
                'current_occupants': []
            },
            'community_center': {
                'type': 'public',
                'resources': ['meeting_space', 'organizing', 'childcare'],
                'cost': 0,
                'hours': '8am-9pm',
                'description': 'Space for community organizing and rent strike meetings',
                'capacity': 100,
                'current_occupants': []
            },
            'food_bank': {
                'type': 'public',
                'resources': ['free_food', 'community', 'information'],
                'cost': 0,
                'hours': 'Tue/Thu 10am-2pm',
                'description': 'Local food bank and resource center',
                'capacity': 30,
                'current_occupants': []
            }
        }
        
        # Define connections between locations (travel time in minutes)
        self.connections = {
            'library': [
                ('coffee_shop', 5),
                ('street', 1),
                ('mcdonalds', 10),
                ('community_center', 15)
            ],
            'coffee_shop': [
                ('library', 5),
                ('street', 1),
                ('downtown_office', 20),
                ('mcdonalds', 8)
            ],
            'luxury_apartment': [
                ('downtown_office', 10),
                ('street', 2)
            ],
            'alex_apartment': [
                ('street', 1),
                ('library', 12),
                ('food_bank', 8)
            ],
            'hospital': [
                ('street', 1),
                ('mcdonalds', 5),
                ('car', 1)
            ],
            'downtown_office': [
                ('luxury_apartment', 10),
                ('coffee_shop', 20),
                ('street', 1)
            ],
            'street': [
                ('library', 1),
                ('coffee_shop', 1),
                ('hospital', 1),
                ('downtown_office', 1),
                ('alex_apartment', 1),
                ('old_house', 5),
                ('community_center', 10)
            ],
            'car': [
                ('hospital', 1),
                ('street', 0),
                ('mcdonalds', 3)
            ],
            'mcdonalds': [
                ('library', 10),
                ('coffee_shop', 8),
                ('hospital', 5),
                ('car', 3),
                ('street', 1)
            ],
            'old_house': [
                ('street', 5),
                ('community_center', 8),
                ('food_bank', 6)
            ],
            'community_center': [
                ('library', 15),
                ('street', 10),
                ('old_house', 8),
                ('food_bank', 4)
            ],
            'food_bank': [
                ('alex_apartment', 8),
                ('old_house', 6),
                ('community_center', 4)
            ]
        }
        
        # Initialize character locations
        self.character_locations = {
            'alex_chen': 'alex_apartment',
            'tyler_chen': 'luxury_apartment',
            'jamie_rodriguez': 'coffee_shop',
            'maria_gonzalez': 'hospital',
            'ashley_kim': 'downtown_office',
            'dorothy_jackson': 'old_house',
            'brittany_torres': 'car'
        }
        
        # Update occupants
        for char, loc in self.character_locations.items():
            self.locations[loc]['current_occupants'].append(char)
            
    def get_available_connections(self, current_location: str) -> List[Tuple[str, int]]:
        """Get locations accessible from current location"""
        return self.connections.get(current_location, [])
        
    def move_character(self, character: str, from_loc: str, to_loc: str) -> Dict:
        """Move character between locations"""
        # Remove from old location
        if character in self.locations[from_loc]['current_occupants']:
            self.locations[from_loc]['current_occupants'].remove(character)
            
        # Add to new location
        self.locations[to_loc]['current_occupants'].append(character)
        self.character_locations[character] = to_loc
        
        # Return movement info
        travel_time = next((time for loc, time in self.connections[from_loc] if loc == to_loc), 10)
        
        return {
            'from': from_loc,
            'to': to_loc,
            'travel_time': travel_time,
            'new_occupants': self.locations[to_loc]['current_occupants']
        }
        
    def get_location_context(self, location: str) -> str:
        """Get description of what's at a location"""
        loc = self.locations[location]
        occupants = loc['current_occupants']
        
        context = f"{loc['description']}. "
        
        if occupants:
            others = [o for o in occupants if o != location]
            if others:
                context += f"Also here: {', '.join(others)}. "
                
        if loc['resources']:
            context += f"Available: {', '.join(loc['resources'])}. "
            
        if loc['cost'] > 0:
            context += f"Cost: ${loc['cost']}. "
            
        return context

class SpatialCharacter:
    """Character with spatial awareness and navigation ability"""
    
    def __init__(self, name: str, world: SpatialWorld):
        self.name = name
        self.world = world
        self.current_location = world.character_locations.get(name, 'street')
        self.memories_table = dynamodb.Table('agentic-demo-character-memories')
        self.movement_history = []
        
    def get_spatial_prompt(self, situation: str, memories: List[str]) -> str:
        """Build prompt with spatial awareness"""
        
        # Get current location context
        location_context = self.world.get_location_context(self.current_location)
        
        # Get available moves
        connections = self.world.get_available_connections(self.current_location)
        available_moves = [f"{loc} ({time}min)" for loc, time in connections]
        
        # Get who else is here
        others_here = [c for c in self.world.locations[self.current_location]['current_occupants'] 
                      if c != self.name]
        
        # Build spatial awareness section
        spatial_info = f"""
CURRENT LOCATION: {self.current_location}
{location_context}

OTHERS HERE: {', '.join(others_here) if others_here else 'Nobody else'}

CAN MOVE TO: {', '.join(available_moves)}

RESOURCES HERE: {', '.join(self.world.locations[self.current_location]['resources'])}
"""
        
        # Full prompt
        prompt = f"""You are {self.name.replace('_', ' ').title()}.

YOUR MEMORIES:
{'; '.join(memories[-5:])}

{spatial_info}

SITUATION: {situation}

Respond with a JSON action:
{{
  "thought": "your internal thought",
  "action": "what you do",
  "move_to": "location to go to (or null to stay)",
  "interact_with": "person to interact with (or null)",
  "uses_resource": "resource you use (or null)"
}}"""
        
        return prompt

def run_spatial_narrative():
    """Run narrative with spatial awareness"""
    
    print("=== SPATIAL NARRATIVE SYSTEM ===")
    print("Characters navigate real spaces and interact\n")
    
    world = SpatialWorld()
    bedrock_client = bedrock
    ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'
    
    # Spatial scenarios
    scenarios = [
        ('alex_chen', 'Eviction notice says you must leave by noon'),
        ('tyler_chen', 'You want to check on your new property investment'),
        ('dorothy_jackson', 'You need groceries but worry about spending money'),
        ('alex_chen', 'You need wifi to submit freelance work for pay'),
        ('brittany_torres', 'Gas light comes on, you have a delivery request'),
        ('maria_gonzalez', 'Shift ended, exhausted, kids need pickup'),
        ('jamie_rodriguez', 'Alex walks in looking desperate')
    ]
    
    total_cost = 0
    memories_table = dynamodb.Table('agentic-demo-character-memories')
    
    for turn, (character_name, situation) in enumerate(scenarios, 1):
        print(f"\n--- Turn {turn}: {character_name.upper()} ---")
        print(f"Location: {world.character_locations[character_name]}")
        print(f"Situation: {situation}")
        
        # Load memories
        try:
            char_data = memories_table.get_item(Key={'characterId': character_name})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = ['Just starting out']
            char_data = {'characterId': character_name, 'memories': memories}
            
        # Create spatial character
        character = SpatialCharacter(character_name, world)
        
        # Get AI decision with spatial awareness
        prompt = character.get_spatial_prompt(situation, memories)
        
        try:
            response = bedrock_client.invoke_model(
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
            response_text = result['content'][0]['text']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                decision = {
                    'thought': response_text[:100],
                    'action': response_text[:100],
                    'move_to': None
                }
                
            print(f"Thought: {decision.get('thought', 'Thinking...')[:80]}")
            print(f"Action: {decision.get('action', 'Frozen')[:80]}")
            
            # Process movement
            if decision.get('move_to') and decision['move_to'] != character.current_location:
                move_result = world.move_character(
                    character_name,
                    character.current_location,
                    decision['move_to']
                )
                print(f"Moving: {move_result['from']} → {move_result['to']} ({move_result['travel_time']}min)")
                
                # Update memory with movement
                memories.append(f"Moved to {decision['move_to']}: {decision['action'][:40]}")
            else:
                memories.append(f"At {character.current_location}: {decision['action'][:40]}")
                
            # Process interactions
            if decision.get('interact_with'):
                other = decision['interact_with']
                if other in world.locations[character.current_location]['current_occupants']:
                    print(f"Interacting with: {other}")
                    # Could trigger reaction from other character
                    
            # Save updated memories
            char_data['memories'] = memories
            memories_table.put_item(Item=char_data)
            
            # Send to telemetry
            try:
                ws = websocket.WebSocket()
                ws.connect(ws_url)
                msg = {
                    'goal': f"[{character_name}] at {character.current_location}",
                    'action': decision.get('action', 'Thinking')[:80],
                    'rationale': decision.get('thought', '')[:80],
                    'result': f"Move: {decision.get('move_to', 'staying')}"
                }
                ws.send(json.dumps(msg))
                ws.close()
            except:
                pass
                
            # Track cost
            cost = 0.003 * 0.3 + 0.015 * 0.15  # Larger prompts/responses
            total_cost += cost
            
            time.sleep(2)
            
        except Exception as e:
            print(f"Error: {e}")
            continue
            
    print(f"\n=== SPATIAL NARRATIVE COMPLETE ===")
    print(f"Total cost: ${total_cost:.4f}")
    print("\nFinal locations:")
    for char, loc in world.character_locations.items():
        if char in [s[0] for s in scenarios]:
            others = [o for o in world.locations[loc]['current_occupants'] if o != char]
            print(f"  {char}: {loc} {f'(with {others})' if others else '(alone)'}")

if __name__ == "__main__":
    run_spatial_narrative()
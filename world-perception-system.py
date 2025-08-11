#!/usr/bin/env python3
"""
World Perception System - How characters see and understand their environment
Including multi-character interactions when they meet
"""

import json
from typing import Dict, List, Optional, Set
from datetime import datetime
from decimal import Decimal
import random

class WorldPerception:
    """What characters can perceive about their environment"""
    
    def __init__(self):
        self.locations = {}
        self.characters_present = {}
        self.objects_visible = {}
        self.sounds = {}
        self.smells = {}
        self.social_atmosphere = {}
    
    def generate_perception_data(self, character_id: str, location: str, economic_tier: str) -> Dict:
        """Generate what a character perceives based on their position"""
        
        perception = {
            'timestamp': datetime.now().isoformat(),
            'character_id': character_id,
            'location': location,
            'immediate_surroundings': self.get_immediate_view(location, economic_tier),
            'characters_nearby': self.get_visible_characters(location, character_id),
            'available_objects': self.get_interactable_objects(location, economic_tier),
            'ambient_conditions': self.get_ambient_conditions(location),
            'social_cues': self.get_social_cues(location, economic_tier),
            'possible_actions': self.get_available_actions(location, economic_tier)
        }
        
        return perception

    def get_immediate_view(self, location: str, economic_tier: str) -> Dict:
        """What the character sees around them"""
        
        views = {
            'public_library': {
                'poor': {
                    'description': 'Fluorescent lights flicker. Other homeless people guard power outlets. Security guard watches suspiciously.',
                    'details': [
                        'Worn carpet with stains',
                        'All comfortable chairs taken by housed people', 
                        'Sign: "2 hour computer limit"',
                        'Other exhausted faces hunched over laptops',
                        'Security camera pointed at you'
                    ],
                    'mood': 'tense_survival'
                },
                'wealthy': {
                    'description': 'Quiet study space with natural light. Plenty of available seating.',
                    'details': [
                        'Clean, organized shelves',
                        'Available private study rooms',
                        'Friendly librarian offers help',
                        'New computers available'
                    ],
                    'mood': 'productive_calm'
                }
            },
            'coffee_shop': {
                'poor': {
                    'description': 'You are behind the counter. Steam burns your hands. Customers look through you.',
                    'details': [
                        'Sticky floor you just mopped',
                        'Broken AC, sweat dripping',
                        'Manager watching from office',
                        'Line of impatient customers',
                        '$4 in tip jar (shared with 3 others)'
                    ],
                    'mood': 'exhausting_service'
                },
                'wealthy': {
                    'description': 'Artisanal coffee shop with exposed brick. Your reserved table awaits.',
                    'details': [
                        'Barista knows your name and order',
                        'Other tech workers on MacBooks',
                        'Background jazz',
                        'Today\'s special: $18 adaptogenic latte'
                    ],
                    'mood': 'comfortable_networking'
                }
            },
            'food_bank': {
                'poor': {
                    'description': 'Long line of tired faces. Smell of old vegetables. Volunteers avoid eye contact.',
                    'details': [
                        '45 minute wait',
                        'Everyone avoiding eye contact',
                        'Security guard by door',
                        'Sign: "One bag per family"',
                        'Expired bread, dented cans available'
                    ],
                    'mood': 'desperate_shame'
                },
                'wealthy': {
                    'description': 'You are here for a photo op. Your publicist arranges good lighting.',
                    'details': [
                        'Volunteers excited to see you',
                        'Photographer captures your "generosity"',
                        'You don\'t notice the actual hunger',
                        'Will leave in 10 minutes'
                    ],
                    'mood': 'performative_charity'
                }
            }
        }
        
        return views.get(location, {}).get(economic_tier, {
            'description': 'An undefined space',
            'details': [],
            'mood': 'neutral'
        })
    
    def get_visible_characters(self, location: str, observer_id: str) -> List[Dict]:
        """Which other characters are present and what they're doing"""
        
        # Simulate who might be at each location
        character_locations = {
            'public_library': ['alex_chen', 'sarah_kim', 'other_homeless_1', 'student_1'],
            'coffee_shop': ['jamie_rodriguez', 'tyler_chen', 'customer_1', 'customer_2'],
            'food_bank': ['alex_chen', 'maria_gonzalez', 'brittany_torres', 'volunteer_1'],
            'tech_office': ['tyler_chen', 'ashley_kim', 'coworker_1', 'manager_1'],
            'luxury_apartment': ['madison_worthington', 'richard_blackstone', 'assistant_1']
        }
        
        present = character_locations.get(location, [])
        visible = []
        
        for char_id in present:
            if char_id != observer_id:
                visible.append(self.describe_character_appearance(char_id))
        
        return visible
    
    def describe_character_appearance(self, character_id: str) -> Dict:
        """How a character appears to others"""
        
        appearances = {
            'alex_chen': {
                'id': 'alex_chen',
                'appearance': 'Exhausted person in worn hoodie, hunched over old laptop',
                'animation': 'typing_frantically',
                'emotional_state': 'desperate',
                'held_items': ['cracked_laptop', 'empty_water_bottle'],
                'notable': 'Dark circles under eyes, slight tremor in hands'
            },
            'tyler_chen': {
                'id': 'tyler_chen',
                'appearance': 'Well-groomed tech worker in Patagonia vest',
                'animation': 'confident_typing',
                'emotional_state': 'satisfied',
                'held_items': ['latest_macbook', 'nitro_coldbrew'],
                'notable': 'Checking phone frequently, probably stocks'
            },
            'madison_worthington': {
                'id': 'madison_worthington',
                'appearance': 'Perfectly styled in designer athleisure',
                'animation': 'scrolling_instagram',
                'emotional_state': 'blissfully_unaware',
                'held_items': ['iphone_15_pro', 'green_juice'],
                'notable': 'Takes selfie every few minutes'
            },
            'maria_gonzalez': {
                'id': 'maria_gonzalez',
                'appearance': 'Nurse in faded scrubs, visibly exhausted',
                'animation': 'waiting_anxiously',
                'emotional_state': 'stressed',
                'held_items': ['hospital_badge', 'cheap_phone'],
                'notable': 'Checking time constantly, needs to return to shift'
            }
        }
        
        return appearances.get(character_id, {
            'id': character_id,
            'appearance': 'Another person',
            'animation': 'idle',
            'emotional_state': 'unknown'
        })

class CharacterEncounter:
    """Handle when two or more characters meet"""
    
    def __init__(self):
        self.active_encounters = {}
        self.encounter_history = []
        self.relationship_matrix = {}
    
    def detect_encounter(self, location: str, characters: List[str]) -> Optional[Dict]:
        """Check if characters are close enough to interact"""
        
        if len(characters) < 2:
            return None
        
        # Calculate social dynamics
        encounter = {
            'id': f"encounter_{datetime.now().timestamp()}",
            'location': location,
            'participants': characters,
            'type': self.determine_encounter_type(characters),
            'timestamp': datetime.now().isoformat()
        }
        
        return encounter
    
    def determine_encounter_type(self, characters: List[str]) -> str:
        """What kind of encounter is this?"""
        
        char_types = {
            'alex_chen': 'poor',
            'jamie_rodriguez': 'poor',
            'maria_gonzalez': 'poor',
            'tyler_chen': 'wealthy',
            'madison_worthington': 'ultra_wealthy',
            'ashley_kim': 'middle',
            'sarah_kim': 'poor'
        }
        
        tiers = [char_types.get(c, 'unknown') for c in characters]
        
        if 'poor' in tiers and 'ultra_wealthy' in tiers:
            return 'class_collision'
        elif all(t == 'poor' for t in tiers):
            return 'solidarity'
        elif all(t in ['wealthy', 'ultra_wealthy'] for t in tiers):
            return 'networking'
        else:
            return 'mixed'
    
    def generate_interaction(self, encounter: Dict) -> List[Dict]:
        """Generate interaction between characters"""
        
        interactions = []
        encounter_type = encounter['type']
        participants = encounter['participants']
        
        if encounter_type == 'class_collision':
            interactions.extend(self.class_collision_interaction(participants))
        elif encounter_type == 'solidarity':
            interactions.extend(self.solidarity_interaction(participants))
        elif encounter_type == 'networking':
            interactions.extend(self.networking_interaction(participants))
        
        return interactions
    
    def class_collision_interaction(self, participants: List[str]) -> List[Dict]:
        """When poor and wealthy meet"""
        
        interactions = []
        
        # Example: Alex meets Madison at library
        if 'alex_chen' in participants and 'madison_worthington' in participants:
            interactions = [
                {
                    'character': 'madison_worthington',
                    'action': 'notice',
                    'target': 'alex_chen',
                    'perception': 'Ugh, why do they let these people in here?',
                    'command': {
                        'action': 'look_at',
                        'params': {'target': 'alex_chen', 'duration': 0.5}
                    }
                },
                {
                    'character': 'madison_worthington',
                    'action': 'avoid',
                    'target': 'alex_chen',
                    'perception': 'Moving to a different area',
                    'command': {
                        'action': 'walk_to',
                        'params': {'location': 'far_table', 'speed': 'quick'}
                    }
                },
                {
                    'character': 'alex_chen',
                    'action': 'notice',
                    'target': 'madison_worthington',
                    'perception': 'Rich person disgusted by my existence',
                    'command': {
                        'action': 'set_facial_expression',
                        'params': {'emotion': 'shame', 'intensity': 0.8}
                    }
                },
                {
                    'character': 'alex_chen',
                    'action': 'shrink',
                    'target': 'self',
                    'perception': 'Making myself smaller, less visible',
                    'command': {
                        'action': 'play_animation',
                        'params': {'name': 'hunch_shoulders', 'loop': False}
                    }
                }
            ]
        
        # Example: Tyler sees Maria at coffee shop
        elif 'tyler_chen' in participants and 'maria_gonzalez' in participants:
            interactions = [
                {
                    'character': 'tyler_chen',
                    'action': 'order',
                    'target': 'maria_gonzalez',
                    'perception': 'Another service worker, irrelevant',
                    'command': {
                        'action': 'talk_to',
                        'params': {'target': 'barista', 'message': 'Oat cortado, make it quick'}
                    }
                },
                {
                    'character': 'maria_gonzalez',
                    'action': 'wait',
                    'target': 'line',
                    'perception': 'He cut in front. Too tired to argue.',
                    'command': {
                        'action': 'play_animation',
                        'params': {'name': 'exhausted_sigh', 'loop': False}
                    }
                }
            ]
        
        return interactions
    
    def solidarity_interaction(self, participants: List[str]) -> List[Dict]:
        """When struggling people meet and support each other"""
        
        interactions = []
        
        # Alex and Jamie meet at library
        if 'alex_chen' in participants and 'jamie_rodriguez' in participants:
            interactions = [
                {
                    'character': 'jamie_rodriguez',
                    'action': 'recognize',
                    'target': 'alex_chen',
                    'perception': 'Alex looks worse than last week',
                    'command': {
                        'action': 'walk_to',
                        'params': {'location': 'alex_table', 'speed': 'tired'}
                    }
                },
                {
                    'character': 'jamie_rodriguez',
                    'action': 'share',
                    'target': 'alex_chen',
                    'perception': 'I have half a sandwich from set',
                    'command': {
                        'action': 'give_item',
                        'params': {'item': 'half_sandwich', 'target': 'alex_chen'}
                    }
                },
                {
                    'character': 'alex_chen',
                    'action': 'grateful',
                    'target': 'jamie_rodriguez',
                    'perception': 'Jamie saved me today',
                    'command': {
                        'action': 'gesture',
                        'params': {'type': 'grateful_nod'}
                    }
                },
                {
                    'character': 'alex_chen',
                    'action': 'share_info',
                    'target': 'jamie_rodriguez',
                    'perception': 'Library has new security, be careful',
                    'command': {
                        'action': 'talk_to',
                        'params': {'target': 'jamie', 'message': 'Security kicks people out after 2 hours now'}
                    }
                }
            ]
        
        return interactions
    
    def networking_interaction(self, participants: List[str]) -> List[Dict]:
        """When wealthy people meet to maintain power"""
        
        interactions = []
        
        if 'tyler_chen' in participants and 'richard_blackstone' in participants:
            interactions = [
                {
                    'character': 'tyler_chen',
                    'action': 'approach',
                    'target': 'richard_blackstone',
                    'perception': 'Opportunity to pitch my startup',
                    'command': {
                        'action': 'walk_to',
                        'params': {'location': 'richard', 'speed': 'confident'}
                    }
                },
                {
                    'character': 'tyler_chen',
                    'action': 'pitch',
                    'target': 'richard_blackstone',
                    'perception': 'Rental property automation platform',
                    'command': {
                        'action': 'gesture',
                        'params': {'type': 'enthusiastic_presentation'}
                    }
                },
                {
                    'character': 'richard_blackstone',
                    'action': 'evaluate',
                    'target': 'tyler_chen',
                    'perception': 'Could help evict tenants faster',
                    'command': {
                        'action': 'gesture',
                        'params': {'type': 'calculating_nod'}
                    }
                }
            ]
        
        return interactions

def simulate_world_perception():
    """Simulate how different characters perceive the same location"""
    
    print("=" * 70)
    print("WORLD PERCEPTION SIMULATION")
    print("=" * 70)
    
    perception = WorldPerception()
    location = 'public_library'
    
    print(f"\n📍 Location: {location.upper()}")
    print("Same space, different realities:\n")
    
    # Alex's perception
    print("ALEX CHEN'S VIEW (Poor):")
    print("-" * 40)
    alex_view = perception.get_immediate_view(location, 'poor')
    print(f"What Alex sees: {alex_view['description']}")
    print("Details noticed:")
    for detail in alex_view['details']:
        print(f"  • {detail}")
    print(f"Emotional state: {alex_view['mood']}")
    
    print("\n" + "=" * 40 + "\n")
    
    # Madison's perception
    print("MADISON WORTHINGTON'S VIEW (Ultra-wealthy):")
    print("-" * 40)
    madison_view = perception.get_immediate_view(location, 'wealthy')
    print(f"What Madison sees: {madison_view['description']}")
    print("Details noticed:")
    for detail in madison_view['details']:
        print(f"  • {detail}")
    print(f"Emotional state: {madison_view['mood']}")

def simulate_character_encounter():
    """Simulate when characters meet"""
    
    print("\n" + "=" * 70)
    print("CHARACTER ENCOUNTER SIMULATION")
    print("=" * 70)
    
    encounter_system = CharacterEncounter()
    
    # Scenario 1: Class collision
    print("\n🔥 ENCOUNTER 1: Class Collision at Library")
    print("-" * 40)
    
    encounter = encounter_system.detect_encounter(
        'public_library',
        ['alex_chen', 'madison_worthington']
    )
    
    interactions = encounter_system.generate_interaction(encounter)
    
    for i, interaction in enumerate(interactions, 1):
        print(f"\n{i}. {interaction['character'].upper()}")
        print(f"   Action: {interaction['action']}")
        print(f"   Perception: {interaction['perception']}")
        print(f"   Avatar: {interaction['command']['action']}({interaction['command']['params']})")
    
    # Scenario 2: Solidarity
    print("\n\n💪 ENCOUNTER 2: Solidarity at Library")
    print("-" * 40)
    
    encounter = encounter_system.detect_encounter(
        'public_library',
        ['alex_chen', 'jamie_rodriguez']
    )
    
    interactions = encounter_system.generate_interaction(encounter)
    
    for i, interaction in enumerate(interactions, 1):
        print(f"\n{i}. {interaction['character'].upper()}")
        print(f"   Action: {interaction['action']}")
        print(f"   Perception: {interaction['perception']}")
        print(f"   Avatar: {interaction['command']['action']}({interaction['command']['params']})")

def generate_mcp_world_state():
    """Generate world state that would be sent to characters via MCP"""
    
    print("\n" + "=" * 70)
    print("MCP WORLD STATE MESSAGE")
    print("=" * 70)
    
    world_state = {
        "jsonrpc": "2.0",
        "method": "world.state.update",
        "params": {
            "timestamp": datetime.now().isoformat(),
            "location": "public_library",
            "observer": "alex_chen",
            "perception": {
                "immediate_environment": {
                    "description": "Fluorescent lights flicker. Security guard approaches.",
                    "threat_level": "medium",
                    "comfort_level": "very_low",
                    "available_resources": ["power_outlet", "wifi", "water_fountain"]
                },
                "visible_characters": [
                    {
                        "id": "madison_worthington",
                        "distance": 10,
                        "facing": "away",
                        "activity": "moving_away_disgusted",
                        "threat": "social_shame"
                    },
                    {
                        "id": "jamie_rodriguez",
                        "distance": 30,
                        "facing": "toward",
                        "activity": "approaching_friendly",
                        "resource": "might_share_food"
                    },
                    {
                        "id": "security_guard",
                        "distance": 15,
                        "facing": "toward",
                        "activity": "approaching_suspicious",
                        "threat": "eviction"
                    }
                ],
                "available_actions": [
                    "continue_writing",
                    "pack_and_leave",
                    "approach_jamie",
                    "hide_from_security",
                    "pretend_to_be_student"
                ],
                "sensory_input": {
                    "sounds": ["keyboard_clicks", "whispered_conversation", "security_radio"],
                    "smells": ["old_books", "coffee", "unwashed_clothes"],
                    "temperature": "too_cold",
                    "lighting": "harsh_fluorescent"
                },
                "emotional_atmosphere": {
                    "general_mood": "tense",
                    "toward_observer": "suspicious",
                    "social_acceptance": "barely_tolerated"
                }
            }
        },
        "id": f"world_state_{datetime.now().timestamp()}"
    }
    
    print(json.dumps(world_state, indent=2))
    
    print("\n" + "=" * 70)
    print("CHARACTER AI WOULD PROCESS THIS TO DECIDE:")
    print("=" * 70)
    print("1. Security approaching - pack up or try to look studious?")
    print("2. Jamie might help - approach for food/solidarity?")
    print("3. Madison's disgust - internalize shame or ignore?")
    print("4. Resources available - stay for wifi or leave for safety?")

if __name__ == "__main__":
    simulate_world_perception()
    simulate_character_encounter()
    generate_mcp_world_state()
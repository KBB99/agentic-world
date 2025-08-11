#!/usr/bin/env python3
"""
Unreal Engine Avatar Control System via MCP
Characters send commands through MCP to control their avatars in real-time
"""

import json
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

# Avatar control commands that characters can issue
AVATAR_COMMANDS = {
    'movement': {
        'walk_to': {
            'params': ['location', 'speed'],
            'example': 'walk_to(library, normal)',
            'description': 'Navigate avatar to location'
        },
        'run_to': {
            'params': ['location'],
            'example': 'run_to(coffee_shop)',
            'description': 'Run to location (uses more energy)'
        },
        'turn_to': {
            'params': ['direction_degrees'],
            'example': 'turn_to(90)',
            'description': 'Rotate avatar to face direction'
        },
        'look_at': {
            'params': ['target', 'duration'],
            'example': 'look_at(other_character, 2.0)',
            'description': 'Look at target for duration'
        },
        'sit_on': {
            'params': ['object'],
            'example': 'sit_on(bench)',
            'description': 'Sit on furniture/ground'
        },
        'stand_up': {
            'params': [],
            'example': 'stand_up()',
            'description': 'Stand from sitting position'
        }
    },
    
    'interaction': {
        'pickup': {
            'params': ['object'],
            'example': 'pickup(coffee_cup)',
            'description': 'Pick up an object'
        },
        'drop': {
            'params': ['object'],
            'example': 'drop(coffee_cup)',
            'description': 'Drop held object'
        },
        'use': {
            'params': ['object', 'action'],
            'example': 'use(laptop, type)',
            'description': 'Use an object'
        },
        'open': {
            'params': ['object'],
            'example': 'open(door)',
            'description': 'Open door/container'
        },
        'talk_to': {
            'params': ['character', 'message'],
            'example': 'talk_to(jamie, "Can I crash here tonight?")',
            'description': 'Speak to another character'
        },
        'gesture': {
            'params': ['type'],
            'example': 'gesture(wave)',
            'description': 'Perform gesture animation'
        }
    },
    
    'emotion': {
        'set_facial_expression': {
            'params': ['emotion', 'intensity'],
            'example': 'set_facial_expression(worried, 0.8)',
            'description': 'Change facial expression'
        },
        'play_animation': {
            'params': ['animation_name', 'loop'],
            'example': 'play_animation(exhausted_idle, true)',
            'description': 'Play character animation'
        },
        'set_posture': {
            'params': ['posture_type'],
            'example': 'set_posture(slouched)',
            'description': 'Change body posture'
        }
    },
    
    'needs': {
        'eat': {
            'params': ['food_item'],
            'example': 'eat(cheap_ramen)',
            'description': 'Consume food (affects hunger)'
        },
        'drink': {
            'params': ['drink_item'],
            'example': 'drink(tap_water)',
            'description': 'Drink (affects thirst)'
        },
        'sleep': {
            'params': ['location', 'duration'],
            'example': 'sleep(library_chair, 2)',
            'description': 'Sleep/rest at location'
        },
        'work': {
            'params': ['activity', 'duration'],
            'example': 'work(write_article, 3)',
            'description': 'Perform work activity'
        }
    }
}

class UnrealAvatarController:
    """Translates character decisions into Unreal Engine commands"""
    
    def __init__(self, character_id: str, economic_tier: str):
        self.character_id = character_id
        self.economic_tier = economic_tier
        self.current_location = None
        self.current_animation = 'idle'
        self.held_objects = []
        self.energy = 100
        self.needs = {
            'hunger': 50,
            'thirst': 50,
            'exhaustion': 30,
            'stress': 70 if economic_tier == 'poor' else 30
        }
    
    def generate_command_json(self, action: str, params: Dict) -> Dict:
        """Generate JSON command for Unreal Engine"""
        return {
            'timestamp': datetime.now().isoformat(),
            'character_id': self.character_id,
            'command_type': 'avatar_control',
            'action': action,
            'parameters': params,
            'current_state': {
                'location': self.current_location,
                'animation': self.current_animation,
                'held_objects': self.held_objects,
                'needs': self.needs
            }
        }
    
    def validate_action(self, action: str, context: Dict) -> bool:
        """Check if character can perform action based on their situation"""
        
        # Poor characters have limitations
        if self.economic_tier == 'poor':
            if action == 'eat' and context.get('food_item') not in ['cheap_ramen', 'free_sample', 'dumpster_food']:
                return False  # Can't afford good food
            if action == 'use' and context.get('object') == 'private_office':
                return False  # No access to private spaces
            if action == 'sleep' and context.get('location') in ['hotel', 'apartment']:
                return False  # Can't afford proper accommodation
        
        # Energy constraints
        if action in ['run_to', 'work'] and self.energy < 20:
            return False  # Too exhausted
        
        return True

class CharacterAvatarBehavior:
    """Behavioral patterns based on character personality and situation"""
    
    def __init__(self, character_data: Dict):
        self.character = character_data
        self.personality = character_data.get('personality', {})
        self.current_goal = None
        self.action_history = []
    
    def decide_next_action(self, world_state: Dict) -> Dict:
        """AI decides next avatar action based on personality and world state"""
        
        actions = []
        
        # Alex Chen - exhausted writer behavior
        if self.character['id'] == 'alex_chen':
            hour = datetime.now().hour
            
            if hour < 8:  # Early morning
                actions.append({
                    'action': 'sleep',
                    'params': {'location': 'library_steps', 'duration': 1},
                    'reason': 'Sleeping rough before library opens'
                })
            elif hour < 12:  # Morning
                actions.append({
                    'action': 'walk_to',
                    'params': {'location': 'library', 'speed': 'slow'},
                    'reason': 'Heading to library for free wifi'
                })
                actions.append({
                    'action': 'use',
                    'params': {'object': 'laptop', 'action': 'write'},
                    'reason': 'Writing content mill articles for $6'
                })
            elif self.character['needs']['hunger'] > 70:
                actions.append({
                    'action': 'walk_to',
                    'params': {'location': 'food_bank', 'speed': 'normal'},
                    'reason': 'Getting free food - too broke to buy'
                })
            
            # Stress animations
            if self.character['stress'] > 80:
                actions.append({
                    'action': 'play_animation',
                    'params': {'animation_name': 'head_in_hands', 'loop': False},
                    'reason': 'Overwhelming stress about money'
                })
        
        # Tyler Chen - confident tech PM behavior  
        elif self.character['id'] == 'tyler_chen':
            if hour < 9:
                actions.append({
                    'action': 'walk_to',
                    'params': {'location': 'tech_office', 'speed': 'confident'},
                    'reason': 'Arriving at tech job'
                })
            elif hour < 17:
                actions.append({
                    'action': 'use',
                    'params': {'object': 'standing_desk', 'action': 'work'},
                    'reason': 'Managing sprint, checking stocks on second monitor'
                })
            else:
                actions.append({
                    'action': 'walk_to',
                    'params': {'location': 'craft_brewery', 'speed': 'casual'},
                    'reason': 'Networking over $18 craft beers'
                })
        
        # Madison Worthington - oblivious wealth behavior
        elif self.character['id'] == 'madison_worthington':
            actions.append({
                'action': 'gesture',
                'params': {'type': 'dismissive_wave'},
                'reason': 'Dismissing concerns about housing crisis'
            })
            actions.append({
                'action': 'use',
                'params': {'object': 'phone', 'action': 'instagram'},
                'reason': 'Posting about mindfulness while people suffer'
            })
        
        return actions[0] if actions else {'action': 'idle', 'params': {}}

def generate_mcp_avatar_command(character_id: str, action: str, params: Dict) -> str:
    """Generate MCP command string for Unreal Engine"""
    
    command = {
        'jsonrpc': '2.0',
        'method': 'unreal.avatar.control',
        'params': {
            'character_id': character_id,
            'action': action,
            'parameters': params,
            'timestamp': datetime.now().isoformat()
        },
        'id': f"{character_id}_{datetime.now().timestamp()}"
    }
    
    return json.dumps(command)

# Example: Alex navigating their desperate day
def simulate_alex_avatar_control():
    """Simulate Alex's avatar movements through their struggling day"""
    
    print("=== ALEX CHEN AVATAR CONTROL SIMULATION ===\n")
    
    controller = UnrealAvatarController('alex_chen', 'poor')
    controller.current_location = 'street_corner'
    controller.energy = 35  # Exhausted
    controller.needs['hunger'] = 85  # Very hungry
    
    # Morning routine
    commands = []
    
    # Wake up on street
    commands.append(controller.generate_command_json(
        'play_animation',
        {'animation_name': 'wake_up_rough', 'loop': False}
    ))
    
    # Check phone for gig notifications
    commands.append(controller.generate_command_json(
        'use',
        {'object': 'cracked_phone', 'action': 'check_gigs'}
    ))
    
    # Walk to library (can't afford transit)
    commands.append(controller.generate_command_json(
        'walk_to',
        {'location': 'public_library', 'speed': 'tired'}
    ))
    
    # Facial expression of worry
    commands.append(controller.generate_command_json(
        'set_facial_expression',
        {'emotion': 'anxious', 'intensity': 0.9}
    ))
    
    # Sit and work
    commands.append(controller.generate_command_json(
        'sit_on',
        {'object': 'library_chair'}
    ))
    
    commands.append(controller.generate_command_json(
        'use',
        {'object': 'old_laptop', 'action': 'write_articles'}
    ))
    
    # Print commands that would be sent to Unreal
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd['action']}:")
        print(f"   Params: {cmd['parameters']}")
        print(f"   Energy: {controller.energy}")
        print(f"   Hunger: {controller.needs['hunger']}")
        print()
    
    print("\nMCP COMMAND FOR UNREAL:")
    print("-" * 50)
    mcp_cmd = generate_mcp_avatar_command(
        'alex_chen',
        'walk_to',
        {'location': 'public_library', 'speed': 'tired'}
    )
    print(json.dumps(json.loads(mcp_cmd), indent=2))

# Run simulation
if __name__ == "__main__":
    simulate_alex_avatar_control()
    
    print("\n" + "="*60)
    print("AVAILABLE AVATAR COMMANDS")
    print("="*60)
    
    for category, commands in AVATAR_COMMANDS.items():
        print(f"\n{category.upper()}:")
        for cmd, details in commands.items():
            print(f"  • {cmd}: {details['example']}")
            print(f"    {details['description']}")
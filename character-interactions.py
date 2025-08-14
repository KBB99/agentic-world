#!/usr/bin/env python3
"""
Character-to-Character Interaction System
Enables AI characters to communicate, collaborate, conflict, and form relationships
"""

import json
import boto3
import random
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Tuple, Optional

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# DynamoDB tables
AGENTS_TABLE = 'agentic-demo-agent-contexts'
RELATIONSHIPS_TABLE = 'agentic-demo-relationships'
INTERACTIONS_TABLE = 'agentic-demo-interactions'

class CharacterInteractionSystem:
    def __init__(self):
        self.agents = {}
        self.relationships = {}  # Stores relationship history between characters
        self.load_agents()
        self.load_relationships()
        
    def load_agents(self):
        """Load all agents from DynamoDB"""
        try:
            table = dynamodb.Table(AGENTS_TABLE)
            response = table.scan()
            
            for item in response.get('Items', []):
                agent_id = item['agentId']
                self.agents[agent_id] = item
        except Exception as e:
            print(f"Error loading agents: {e}")
    
    def load_relationships(self):
        """Load existing relationships between characters"""
        try:
            table = dynamodb.Table(RELATIONSHIPS_TABLE)
            response = table.scan()
            
            for item in response.get('Items', []):
                key = f"{item['character1']}_{item['character2']}"
                self.relationships[key] = item
        except:
            # Table might not exist yet
            pass
    
    def get_relationship_status(self, char1: str, char2: str) -> Dict:
        """Get the relationship status between two characters"""
        key1 = f"{char1}_{char2}"
        key2 = f"{char2}_{char1}"
        
        if key1 in self.relationships:
            return self.relationships[key1]
        elif key2 in self.relationships:
            return self.relationships[key2]
        else:
            # No existing relationship
            return {
                'trust': 0,
                'affinity': 0,
                'history': [],
                'type': 'stranger'
            }
    
    def determine_interaction_type(self, char1: Dict, char2: Dict, location: str) -> str:
        """Determine what type of interaction should occur"""
        money1 = float(char1.get('money', 100))
        money2 = float(char2.get('money', 100))
        
        # Economic disparity interactions
        if abs(money1 - money2) > 10000:
            if money1 < 100 or money2 < 100:
                return 'class_tension'
            else:
                return 'class_disconnect'
        
        # Both struggling
        if money1 < 100 and money2 < 100:
            interactions = ['solidarity', 'resource_sharing', 'commiseration', 'collaboration']
            return random.choice(interactions)
        
        # Professional interactions
        if 'tech' in location or 'office' in location:
            return 'professional'
        
        # Coffee shop interactions
        if 'coffee' in location:
            return 'casual_encounter'
        
        # Library interactions
        if 'library' in location:
            if money1 < 100 or money2 < 100:
                return 'quiet_desperation'
            else:
                return 'intellectual'
        
        return 'neutral'
    
    def generate_interaction(self, char1_id: str, char2_id: str, 
                           interaction_type: str, location: str) -> Dict:
        """Generate an AI-driven interaction between two characters"""
        
        char1 = self.agents[char1_id]
        char2 = self.agents[char2_id]
        relationship = self.get_relationship_status(char1_id, char2_id)
        
        # Build prompt for Claude
        prompt = f"""You are simulating an interaction between two characters:

Character 1: {char1_id}
- Background: {char1.get('background', 'Unknown')}
- Personality: {char1.get('personality', 'Unknown')}
- Current situation: {char1.get('current_situation', 'Unknown')}
- Money: ${char1.get('money', 0)}
- Current state: {char1.get('current_state', 'normal')}

Character 2: {char2_id}
- Background: {char2.get('background', 'Unknown')}
- Personality: {char2.get('personality', 'Unknown')}
- Current situation: {char2.get('current_situation', 'Unknown')}
- Money: ${char2.get('money', 0)}
- Current state: {char2.get('current_state', 'normal')}

Location: {location}
Interaction type: {interaction_type}
Previous relationship: {relationship.get('type', 'strangers')}
Trust level: {relationship.get('trust', 0)}
Previous interactions: {len(relationship.get('history', []))}

Generate a realistic interaction between these characters. Consider their economic positions, personalities, and current situations.

Respond with a JSON object containing:
- dialogue: Array of exchanges between characters (at least 2-3 exchanges)
- outcome: What happens as a result
- emotional_impact: How each character feels afterward
- relationship_change: How their relationship changes
- resource_exchange: Any money/resources exchanged (if applicable)
- memory_for_char1: What character 1 will remember
- memory_for_char2: What character 2 will remember
"""

        try:
            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            interaction_text = response_body['content'][0]['text']
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', interaction_text, re.DOTALL)
            if json_match:
                interaction = json.loads(json_match.group())
            else:
                # Fallback interaction
                interaction = self.get_fallback_interaction(char1_id, char2_id, interaction_type)
            
            return interaction
            
        except Exception as e:
            print(f"Error generating interaction: {e}")
            return self.get_fallback_interaction(char1_id, char2_id, interaction_type)
    
    def get_fallback_interaction(self, char1_id: str, char2_id: str, 
                                interaction_type: str) -> Dict:
        """Fallback interaction when AI fails"""
        
        char1 = self.agents[char1_id]
        char2 = self.agents[char2_id]
        money1 = float(char1.get('money', 100))
        money2 = float(char2.get('money', 100))
        
        if interaction_type == 'solidarity':
            return {
                'dialogue': [
                    {char1_id: "Rough day?"},
                    {char2_id: "You know it. You too?"},
                    {char1_id: "Yeah. We'll get through this."}
                ],
                'outcome': 'Mutual support and understanding',
                'emotional_impact': {
                    char1_id: 'slightly less alone',
                    char2_id: 'slightly less alone'
                },
                'relationship_change': {'trust': 5, 'affinity': 5},
                'resource_exchange': None,
                'memory_for_char1': f"Found solidarity with {char2_id}",
                'memory_for_char2': f"Found solidarity with {char1_id}"
            }
        
        elif interaction_type == 'class_tension':
            wealthy = char1_id if money1 > money2 else char2_id
            poor = char2_id if money1 > money2 else char1_id
            
            return {
                'dialogue': [
                    {wealthy: "Excuse me, you're in my way."},
                    {poor: "There's plenty of room."},
                    {wealthy: "Not for everyone, apparently."}
                ],
                'outcome': 'Uncomfortable class-based tension',
                'emotional_impact': {
                    wealthy: 'annoyed',
                    poor: 'humiliated and angry'
                },
                'relationship_change': {'trust': -10, 'affinity': -10},
                'resource_exchange': None,
                'memory_for_char1': f"Unpleasant encounter with {char2_id}",
                'memory_for_char2': f"Felt dismissed by {char1_id}"
            }
        
        elif interaction_type == 'resource_sharing':
            giver = char1_id if money1 > money2 else char2_id
            receiver = char2_id if money1 > money2 else char1_id
            amount = min(5, money1 if giver == char1_id else money2)
            
            return {
                'dialogue': [
                    {giver: "Hey, you look like you could use this."},
                    {receiver: "I... thank you. I'll pay you back."},
                    {giver: "Don't worry about it. We look out for each other."}
                ],
                'outcome': f"{giver} shares ${amount} with {receiver}",
                'emotional_impact': {
                    giver: 'generous despite struggles',
                    receiver: 'grateful but ashamed'
                },
                'relationship_change': {'trust': 15, 'affinity': 10},
                'resource_exchange': {
                    'from': giver,
                    'to': receiver,
                    'amount': amount
                },
                'memory_for_char1': f"Helped {char2_id} when they needed it",
                'memory_for_char2': f"{char1_id} showed unexpected kindness"
            }
        
        else:
            return {
                'dialogue': [
                    {char1_id: "Hey."},
                    {char2_id: "Hey."}
                ],
                'outcome': 'Brief acknowledgment',
                'emotional_impact': {
                    char1_id: 'neutral',
                    char2_id: 'neutral'
                },
                'relationship_change': {'trust': 1, 'affinity': 0},
                'resource_exchange': None,
                'memory_for_char1': f"Saw {char2_id}",
                'memory_for_char2': f"Saw {char1_id}"
            }
    
    def apply_interaction_effects(self, char1_id: str, char2_id: str, 
                                 interaction: Dict):
        """Apply the effects of an interaction to both characters"""
        
        # Update memories
        if char1_id in self.agents:
            if 'memories' not in self.agents[char1_id]:
                self.agents[char1_id]['memories'] = []
            self.agents[char1_id]['memories'].append(
                f"[{datetime.now().strftime('%I:%M%p')}] {interaction['memory_for_char1']}"
            )
        
        if char2_id in self.agents:
            if 'memories' not in self.agents[char2_id]:
                self.agents[char2_id]['memories'] = []
            self.agents[char2_id]['memories'].append(
                f"[{datetime.now().strftime('%I:%M%p')}] {interaction['memory_for_char2']}"
            )
        
        # Apply resource exchange
        if interaction.get('resource_exchange'):
            exchange = interaction['resource_exchange']
            giver = exchange['from']
            receiver = exchange['to']
            amount = Decimal(str(exchange['amount']))
            
            if giver in self.agents:
                self.agents[giver]['money'] = self.agents[giver].get('money', Decimal('100')) - amount
            if receiver in self.agents:
                self.agents[receiver]['money'] = self.agents[receiver].get('money', Decimal('100')) + amount
        
        # Update relationship
        rel_change = interaction.get('relationship_change', {})
        self.update_relationship(char1_id, char2_id, rel_change, interaction)
        
        # Update emotional states
        emotional_impact = interaction.get('emotional_impact', {})
        if char1_id in self.agents and char1_id in emotional_impact:
            self.agents[char1_id]['current_state'] = emotional_impact[char1_id]
        if char2_id in self.agents and char2_id in emotional_impact:
            self.agents[char2_id]['current_state'] = emotional_impact[char2_id]
    
    def update_relationship(self, char1: str, char2: str, 
                           changes: Dict, interaction: Dict):
        """Update the relationship between two characters"""
        key = f"{char1}_{char2}"
        
        if key not in self.relationships:
            self.relationships[key] = {
                'character1': char1,
                'character2': char2,
                'trust': 0,
                'affinity': 0,
                'history': [],
                'type': 'stranger'
            }
        
        # Apply changes
        self.relationships[key]['trust'] += changes.get('trust', 0)
        self.relationships[key]['affinity'] += changes.get('affinity', 0)
        
        # Add to history
        self.relationships[key]['history'].append({
            'timestamp': datetime.now().isoformat(),
            'type': interaction.get('type', 'interaction'),
            'outcome': interaction.get('outcome', 'unknown')
        })
        
        # Update relationship type based on trust and affinity
        trust = self.relationships[key]['trust']
        affinity = self.relationships[key]['affinity']
        
        if trust > 50 and affinity > 50:
            self.relationships[key]['type'] = 'friend'
        elif trust > 30 and affinity > 30:
            self.relationships[key]['type'] = 'ally'
        elif trust < -30 or affinity < -30:
            self.relationships[key]['type'] = 'adversary'
        elif trust < -50 and affinity < -50:
            self.relationships[key]['type'] = 'enemy'
        elif len(self.relationships[key]['history']) > 1:
            self.relationships[key]['type'] = 'acquaintance'
        else:
            self.relationships[key]['type'] = 'stranger'
        
        # Save to DynamoDB
        self.save_relationship(self.relationships[key])
    
    def save_relationship(self, relationship: Dict):
        """Save relationship to DynamoDB"""
        try:
            table = dynamodb.Table(RELATIONSHIPS_TABLE)
            table.put_item(Item=relationship)
        except:
            # Table might not exist
            pass
    
    def save_interaction(self, interaction: Dict, char1: str, char2: str, location: str):
        """Save interaction details to DynamoDB"""
        try:
            table = dynamodb.Table(INTERACTIONS_TABLE)
            table.put_item(Item={
                'interaction_id': f"{datetime.now().isoformat()}_{char1}_{char2}",
                'timestamp': datetime.now().isoformat(),
                'character1': char1,
                'character2': char2,
                'location': location,
                'interaction': interaction
            })
        except:
            # Table might not exist
            pass
    
    def simulate_location_interactions(self, location: str, characters_present: List[str]):
        """Simulate all interactions at a specific location"""
        
        if len(characters_present) < 2:
            return []
        
        interactions = []
        
        # Randomly select pairs to interact (not everyone talks to everyone)
        num_interactions = min(3, len(characters_present) // 2)
        
        for _ in range(num_interactions):
            if len(characters_present) >= 2:
                # Select two characters
                char1, char2 = random.sample(characters_present, 2)
                
                # Determine interaction type
                interaction_type = self.determine_interaction_type(
                    self.agents[char1], 
                    self.agents[char2], 
                    location
                )
                
                print(f"\n🤝 INTERACTION at {location}: {char1} meets {char2}")
                print(f"   Type: {interaction_type}")
                
                # Generate interaction
                interaction = self.generate_interaction(
                    char1, char2, interaction_type, location
                )
                
                # Show dialogue
                for exchange in interaction.get('dialogue', []):
                    for speaker, line in exchange.items():
                        print(f"   {speaker}: \"{line}\"")
                
                print(f"   Outcome: {interaction['outcome']}")
                
                # Apply effects
                self.apply_interaction_effects(char1, char2, interaction)
                
                # Save interaction
                self.save_interaction(interaction, char1, char2, location)
                
                interactions.append({
                    'participants': [char1, char2],
                    'type': interaction_type,
                    'outcome': interaction['outcome']
                })
        
        return interactions
    
    def get_interaction_network(self) -> Dict:
        """Get the full network of character relationships"""
        network = {
            'nodes': [],
            'edges': []
        }
        
        # Add all characters as nodes
        for agent_id, agent in self.agents.items():
            network['nodes'].append({
                'id': agent_id,
                'money': float(agent.get('money', 0)),
                'state': agent.get('current_state', 'normal')
            })
        
        # Add relationships as edges
        for key, rel in self.relationships.items():
            network['edges'].append({
                'source': rel['character1'],
                'target': rel['character2'],
                'type': rel['type'],
                'trust': rel['trust'],
                'affinity': rel['affinity'],
                'interactions': len(rel['history'])
            })
        
        return network

def demonstrate_interactions():
    """Demonstrate character interactions"""
    
    system = CharacterInteractionSystem()
    
    # Simulate interactions at different locations
    locations = {
        'public_library': ['alex_chen', 'maria_gonzalez', 'brandon_walsh'],
        'coffee_shop': ['jamie_rodriguez', 'ashley_kim'],
        'luxury_apartment': ['victoria_sterling', 'madison_worthington']
    }
    
    print("="*80)
    print("CHARACTER INTERACTION DEMONSTRATION")
    print("="*80)
    
    for location, characters in locations.items():
        if len(characters) >= 2:
            print(f"\n📍 Location: {location}")
            system.simulate_location_interactions(location, characters)
    
    # Show relationship network
    print("\n" + "="*80)
    print("RELATIONSHIP NETWORK")
    print("="*80)
    
    for key, rel in system.relationships.items():
        print(f"\n{rel['character1']} <-> {rel['character2']}")
        print(f"  Relationship: {rel['type']}")
        print(f"  Trust: {rel['trust']}, Affinity: {rel['affinity']}")
        print(f"  Interactions: {len(rel['history'])}")

if __name__ == "__main__":
    # Create tables if needed
    try:
        dynamodb.create_table(
            TableName=RELATIONSHIPS_TABLE,
            KeySchema=[
                {'AttributeName': 'character1', 'KeyType': 'HASH'},
                {'AttributeName': 'character2', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'character1', 'AttributeType': 'S'},
                {'AttributeName': 'character2', 'AttributeType': 'S'}
            ],
            BillingModeSummary={'BillingMode': 'PAY_PER_REQUEST'}
        )
        print("Created relationships table")
    except:
        pass
    
    try:
        dynamodb.create_table(
            TableName=INTERACTIONS_TABLE,
            KeySchema=[
                {'AttributeName': 'interaction_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'interaction_id', 'AttributeType': 'S'}
            ],
            BillingModeSummary={'BillingMode': 'PAY_PER_REQUEST'}
        )
        print("Created interactions table")
    except:
        pass
    
    # Run demonstration
    demonstrate_interactions()
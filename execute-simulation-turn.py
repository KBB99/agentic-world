#!/usr/bin/env python3
"""
Execute AI Agent Simulation Turns
Integrates with AWS Bedrock for decisions and DynamoDB for persistence
"""

import json
import boto3
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import os
import time

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# DynamoDB tables
AGENTS_TABLE = 'agentic-demo-agent-contexts'
WORLD_TABLE = 'agentic-demo-world-state'
MEMORIES_TABLE = 'agentic-demo-character-memories'

class AIAgentSimulation:
    def __init__(self, use_bedrock=True, verbose=False):
        self.use_bedrock = use_bedrock
        self.verbose = verbose
        self.world_state = self.load_world_state()
        self.agents = self.load_agents()
        self.turn_number = self.world_state.get('turn_number', 0)
        self.world_time = datetime.fromisoformat(
            self.world_state.get('world_time', datetime.now().replace(hour=6, minute=0).isoformat())
        )
        
    def load_world_state(self) -> Dict:
        """Load world state from DynamoDB"""
        try:
            table = dynamodb.Table(WORLD_TABLE)
            response = table.get_item(Key={'worldId': 'main'})
            if 'Item' in response:
                # Ensure locations key exists
                state = response['Item']
                if 'locations' not in state:
                    state['locations'] = self.initialize_world_state()['locations']
                return state
            else:
                # Initialize world state
                return self.initialize_world_state()
        except Exception as e:
            print(f"Warning: Could not load world state from DynamoDB: {e}")
            return self.initialize_world_state()
    
    def initialize_world_state(self) -> Dict:
        """Initialize a new world state"""
        return {
            'worldId': 'main',
            'turn_number': 0,
            'world_time': datetime.now().replace(hour=6, minute=0).isoformat(),
            'locations': {
                'public_library': {
                    'occupants': [],
                    'resources': ['wifi', 'power_outlets', 'water_fountain'],
                    'atmosphere': 'tense',
                    'security_level': 'high'
                },
                'coffee_shop': {
                    'occupants': [],
                    'resources': ['wifi', 'coffee', 'food'],
                    'atmosphere': 'busy',
                    'entry_cost': 5
                },
                'food_bank': {
                    'occupants': [],
                    'resources': ['free_food'],
                    'atmosphere': 'desperate',
                    'wait_time': 45
                },
                'tech_office': {
                    'occupants': [],
                    'resources': ['high_speed_internet', 'free_food', 'gym'],
                    'atmosphere': 'productive',
                    'access': 'employees_only'
                },
                'hospital': {
                    'occupants': [],
                    'resources': ['vending_machines'],
                    'atmosphere': 'exhausting',
                    'always_open': True
                },
                'luxury_apartment': {
                    'occupants': [],
                    'resources': ['everything'],
                    'atmosphere': 'comfortable',
                    'access': 'residents_only'
                }
            },
            'weather': 'cold',
            'events': []
        }
    
    def load_agents(self) -> Dict:
        """Load agent contexts from DynamoDB"""
        agents = {}
        try:
            table = dynamodb.Table(AGENTS_TABLE)
            response = table.scan()
            
            for item in response.get('Items', []):
                agent_id = item['agentId']
                
                # Determine economic tier based on background
                background = item.get('background', '')
                if '$500K' in background or '$25M' in background or 'trust fund' in background.lower():
                    money = Decimal('25000000') if 'trust fund' in background.lower() else Decimal('500000')
                    location = 'luxury_apartment'
                elif 'tech' in background.lower() or 'PM' in background.lower():
                    money = Decimal('47000')
                    location = 'tech_office'
                elif 'writer' in background.lower() or 'couch' in background.lower():
                    money = Decimal('53.09')
                    location = 'public_library'
                elif 'barista' in background.lower() or 'film' in background.lower():
                    money = Decimal('43')
                    location = 'coffee_shop'
                elif 'nurse' in background.lower() or 'ICU' in background.lower():
                    money = Decimal('340')
                    location = 'hospital'
                else:
                    money = Decimal('100')
                    location = 'public_library'
                
                agents[agent_id] = {
                    'id': agent_id,
                    'personality': item.get('personality', ''),
                    'background': item.get('background', ''),
                    'current_situation': item.get('current_situation', ''),
                    'goals': item.get('goals', []),
                    'current_state': item.get('current_state', 'normal'),
                    'location': item.get('location', location),
                    'money': money,
                    'needs': item.get('needs', {
                        'hunger': 10 if money > 10000 else 75,
                        'exhaustion': 0 if money > 10000 else 85,
                        'stress': 5 if money > 10000 else 90
                    }),
                    'inventory': item.get('inventory', []),
                    'memories': self.load_memories(agent_id)
                }
        except Exception as e:
            print(f"Warning: Could not load agents from DynamoDB: {e}")
            # Fallback to default agents
            agents = self.get_default_agents()
        
        return agents
    
    def get_default_agents(self) -> Dict:
        """Get default agent configurations"""
        return {
            'alex_chen': {
                'id': 'alex_chen',
                'personality': 'Exhausted writer, talented but desperate',
                'background': '28yo writer, couchsurfing, 2 weeks until kicked out',
                'current_situation': 'Writing at library for wifi',
                'goals': ['Finish article', 'Find food', 'Avoid eviction'],
                'current_state': 'exhausted',
                'location': 'public_library',
                'money': Decimal('53.09'),
                'needs': {'hunger': 75, 'exhaustion': 85, 'stress': 90},
                'inventory': ['old_laptop', 'water_bottle'],
                'memories': []
            },
            'jamie_rodriguez': {
                'id': 'jamie_rodriguez',
                'personality': 'Film PA/barista, optimistic but wearing down',
                'background': '26yo, part-time barista, dreams of directing',
                'current_situation': 'Working coffee shift before film gig',
                'goals': ['Get into film union', 'Pay rent', 'Make connections'],
                'current_state': 'hopeful_but_tired',
                'location': 'coffee_shop',
                'money': Decimal('43'),
                'needs': {'hunger': 60, 'exhaustion': 70, 'stress': 75},
                'inventory': ['apron', 'phone'],
                'memories': []
            }
        }
    
    def load_memories(self, agent_id: str) -> List[str]:
        """Load agent memories from DynamoDB"""
        try:
            table = dynamodb.Table(MEMORIES_TABLE)
            response = table.get_item(Key={'characterId': agent_id})
            if 'Item' in response:
                return response['Item'].get('memories', [])
        except:
            pass
        return []
    
    def save_world_state(self):
        """Save world state to DynamoDB"""
        try:
            table = dynamodb.Table(WORLD_TABLE)
            self.world_state['turn_number'] = self.turn_number
            self.world_state['world_time'] = self.world_time.isoformat()
            table.put_item(Item=self.world_state)
            if self.verbose:
                print("✓ World state saved to DynamoDB")
        except Exception as e:
            print(f"Warning: Could not save world state: {e}")
    
    def save_agent_state(self, agent_id: str, agent: Dict):
        """Save agent state to DynamoDB"""
        try:
            table = dynamodb.Table(AGENTS_TABLE)
            table.update_item(
                Key={'agentId': agent_id},
                UpdateExpression="""
                    SET current_state = :state,
                    #loc = :location,
                    money = :money,
                    needs = :needs,
                    inventory = :inventory
                """,
                ExpressionAttributeNames={'#loc': 'location'},
                ExpressionAttributeValues={
                    ':state': agent['current_state'],
                    ':location': agent['location'],
                    ':money': agent['money'],
                    ':needs': agent['needs'],
                    ':inventory': agent['inventory']
                }
            )
            
            # Save memories separately
            self.save_memories(agent_id, agent['memories'])
            
            if self.verbose:
                print(f"  ✓ {agent_id} state saved")
        except Exception as e:
            print(f"Warning: Could not save {agent_id} state: {e}")
    
    def save_memories(self, agent_id: str, memories: List[str]):
        """Save agent memories to DynamoDB"""
        try:
            table = dynamodb.Table(MEMORIES_TABLE)
            table.put_item(Item={
                'characterId': agent_id,
                'memories': memories[-30:],  # Keep last 30 memories
                'last_updated': datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Warning: Could not save memories for {agent_id}: {e}")
    
    def get_agent_perception(self, agent_id: str, agent: Dict) -> Dict:
        """Generate what the agent perceives about their environment"""
        location = agent['location']
        location_data = self.world_state['locations'].get(location, {})
        
        # Get other agents in same location
        others_here = [
            other_id for other_id, other in self.agents.items()
            if other['location'] == location and other_id != agent_id
        ]
        
        perception = {
            'location': location,
            'location_data': location_data,
            'others_present': others_here,
            'time': self.world_time.strftime('%I:%M %p'),
            'weather': self.world_state.get('weather', 'mild'),
            'my_state': {
                'money': float(agent['money']),
                'hunger': agent['needs']['hunger'],
                'exhaustion': agent['needs']['exhaustion'],
                'stress': agent['needs']['stress'],
                'inventory': agent['inventory']
            }
        }
        
        # Add economic tier-specific perceptions
        if agent['money'] < 100:
            perception['threats'] = self.identify_threats(agent, location_data)
            perception['opportunities'] = self.identify_opportunities(agent, location_data)
        else:
            perception['threats'] = []
            perception['opportunities'] = ['everything_available']
        
        return perception
    
    def identify_threats(self, agent: Dict, location_data: Dict) -> List[str]:
        """Identify threats for poor agents"""
        threats = []
        
        if location_data.get('security_level') == 'high':
            threats.append('security_watching')
        
        if agent['needs']['hunger'] > 80:
            threats.append('starvation_imminent')
        
        if agent['needs']['exhaustion'] > 90:
            threats.append('collapse_risk')
        
        if agent['money'] < 20:
            threats.append('cannot_afford_food')
        
        return threats
    
    def identify_opportunities(self, agent: Dict, location_data: Dict) -> List[str]:
        """Identify opportunities for agents"""
        opportunities = []
        
        if 'wifi' in location_data.get('resources', []):
            opportunities.append('submit_gig_work')
        
        if 'free_food' in location_data.get('resources', []):
            opportunities.append('get_food')
        
        if 'water_fountain' in location_data.get('resources', []):
            opportunities.append('drink_water')
        
        return opportunities
    
    def get_ai_decision(self, agent_id: str, agent: Dict, perception: Dict) -> Dict:
        """Get AI decision from Bedrock Claude"""
        
        if not self.use_bedrock:
            return self.get_simulated_decision(agent_id, agent, perception)
        
        try:
            # Construct prompt for Claude
            prompt = f"""You are {agent_id}, with this background: {agent['background']}
Your personality: {agent['personality']}
Current situation: {agent['current_situation']}
Your goals: {', '.join(agent['goals'])}

Current perception:
- Location: {perception['location']}
- Time: {perception['time']}
- Money: ${perception['my_state']['money']}
- Hunger: {perception['my_state']['hunger']}/100
- Exhaustion: {perception['my_state']['exhaustion']}/100
- Stress: {perception['my_state']['stress']}/100
- Others here: {', '.join(perception['others_present']) if perception['others_present'] else 'alone'}
- Threats: {', '.join(perception.get('threats', []))}
- Opportunities: {', '.join(perception.get('opportunities', []))}

Recent memories:
{chr(10).join(agent['memories'][-5:])}

What is your next action? Respond with a JSON object containing:
- action: what you do
- reasoning: why you're doing it
- emotion: how you feel
- urgency: immediate/high/medium/low

Be specific and realistic given your desperate situation."""

            # Call Bedrock Claude
            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 500,
                    'messages': [{
                        'role': 'user',
                        'content': prompt
                    }]
                })
            )
            
            response_body = json.loads(response['body'].read())
            decision_text = response_body['content'][0]['text']
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                decision = {
                    'action': 'wait',
                    'reasoning': 'Could not parse AI response',
                    'emotion': 'confused',
                    'urgency': 'low'
                }
            
            return decision
            
        except Exception as e:
            print(f"Warning: Bedrock call failed: {e}")
            return self.get_simulated_decision(agent_id, agent, perception)
    
    def get_simulated_decision(self, agent_id: str, agent: Dict, perception: Dict) -> Dict:
        """Get simulated decision based on character personality"""
        
        # Use actual character personality and situation
        personality = agent.get('personality', '')
        background = agent.get('background', '')
        current_situation = agent.get('current_situation', '')
        goals = agent.get('goals', [])
        
        # Poor character decisions based on needs
        if tier == 'poor':
            if agent['needs']['hunger'] > 80:
                return {
                    'action': 'search_for_food',
                    'reasoning': 'Desperately hungry, need food now',
                    'emotion': 'desperate',
                    'urgency': 'immediate'
                }
            elif agent['needs']['exhaustion'] > 90:
                return {
                    'action': 'find_place_to_rest',
                    'reasoning': 'About to collapse from exhaustion',
                    'emotion': 'exhausted',
                    'urgency': 'high'
                }
            elif agent['needs']['stress'] > 85:
                return {
                    'action': 'take_moment_to_breathe',
                    'reasoning': 'Stress overwhelming, need to calm down',
                    'emotion': 'anxious',
                    'urgency': 'high'
                }
            elif 'wifi' in perception.get('opportunities', []):
                return {
                    'action': 'submit_gig_work',
                    'reasoning': 'Have wifi access, can submit work for money',
                    'emotion': 'determined',
                    'urgency': 'high'
                }
            elif agent['location'] == 'public_library':
                return {
                    'action': 'continue_working',
                    'reasoning': 'Using free wifi to find work',
                    'emotion': 'focused',
                    'urgency': 'medium'
                }
            elif agent['location'] == 'coffee_shop':
                return {
                    'action': 'work_shift',
                    'reasoning': 'Need to earn tips',
                    'emotion': 'tired',
                    'urgency': 'high'
                }
            else:
                return {
                    'action': 'look_for_resources',
                    'reasoning': 'Searching for any opportunity',
                    'emotion': 'desperate',
                    'urgency': 'medium'
                }
        
        # Middle class decisions
        elif tier == 'middle':
            if agent['needs']['hunger'] > 60:
                return {
                    'action': 'buy_lunch',
                    'reasoning': 'Getting hungry, time for food',
                    'emotion': 'content',
                    'urgency': 'medium'
                }
            elif agent['location'] == 'tech_office':
                return {
                    'action': 'work_on_project',
                    'reasoning': 'Need to maintain job performance',
                    'emotion': 'focused',
                    'urgency': 'medium'
                }
            else:
                return {
                    'action': 'manage_finances',
                    'reasoning': 'Checking budget and investments',
                    'emotion': 'calculating',
                    'urgency': 'low'
                }
        
        # Wealthy decisions
        elif tier == 'wealthy':
            hour = self.world_time.hour
            if hour < 10:
                return {
                    'action': 'morning_routine',
                    'reasoning': 'Starting day with exercise and meditation',
                    'emotion': 'energized',
                    'urgency': 'low'
                }
            elif hour < 17:
                return {
                    'action': 'check_investments',
                    'reasoning': 'Monitoring portfolio performance',
                    'emotion': 'confident',
                    'urgency': 'low'
                }
            else:
                return {
                    'action': 'network_socially',
                    'reasoning': 'Building connections over drinks',
                    'emotion': 'social',
                    'urgency': 'low'
                }
        
        # Ultra wealthy decisions
        else:
            activities = [
                {
                    'action': 'review_portfolio',
                    'reasoning': 'Checking on multiple income streams',
                    'emotion': 'satisfied',
                    'urgency': 'low'
                },
                {
                    'action': 'plan_vacation',
                    'reasoning': 'Deciding between Aspen and St. Barts',
                    'emotion': 'bored',
                    'urgency': 'low'
                },
                {
                    'action': 'ignore_problems',
                    'reasoning': 'Other people\'s struggles aren\'t my concern',
                    'emotion': 'indifferent',
                    'urgency': 'none'
                },
                {
                    'action': 'post_on_social_media',
                    'reasoning': 'Sharing my blessed life',
                    'emotion': 'performative',
                    'urgency': 'low'
                }
            ]
            
            # Pick random activity for variety
            import random
            return random.choice(activities)
    
    def execute_action(self, agent_id: str, agent: Dict, decision: Dict) -> str:
        """Execute the agent's decided action"""
        
        action = decision['action']
        money = float(agent['money'])
        
        # Determine economic tier for action results
        if money >= 1000000:
            tier = 'ultra_wealthy'
        elif money >= 10000:
            tier = 'wealthy'
        elif money >= 1000:
            tier = 'middle'
        else:
            tier = 'poor'
        
        # Process actions based on what they are
        if 'food' in action or 'lunch' in action or 'eat' in action:
            if tier == 'poor':
                if agent['money'] >= 5:
                    agent['money'] -= Decimal('5')
                    agent['needs']['hunger'] = max(0, agent['needs']['hunger'] - 30)
                    result = "Bought dollar menu food, still hungry"
                else:
                    agent['location'] = 'food_bank'
                    agent['needs']['hunger'] = max(0, agent['needs']['hunger'] - 20)
                    result = "No money for food, went to food bank"
            elif tier == 'middle':
                agent['money'] -= Decimal('15')
                agent['needs']['hunger'] = 0
                result = "Had a decent lunch at cafe"
            else:
                agent['money'] -= Decimal('45')
                agent['needs']['hunger'] = 0
                result = "Enjoyed artisanal lunch"
                
        elif 'work' in action or 'shift' in action or 'gig' in action or 'submit' in action:
            if tier == 'poor':
                earnings = Decimal('6.47')
                agent['money'] += earnings
                agent['needs']['exhaustion'] = min(100, agent['needs']['exhaustion'] + 10)
                result = f"Worked desperately, earned ${earnings}"
            elif tier == 'middle':
                earnings = Decimal('240')  # Daily salary
                agent['money'] += earnings
                result = f"Completed work day, earned ${earnings}"
            else:
                earnings = Decimal('2000')  # Investment gains
                agent['money'] += earnings
                result = f"Portfolio gained ${earnings} today"
                
        elif 'rest' in action or 'sleep' in action or 'breathe' in action:
            if tier == 'poor':
                agent['needs']['exhaustion'] = max(0, agent['needs']['exhaustion'] - 15)
                agent['needs']['stress'] = max(0, agent['needs']['stress'] - 10)
                result = "Rested on bench, still tired"
            else:
                agent['needs']['exhaustion'] = 0
                agent['needs']['stress'] = max(0, agent['needs']['stress'] - 20)
                result = "Relaxed comfortably"
                
        elif 'investment' in action or 'portfolio' in action or 'finance' in action:
            if tier == 'wealthy' or tier == 'ultra_wealthy':
                gains = Decimal(str(money * 0.002))  # 0.2% daily return
                agent['money'] += gains
                result = f"Investment returns: ${gains:.2f}"
            elif tier == 'middle':
                gains = Decimal('5')
                agent['money'] += gains
                result = f"401k contribution saved ${gains}"
            else:
                result = "No money to invest"
                
        elif 'social' in action or 'network' in action:
            if tier == 'wealthy' or tier == 'ultra_wealthy':
                agent['money'] -= Decimal('50')  # Drinks and dinner
                result = "Networked at exclusive venue, new opportunities"
            else:
                result = "No access to networking events"
                
        elif 'routine' in action or 'morning' in action:
            if tier == 'wealthy' or tier == 'ultra_wealthy':
                agent['needs']['exhaustion'] = 0
                agent['needs']['stress'] = 0
                result = "Completed morning wellness routine"
            else:
                result = "No time for routines, need to survive"
                
        elif 'vacation' in action or 'plan' in action:
            if tier == 'ultra_wealthy':
                agent['money'] -= Decimal('10000')
                result = "Booked $10,000 vacation package"
            else:
                result = "Can only dream of vacations"
                
        elif 'ignore' in action:
            result = "Successfully ignored suffering around me"
            
        elif 'post' in action or 'social_media' in action:
            if tier == 'ultra_wealthy':
                result = "Posted about gratitude, gained 10K likes"
            else:
                result = "No time for social media, too busy surviving"
                
        else:
            # Default actions
            if tier == 'poor':
                result = "Struggled to survive another moment"
            elif tier == 'middle':
                result = "Maintained middle class stability"
            else:
                result = "Continued accumulating wealth"
        
        # Update stress based on urgency and tier
        if decision['urgency'] == 'immediate':
            agent['needs']['stress'] = min(100, agent['needs']['stress'] + 10)
        elif decision['urgency'] == 'low':
            agent['needs']['stress'] = max(0, agent['needs']['stress'] - 5)
        
        # Wealthy people's needs naturally decrease
        if tier in ['wealthy', 'ultra_wealthy']:
            agent['needs']['hunger'] = max(0, agent['needs']['hunger'] - 5)
            agent['needs']['exhaustion'] = max(0, agent['needs']['exhaustion'] - 5)
            agent['needs']['stress'] = max(0, agent['needs']['stress'] - 5)
        
        return result
    
    def update_needs(self, agent: Dict):
        """Update agent needs over time"""
        # Increase needs for poor agents
        if agent['money'] < 100:
            agent['needs']['hunger'] = min(100, agent['needs']['hunger'] + 5)
            agent['needs']['exhaustion'] = min(100, agent['needs']['exhaustion'] + 3)
            agent['needs']['stress'] = min(100, agent['needs']['stress'] + 2)
        else:
            # Wealthy agents have needs met
            agent['needs']['hunger'] = max(0, agent['needs']['hunger'] - 5)
            agent['needs']['exhaustion'] = max(0, agent['needs']['exhaustion'] - 10)
            agent['needs']['stress'] = max(0, agent['needs']['stress'] - 5)
    
    def check_encounters(self):
        """Check for character encounters in same location"""
        encounters = []
        
        for location, data in self.world_state['locations'].items():
            agents_here = [
                agent_id for agent_id, agent in self.agents.items()
                if agent['location'] == location
            ]
            
            if len(agents_here) > 1:
                encounters.append({
                    'location': location,
                    'participants': agents_here,
                    'type': self.determine_encounter_type(agents_here)
                })
        
        return encounters
    
    def determine_encounter_type(self, agent_ids: List[str]) -> str:
        """Determine the type of encounter"""
        wealth_levels = []
        for agent_id in agent_ids:
            agent = self.agents[agent_id]
            if agent['money'] < 100:
                wealth_levels.append('poor')
            elif agent['money'] < 10000:
                wealth_levels.append('middle')
            else:
                wealth_levels.append('wealthy')
        
        if all(w == 'poor' for w in wealth_levels):
            return 'solidarity'
        elif 'poor' in wealth_levels and 'wealthy' in wealth_levels:
            return 'class_collision'
        else:
            return 'neutral'
    
    def execute_turn(self):
        """Execute a single simulation turn"""
        self.turn_number += 1
        
        print("\n" + "="*80)
        print(f"TURN {self.turn_number} - {self.world_time.strftime('%I:%M %p')}")
        print("="*80)
        
        # Process each agent
        for agent_id, agent in self.agents.items():
            print(f"\n🎭 {agent_id}")
            print(f"📍 Location: {agent['location']}")
            print(f"💰 Money: ${agent['money']}")
            print(f"🔋 Needs: Hunger {agent['needs']['hunger']}, Exhaustion {agent['needs']['exhaustion']}, Stress {agent['needs']['stress']}")
            
            # Get perception
            perception = self.get_agent_perception(agent_id, agent)
            
            # Get AI decision
            decision = self.get_ai_decision(agent_id, agent, perception)
            print(f"🤔 Decision: {decision['action']}")
            print(f"💭 Reasoning: {decision['reasoning']}")
            print(f"😔 Emotion: {decision['emotion']}")
            
            # Execute action
            result = self.execute_action(agent_id, agent, decision)
            print(f"✅ Result: {result}")
            
            # Add to memories
            memory = f"[{self.world_time.strftime('%I:%M%p')}] {decision['action']}: {result}"
            agent['memories'].append(memory)
            
            # Update needs
            self.update_needs(agent)
            
            # Save agent state
            self.save_agent_state(agent_id, agent)
        
        # Check for encounters
        encounters = self.check_encounters()
        if encounters:
            print("\n🤝 ENCOUNTERS:")
            for encounter in encounters:
                print(f"  {encounter['type']} at {encounter['location']}: {', '.join(encounter['participants'])}")
        
        # Update world time
        self.world_time += timedelta(minutes=30)
        
        # Save world state
        self.save_world_state()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print turn summary"""
        print("\n" + "-"*80)
        print("TURN SUMMARY")
        print("-"*80)
        
        for agent_id, agent in self.agents.items():
            survival_days = float(agent['money']) / 15  # $15/day minimum
            print(f"{agent_id}: ${agent['money']:.2f} ({survival_days:.1f} days)")
        
        # Calculate inequality
        poorest = min(self.agents.values(), key=lambda x: x['money'])
        richest = max(self.agents.values(), key=lambda x: x['money'])
        
        if richest['money'] > 0 and poorest['money'] > 0:
            ratio = richest['money'] / poorest['money']
            print(f"\nWealth ratio: {ratio:.0f}:1")

def main():
    parser = argparse.ArgumentParser(description='Execute AI Agent Simulation Turns')
    parser.add_argument('--turns', type=int, default=1, help='Number of turns to execute')
    parser.add_argument('--use-bedrock', action='store_true', help='Use AWS Bedrock for AI decisions')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--reset', action='store_true', help='Reset world state')
    
    args = parser.parse_args()
    
    print("🎮 AI AGENT SIMULATION")
    print("="*80)
    
    if args.use_bedrock:
        print("Using AWS Bedrock Claude for AI decisions")
    else:
        print("Using simulated decisions (no Bedrock)")
    
    # Create simulation
    sim = AIAgentSimulation(use_bedrock=args.use_bedrock, verbose=args.verbose)
    
    if args.reset:
        print("Resetting world state...")
        sim.world_state = sim.initialize_world_state()
        sim.turn_number = 0
    
    # Execute turns
    for i in range(args.turns):
        sim.execute_turn()
        if i < args.turns - 1:
            time.sleep(1)  # Brief pause between turns
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    print(f"Executed {args.turns} turn(s)")
    print(f"World time: {sim.world_time.strftime('%I:%M %p')}")
    print(f"Total turns: {sim.turn_number}")

if __name__ == "__main__":
    main()
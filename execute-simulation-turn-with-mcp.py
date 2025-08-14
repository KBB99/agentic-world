#!/usr/bin/env python3
"""
Execute AI Agent Simulation Turns with MCP Tool Access
Integrates with AWS Bedrock for decisions and provides MCP tools to characters
"""

import json
import boto3
import argparse
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional
import os
import time
import subprocess
import asyncio
import random

# AWS clients
bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# DynamoDB tables
AGENTS_TABLE = 'agentic-demo-agent-contexts'
WORLD_TABLE = 'agentic-demo-world-state'
MEMORIES_TABLE = 'agentic-demo-character-memories'
RELATIONSHIPS_TABLE = 'agentic-demo-relationships'

# MCP Tools available to characters
MCP_TOOLS = {
    'read_viewer_messages': {
        'description': 'Read recent messages from stream viewers',
        'parameters': {'count': 'number of messages to read'}
    },
    'respond_to_viewer': {
        'description': 'Respond to a specific viewer message',
        'parameters': {'viewer': 'viewer name', 'message': 'response message'}
    },
    'check_viewer_sentiment': {
        'description': 'Check the overall sentiment of viewers',
        'parameters': {}
    },
    'read_donations': {
        'description': 'Read recent donations and support messages',
        'parameters': {'count': 'number of donations to read'}
    },
    'thank_donor': {
        'description': 'Thank a donor for their support',
        'parameters': {'donor': 'donor name', 'amount': 'donation amount'}
    },
    'ask_viewers_for_help': {
        'description': 'Ask viewers for help with a specific problem',
        'parameters': {'problem': 'description of the problem', 'urgency': 'how urgent it is'}
    },
    'post_to_social': {
        'description': 'Post a message to social media',
        'parameters': {'platform': 'social platform', 'message': 'message to post'}
    },
    'check_crowdfunding': {
        'description': 'Check crowdfunding campaign status',
        'parameters': {}
    },
    'stream_performance': {
        'description': 'Perform or create content for viewers',
        'parameters': {'type': 'type of performance', 'content': 'what to perform'}
    }
}

class MCPEnabledSimulation:
    def __init__(self, use_bedrock=True, verbose=False):
        self.use_bedrock = use_bedrock
        self.verbose = verbose
        self.world_state = self.load_world_state()
        self.agents = self.load_agents()
        self.turn_number = self.world_state.get('turn_number', 0)
        self.world_time = datetime.fromisoformat(
            self.world_state.get('world_time', datetime.now().replace(hour=6, minute=0).isoformat())
        )
        self.viewer_messages = []  # Simulated viewer messages
        self.donations = []  # Simulated donations
        self.relationships = {}  # Track relationships between characters
        self.load_relationships()
        
    def load_world_state(self) -> Dict:
        """Load world state from DynamoDB"""
        try:
            table = dynamodb.Table(WORLD_TABLE)
            response = table.get_item(Key={'worldId': 'main'})
            if 'Item' in response:
                state = response['Item']
                if 'locations' not in state:
                    state['locations'] = self.initialize_world_state()['locations']
                return state
            else:
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
                    'security_level': 'high',
                    'has_streaming_setup': True  # Can stream from here
                },
                'coffee_shop': {
                    'occupants': [],
                    'resources': ['wifi', 'coffee', 'food'],
                    'atmosphere': 'busy',
                    'entry_cost': 5,
                    'has_streaming_setup': True  # Can stream from here
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
                    'access': 'employees_only',
                    'has_streaming_setup': True  # Best streaming location
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
                    'access': 'residents_only',
                    'has_streaming_setup': True  # Premium streaming setup
                }
            },
            'weather': 'cold',
            'events': [],
            'stream_active': False,
            'viewer_count': 0
        }
    
    def load_agents(self) -> Dict:
        """Load agent contexts from DynamoDB"""
        agents = {}
        try:
            table = dynamodb.Table(AGENTS_TABLE)
            response = table.scan()
            
            for item in response.get('Items', []):
                agent_id = item['agentId']
                
                # Determine economic tier and streaming capability
                background = item.get('background', '')
                has_streaming_access = False
                
                if '$500K' in background or '$25M' in background or 'trust fund' in background.lower():
                    money = Decimal('25000000') if 'trust fund' in background.lower() else Decimal('500000')
                    location = 'luxury_apartment'
                    has_streaming_access = True
                elif 'tech' in background.lower() or 'PM' in background.lower():
                    money = Decimal('47000')
                    location = 'tech_office'
                    has_streaming_access = True
                elif 'writer' in background.lower() or 'couch' in background.lower():
                    money = Decimal('53.09')
                    location = 'public_library'
                    has_streaming_access = True  # Desperate enough to stream
                elif 'barista' in background.lower() or 'film' in background.lower():
                    money = Decimal('43')
                    location = 'coffee_shop'
                    has_streaming_access = True  # Creative types stream
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
                    'memories': self.load_memories(agent_id) or [],
                    'has_streaming_access': has_streaming_access,
                    'stream_followers': item.get('stream_followers', 0),
                    'social_media_followers': item.get('social_media_followers', 0)
                }
        except Exception as e:
            print(f"Warning: Could not load agents from DynamoDB: {e}")
            agents = self.get_default_agents()
        
        return agents
    
    def get_default_agents(self) -> Dict:
        """Get default agent configurations with MCP capabilities"""
        return {
            'alex_chen': {
                'id': 'alex_chen',
                'personality': 'Exhausted writer, talented but desperate',
                'background': '28yo writer, couchsurfing, 2 weeks until kicked out',
                'current_situation': 'Writing at library for wifi',
                'goals': ['Finish article', 'Find food', 'Avoid eviction', 'Build audience'],
                'current_state': 'exhausted',
                'location': 'public_library',
                'money': Decimal('53.09'),
                'needs': {'hunger': 75, 'exhaustion': 85, 'stress': 90},
                'inventory': ['old_laptop', 'water_bottle', 'phone'],
                'memories': [],
                'has_streaming_access': True,
                'stream_followers': 127,
                'social_media_followers': 892
            },
            'jamie_rodriguez': {
                'id': 'jamie_rodriguez',
                'personality': 'Film PA/barista, optimistic but wearing down',
                'background': '26yo, part-time barista, dreams of directing',
                'current_situation': 'Working coffee shift before film gig',
                'goals': ['Get into film union', 'Pay rent', 'Make connections', 'Film content'],
                'current_state': 'hopeful_but_tired',
                'location': 'coffee_shop',
                'money': Decimal('43'),
                'needs': {'hunger': 60, 'exhaustion': 70, 'stress': 75},
                'inventory': ['apron', 'phone', 'camera'],
                'memories': [],
                'has_streaming_access': True,
                'stream_followers': 2341,
                'social_media_followers': 5621
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
    
    def simulate_viewer_interaction(self, agent_id: str) -> Dict:
        """Simulate viewer messages and donations for the character"""
        agent = self.agents[agent_id]
        interactions = {
            'messages': [],
            'donations': [],
            'sentiment': 'neutral'
        }
        
        # Poor characters get more sympathy
        if agent['money'] < 100:
            interactions['messages'] = [
                {'viewer': 'supportive_fan', 'message': 'Stay strong! You got this!'},
                {'viewer': 'fellow_struggler', 'message': 'I know how hard it is. Sending love.'},
                {'viewer': 'curious_viewer', 'message': 'How do you keep going?'}
            ]
            if agent['needs']['hunger'] > 70:
                interactions['donations'].append({
                    'donor': 'anonymous', 
                    'amount': 5, 
                    'message': 'Get yourself some food'
                })
            interactions['sentiment'] = 'supportive'
            
        elif agent['money'] < 10000:
            interactions['messages'] = [
                {'viewer': 'career_watcher', 'message': 'Love your content!'},
                {'viewer': 'regular_viewer', 'message': 'First!'}
            ]
            interactions['sentiment'] = 'positive'
            
        else:
            interactions['messages'] = [
                {'viewer': 'skeptical_viewer', 'message': 'Must be nice to have money'},
                {'viewer': 'troll_42', 'message': 'Out of touch much?'}
            ]
            interactions['sentiment'] = 'negative'
        
        return interactions
    
    def get_ai_decision_with_mcp(self, agent_id: str, agent: Dict, perception: Dict) -> Dict:
        """Get AI decision from Bedrock Claude with MCP tool access"""
        
        if not self.use_bedrock:
            return self.get_simulated_decision(agent_id, agent, perception)
        
        try:
            # Get simulated viewer interactions
            interactions = self.simulate_viewer_interaction(agent_id)
            
            # Construct prompt for Claude with MCP tools
            prompt = f"""You are {agent_id}, with this background: {agent['background']}
Your personality: {agent['personality']}
Current situation: {agent['current_situation']}
Your goals: {', '.join(str(g) for g in agent['goals'])}

Current perception:
- Location: {perception['location']} (can stream: {perception['location_data'].get('has_streaming_setup', False)})
- Time: {perception['time']}
- Money: ${perception['my_state']['money']}
- Hunger: {perception['my_state']['hunger']}/100
- Exhaustion: {perception['my_state']['exhaustion']}/100
- Stress: {perception['my_state']['stress']}/100
- Others here: {', '.join(perception['others_present']) if perception['others_present'] else 'alone'}
- Threats: {', '.join(perception.get('threats', []))}
- Opportunities: {', '.join(perception.get('opportunities', []))}

Digital presence:
- Stream followers: {agent.get('stream_followers', 0)}
- Social media followers: {agent.get('social_media_followers', 0)}
- Has streaming access: {agent.get('has_streaming_access', False)}
- Recent viewer messages: {json.dumps(interactions['messages'][:2]) if interactions['messages'] else 'none'}
- Recent donations: ${sum(d['amount'] for d in interactions['donations'])} total
- Viewer sentiment: {interactions['sentiment']}

Available MCP tools you can use:
{json.dumps(MCP_TOOLS, indent=2)}

Recent memories:
{chr(10).join(agent['memories'][-5:])}

What is your next action? Consider both physical actions and digital interactions. You can use MCP tools to interact with viewers, post to social media, or check crowdfunding.

Respond with a JSON object containing:
- action: what you do (can include MCP tool use)
- mcp_tool: which MCP tool to use (if any)
- tool_params: parameters for the MCP tool (if using one)
- reasoning: why you're doing it
- emotion: how you feel
- urgency: immediate/high/medium/low

Be specific and realistic given your situation. If you're desperate, consider streaming or asking for help."""

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
    
    def execute_mcp_tool(self, agent_id: str, tool_name: str, params: Dict) -> str:
        """Execute an MCP tool and return the result"""
        agent = self.agents[agent_id]
        
        if tool_name == 'read_viewer_messages':
            interactions = self.simulate_viewer_interaction(agent_id)
            messages = interactions['messages'][:params.get('count', 3)]
            return f"Read {len(messages)} viewer messages"
            
        elif tool_name == 'respond_to_viewer':
            viewer = params.get('viewer', 'unknown')
            message = params.get('message', '')
            return f"Responded to {viewer}: {message}"
            
        elif tool_name == 'check_viewer_sentiment':
            interactions = self.simulate_viewer_interaction(agent_id)
            return f"Viewer sentiment is {interactions['sentiment']}"
            
        elif tool_name == 'read_donations':
            interactions = self.simulate_viewer_interaction(agent_id)
            total = sum(d['amount'] for d in interactions['donations'])
            return f"Received ${total} in donations"
            
        elif tool_name == 'thank_donor':
            return f"Thanked {params.get('donor', 'anonymous')} for ${params.get('amount', 0)}"
            
        elif tool_name == 'ask_viewers_for_help':
            problem = params.get('problem', 'unspecified')
            # Simulate getting help based on desperation
            if agent['money'] < 50 and agent['needs']['hunger'] > 70:
                agent['money'] += Decimal('10')
                return f"Asked for help with {problem}, received $10 donation"
            return f"Asked for help with {problem}"
            
        elif tool_name == 'post_to_social':
            platform = params.get('platform', 'twitter')
            content = params.get('content', params.get('message', ''))
            
            # Actually generate content if it's a blog
            if platform == 'blog':
                # Import content generation
                import subprocess
                import json
                
                # Generate real blog post
                try:
                    result = subprocess.run([
                        'python3', 'quick-content-generator.py',
                        '--character', agent_id,
                        '--type', 'blog',
                        '--topic', content
                    ], capture_output=True, text=True, timeout=2)
                    
                    if result.returncode == 0 and 'Created:' in result.stdout:
                        # Extract path from output
                        import re
                        match = re.search(r'Created: (.+)', result.stdout)
                        if match:
                            path = match.group(1)
                            agent['social_media_followers'] = agent.get('social_media_followers', 0) + 10
                            return f"Posted blog at {path}"
                except Exception as e:
                    print(f"Content generation failed: {e}")
            
            # Regular social post
            agent['social_media_followers'] = agent.get('social_media_followers', 0) + 5
            return f"Posted to {platform}: {content[:50]}..."
            
        elif tool_name == 'check_crowdfunding':
            # Simulate crowdfunding based on follower count
            if agent.get('stream_followers', 0) > 1000:
                amount = Decimal('50')
                agent['money'] += amount
                return f"Crowdfunding raised ${amount}"
            return "Crowdfunding: $0 raised"
            
        elif tool_name == 'stream_performance':
            perf_type = params.get('type', 'general')
            # Increase followers
            agent['stream_followers'] = agent.get('stream_followers', 0) + 10
            return f"Streamed {perf_type} content, gained 10 followers"
            
        else:
            return f"Unknown tool: {tool_name}"
    
    def execute_action_with_mcp(self, agent_id: str, agent: Dict, decision: Dict) -> str:
        """Execute the agent's decided action, including MCP tools"""
        
        # First execute any MCP tool if specified
        mcp_result = ""
        if decision.get('mcp_tool'):
            mcp_result = self.execute_mcp_tool(
                agent_id, 
                decision['mcp_tool'], 
                decision.get('tool_params', {})
            )
            
        # Then execute the regular action
        action = decision['action']
        money = float(agent['money'])
        
        # Determine economic tier
        if money >= 1000000:
            tier = 'ultra_wealthy'
        elif money >= 10000:
            tier = 'wealthy'
        elif money >= 1000:
            tier = 'middle'
        else:
            tier = 'poor'
        
        # Process combined result
        base_result = self.execute_regular_action(agent_id, agent, decision, tier)
        
        if mcp_result:
            return f"{base_result}. {mcp_result}"
        return base_result
    
    def execute_regular_action(self, agent_id: str, agent: Dict, decision: Dict, tier: str) -> str:
        """Execute non-MCP actions"""
        action = decision['action']
        
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
                earnings = Decimal('240')
                agent['money'] += earnings
                result = f"Completed work day, earned ${earnings}"
            else:
                earnings = Decimal('2000')
                agent['money'] += earnings
                result = f"Portfolio gained ${earnings} today"
                
        elif 'write' in action.lower() or 'blog' in action.lower():
            # Writing/blogging action - generate actual content!
            import subprocess
            try:
                # Determine topic based on character state
                if agent['needs']['hunger'] > 70:
                    topic = "survival on no money"
                elif agent['needs']['exhaustion'] > 80:
                    topic = "exhaustion and burnout"
                else:
                    topic = "life in the gig economy"
                
                result_proc = subprocess.run([
                    'python3', 'quick-content-generator.py',
                    '--character', agent_id,
                    '--type', 'blog',
                    '--topic', topic
                ], capture_output=True, text=True, timeout=2)
                
                if tier == 'poor':
                    agent['needs']['exhaustion'] = min(100, agent['needs']['exhaustion'] + 5)
                    agent['money'] += Decimal('3.50')  # $0.03/word for ~100 words
                    result = f"Wrote blog post about {topic}, earned $3.50"
                else:
                    agent['money'] += Decimal('50')
                    result = f"Completed blog post about {topic}, earned $50"
                    
                if 'Created:' in result_proc.stdout:
                    import re
                    match = re.search(r'Created: (.+)', result_proc.stdout)
                    if match:
                        local_path = match.group(1)
                        result += f" - View at {local_path}"
                        
                        # Also upload to existing S3/CloudFront
                        try:
                            s3_result = subprocess.run([
                                'python3', 'publish-to-existing-s3.py',
                                '--character', agent_id,
                                '--type', 'blogs',
                                '--file', f"web-interface/public{local_path}"
                            ], capture_output=True, text=True, timeout=5)
                            
                            if 'CloudFront:' in s3_result.stdout:
                                s3_match = re.search(r'CloudFront: (.+)', s3_result.stdout)
                                if s3_match:
                                    cdn_url = s3_match.group(1)
                                    result += f"\n   📌 Published to: {cdn_url}"
                                    print(f"   📌 CloudFront: {cdn_url}")
                        except Exception as e:
                            print(f"   ⚠️ S3 upload failed: {e}")
            except:
                if tier == 'poor':
                    agent['needs']['exhaustion'] = min(100, agent['needs']['exhaustion'] + 5)
                    result = "Wrote desperately for pennies per word"
                else:
                    result = "Completed writing project"
                    
        elif 'stream' in action.lower():
            # Streaming action
            if agent.get('has_streaming_access'):
                followers_gained = 15 if tier == 'poor' else 5
                agent['stream_followers'] = agent.get('stream_followers', 0) + followers_gained
                tips = Decimal('5') if tier == 'poor' else Decimal('0')
                agent['money'] += tips
                result = f"Streamed for 2 hours, gained {followers_gained} followers, ${tips} in tips"
            else:
                result = "No streaming access available"
                
        else:
            # Default actions
            if tier == 'poor':
                result = "Struggled to survive another moment"
            elif tier == 'middle':
                result = "Maintained middle class stability"
            else:
                result = "Continued accumulating wealth"
        
        # Update stress based on urgency
        if decision['urgency'] == 'immediate':
            agent['needs']['stress'] = min(100, agent['needs']['stress'] + 10)
        elif decision['urgency'] == 'low':
            agent['needs']['stress'] = max(0, agent['needs']['stress'] - 5)
        
        return result
    
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
            if location_data.get('has_streaming_setup'):
                opportunities.append('stream_content')
        
        if 'free_food' in location_data.get('resources', []):
            opportunities.append('get_food')
        
        if 'water_fountain' in location_data.get('resources', []):
            opportunities.append('drink_water')
        
        return opportunities
    
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
                    inventory = :inventory,
                    stream_followers = :stream_followers,
                    social_media_followers = :social_followers
                """,
                ExpressionAttributeNames={'#loc': 'location'},
                ExpressionAttributeValues={
                    ':state': agent['current_state'],
                    ':location': agent['location'],
                    ':money': agent['money'],
                    ':needs': agent['needs'],
                    ':inventory': agent['inventory'],
                    ':stream_followers': agent.get('stream_followers', 0),
                    ':social_followers': agent.get('social_media_followers', 0)
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
            return {
                'trust': 0,
                'affinity': 0,
                'history': [],
                'type': 'stranger'
            }
    
    def simulate_character_interaction(self, char1_id: str, char2_id: str, location: str):
        """Simulate an interaction between two characters"""
        char1 = self.agents[char1_id]
        char2 = self.agents[char2_id]
        relationship = self.get_relationship_status(char1_id, char2_id)
        
        # Determine interaction type based on economic disparity
        money1 = float(char1['money'])
        money2 = float(char2['money'])
        
        if money1 < 100 and money2 < 100:
            interaction_type = 'solidarity'
        elif abs(money1 - money2) > 10000:
            interaction_type = 'class_tension'
        elif money1 < 100 or money2 < 100:
            interaction_type = 'compassion_or_dismissal'
        else:
            interaction_type = 'neutral'
        
        print(f"\n🤝 {char1_id} meets {char2_id} at {location}")
        print(f"   Interaction type: {interaction_type}")
        print(f"   Previous relationship: {relationship['type']}")
        
        # Generate simple interaction outcome
        if interaction_type == 'solidarity':
            # Poor characters support each other
            print(f"   💬 Sharing survival tips and emotional support")
            char1['memories'].append(f"Found solidarity with {char2_id} at {location}")
            char2['memories'].append(f"Found solidarity with {char1_id} at {location}")
            
            # Maybe share resources
            if money1 > 10 and money2 < 5:
                share_amount = Decimal('5')
                char1['money'] -= share_amount
                char2['money'] += share_amount
                print(f"   💰 {char1_id} shares ${share_amount} with {char2_id}")
            
            # Update relationship
            self.update_relationship(char1_id, char2_id, {'trust': 10, 'affinity': 10})
            
        elif interaction_type == 'class_tension':
            # Uncomfortable encounter
            print(f"   😣 Tense encounter highlighting class differences")
            char1['memories'].append(f"Uncomfortable encounter with {char2_id}")
            char2['memories'].append(f"Awkward interaction with {char1_id}")
            
            # Update relationship negatively
            self.update_relationship(char1_id, char2_id, {'trust': -5, 'affinity': -10})
            
        elif interaction_type == 'compassion_or_dismissal':
            # Wealthier character might help or ignore
            if random.random() < 0.3:  # 30% chance of help
                wealthy = char1_id if money1 > money2 else char2_id
                poor = char2_id if money1 > money2 else char1_id
                help_amount = Decimal('20')
                
                self.agents[wealthy]['money'] -= help_amount
                self.agents[poor]['money'] += help_amount
                
                print(f"   💝 {wealthy} gives ${help_amount} to {poor}")
                self.agents[wealthy]['memories'].append(f"Helped {poor} with ${help_amount}")
                self.agents[poor]['memories'].append(f"Received help from {wealthy}")
                
                self.update_relationship(char1_id, char2_id, {'trust': 15, 'affinity': 10})
            else:
                print(f"   🚶 Brief acknowledgment, no meaningful interaction")
                self.update_relationship(char1_id, char2_id, {'trust': 0, 'affinity': -2})
        
        else:
            print(f"   👋 Casual greeting")
            self.update_relationship(char1_id, char2_id, {'trust': 1, 'affinity': 1})
    
    def update_relationship(self, char1: str, char2: str, changes: Dict):
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
            'timestamp': self.world_time.isoformat(),
            'location': self.agents[char1].get('location', 'unknown')
        })
        
        # Update relationship type
        trust = self.relationships[key]['trust']
        affinity = self.relationships[key]['affinity']
        
        if trust > 30 and affinity > 30:
            self.relationships[key]['type'] = 'friends'
        elif trust > 15 and affinity > 15:
            self.relationships[key]['type'] = 'allies'
        elif trust < -15 or affinity < -15:
            self.relationships[key]['type'] = 'tension'
        elif len(self.relationships[key]['history']) > 1:
            self.relationships[key]['type'] = 'acquaintances'
        else:
            self.relationships[key]['type'] = 'strangers'
        
        # Save to DynamoDB
        try:
            table = dynamodb.Table(RELATIONSHIPS_TABLE)
            table.put_item(Item=self.relationships[key])
        except:
            # Table might not exist
            pass
    
    def process_location_interactions(self):
        """Process interactions between characters in the same location"""
        # Group characters by location
        locations = {}
        for agent_id, agent in self.agents.items():
            loc = agent['location']
            if loc not in locations:
                locations[loc] = []
            locations[loc].append(agent_id)
        
        # Process interactions at each location
        for location, characters in locations.items():
            if len(characters) >= 2:
                # Randomly select pairs to interact
                num_interactions = min(2, len(characters) // 2)
                
                for _ in range(num_interactions):
                    if len(characters) >= 2:
                        char1_id, char2_id = random.sample(characters, 2)
                        self.simulate_character_interaction(char1_id, char2_id, location)
    
    def get_simulated_decision(self, agent_id: str, agent: Dict, perception: Dict) -> Dict:
        """Get simulated decision for non-AI mode with variety"""
        import random
        
        # Get recent memories to avoid repetition
        recent_memories = agent.get('memories', [])[-5:]
        recent_actions = [m.split(':')[-1].strip() if ':' in m else m for m in recent_memories]
        
        # Time-based variety
        hour = self.world_time.hour
        is_work_hours = 9 <= hour <= 17
        is_night = hour >= 22 or hour <= 5
        
        # Location awareness
        location = agent['location']
        others_present = perception.get('others_present', [])
        
        # Character-specific behaviors
        character_traits = {
            'alex_chen': ['write', 'code', 'blog', 'search_wifi'],
            'jamie_rodriguez': ['film', 'coffee', 'network', 'edit_video'],
            'ashley_kim': ['manage_project', 'code', 'meeting', 'exercise'],
            'victoria_sterling': ['meeting', 'delegate', 'network', 'luxury']
        }
        
        preferred_actions = character_traits.get(agent_id, ['work', 'rest'])
        
        # Decision tree with variety
        possible_decisions = []
        
        # Critical needs first
        if agent['needs']['hunger'] > 90:
            possible_decisions.append({
                'action': 'desperately_search_for_food',
                'reasoning': 'Starving, must find food immediately',
                'emotion': 'panicked',
                'urgency': 'immediate',
                'weight': 100
            })
        elif agent['needs']['hunger'] > 70:
            if agent['money'] > 10:
                possible_decisions.append({
                    'action': 'buy_cheap_food',
                    'reasoning': 'Hungry, buying dollar menu items',
                    'emotion': 'anxious',
                    'urgency': 'high',
                    'weight': 80
                })
            else:
                possible_decisions.append({
                    'action': 'visit_food_bank',
                    'reasoning': 'Hungry but broke, seeking free food',
                    'emotion': 'ashamed',
                    'urgency': 'high',
                    'weight': 80
                })
        
        # Exhaustion-based actions
        if agent['needs']['exhaustion'] > 85:
            if location == 'public_library':
                possible_decisions.append({
                    'action': 'nap_in_library_corner',
                    'reasoning': 'Exhausted, catching a quick nap',
                    'emotion': 'exhausted',
                    'urgency': 'high',
                    'weight': 70
                })
            else:
                possible_decisions.append({
                    'action': 'find_place_to_rest',
                    'reasoning': 'Too tired to continue',
                    'emotion': 'drained',
                    'urgency': 'high',
                    'weight': 70
                })
        
        # Money-making actions
        if agent['money'] < 50:
            # Vary money-making strategies
            money_actions = [
                {
                    'action': 'stream_for_donations',
                    'mcp_tool': 'ask_viewers_for_help',
                    'tool_params': {'problem': 'need money for food', 'urgency': 'high'},
                    'reasoning': 'Streaming to viewers for support',
                    'emotion': 'hopeful',
                    'urgency': 'high',
                    'weight': 60
                },
                {
                    'action': 'post_crowdfunding_update',
                    'mcp_tool': 'check_crowdfunding',
                    'tool_params': {},
                    'reasoning': 'Checking if anyone donated',
                    'emotion': 'anxious',
                    'urgency': 'medium',
                    'weight': 40
                },
                {
                    'action': 'freelance_gig_search',
                    'reasoning': 'Looking for quick freelance work',
                    'emotion': 'determined',
                    'urgency': 'high',
                    'weight': 50
                }
            ]
            
            # Add money actions not recently done
            for action in money_actions:
                if action['action'] not in str(recent_actions):
                    possible_decisions.append(action)
        
        # Social interactions if others present
        if others_present and random.random() < 0.3:
            other = random.choice(others_present)
            possible_decisions.append({
                'action': f'interact_with_{other}',
                'reasoning': f'Noticed {other} is here',
                'emotion': 'curious',
                'urgency': 'low',
                'weight': 30
            })
        
        # Time-specific actions
        if is_night:
            possible_decisions.append({
                'action': 'find_safe_sleeping_spot',
                'reasoning': 'Late night, need somewhere safe',
                'emotion': 'worried',
                'urgency': 'medium',
                'weight': 40
            })
        elif is_work_hours:
            work_action = random.choice(preferred_actions)
            possible_decisions.append({
                'action': f'work_on_{work_action}',
                'reasoning': f'Work hours, focusing on {work_action}',
                'emotion': 'focused',
                'urgency': 'medium',
                'weight': 35
            })
        
        # Character-specific actions
        if agent_id == 'alex_chen' and location == 'public_library':
            possible_decisions.append({
                'action': 'write_blog_post',
                'mcp_tool': 'post_to_social',
                'tool_params': {'platform': 'blog', 'content': 'New post about survival'},
                'reasoning': 'Library has wifi, time to write',
                'emotion': 'creative',
                'urgency': 'medium',
                'weight': 45
            })
        elif agent_id == 'jamie_rodriguez' and hour in [5, 6, 7]:
            possible_decisions.append({
                'action': 'morning_coffee_shift',
                'reasoning': 'Early morning barista shift',
                'emotion': 'tired',
                'urgency': 'high',
                'weight': 80
            })
        
        # Default action if nothing critical
        if not possible_decisions:
            possible_decisions.append({
                'action': 'survive_another_hour',
                'reasoning': 'Just getting through the day',
                'emotion': 'numb',
                'urgency': 'low',
                'weight': 10
            })
        
        # Weight-based selection with randomness
        total_weight = sum(d.get('weight', 10) for d in possible_decisions)
        rand_val = random.random() * total_weight
        current_weight = 0
        
        for decision in possible_decisions:
            current_weight += decision.get('weight', 10)
            if rand_val <= current_weight:
                # Remove weight from final decision
                decision.pop('weight', None)
                return decision
        
        # Fallback
        decision = possible_decisions[0]
        decision.pop('weight', None)
        return decision
    
    def execute_turn(self):
        """Execute a single simulation turn with MCP capabilities"""
        self.turn_number += 1
        
        print("\n" + "="*80)
        print(f"TURN {self.turn_number} - {self.world_time.strftime('%I:%M %p')}")
        print("="*80)
        
        # Process each agent
        for agent_id, agent in self.agents.items():
            print(f"\n🎭 {agent_id}")
            print(f"📍 Location: {agent['location']}")
            print(f"💰 Money: ${agent['money']}")
            print(f"📱 Followers: Stream {agent.get('stream_followers', 0)}, Social {agent.get('social_media_followers', 0)}")
            print(f"🔋 Needs: Hunger {agent['needs']['hunger']}, Exhaustion {agent['needs']['exhaustion']}, Stress {agent['needs']['stress']}")
            
            # Get perception
            perception = self.get_agent_perception(agent_id, agent)
            
            # Get AI decision with MCP
            decision = self.get_ai_decision_with_mcp(agent_id, agent, perception)
            print(f"🤔 Decision: {decision['action']}")
            if decision.get('mcp_tool'):
                print(f"🔧 Using MCP: {decision['mcp_tool']}")
            print(f"💭 Reasoning: {decision['reasoning']}")
            print(f"😔 Emotion: {decision['emotion']}")
            
            # Execute action with MCP
            result = self.execute_action_with_mcp(agent_id, agent, decision)
            print(f"✅ Result: {result}")
            
            # Add to memories with timestamp and emotion
            memory = f"Turn {self.turn_number} at {self.world_time.strftime('%I:%M %p')}: {decision['action']} ({decision.get('emotion', 'neutral')}) - {result}"
            agent['memories'].append(memory)
            
            # Keep only last 30 memories
            agent['memories'] = agent['memories'][-30:]
            
            # Add to memories
            memory = f"[{self.world_time.strftime('%I:%M%p')}] {decision['action']}: {result}"
            agent['memories'].append(memory)
            
            # Update needs
            self.update_needs(agent)
            
            # Save agent state
            self.save_agent_state(agent_id, agent)
        
        # Process character interactions at each location
        print("\n" + "="*80)
        print("CHARACTER INTERACTIONS")
        print("="*80)
        self.process_location_interactions()
        
        # Update world time by 15-45 minutes for variety
        import random
        time_advance = random.randint(15, 45)
        self.world_time += timedelta(minutes=time_advance)
        print(f"\n⏰ Time advances {time_advance} minutes to {self.world_time.strftime('%I:%M %p')}")
        
        # Save world state
        self.save_world_state()
        
        # Save all agent states with memories
        for agent_id, agent in self.agents.items():
            self.save_agent_state(agent_id, agent)
            self.save_memories(agent_id, agent.get('memories', []))
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print turn summary"""
        print("\n" + "-"*80)
        print("TURN SUMMARY")
        print("-"*80)
        
        for agent_id, agent in self.agents.items():
            survival_days = float(agent['money']) / 15
            print(f"{agent_id}: ${agent['money']:.2f} ({survival_days:.1f} days) | Followers: {agent.get('stream_followers', 0)}")
        
        # Calculate inequality
        poorest = min(self.agents.values(), key=lambda x: x['money'])
        richest = max(self.agents.values(), key=lambda x: x['money'])
        
        if richest['money'] > 0 and poorest['money'] > 0:
            ratio = richest['money'] / poorest['money']
            print(f"\nWealth ratio: {ratio:.0f}:1")

def main():
    parser = argparse.ArgumentParser(description='Execute AI Agent Simulation with MCP Tools')
    parser.add_argument('--turns', type=int, default=1, help='Number of turns to execute')
    parser.add_argument('--use-bedrock', action='store_true', help='Use AWS Bedrock for AI decisions')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--reset', action='store_true', help='Reset world state')
    
    args = parser.parse_args()
    
    print("🎮 AI AGENT SIMULATION WITH MCP TOOLS")
    print("="*80)
    
    if args.use_bedrock:
        print("Using AWS Bedrock Claude with MCP tool access")
    else:
        print("Using simulated decisions with MCP tools")
    
    # Create simulation
    sim = MCPEnabledSimulation(use_bedrock=args.use_bedrock, verbose=args.verbose)
    
    if args.reset:
        print("Resetting world state...")
        sim.world_state = sim.initialize_world_state()
        sim.turn_number = 0
    
    # Execute turns
    for i in range(args.turns):
        sim.execute_turn()
        if i < args.turns - 1:
            time.sleep(1)
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    print(f"Executed {args.turns} turn(s)")
    print(f"World time: {sim.world_time.strftime('%I:%M %p')}")
    print(f"Total turns: {sim.turn_number}")

if __name__ == "__main__":
    main()
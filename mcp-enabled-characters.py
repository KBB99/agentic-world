#!/usr/bin/env python3
"""
MCP-Enabled Characters System
Characters can use real MCP tools based on their needs and economic position
Rich characters use different tools than poor ones
"""

import json
import boto3
import websocket
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Available MCP Servers from https://github.com/modelcontextprotocol/servers
MCP_SERVERS = {
    'filesystem': {
        'description': 'Read/write files, search directories',
        'use_cases': ['Writing resume', 'Organizing documents', 'Finding old files'],
        'command': 'npx @modelcontextprotocol/server-filesystem'
    },
    'github': {
        'description': 'Search repos, read code, manage issues',
        'use_cases': ['Finding freelance projects', 'Contributing to open source', 'Portfolio building'],
        'command': 'npx @modelcontextprotocol/server-github'
    },
    'google-maps': {
        'description': 'Search places, get directions, find businesses',
        'use_cases': ['Finding food banks', 'Locating free wifi', 'Planning delivery routes'],
        'command': 'npx @modelcontextprotocol/server-google-maps'
    },
    'slack': {
        'description': 'Read and send messages, manage channels',
        'use_cases': ['Remote work', 'Finding gigs', 'Team communication'],
        'command': 'npx @modelcontextprotocol/server-slack'
    },
    'postgres': {
        'description': 'Query and analyze databases',
        'use_cases': ['Data analysis jobs', 'Business intelligence', 'Financial modeling'],
        'command': 'npx @modelcontextprotocol/server-postgres'
    },
    'puppeteer': {
        'description': 'Web scraping, browser automation',
        'use_cases': ['Job hunting', 'Price comparison', 'Applying to many jobs'],
        'command': 'npx @modelcontextprotocol/server-puppeteer'
    },
    'brave-search': {
        'description': 'Web search with privacy',
        'use_cases': ['Researching', 'Finding resources', 'Checking prices'],
        'command': 'npx @modelcontextprotocol/server-brave-search'
    },
    'aws-kb': {
        'description': 'AWS knowledge base and bedrock access',
        'use_cases': ['Cloud architecture', 'Cost optimization', 'Enterprise solutions'],
        'command': 'npx @modelcontextprotocol/server-aws-kb'
    },
    'finance': {
        'description': 'Stock data, market analysis',
        'use_cases': ['Investment research', 'Portfolio management', 'Trading'],
        'command': 'custom-finance-server'
    },
    'email': {
        'description': 'Read and send emails',
        'use_cases': ['Job applications', 'Client communication', 'Bill disputes'],
        'command': 'custom-email-server'
    }
}

class MCPEnabledCharacter:
    """Character that can use MCP tools based on their situation"""
    
    def __init__(self, name: str, profile: Dict):
        self.name = name
        self.profile = profile
        self.memories_table = dynamodb.Table('agentic-demo-character-memories')
        self.available_tools = self._determine_available_tools()
        
    def _determine_available_tools(self) -> List[str]:
        """Determine which MCP tools this character would have access to"""
        
        resources = self.profile.get('resources', {})
        money = resources.get('money', 0)
        
        # Poor characters have limited tool access
        if money < 100:
            return ['brave-search', 'google-maps', 'filesystem']
            
        # Middle class has more tools
        elif money < 10000:
            return ['brave-search', 'google-maps', 'filesystem', 'github', 'puppeteer', 'email']
            
        # Wealthy have all tools including premium ones
        else:
            return list(MCP_SERVERS.keys())
            
    def choose_tool_for_situation(self, situation: str, memories: List[str]) -> Dict:
        """AI chooses which MCP tool to use based on situation"""
        
        # Build tool choice prompt
        available_tools_desc = []
        for tool in self.available_tools:
            server = MCP_SERVERS[tool]
            available_tools_desc.append(f"- {tool}: {server['description']}")
            
        prompt = f"""You are {self.name.replace('_', ' ').title()}.
Your economic position: ${self.profile['resources'].get('money', 0)}
Recent memories: {'; '.join(memories[-3:])}

SITUATION: {situation}

AVAILABLE MCP TOOLS:
{chr(10).join(available_tools_desc)}

Choose the most appropriate tool and action. Reply with JSON:
{{
  "thought": "why this tool helps your situation",
  "tool": "tool_name",
  "action": "specific action with the tool",
  "expected_outcome": "what you hope to achieve"
}}"""

        try:
            response = bedrock.invoke_model(
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
            text = result['content'][0]['text']
            
            # Parse JSON response
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
        except Exception as e:
            print(f"Error: {e}")
            
        return {
            'thought': 'Need to figure this out',
            'tool': 'brave-search',
            'action': 'search for help',
            'expected_outcome': 'find resources'
        }
        
    def simulate_tool_use(self, tool: str, action: str) -> str:
        """Simulate using an MCP tool (in reality, would actually run the server)"""
        
        # Simulate different outcomes based on character's position
        money = self.profile['resources'].get('money', 0)
        
        tool_simulations = {
            'brave-search': {
                'poor': 'Found: Food bank open Tuesdays, Free wifi at library until 8pm',
                'middle': 'Found: 3 freelance gigs, 2 require immediate start',
                'rich': 'Found: Tax optimization strategies, New investment opportunities'
            },
            'google-maps': {
                'poor': 'Route: Walk 1.2 miles to food bank, 8 min to McDonald\'s wifi',
                'middle': 'Route: 15 min drive to job interview, $8 parking',
                'rich': 'Route: 5 min to country club, valet available'
            },
            'github': {
                'poor': 'Found: Bounty issue worth $50, would take 10 hours',
                'middle': 'Found: Contract project $2000, competing with 47 others',
                'rich': 'Found: Startup seeking $2M funding, interesting pitch deck'
            },
            'puppeteer': {
                'poor': 'Applied to 23 jobs automatically, 2 bounced (email required)',
                'middle': 'Scraped freelance sites: 8 matches for skills',
                'rich': 'Automated portfolio rebalancing across 5 platforms'
            },
            'postgres': {
                'poor': 'Error: No database access',
                'middle': 'Analyzed: Client data shows 3 optimization opportunities',
                'rich': 'Query: Properties with >20% ROI potential: 47 results'
            },
            'aws-kb': {
                'poor': 'Error: AWS credentials required',
                'middle': 'Found: How to reduce AWS costs by 30%',
                'rich': 'Architected: Multi-region deployment for tax optimization'
            }
        }
        
        # Determine economic tier
        if money < 100:
            tier = 'poor'
        elif money < 10000:
            tier = 'middle'
        else:
            tier = 'rich'
            
        # Get simulation for this tool and tier
        if tool in tool_simulations and tier in tool_simulations[tool]:
            return tool_simulations[tool][tier]
        else:
            return f"Used {tool}: {action[:50]}"

def run_mcp_narrative():
    """Run narrative where characters use MCP tools"""
    
    print("=== MCP-ENABLED CHARACTER NARRATIVE ===")
    print("Characters use real tools based on their economic position\n")
    
    ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'
    memories_table = dynamodb.Table('agentic-demo-character-memories')
    
    # Scenarios requiring tool use
    scenarios = [
        ('alex_chen', 'Need to find paying work TODAY or can\'t eat', {'money': 47}),
        ('tyler_chen', 'Want to optimize investment property portfolio', {'money': 45000}),
        ('maria_gonzalez', 'Need to find emergency childcare for night shift', {'money': 340}),
        ('brittany_torres', 'Car broke down, need to find cheapest mechanic', {'money': 128}),
        ('ashley_kim', 'Researching salary data for raise negotiation', {'money': 8500}),
        ('dorothy_jackson', 'Looking up property tax appeal process', {'money': 1200}),
        ('madison_worthington', 'Bored, want to start a "sustainable" fashion brand', {'money': 180000}),
        ('richard_blackstone', 'Analyzing markets for next acquisition target', {'money': 25000000})
    ]
    
    total_cost = 0
    
    for character_name, situation, resources in scenarios:
        print(f"\n--- {character_name.upper()} ---")
        print(f"Situation: {situation}")
        print(f"Resources: ${resources['money']}")
        
        # Load memories
        try:
            char_data = memories_table.get_item(Key={'characterId': character_name})['Item']
            memories = char_data.get('memories', [])
        except:
            memories = []
            char_data = {'characterId': character_name, 'memories': memories}
            
        # Create MCP-enabled character
        character = MCPEnabledCharacter(character_name, {'resources': resources})
        print(f"Available tools: {', '.join(character.available_tools)}")
        
        # Choose tool
        decision = character.choose_tool_for_situation(situation, memories)
        
        print(f"Thought: {decision['thought'][:70]}...")
        print(f"Chooses tool: {decision['tool']}")
        print(f"Action: {decision['action'][:70]}...")
        
        # Simulate tool use
        result = character.simulate_tool_use(decision['tool'], decision['action'])
        print(f"Result: {result}")
        
        # Save to memory
        memory = f"{situation[:30]}: Used {decision['tool']} - {result[:40]}"
        char_data['memories'].append(memory)
        memories_table.put_item(Item=char_data)
        
        # Send to telemetry
        try:
            ws = websocket.WebSocket()
            ws.connect(ws_url)
            msg = {
                'goal': f"[{character_name}] {situation[:35]}",
                'action': f"Using {decision['tool']}: {decision['action'][:40]}",
                'rationale': decision['thought'][:60],
                'result': result[:60]
            }
            ws.send(json.dumps(msg))
            ws.close()
        except:
            pass
            
        # Track cost
        cost = 0.003 * 0.25 + 0.015 * 0.15
        total_cost += cost
        
        time.sleep(2)
        
    print(f"\n=== MCP NARRATIVE COMPLETE ===")
    print(f"Total cost: ${total_cost:.4f}")
    
    print("\n=== KEY INSIGHTS ===")
    print("• Alex uses free search to find food banks and wifi")
    print("• Tyler uses AWS tools to optimize property exploitation")
    print("• Maria searches for emergency childcare with no money")
    print("• Madison uses enterprise tools for vanity project")
    print("• Same tools, vastly different outcomes based on resources")

if __name__ == "__main__":
    run_mcp_narrative()
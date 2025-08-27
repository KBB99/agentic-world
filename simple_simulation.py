import json
import boto3
import random
import os
from datetime import datetime
from decimal import Decimal

class SimulationRunner:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        self.s3 = boto3.client('s3', region_name='us-east-1')
        self.agents_table = self.dynamodb.Table('agentic-demo-agent-contexts')
        self.world_table = self.dynamodb.Table('agentic-demo-world-state')
        self.memories_table = self.dynamodb.Table('agentic-demo-character-memories')

    def run_turn(self, use_ai=True, specific_agents=None):
        """Run a simplified simulation turn"""
        try:
            # Get all agents
            agents_response = self.agents_table.scan()
            agents = agents_response.get('Items', [])
            
            # Get world state
            try:
                world_response = self.world_table.get_item(Key={'worldId': 'main'})
                world = world_response.get('Item', {})
            except:
                world = {'worldId': 'main', 'current_time': datetime.now().isoformat(), 'turn': 1}
            
            # Update world time and turn
            current_turn = world.get('turn', 1) + 1
            world['turn'] = current_turn
            world['current_time'] = datetime.now().isoformat()
            world['last_update'] = datetime.now().isoformat()
            
            # Save updated world state
            self.world_table.put_item(Item=world)
            
            # Simulate character changes
            updated_agents = []
            for agent in agents:
                agent_id = agent.get('agentId')
                if specific_agents and agent_id not in specific_agents:
                    continue
                    
                # Simple simulation: randomly adjust money and needs
                current_money = float(agent.get('money', 100))
                needs = agent.get('needs', {})
                
                # Random events based on character wealth
                if current_money > 100000:  # Rich characters
                    money_change = random.randint(-1000, 5000)
                    new_state = random.choice(['satisfied', 'bored', 'scheming', 'investing'])
                elif current_money > 1000:  # Middle class
                    money_change = random.randint(-200, 500)
                    new_state = random.choice(['working', 'stressed', 'hopeful', 'planning'])
                else:  # Poor characters
                    money_change = random.randint(-50, 100)
                    new_state = random.choice(['struggling', 'desperate', 'hustling', 'surviving'])
                
                # Update agent
                new_money = max(0, current_money + money_change)
                agent['money'] = Decimal(str(new_money))
                agent['current_state'] = new_state
                
                # Update needs
                if 'needs' not in agent:
                    agent['needs'] = {}
                
                # Adjust needs based on money
                if new_money < 100:
                    agent['needs']['hunger'] = min(100, needs.get('hunger', 0) + random.randint(5, 20))
                    agent['needs']['stress'] = min(100, needs.get('stress', 0) + random.randint(5, 15))
                    agent['needs']['exhaustion'] = min(100, needs.get('exhaustion', 0) + random.randint(5, 15))
                else:
                    agent['needs']['hunger'] = max(0, needs.get('hunger', 0) - random.randint(0, 10))
                    agent['needs']['stress'] = max(0, needs.get('stress', 0) - random.randint(0, 10))
                    agent['needs']['exhaustion'] = max(0, needs.get('exhaustion', 0) - random.randint(0, 10))
                
                # Generate content occasionally for creative characters
                should_create_content = random.random() < 0.3  # 30% chance per turn
                if should_create_content and agent_id in ['alex_chen', 'jamie_rodriguez', 'ashley_kim']:
                    self.generate_character_content(agent_id, agent, current_turn)
                
                # Save agent
                self.agents_table.put_item(Item=agent)
                updated_agents.append(agent_id)
                
                # Add a memory
                memory_text = f"Turn {current_turn}: {new_state}, money: ${new_money:.2f}"
                try:
                    memories_response = self.memories_table.get_item(Key={'characterId': agent_id})
                    memories_item = memories_response.get('Item', {'characterId': agent_id, 'memories': []})
                    memories = memories_item.get('memories', [])
                    memories.append({
                        'timestamp': datetime.now().isoformat(),
                        'event': memory_text,
                        'turn': current_turn
                    })
                    # Keep only last 10 memories
                    memories = memories[-10:]
                    memories_item['memories'] = memories
                    self.memories_table.put_item(Item=memories_item)
                except Exception as e:
                    print(f"Error updating memories for {agent_id}: {e}")
            
            return {
                'success': True,
                'turn': current_turn,
                'agents_updated': updated_agents,
                'world': world,
                'message': f"Simulation turn {current_turn} completed. Updated {len(updated_agents)} agents."
            }
            
        except Exception as e:
            print(f"Error in run_turn: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Simulation failed'
            }
    
    def generate_character_content(self, agent_id, agent, turn):
        """Generate content for creative characters"""
        try:
            content_templates = {
                'alex_chen': {
                    'topics': ['literary analysis', 'writing struggles', 'coffee shop observations', 'student debt reality'],
                    'format': 'blog',
                    'style': 'melancholic literary'
                },
                'jamie_rodriguez': {
                    'topics': ['film industry insights', 'LA survival guide', 'indie film reviews', 'networking tips'],
                    'format': 'blog',
                    'style': 'optimistic hustle'
                },
                'ashley_kim': {
                    'topics': ['tech career advice', 'investment strategies', 'work-life balance', 'impostor syndrome'],
                    'format': 'code',
                    'style': 'professional analytical'
                }
            }
            
            if agent_id not in content_templates:
                return
                
            template = content_templates[agent_id]
            topic = random.choice(template['topics'])
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            money = float(agent.get('money', 0))
            state = agent.get('current_state', 'unknown')
            
            # Create content based on character's situation
            if template['format'] == 'blog':
                if money < 100:
                    content = self.create_desperate_blog(agent_id, topic, state, money)
                else:
                    content = self.create_normal_blog(agent_id, topic, state, money)
                filename = f"{agent_id}_{timestamp}_{topic.replace(' ', '_')}.html"
                content_type = 'blogs'
            else:  # code
                content = self.create_code_project(agent_id, topic, state, money)
                filename = f"{agent_id}_{timestamp}_{topic.replace(' ', '_')}.py"
                content_type = 'code'
            
            # Upload to S3 (using existing content structure)
            s3_key = f"content/{agent_id}/{content_type}/{filename}"
            bucket_name = os.environ.get('CONTENT_BUCKET', 'agentic-demo-viewer-20250808-nyc-01')
            
            self.s3.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=content,
                ContentType='text/html' if content_type == 'blogs' else 'text/plain'
            )
            
            print(f"Generated content for {agent_id}: {filename}")
            return filename
            
        except Exception as e:
            print(f"Error generating content for {agent_id}: {e}")
            return None
    
    def create_desperate_blog(self, character, topic, state, money):
        """Create blog content for desperate characters"""
        templates = {
            'alex_chen': f"""<!DOCTYPE html>
<html><head><title>3AM Thoughts on {topic}</title></head><body>
<h1>3AM Thoughts on {topic}</h1>
<p><em>Currently {state}, ${money:.2f} in account</em></p>
<p>Another sleepless night at the library. The wifi cuts out every hour but it's still better than home... well, wherever home is this week.</p>
<p>I've been thinking about {topic} while nursing my third cup of day-old coffee. The barista gave me a look but didn't charge me for the refill. Small victories.</p>
<p>The cursor blinks mockingly at me. Seventeen rejection letters and counting. Maybe I should have studied something practical.</p>
<p>But here I am, still writing. Still believing that words matter, even when the rent doesn't care about beautiful sentences.</p>
<p><em>Posted from: Public Library, 3:24 AM</em></p>
</body></html>""",
            'jamie_rodriguez': f"""<!DOCTYPE html>
<html><head><title>Surviving LA: {topic}</title></head><body>
<h1>Surviving LA: {topic}</h1>
<p><em>Status: {state}, Bank account: ${money:.2f}</em></p>
<p>Day 847 in Los Angeles. Still here, still dreaming, still eating craft services leftovers for dinner.</p>
<p>Today's wisdom about {topic}: You can't make it in this town without connections, but you can't make connections without making it. Catch-22 city.</p>
<p>Shot a music video for exposure today. Literally. No pay, just exposure. My landlord doesn't accept exposure as currency.</p>
<p>But I met a DP who knows a guy who knows Sundance. Six degrees of Kevin Bacon, but for broke filmmakers.</p>
<p>Tomorrow: more coffee, more networking, more believing this is all worth it.</p>
<p><em>Typed on phone while waiting for the 101 bus</em></p>
</body></html>"""
        }
        return templates.get(character, f"<html><body><h1>{topic}</h1><p>Currently {state} with ${money:.2f}</p></body></html>")
    
    def create_normal_blog(self, character, topic, state, money):
        """Create blog content for stable characters"""
        return f"""<!DOCTYPE html>
<html><head><title>{topic.title()}</title></head><body>
<h1>{topic.title()}</h1>
<p><em>Status: {state}, Finances: ${money:.2f}</em></p>
<p>Some thoughts on {topic} from my current perspective...</p>
<p>Things are looking up lately. Having stable income changes everything about how you approach creative work.</p>
<p>More content coming soon!</p>
</body></html>"""
    
    def create_code_project(self, character, topic, state, money):
        """Create code content"""
        return f'''# {topic.title()}
# By {character.replace('_', ' ').title()}
# Status: {state}, Funds: ${money:.2f}

def main():
    """
    A quick project about {topic}
    Written during a {state} phase
    """
    print("Hello from {character}!")
    print("Working on: {topic}")
    
    # TODO: Implement actual functionality
    # Current budget: ${money:.2f}
    
if __name__ == "__main__":
    main()
'''
#!/usr/bin/env python3
"""
MCP Money-Making Systems for Characters
Connects poor characters to real opportunities that update their resources
"""

import json
import boto3
import subprocess
import os
import hashlib
from datetime import datetime
from decimal import Decimal

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')

# Money-making MCP opportunities
MONEY_OPPORTUNITIES = {
    'content_mill': {
        'description': 'Write articles for content mills',
        'rate_per_word': 0.01,  # 1 cent per word
        'minimum_words': 500,
        'tool': 'filesystem',
        'action': 'write_file'
    },
    'micro_tasks': {
        'description': 'Data labeling and micro tasks',
        'rate_per_task': 0.25,  # 25 cents per task
        'tasks_per_hour': 20,
        'tool': 'filesystem',
        'action': 'create_labels'
    },
    'code_bounties': {
        'description': 'Small bug fixes and code tasks',
        'rate_per_fix': 25,  # $25 per fix
        'difficulty': 'medium',
        'tool': 'github',
        'action': 'submit_pr'
    },
    'transcription': {
        'description': 'Audio transcription work',
        'rate_per_minute': 0.60,  # 60 cents per audio minute
        'tool': 'filesystem',
        'action': 'write_transcript'
    },
    'survey_farming': {
        'description': 'Complete online surveys',
        'rate_per_survey': 2,  # $2 per survey
        'surveys_per_day': 5,
        'tool': 'puppeteer',
        'action': 'complete_survey'
    }
}

def calculate_earnings(work_type, output):
    """Calculate how much character earned from their work"""
    
    opportunity = MONEY_OPPORTUNITIES[work_type]
    
    if work_type == 'content_mill':
        # Count words in output
        word_count = len(output.split())
        if word_count >= opportunity['minimum_words']:
            earnings = word_count * opportunity['rate_per_word']
            return earnings, f"Wrote {word_count} words at ${opportunity['rate_per_word']}/word"
        return 0, "Article too short, rejected"
        
    elif work_type == 'micro_tasks':
        # Simulate completing tasks
        tasks_completed = min(20, len(output) // 50)  # Rough estimate
        earnings = tasks_completed * opportunity['rate_per_task']
        return earnings, f"Completed {tasks_completed} tasks at ${opportunity['rate_per_task']}/task"
        
    elif work_type == 'transcription':
        # Estimate audio minutes from transcript length
        chars_per_minute = 600  # Average speaking rate
        minutes = len(output) / chars_per_minute
        earnings = minutes * opportunity['rate_per_minute']
        return earnings, f"Transcribed {minutes:.1f} minutes at ${opportunity['rate_per_minute']}/min"
        
    else:
        return 5, "Completed basic task"

def update_character_money(character_name, earnings, description):
    """Update character's money in DynamoDB"""
    
    try:
        # Get current character data
        response = memories_table.get_item(Key={'characterId': character_name})
        char_data = response['Item']
        
        # Update resources
        current_money = float(char_data.get('resources', {}).get('money', 0))
        new_money = current_money + earnings
        
        char_data['resources']['money'] = Decimal(str(new_money))
        
        # Add memory of earning
        memory = f"Earned ${earnings:.2f}: {description}"
        char_data['memories'].append(memory)
        
        # Save back to DynamoDB
        memories_table.put_item(Item=char_data)
        
        return current_money, new_money
        
    except Exception as e:
        print(f"Error updating money: {e}")
        return 0, earnings

def execute_money_making_mcp(character_name, work_type, content):
    """Execute MCP action to create monetizable content"""
    
    opportunity = MONEY_OPPORTUNITIES[work_type]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create work output file
    output_path = f"/Users/kentonblacutt/Documents/world/agentic/character_files/{character_name}/work_{timestamp}.txt"
    
    # Build MCP decision
    decision = {
        'character': character_name,
        'mcp_server': 'filesystem',
        'mcp_tool': 'write_file',
        'mcp_arguments': {
            'path': output_path,
            'content': content
        }
    }
    
    print(f"\n📝 Creating work output via MCP...")
    
    # Execute via MCP
    try:
        result = subprocess.run(
            ['node', 'real-mcp-connection.js', json.dumps(decision)],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=os.getcwd()
        )
        
        # Check if file was created
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                actual_content = f.read()
            
            print(f"✅ Work output saved: {output_path}")
            print(f"   Length: {len(actual_content)} characters")
            
            # Calculate earnings
            earnings, description = calculate_earnings(work_type, actual_content)
            
            return {
                'success': True,
                'earnings': earnings,
                'description': description,
                'output_path': output_path,
                'content_length': len(actual_content)
            }
            
    except Exception as e:
        print(f"❌ MCP Error: {e}")
        
    return {'success': False, 'earnings': 0}

def run_money_making_turn():
    """Run a turn where poor characters try to make money"""
    
    print("=== MCP MONEY-MAKING SYSTEM ===")
    print("Poor characters work to earn real money\n")
    
    scenarios = [
        {
            'character': 'alex_chen',
            'current_money': 47,
            'situation': 'Desperate for money, found content mill that pays per article',
            'work_type': 'content_mill'
        },
        {
            'character': 'brittany_torres',
            'current_money': 128,
            'situation': 'Between delivery runs, doing transcription work on phone',
            'work_type': 'transcription'
        },
        {
            'character': 'maria_gonzalez',
            'current_money': 340,
            'situation': 'Break between shifts, doing micro tasks for extra cash',
            'work_type': 'micro_tasks'
        }
    ]
    
    ws_url = 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod'
    
    for scenario in scenarios:
        print(f"\n{'='*60}")
        print(f"CHARACTER: {scenario['character'].upper()}")
        print(f"Current money: ${scenario['current_money']}")
        print(f"Situation: {scenario['situation']}")
        print(f"Work type: {scenario['work_type']}")
        print('='*60)
        
        opportunity = MONEY_OPPORTUNITIES[scenario['work_type']]
        
        # Get AI to generate work output
        prompt = f"""You are {scenario['character'].replace('_', ' ').title()} with ${scenario['current_money']}.

SITUATION: {scenario['situation']}

You need to create content for: {opportunity['description']}
Payment rate: {json.dumps(opportunity)}

Generate the actual work output (article, transcript, or task responses).
Make it at least 500 words if it's an article, or appropriate length for the task.

Reply with JSON:
{{
  "thought": "your desperate reasoning",
  "work_output": "the actual content you create to earn money",
  "hope": "how much you hope to earn"
}}"""

        print("\n🤖 AI generating work output...")
        
        try:
            response = bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                contentType='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': 1000,
                    'temperature': 0.7,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            text = result['content'][0]['text']
            
            # Parse JSON
            import re
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
                
                print(f"Thought: {decision['thought'][:70]}...")
                print(f"Hope: {decision['hope'][:70]}...")
                
                # Execute work via MCP and calculate earnings
                work_result = execute_money_making_mcp(
                    scenario['character'],
                    scenario['work_type'],
                    decision['work_output']
                )
                
                if work_result['success']:
                    print(f"\n💰 EARNINGS: ${work_result['earnings']:.2f}")
                    print(f"   {work_result['description']}")
                    
                    # Update character's money in database
                    old_money, new_money = update_character_money(
                        scenario['character'],
                        work_result['earnings'],
                        work_result['description']
                    )
                    
                    print(f"\n💵 MONEY UPDATE:")
                    print(f"   Before: ${old_money:.2f}")
                    print(f"   Earned: ${work_result['earnings']:.2f}")
                    print(f"   After:  ${new_money:.2f}")
                    
                    # Send to telemetry
                    try:
                        ws = websocket.WebSocket()
                        ws.connect(ws_url)
                        msg = {
                            'goal': f"[{scenario['character']}] Make money to survive",
                            'action': f"Created {scenario['work_type']} content",
                            'rationale': f"Earned ${work_result['earnings']:.2f}",
                            'result': f"New balance: ${new_money:.2f}"
                        }
                        ws.send(json.dumps(msg))
                        ws.close()
                    except:
                        pass
                        
                else:
                    print("❌ Work rejected or failed")
                    
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("MONEY-MAKING COMPLETE")
    print("="*60)
    print("\nPoor characters exchanged labor for small amounts of money")
    print("Their bank accounts were actually updated in the database")
    print("This is how they survive - penny by penny")

if __name__ == "__main__":
    run_money_making_turn()
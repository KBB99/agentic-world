#!/usr/bin/env python3
"""
Simple Money-Making System via MCP
Characters create content, earn money, update their resources
"""

import json
import boto3
import subprocess
import os
from datetime import datetime
from decimal import Decimal

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')

print("=== ALEX CHEN MAKES MONEY VIA MCP ===\n")

# 1. Get current money
print("1. Checking Alex's current funds...")
try:
    response = memories_table.get_item(Key={'characterId': 'alex_chen'})
    char_data = response['Item']
    current_money = float(char_data.get('resources', {}).get('money', 47))
    print(f"   Current balance: ${current_money:.2f}")
except:
    char_data = {'characterId': 'alex_chen', 'memories': [], 'resources': {'money': Decimal('47')}}
    current_money = 47
    print(f"   Starting balance: ${current_money:.2f}")

# 2. AI decides what content to create
print("\n2. AI deciding what to write for money...")
prompt = """You are Alex Chen, desperate writer with $47.

You found a content mill that pays $0.01 per word (minimum 500 words).
Write an article about "5 Ways to Save Money When You're Broke"
Make it at least 500 words so you earn at least $5.

Write the ACTUAL ARTICLE TEXT (not JSON, just the article)."""

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
article_content = result['content'][0]['text']

word_count = len(article_content.split())
earnings = word_count * 0.01

print(f"   Generated {word_count} words")
print(f"   Will earn: ${earnings:.2f}")
print(f"   Preview: {article_content[:100]}...")

# 3. Save via MCP
print("\n3. Saving work via MCP filesystem server...")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_path = f"/Users/kentonblacutt/Documents/world/agentic/character_files/alex_chen/paid_article_{timestamp}.txt"

decision = {
    'character': 'alex_chen',
    'mcp_server': 'filesystem',
    'mcp_tool': 'write_file',
    'mcp_arguments': {
        'path': output_path,
        'content': f"PAID ARTICLE - {word_count} words @ $0.01/word = ${earnings:.2f}\n\n{article_content}"
    }
}

# Execute via MCP
result = subprocess.run(
    ['node', 'real-mcp-connection.js', json.dumps(decision)],
    capture_output=True,
    text=True,
    timeout=30,
    cwd=os.getcwd()
)

# Check if file was created
if os.path.exists(output_path):
    file_size = os.path.getsize(output_path)
    print(f"   ✅ Article saved: {output_path}")
    print(f"   File size: {file_size} bytes")
else:
    print("   ❌ Failed to save")

# 4. Update Alex's money in database
print("\n4. Updating Alex's bank account...")
new_money = current_money + earnings

char_data['resources']['money'] = Decimal(str(new_money))
char_data['memories'].append(f"Wrote {word_count}-word article, earned ${earnings:.2f}")

memories_table.put_item(Item=char_data)

print(f"   💰 MONEY UPDATED:")
print(f"      Before: ${current_money:.2f}")
print(f"      Earned: ${earnings:.2f}")
print(f"      After:  ${new_money:.2f}")

# 5. Verify the update
print("\n5. Verifying database update...")
response = memories_table.get_item(Key={'characterId': 'alex_chen'})
verified_money = float(response['Item']['resources']['money'])
print(f"   Database confirms: ${verified_money:.2f}")

print("\n" + "="*60)
print("SUCCESS!")
print("="*60)
print(f"Alex Chen wrote {word_count} words")
print(f"Earned ${earnings:.2f} at $0.01 per word")
print(f"Money increased from ${current_money:.2f} to ${new_money:.2f}")
print(f"File saved: {output_path}")
print("\nThis is how poor characters survive:")
print("Trading hours of labor for pennies, but it's real money.")
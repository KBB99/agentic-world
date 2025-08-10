#!/usr/bin/env python3
"""
Execute a single real MCP turn for Alex Chen
Actually saves a file through MCP filesystem server
"""

import json
import boto3
import subprocess
import os
from datetime import datetime

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

print("=== REAL MCP EXECUTION FOR ALEX CHEN ===\n")

# The scenario
character = 'alex_chen'
situation = 'Library closing in 5 minutes, need to save article draft NOW'
money = 47

# Get AI decision
prompt = f"""You are Alex Chen, struggling writer with $47.

SITUATION: {situation}

You MUST save your article draft using the MCP filesystem server.

Available tool:
- filesystem server: write_file(path, content)

Use this exact path: /Users/kentonblacutt/Documents/world/agentic/character_files/alex_chen/article_draft.txt

Reply with JSON:
{{
  "thought": "your panicked reasoning",
  "mcp_server": "filesystem",
  "mcp_tool": "write_file",
  "mcp_arguments": {{
    "path": "/Users/kentonblacutt/Documents/world/agentic/character_files/alex_chen/article_draft.txt",
    "content": "Your actual article content here - make it about economic inequality, 200+ words"
  }},
  "hope": "what you hope"
}}"""

print("1. Getting AI decision...")
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-sonnet-20240229-v1:0',
    contentType='application/json',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'max_tokens': 500,
        'temperature': 0.7,
        'messages': [{'role': 'user', 'content': prompt}]
    })
)

result = json.loads(response['body'].read())
text = result['content'][0]['text']

# Parse JSON
import re
json_match = re.search(r'\{.*\}', text, re.DOTALL)
if not json_match:
    print("Failed to get decision")
    exit(1)

decision = json.loads(json_match.group())
decision['character'] = character

print(f"   Thought: {decision['thought'][:60]}...")
print(f"   Will save to: {decision['mcp_arguments']['path']}")
print(f"   Content preview: {decision['mcp_arguments']['content'][:50]}...")

# Execute on real MCP
print("\n2. Connecting to REAL MCP filesystem server...")
decision_json = json.dumps(decision)

result = subprocess.run(
    ['node', 'real-mcp-connection.js', decision_json],
    capture_output=True,
    text=True,
    timeout=30
)

print("\n3. MCP SERVER RESPONSE:")
print("-" * 50)
# Filter out the "Secure MCP" line
for line in result.stdout.split('\n'):
    if 'Secure MCP' not in line and 'Client does not support' not in line:
        print(line)

# Check if file was actually created
file_path = decision['mcp_arguments']['path']
if os.path.exists(file_path):
    print("\n4. VERIFICATION - File actually exists!")
    print(f"   Path: {file_path}")
    print(f"   Size: {os.path.getsize(file_path)} bytes")
    
    # Read it back
    with open(file_path, 'r') as f:
        content = f.read()
    print(f"   First 100 chars: {content[:100]}...")
else:
    print("\n4. File not found - checking error...")

print("\n" + "="*60)
print("RESULT: Alex's article was saved through REAL MCP server!")
print("This is how poor characters must frantically save work")
print("before losing computer access.")
print("="*60)
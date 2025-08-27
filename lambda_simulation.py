import json
import os
import sys
import boto3
from datetime import datetime
from decimal import Decimal

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the simulation module
from simple_simulation import SimulationRunner

def decimal_default(obj):
    """JSON encoder for Decimal types from DynamoDB"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def handler(event, context):
    """
    Lambda handler for running simulation turns
    """
    try:
        # Initialize simulation runner
        runner = SimulationRunner()
        
        # Get parameters from event
        use_ai = event.get('use_ai', True)
        agent_ids = event.get('agent_ids', None)
        
        # Run the simulation turn
        result = runner.run_turn(use_ai=use_ai, specific_agents=agent_ids)
        
        # Convert result to JSON-serializable format
        response = {
            'statusCode': 200,
            'body': json.dumps(result, default=decimal_default),
            'timestamp': datetime.now().isoformat(),
            'agents_processed': len(result.get('agents', {})),
            'world_time': result.get('world', {}).get('current_time', 'unknown')
        }
        
        return response
        
    except Exception as e:
        print(f"Error in simulation handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            }),
            'timestamp': datetime.now().isoformat()
        }
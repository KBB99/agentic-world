#!/usr/bin/env python3
"""
Cost Control and Tracking System
Monitors AWS usage and provides pause/resume functionality
"""

import json
import boto3
import os
from datetime import datetime, timedelta
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
cloudwatch = boto3.client('cloudwatch', region_name='us-east-1')
pricing = boto3.client('pricing', region_name='us-east-1')

# Control file for pause state
PAUSE_FILE = '/Users/kentonblacutt/Documents/world/agentic/.paused'
COST_LOG = '/Users/kentonblacutt/Documents/world/agentic/costs.json'

class CostTracker:
    """Track and estimate costs for AWS services"""
    
    def __init__(self):
        self.costs = self.load_costs()
        
        # Pricing estimates (as of 2024)
        self.pricing = {
            'bedrock_claude_sonnet': {
                'input_per_1k_tokens': 0.003,
                'output_per_1k_tokens': 0.015
            },
            'dynamodb': {
                'read_per_million': 0.25,
                'write_per_million': 1.25,
                'storage_per_gb_month': 0.25
            },
            'websocket_api': {
                'messages_per_million': 1.00,
                'connection_minutes_per_million': 0.25
            },
            'medialive': {
                'standard_channel_per_hour': 0.59,  # Standard input
                'hd_channel_per_hour': 2.30  # HD input
            },
            'ec2_gpu': {
                'g4dn_xlarge_per_hour': 0.526,  # GPU instance for Unreal
                't3_medium_per_hour': 0.0416  # Regular instance
            }
        }
        
    def load_costs(self):
        """Load cost history from file"""
        if os.path.exists(COST_LOG):
            try:
                with open(COST_LOG, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'sessions': [],
            'total_estimated': 0.0,
            'daily_totals': {},
            'service_totals': {}
        }
        
    def save_costs(self):
        """Save cost history to file"""
        with open(COST_LOG, 'w') as f:
            json.dump(self.costs, f, indent=2, default=str)
            
    def track_bedrock_call(self, input_tokens=100, output_tokens=100):
        """Track a Bedrock API call"""
        cost = (input_tokens / 1000 * self.pricing['bedrock_claude_sonnet']['input_per_1k_tokens'] +
                output_tokens / 1000 * self.pricing['bedrock_claude_sonnet']['output_per_1k_tokens'])
        
        self.add_cost('bedrock', cost, {
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        })
        return cost
        
    def track_dynamodb_operation(self, reads=0, writes=0):
        """Track DynamoDB operations"""
        cost = (reads / 1000000 * self.pricing['dynamodb']['read_per_million'] +
                writes / 1000000 * self.pricing['dynamodb']['write_per_million'])
        
        self.add_cost('dynamodb', cost, {
            'reads': reads,
            'writes': writes
        })
        return cost
        
    def track_websocket_message(self):
        """Track WebSocket API message"""
        cost = self.pricing['websocket_api']['messages_per_million'] / 1000000
        self.add_cost('websocket', cost, {'messages': 1})
        return cost
        
    def add_cost(self, service, amount, details=None):
        """Add cost to tracking"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'service': service,
            'amount': amount,
            'details': details
        }
        
        self.costs['sessions'].append(entry)
        self.costs['total_estimated'] += amount
        
        # Update daily total
        if today not in self.costs['daily_totals']:
            self.costs['daily_totals'][today] = 0
        self.costs['daily_totals'][today] += amount
        
        # Update service total
        if service not in self.costs['service_totals']:
            self.costs['service_totals'][service] = 0
        self.costs['service_totals'][service] += amount
        
        self.save_costs()
        
    def get_today_cost(self):
        """Get today's total cost"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.costs['daily_totals'].get(today, 0.0)
        
    def get_summary(self):
        """Get cost summary"""
        return {
            'total': self.costs['total_estimated'],
            'today': self.get_today_cost(),
            'by_service': self.costs['service_totals'],
            'sessions_count': len(self.costs['sessions'])
        }

class PauseControl:
    """Control system to pause/resume AI operations"""
    
    @staticmethod
    def is_paused():
        """Check if system is paused"""
        return os.path.exists(PAUSE_FILE)
        
    @staticmethod
    def pause():
        """Pause all AI operations"""
        with open(PAUSE_FILE, 'w') as f:
            f.write(json.dumps({
                'paused_at': datetime.now().isoformat(),
                'reason': 'Manual pause to prevent costs'
            }))
        print("⏸️  SYSTEM PAUSED - No AI calls will be made")
        return True
        
    @staticmethod
    def resume():
        """Resume AI operations"""
        if os.path.exists(PAUSE_FILE):
            os.remove(PAUSE_FILE)
            print("▶️  SYSTEM RESUMED - AI operations enabled")
            return True
        return False
        
    @staticmethod
    def get_status():
        """Get pause status"""
        if os.path.exists(PAUSE_FILE):
            try:
                with open(PAUSE_FILE, 'r') as f:
                    data = json.load(f)
                    return {
                        'paused': True,
                        'since': data.get('paused_at'),
                        'reason': data.get('reason')
                    }
            except:
                pass
        return {'paused': False}

class SafeAIClient:
    """Wrapper for AI operations with cost tracking and pause control"""
    
    def __init__(self):
        self.tracker = CostTracker()
        self.bedrock = bedrock
        
    def invoke_model_safe(self, prompt, max_tokens=100):
        """Safely invoke Bedrock with cost tracking and pause check"""
        
        # Check if paused
        if PauseControl.is_paused():
            print("❌ AI CALL BLOCKED - System is paused")
            return {
                'error': 'System paused',
                'message': 'Use resume-ai.sh to enable AI calls'
            }
            
        # Check cost threshold
        today_cost = self.tracker.get_today_cost()
        if today_cost > 10.0:  # $10 daily limit
            PauseControl.pause()
            print(f"⚠️  DAILY LIMIT REACHED (${today_cost:.2f}) - Auto-paused")
            return {
                'error': 'Daily limit reached',
                'cost': today_cost
            }
            
        try:
            # Make the actual call
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                contentType='application/json',
                body=json.dumps({
                    'anthropic_version': 'bedrock-2023-05-31',
                    'max_tokens': max_tokens,
                    'messages': [{'role': 'user', 'content': prompt}]
                })
            )
            
            result = json.loads(response['body'].read())
            
            # Track cost (rough estimate)
            input_tokens = len(prompt.split()) * 1.3  # Rough token estimate
            output_tokens = max_tokens * 0.7  # Assume 70% of max
            cost = self.tracker.track_bedrock_call(input_tokens, output_tokens)
            
            print(f"💵 AI call cost: ${cost:.4f} (Today: ${self.tracker.get_today_cost():.2f})")
            
            return {
                'success': True,
                'content': result['content'][0]['text'],
                'cost': cost
            }
            
        except Exception as e:
            return {
                'error': str(e)
            }

def check_running_services():
    """Check which AWS services are currently running"""
    
    print("\n=== CHECKING RUNNING SERVICES ===")
    
    services_status = {}
    
    # Check MediaLive channels
    try:
        medialive = boto3.client('medialive', region_name='us-east-1')
        channels = medialive.list_channels()
        
        running_channels = []
        for channel in channels.get('Channels', []):
            if channel['State'] in ['RUNNING', 'STARTING']:
                running_channels.append({
                    'id': channel['Id'],
                    'name': channel['Name'],
                    'state': channel['State']
                })
                
        services_status['medialive'] = {
            'running': len(running_channels) > 0,
            'channels': running_channels,
            'estimated_hourly_cost': len(running_channels) * 0.59
        }
        
        if running_channels:
            print(f"⚠️  MediaLive: {len(running_channels)} channels RUNNING (${len(running_channels) * 0.59}/hour)")
        else:
            print("✅ MediaLive: No channels running")
            
    except Exception as e:
        print(f"❌ MediaLive: Could not check - {e}")
        
    # Check EC2 instances
    try:
        ec2 = boto3.client('ec2', region_name='us-east-1')
        instances = ec2.describe_instances(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
        )
        
        running_instances = []
        hourly_cost = 0
        
        for reservation in instances['Reservations']:
            for instance in reservation['Instances']:
                instance_type = instance['InstanceType']
                
                # Estimate cost based on instance type
                if 'g4dn' in instance_type:
                    cost = 0.526
                elif 't3.medium' in instance_type:
                    cost = 0.0416
                else:
                    cost = 0.10  # Default estimate
                    
                hourly_cost += cost
                running_instances.append({
                    'id': instance['InstanceId'],
                    'type': instance_type,
                    'hourly_cost': cost
                })
                
        services_status['ec2'] = {
            'running': len(running_instances) > 0,
            'instances': running_instances,
            'estimated_hourly_cost': hourly_cost
        }
        
        if running_instances:
            print(f"⚠️  EC2: {len(running_instances)} instances RUNNING (${hourly_cost:.2f}/hour)")
        else:
            print("✅ EC2: No instances running")
            
    except Exception as e:
        print(f"❌ EC2: Could not check - {e}")
        
    # Calculate total hourly burn rate
    total_hourly = sum(s.get('estimated_hourly_cost', 0) for s in services_status.values())
    
    if total_hourly > 0:
        print(f"\n💸 TOTAL BURN RATE: ${total_hourly:.2f}/hour (${total_hourly * 24:.2f}/day)")
        print("⚠️  Consider stopping unused services!")
    else:
        print("\n✅ No expensive services running")
        
    return services_status

def main():
    """Main cost control interface"""
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 cost-control.py [command]")
        print("Commands:")
        print("  status    - Show pause status and costs")
        print("  pause     - Pause all AI operations")
        print("  resume    - Resume AI operations")
        print("  costs     - Show detailed cost breakdown")
        print("  check     - Check running AWS services")
        print("  reset     - Reset cost tracking")
        return
        
    command = sys.argv[1]
    
    if command == 'status':
        pause_status = PauseControl.get_status()
        tracker = CostTracker()
        summary = tracker.get_summary()
        
        print("\n=== SYSTEM STATUS ===")
        if pause_status['paused']:
            print(f"⏸️  PAUSED since {pause_status['since']}")
            print(f"   Reason: {pause_status['reason']}")
        else:
            print("▶️  RUNNING - AI operations enabled")
            
        print(f"\n=== COST SUMMARY ===")
        print(f"Today: ${summary['today']:.4f}")
        print(f"Total: ${summary['total']:.4f}")
        print(f"Sessions: {summary['sessions_count']}")
        
        if summary['by_service']:
            print("\nBy Service:")
            for service, cost in summary['by_service'].items():
                print(f"  {service}: ${cost:.4f}")
                
        check_running_services()
        
    elif command == 'pause':
        PauseControl.pause()
        
    elif command == 'resume':
        PauseControl.resume()
        
    elif command == 'costs':
        tracker = CostTracker()
        summary = tracker.get_summary()
        
        print("\n=== DETAILED COSTS ===")
        print(f"Total Estimated: ${summary['total']:.4f}")
        
        if summary['by_service']:
            print("\nBy Service:")
            for service, cost in summary['by_service'].items():
                print(f"  {service}: ${cost:.4f}")
                
        if tracker.costs['daily_totals']:
            print("\nDaily Totals:")
            for date, cost in sorted(tracker.costs['daily_totals'].items())[-7:]:
                print(f"  {date}: ${cost:.4f}")
                
    elif command == 'check':
        check_running_services()
        
    elif command == 'reset':
        if os.path.exists(COST_LOG):
            os.remove(COST_LOG)
            print("✅ Cost tracking reset")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()
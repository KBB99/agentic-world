#!/usr/bin/env python3
"""
Create diverse characters including successful ones and female characters
Shows the full spectrum of economic experiences
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal

# AWS clients
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
contexts_table = dynamodb.Table('agentic-demo-agent-contexts')

def create_character(character_id, profile):
    """Create a character with initial memories and context"""
    
    # Save to memories table
    memories_table.put_item(Item={
        'characterId': character_id,
        'memories': profile['initial_memories'],
        'resources': {k: Decimal(str(v)) if isinstance(v, (int, float)) else v 
                     for k, v in profile['resources'].items()},
        'location': profile['location'],
        'lastUpdated': datetime.now().isoformat()
    })
    
    # Save to contexts table
    contexts_table.put_item(Item={
        'agentId': character_id,
        'personality': profile['personality'],
        'background': profile['background'],
        'current_situation': profile['current_situation'],
        'stress_response': profile['stress_response'],
        'goals': profile['goals'],
        'current_state': profile['current_state']
    })
    
    print(f"✓ Created: {character_id}")
    return character_id

# Create diverse characters
characters = {
    # Successful tech bro benefiting from system
    'tyler_chen': {
        'personality': 'Tech PM at FAANG, stock options vesting, believes in meritocracy. Genuinely thinks everyone could succeed if they worked harder.',
        'background': '29yo, Stanford CS, parents paid tuition, $180K base + $200K stock/year. Has investment property.',
        'current_situation': 'Just got promoted, buying second rental property, complains about taxes',
        'stress_response': 'Checks portfolio, posts on LinkedIn about grinding, orders $30 smoothie',
        'goals': ['FIRE by 35', 'Angel invest', 'Build passive income', 'Minimize taxes'],
        'current_state': 'thriving',
        'initial_memories': [
            'RSUs vested, gained $80K this month',
            'Bought rental property in gentrifying neighborhood',
            'Complained about 40% tax rate at brunch'
        ],
        'resources': {'money': 45000, 'investments': 380000, 'energy': 'high'},
        'location': 'luxury_apartment'
    },
    
    # Single mom nurse
    'maria_gonzalez': {
        'personality': 'ICU nurse, single mom of two, exhausted but fierce. Union organizer, sees everything, trusts no one in power.',
        'background': '38yo, nursing degree, $75K/year, childcare costs $2K/month, no family nearby',
        'current_situation': 'Working 60hr weeks, kids need school supplies, ex disappeared',
        'stress_response': 'Power naps in car, energy drinks, cries in supply closet',
        'goals': ['Keep kids safe', 'Save for their college', 'Get through the week', 'Fight for better ratios'],
        'current_state': 'surviving',
        'initial_memories': [
            'Worked 16-hour shift, patient died',
            'Daycare late fee again, $50 gone',
            'Union meeting tonight but need to find babysitter',
            'Tyler Chen was my COVID patient, didn\'t recognize me at coffee shop'
        ],
        'resources': {'money': 340, 'energy': 'depleted', 'patience': 'thin'},
        'location': 'hospital'
    },
    
    # Young finance woman climbing ladder
    'ashley_kim': {
        'personality': 'Investment analyst, imposter syndrome, code switches constantly. Pretends to love golf.',
        'background': '26yo, first-gen American, Wharton MBA, $110K + bonus. Parents sacrificed everything.',
        'current_situation': 'Only woman on team, working 90hr weeks for promotion',
        'stress_response': 'Adderall, designer bags, perfect Instagram, silent panic attacks',
        'goals': ['Make VP', 'Pay off MBA loans', 'Buy parents a house', 'Prove she belongs'],
        'current_state': 'anxious_achieving',
        'initial_memories': [
            'Boss asked me to get coffee for client meeting again',
            'Bonus was 40% less than male colleague',
            'Parents proud but don\'t understand the pressure',
            'Saw Tyler Chen\'s LinkedIn post about "working smart not hard"'
        ],
        'resources': {'money': 8500, 'debt': -95000, 'reputation': 'building'},
        'location': 'office'
    },
    
    # Retired teacher on fixed income
    'dorothy_jackson': {
        'personality': 'Retired teacher, 68yo, sharp as hell, watching neighborhood gentrify. Raised everyone, now priced out.',
        'background': 'Taught for 35 years, pension $2800/month, property tax doubled, medical costs rising',
        'current_situation': 'Choosing between medications and groceries, house needs repairs',
        'stress_response': 'Knits furiously, writes letters to representatives, helps neighbors',
        'goals': ['Keep house', 'Stay independent', 'Help struggling young people', 'Fight gentrification'],
        'current_state': 'worried_but_wise',
        'initial_memories': [
            'Property tax bill arrived, up 30% again',
            'New luxury building going up next door',
            'Helped Alex with resume, reminded me of former student',
            'Tyler Chen\'s company buying up the block'
        ],
        'resources': {'money': 1200, 'wisdom': 'infinite', 'time': 'plenty'},
        'location': 'old_house'
    },
    
    # Gig economy queen juggling apps
    'brittany_torres': {
        'personality': 'Multi-app driver, entrepreneur mindset but no capital. Calls it "being her own boss" but algorithms control everything.',
        'background': '31yo, some college, drives Uber/DoorDash/Instacart, makes $35K, no benefits',
        'current_situation': 'Car needs brakes, gas prices up, fighting deactivation on DoorDash',
        'stress_response': 'Manifesting, MLM side hustles, financial TikTok, crying in parking lots',
        'goals': ['Fix car', 'Start real business', 'Get health insurance', 'Escape gig trap'],
        'current_state': 'hustling',
        'initial_memories': [
            'Made $47 in 6 hours after gas',
            'Delivered to Tyler\'s luxury building, no tip',
            'Car making weird noise, can\'t afford mechanic',
            'Saw Maria at hospital delivery, both pretended not to know each other'
        ],
        'resources': {'money': 128, 'gas': 'quarter_tank', 'apps_active': 4},
        'location': 'car'
    }
}

print("=== CREATING DIVERSE CHARACTER SET ===\n")

for char_id, profile in characters.items():
    create_character(char_id, profile)

print("\n=== CHARACTER RELATIONSHIPS ===")
print("• Tyler (successful) buying property that prices out others")
print("• Maria (nurse) saved Tyler during COVID, he doesn't remember")
print("• Ashley (finance) sees Tyler's success, feels pressure")
print("• Dorothy (retired) watching Tyler's company gentrify her block")
print("• Brittany (gig) delivers to Tyler, never gets tipped")
print("• Alex & Jamie (existing) facing eviction from Tyler-types")

print("\n=== ECONOMIC SPECTRUM ===")
print("Thriving:  Tyler ($425K assets)")
print("Climbing:  Ashley ($8.5K cash, -$95K debt)")
print("Surviving: Maria ($340)")
print("Struggling: Alex ($47), Jamie ($27), Brittany ($128)")
print("Fixed:     Dorothy ($1200)")

print("\n✅ Characters created with interconnected stories!")
print("Their paths will cross and affect each other in the narrative")
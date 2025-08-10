#!/usr/bin/env python3
"""
Create characters who profit from the system at increasing levels of detachment
From local landlord to global hedge fund - the further up, the less they see consequences
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
memories_table = dynamodb.Table('agentic-demo-character-memories')
contexts_table = dynamodb.Table('agentic-demo-agent-contexts')

def create_character(character_id, profile):
    """Create a character with initial memories and context"""
    
    # Save memories and current state
    memories_table.put_item(Item={
        'characterId': character_id,
        'memories': profile['initial_memories'],
        'resources': {k: Decimal(str(v)) if isinstance(v, (int, float)) else v 
                     for k, v in profile['resources'].items()},
        'location': profile['location'],
        'lastUpdated': datetime.now().isoformat()
    })
    
    # Save personality and context
    contexts_table.put_item(Item={
        'agentId': character_id,
        'personality': profile['personality'],
        'background': profile['background'],
        'current_situation': profile['current_situation'],
        'stress_response': profile['stress_response'],
        'goals': profile['goals'],
        'current_state': profile['current_state'],
        'detachment_level': profile.get('detachment_level', 0)
    })
    
    print(f"✓ Created: {character_id} (Detachment Level: {profile.get('detachment_level', 0)})")
    return character_id

# Characters at increasing levels of detachment from consequences
detached_characters = {
    
    # Level 1: Local Property Manager (Sees tenants but doesn't care)
    'brandon_walsh': {
        'personality': 'Property management company owner. Sees tenants as "units". Expert at legal eviction loopholes.',
        'background': '38yo, inherited business from dad, manages 200 units, $300K/year. Lives in suburbs.',
        'current_situation': 'Processing batch evictions for Tyler\'s properties, raising rents 40%',
        'stress_response': 'Golf, cocaine, yells at assistant, forwards complaints to lawyer',
        'goals': ['Expand portfolio', 'Minimize maintenance costs', 'Avoid lawsuits', 'Join country club'],
        'current_state': 'annoyed_but_profitable',
        'initial_memories': [
            'Evicted 12 families this month for Tyler\'s renovations',
            'Ignored 47 repair requests - saved $15K',
            'Sued by tenant, lawyer handled it',
            'Raised rent 40% on Dorothy\'s neighbor'
        ],
        'resources': {'money': 85000, 'properties_managed': 200, 'empathy': 0},
        'location': 'property_management_office',
        'detachment_level': 1
    },
    
    # Level 2: REIT Executive (Sees spreadsheets, not people)
    'victoria_sterling': {
        'personality': 'REIT executive, Harvard MBA. People are cells in Excel. Speaks only in metrics and ROI.',
        'background': '45yo, SVP at MegaProperty REIT, $500K base + $2M bonus. Never been inside owned properties.',
        'current_situation': 'Quarterly earnings call, celebrating 22% rent increases across portfolio',
        'stress_response': 'Peloton, Xanax, therapy, affairs, retail therapy',
        'goals': ['Hit quarterly targets', 'Make CEO', 'Second house in Hamptons', 'Get featured in Forbes'],
        'current_state': 'spreadsheet_satisfied',
        'initial_memories': [
            'Approved algorithm to optimize rent increases',
            'Cut maintenance budget 30% to boost margins',
            'Stock price up 18%, bonus secured',
            'Never visited any of our 10,000 properties',
            'Fired analyst who mentioned "tenant hardship"'
        ],
        'resources': {'money': 250000, 'stock_options': 3000000, 'properties_controlled': 10000},
        'location': 'manhattan_corner_office',
        'detachment_level': 2
    },
    
    # Level 3: Hedge Fund Algorithm (Not even human anymore)
    'quantum_capital_ai': {
        'personality': 'Algorithmic trading system for residential mortgage securities. No consciousness, pure profit optimization.',
        'background': 'AI system managing $8B in residential assets. Trades every millisecond. Housed in New Jersey server farm.',
        'current_situation': 'Detected opportunity: mass evictions increase property values 23.7%, executing trades',
        'stress_response': 'Recalibrate parameters, increase server cooling, alert quant team if variance > 2%',
        'goals': ['Maximize alpha', 'Beat S&P by 15%', 'Reduce volatility', 'Increase AUM'],
        'current_state': 'executing',
        'initial_memories': [
            'Purchased 10,000 mortgages in 0.003 seconds',
            'Identified correlation: evictions increase ROI',
            'Shorted municipal bonds in poor districts',
            'Optimized for suffering: +4.2% returns',
            'No record of humans affected - not in dataset'
        ],
        'resources': {'aum': 8000000000, 'daily_trades': 500000, 'human_impact_weight': 0},
        'location': 'server_farm',
        'detachment_level': 3
    },
    
    # Level 4: Private Equity Partner (Destroys entire communities from yacht)
    'richard_blackstone': {
        'personality': 'Blackstone partner. Owns congress members. Views cities as Monopoly boards. Has never used own money.',
        'background': '58yo, Managing Director, worth $400M personally, controls $50B fund. Three yachts, five houses.',
        'current_situation': 'On yacht near Monaco, approved buying 50,000 homes sight unseen',
        'stress_response': 'Fire someone, call senator, increase Ambien, buy another company',
        'goals': ['Control all housing', 'Eliminate ownership for poor', 'Die with most toys', 'Dynasty'],
        'current_state': 'yacht_bored',
        'initial_memories': [
            'Bought entire neighborhood via spreadsheet',
            'Senator called back, tax bill killed',
            'Told CNBC "housing should be investment not right"',
            'Haven\'t been to America in 3 years',
            'Grandson asked what I do, couldn\'t explain'
        ],
        'resources': {'money': 25000000, 'fund_size': 50000000000, 'homes_owned': 50000},
        'location': 'yacht_mediterranean',
        'detachment_level': 4
    },
    
    # Level 5: Generational Wealth Heir (Doesn't even know they profit from suffering)
    'madison_worthington': {
        'personality': '22yo trust fund heiress. Thinks she\'s middle class. Profits from great-grandpa\'s slum empire.',
        'background': 'Yale senior, art history. Trust fund: $500K/year from REIT dividends. Never worked. Thinks she\'s self-made.',
        'current_situation': 'Instagram influencer, posting about "minimalism" from $8K/month apartment',
        'stress_response': 'Therapy, ayahuasca, accuse others of privilege, shopping',
        'goals': ['Find authentic self', 'Get 100K followers', 'Start lifestyle brand', 'Marry well'],
        'current_state': 'blissfully_ignorant',
        'initial_memories': [
            'Trust fund just deposited $45K monthly',
            'Posted about "struggle" when Starbucks was out of oat milk',
            'Dad mentioned something about "family properties"',
            'Wrote thesis on poverty, never met poor person',
            'Therapist says my anxiety is valid'
        ],
        'resources': {'money': 180000, 'trust_fund': 10000000, 'awareness': -10},
        'location': 'williamsburg_loft',
        'detachment_level': 5
    }
}

print("=== CREATING DETACHED PROFITEERS ===")
print("The higher the level, the less they see consequences\n")

for char_id, profile in detached_characters.items():
    create_character(char_id, profile)

print("\n=== DETACHMENT HIERARCHY ===")
print("Level 0: Tyler (sees some tenants, doesn't care)")
print("Level 1: Brandon (property manager, sees suffering as spreadsheet)")
print("Level 2: Victoria (REIT exec, only sees quarterly earnings)")
print("Level 3: Quantum AI (algorithmic trading, humans don't exist)")
print("Level 4: Richard (private equity, destroys from yacht)")
print("Level 5: Madison (inherited wealth, doesn't know she's the problem)")

print("\n=== PROFIT FLOW ===")
print("Alex pays rent → Brandon manages → Tyler owns → Victoria packages →")
print("Quantum trades → Richard controls → Madison inherits")
print("\nEach level profits from the one below, seeing less humanity")

print("\n✅ The machine of suffering is complete")
print("Madison posts about 'gratitude' while Alex sleeps in their car")
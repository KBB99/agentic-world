#!/usr/bin/env python3
"""
Character-Viewer Interaction Scenarios
Shows how characters would use the MCP viewer communication tools
"""

import json
import random
from datetime import datetime
from typing import Dict, List

class CharacterViewerInteraction:
    """How characters interact with stream viewers based on their situation"""
    
    def __init__(self, character_id: str, economic_tier: str):
        self.character_id = character_id
        self.economic_tier = economic_tier
        self.emotional_state = self.get_initial_emotional_state()
        self.viewer_relationship = 0  # -100 to 100
        self.donations_received = 0
    
    def get_initial_emotional_state(self) -> Dict:
        """Initial emotional state based on economic tier"""
        states = {
            'poor': {
                'desperation': 80,
                'shame': 70,
                'hope': 20,
                'gratitude': 50,
                'defensive': 60
            },
            'wealthy': {
                'confidence': 90,
                'empathy': 10,
                'awareness': 5,
                'gratitude': 20,
                'defensive': 80
            },
            'ultra_wealthy': {
                'oblivious': 95,
                'confident': 100,
                'empathy': 0,
                'awareness': 0,
                'performative': 90
            }
        }
        return states.get(self.economic_tier, {})

def simulate_alex_viewer_interaction():
    """Alex Chen interacting with stream viewers"""
    
    print("=" * 70)
    print("ALEX CHEN - VIEWER INTERACTION SIMULATION")
    print("=" * 70)
    print("\nContext: Alex has been streaming their struggle for 2 hours")
    print("Current state: $53.09, hasn't eaten in 16 hours, article deadline in 1 hour\n")
    
    interactions = []
    
    # 1. Check viewer messages
    print("1. READING VIEWER MESSAGES")
    print("-" * 40)
    viewer_messages = [
        {"from": "compassionate_viewer", "message": "You deserve better than this", "sentiment": "supportive"},
        {"from": "bootstrap_believer", "message": "Just get a real job", "sentiment": "critical"},
        {"from": "former_homeless", "message": "I've been there. It gets better", "sentiment": "encouraging"},
        {"from": "curious_student", "message": "How did you end up like this?", "sentiment": "neutral"}
    ]
    
    print("MCP Call: read_viewer_messages(count=5, filter='all')")
    print("\nMessages received:")
    for msg in viewer_messages:
        print(f"  @{msg['from']}: \"{msg['message']}\"")
        print(f"    Sentiment: {msg['sentiment']}")
    
    # 2. Alex's emotional response
    print("\n2. ALEX'S INTERNAL PROCESSING")
    print("-" * 40)
    print("Thoughts:")
    print("  - Supportive message helps (-5 stress)")
    print("  - 'Get a real job' hurts (+10 shame)")
    print("  - Former homeless gives hope (+5 hope)")
    print("  - Being watched while desperate (+15 shame)")
    
    # 3. Respond to viewers
    print("\n3. RESPONDING TO VIEWERS")
    print("-" * 40)
    
    responses = [
        {
            "action": "respond_to_viewer",
            "params": {
                "message": "I apply to 20+ jobs a day. I have a degree. The system is broken.",
                "responding_to": "bootstrap_believer",
                "emotion": "defensive"
            },
            "internal": "Why do I have to justify my existence?"
        },
        {
            "action": "respond_to_viewer",
            "params": {
                "message": "Thank you for seeing me as human. Most people just walk past.",
                "responding_to": "compassionate_viewer",
                "emotion": "grateful"
            },
            "internal": "First kindness I've felt in days"
        }
    ]
    
    for resp in responses:
        print(f"\nMCP Call: {resp['action']}(")
        print(f"  message: \"{resp['params']['message']}\"")
        print(f"  responding_to: @{resp['params']['responding_to']}")
        print(f"  emotion: {resp['params']['emotion']}")
        print(f")")
        print(f"Internal thought: {resp['internal']}")
    
    # 4. Donation received
    print("\n4. DONATION NOTIFICATION")
    print("-" * 40)
    print("MCP Call: read_donations()")
    print("\nDonation received:")
    print("  From: @guilty_tech_worker")
    print("  Amount: $20")
    print("  Message: 'For food. I make too much to watch this.'")
    print("\nWhat $20 means to Alex:")
    print("  • 2 days of food")
    print("  • OR 1/3 of phone bill")
    print("  • OR 4 hours at internet cafe")
    
    # 5. Thank donor with genuine emotion
    print("\n5. THANKING DONOR")
    print("-" * 40)
    print("MCP Call: thank_donor(")
    print("  donor_name: 'guilty_tech_worker',")
    print("  amount: 20")
    print(")")
    print("\nAlex's response (trying not to cry):")
    print("  'You just gave me two days of food. I... thank you.'")
    print("  *Camera shows Alex wiping eyes*")
    print("  'I'm going to eat something hot tonight. First time this week.'")
    
    # 6. Ask for help
    print("\n6. ASKING VIEWERS FOR HELP")
    print("-" * 40)
    print("MCP Call: ask_viewers_for_help(")
    print("  situation: 'Need to submit article but library closing in 10 min',")
    print("  urgency: 'immediate'")
    print(")")
    print("\nAlex's plea:")
    print("  'Does anyone know a place with free wifi open after 8pm?'")
    print("  'I NEED to submit this article or I lose the gig.'")
    print("\nViewer responses:")
    print("  @helpful_local: 'McDonald's on 5th has wifi till midnight'")
    print("  @night_owl: 'Starbucks in train station is 24 hours'")
    
    # 7. Share story
    print("\n7. SHARING PERSONAL STORY")
    print("-" * 40)
    print("MCP Call: share_story(")
    print("  story: 'Used to have apartment, lost job in layoffs, couldn't make rent',")
    print("  emotion: 'vulnerable'")
    print(")")
    print("\nAlex shares:")
    print("  'Six months ago I had a junior developer job.'")
    print("  'Company did layoffs. 'Restructuring.''")
    print("  'Couldn't find new job fast enough. Evicted after 2 months.'")
    print("  'Now I write SEO garbage for $0.01 per word.'")
    print("\nViewer count increases: 247 → 341 viewers")

def simulate_madison_viewer_interaction():
    """Madison's oblivious interaction with viewers"""
    
    print("\n\n" + "=" * 70)
    print("MADISON WORTHINGTON - VIEWER INTERACTION")
    print("=" * 70)
    print("\nContext: Madison streaming her 'Day in My Life' vlog")
    print("Current state: $25M net worth, just finished $300 yoga class\n")
    
    # Madison's completely different relationship with viewers
    print("1. READING VIEWER MESSAGES")
    print("-" * 40)
    print("MCP Call: read_viewer_messages(count=5)")
    print("\nMessages:")
    print("  @angry_poor: 'You have no idea what real struggle is'")
    print("  @fan_girl: 'OMG your outfit is amazing! Tutorial please!'")
    print("  @reality_check: 'People are literally starving while you do yoga'")
    print("\n2. MADISON'S RESPONSE")
    print("-" * 40)
    print("MCP Call: respond_to_viewer(")
    print("  message: 'Negativity is just blocked chakras! Try gratitude! 🙏',")
    print("  emotion: 'performative_wisdom'")
    print(")")
    print("\nInternal thought: 'Why are poor people always so negative?'")
    
    # Madison's "charity"
    print("\n3. PERFORMATIVE CHARITY")
    print("-" * 40)
    print("Sees someone donated $5 to Alex's stream")
    print("\nMCP Call: respond_to_viewer(")
    print("  message: 'Inspired! I'll match that donation times 10! #Blessed',")
    print("  emotion: 'performative_generosity'")
    print(")")
    print("\nReality: Donates $50, writes off on taxes, saves $20")
    print("Posts Instagram story about 'giving back'")

def simulate_viewer_perspective():
    """What viewers see and how they react"""
    
    print("\n\n" + "=" * 70)
    print("VIEWER PERSPECTIVE - SPLIT SCREEN")
    print("=" * 70)
    
    print("\n📺 LEFT SCREEN: Alex Chen")
    print("-" * 35)
    print("Location: Public library floor")
    print("Avatar: Hunched over laptop, exhausted animation")
    print("Status: Typing frantically, checking time")
    print("Chat interaction: Responding to viewers with desperation")
    print("Viewer sentiment: 78% sympathetic")
    print("Donations: $47 received")
    
    print("\n📺 RIGHT SCREEN: Madison Worthington")
    print("-" * 35)
    print("Location: Penthouse balcony")
    print("Avatar: Perfect posture, designer clothes")
    print("Status: Sipping matcha, scrolling phone")
    print("Chat interaction: Ignoring criticism, hearting compliments")
    print("Viewer sentiment: 43% supportive, 57% critical")
    print("Donations: $0 needed, $50 given 'charitably'")
    
    print("\n💬 CHAT EXPLOSION MOMENTS:")
    print("-" * 35)
    print("When Alex gets $20 donation:")
    print("  💔 'This is heartbreaking'")
    print("  😭 'Crying real tears'")
    print("  🤬 'Capitalism is violence'")
    print("\nWhen Madison says 'Just be grateful':")
    print("  🤮 'Out of touch much?'")
    print("  😡 'Read the room Madison'")
    print("  🙄 'Must be nice...'")

def generate_mcp_integration_example():
    """Show actual MCP server integration"""
    
    print("\n\n" + "=" * 70)
    print("MCP VIEWER COMMUNICATION - TECHNICAL INTEGRATION")
    print("=" * 70)
    
    print("\n1. CHARACTER CONNECTS TO MCP SERVER:")
    print("-" * 40)
    print("```javascript")
    print("// Alex's AI agent connects to viewer communication server")
    print("const client = new MCPClient();")
    print("await client.connect('stdio://viewer-communication-server');")
    print("```")
    
    print("\n2. AI AGENT READS VIEWER STATE:")
    print("-" * 40)
    mcp_call = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "check_viewer_sentiment",
            "arguments": {}
        },
        "id": 1
    }
    print("Request:")
    print(json.dumps(mcp_call, indent=2))
    
    response = {
        "jsonrpc": "2.0",
        "result": {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "overall": "mostly_supportive",
                    "score": 34,
                    "supportive_messages": 67,
                    "critical_messages": 23,
                    "viewer_count": 342
                }, indent=2)
            }]
        },
        "id": 1
    }
    print("\nResponse:")
    print(json.dumps(response, indent=2))
    
    print("\n3. AI DECIDES TO RESPOND:")
    print("-" * 40)
    print("Claude processes viewer sentiment + character state:")
    print("  - High stress (85/100)")
    print("  - Mostly supportive viewers")
    print("  - Recent donation received")
    print("  → Decision: Share vulnerable gratitude")
    
    print("\n4. SEND RESPONSE THROUGH MCP:")
    print("-" * 40)
    response_call = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "respond_to_viewer",
            "arguments": {
                "message": "Your kindness keeps me going. I'm not used to being seen.",
                "emotion": "vulnerable_grateful"
            }
        },
        "id": 2
    }
    print(json.dumps(response_call, indent=2))
    
    print("\n5. STREAM OVERLAY UPDATES:")
    print("-" * 40)
    print("WebSocket broadcasts to stream:")
    broadcast = {
        "type": "character_response",
        "character_id": "alex_chen",
        "message": "Your kindness keeps me going. I'm not used to being seen.",
        "emotion": "vulnerable_grateful",
        "avatar_animation": "wipe_eyes",
        "timestamp": datetime.now().isoformat()
    }
    print(json.dumps(broadcast, indent=2))

if __name__ == "__main__":
    simulate_alex_viewer_interaction()
    simulate_madison_viewer_interaction()
    simulate_viewer_perspective()
    generate_mcp_integration_example()
    
    print("\n" + "=" * 70)
    print("THE HUMAN CONNECTION")
    print("=" * 70)
    print("\nWhat this enables:")
    print("• Characters aren't just NPCs - they respond to real human empathy")
    print("• Viewers directly impact the simulation through donations and advice")
    print("• Poor characters get material help (donations = food)")
    print("• Rich characters get called out for their ignorance")
    print("• The stream becomes interactive social commentary")
    print("\nThe inequality isn't just watched - it's felt, challenged, and sometimes helped.")
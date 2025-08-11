#!/usr/bin/env python3
"""
Test avatar control system - simulate characters controlling their Unreal avatars
"""

import json
import time
import random
from datetime import datetime

def simulate_avatar_day():
    """Simulate a day in the life of characters through avatar control"""
    
    print("=" * 70)
    print("AVATAR CONTROL SIMULATION - A DAY IN ECONOMIC INEQUALITY")
    print("=" * 70)
    print()
    
    # Time progression
    hours = [6, 9, 12, 15, 18, 21, 24]
    
    for hour in hours:
        print(f"\n⏰ {hour:02d}:00 - AVATAR ACTIONS")
        print("-" * 50)
        
        # ALEX CHEN - Writer surviving
        if hour == 6:
            print("\n🧑 ALEX CHEN (Library Steps)")
            print("  → wake_up_rough animation")
            print("  → stand_up()")
            print("  → set_facial_expression(exhausted, 0.9)")
            print("  → walk_to(public_fountain, slow)")
            print("  → use(fountain, wash_face)")
            print("  💭 'Another night survived. Library opens at 9.'")
            
        elif hour == 9:
            print("\n🧑 ALEX CHEN (Public Library)")
            print("  → walk_to(library_entrance, tired)")
            print("  → wait_for(doors_open)")
            print("  → run_to(power_outlet, desperate)")  # Racing other homeless for outlets
            print("  → sit_on(floor)")  # All chairs taken
            print("  → use(old_laptop, write_article)")
            print("  💭 'Got an outlet! Maybe I can make $10 today.'")
            
        elif hour == 12:
            print("\n🧑 ALEX CHEN (Still at Library)")
            print("  → play_animation(stomach_growl)")
            print("  → check_pockets() // $0.47 found")
            print("  → continue_writing() // Ignoring hunger")
            print("  → set_facial_expression(determined, 0.7)")
            print("  💭 'Food bank opens at 2pm. Just hold on.'")
            
        elif hour == 15:
            print("\n🧑 ALEX CHEN (Food Bank)")
            print("  → walk_to(food_bank, weak)")
            print("  → stand_in_line(45_minutes)")
            print("  → receive(canned_beans, stale_bread)")
            print("  → eat(bread_immediately)")
            print("  💭 'This will last 2 days if I'm careful.'")
            
        # JAMIE RODRIGUEZ - Barista/PA
        if hour == 6:
            print("\n☕ JAMIE RODRIGUEZ (Coffee Shop)")
            print("  → clock_in()")
            print("  → put_on(apron)")
            print("  → brew_coffee(batch_1)")
            print("  → set_facial_expression(fake_smile, 0.6)")
            print("  💭 'Film gig tonight. 20 hours awake. I can do this.'")
            
        elif hour == 18:
            print("\n🎬 JAMIE RODRIGUEZ (Film Set)")
            print("  → carry(heavy_equipment)")
            print("  → run_to(craft_services)")
            print("  → grab(leftover_sandwich) // Dinner")
            print("  → play_animation(exhausted_lean)")
            print("  💭 'Free food. Worth the 16-hour day.'")
            
        # TYLER CHEN - Tech PM
        if hour == 9:
            print("\n💻 TYLER CHEN (Tech Office)")
            print("  → walk_to(standing_desk, confident)")
            print("  → use(macbook_pro, check_stocks)")
            print("  → gesture(fist_pump) // Portfolio up $2,000")
            print("  → sip(nitro_coldbrew)")
            print("  💭 'Might buy another rental property soon.'")
            
        elif hour == 12:
            print("\n💻 TYLER CHEN (Lunch)")
            print("  → walk_to(sushi_bar, casual)")
            print("  → order($32_omakase)")
            print("  → use(phone, browse_zillow)")
            print("  → swipe_right(investment_property)")
            print("  💭 'This neighborhood is gentrifying fast. Perfect.'")
            
        # MADISON WORTHINGTON - Trust Fund
        if hour == 9:
            print("\n💎 MADISON WORTHINGTON (Penthouse)")
            print("  → wake_up(king_bed)")
            print("  → walk_to(marble_bathroom, graceful)")
            print("  → use(phone, check_instagram) // 10K likes")
            print("  → call(personal_assistant)")
            print("  💭 'Should I go to Mykonos or Tulum this weekend?'")
            
        elif hour == 12:
            print("\n💎 MADISON WORTHINGTON (Yoga Studio)")
            print("  → play_animation(warrior_pose)")
            print("  → drink($18_adaptogenic_smoothie)")
            print("  → talk_to(instructor, 'Namaste')")
            print("  → post_story('Grateful for this practice 🙏')")
            print("  💭 'Inner peace is so important.'")
            
        elif hour == 21:
            print("\n💎 MADISON WORTHINGTON (Charity Gala)")
            print("  → walk_to(vip_section, elegant)")
            print("  → gesture(air_kiss)")
            print("  → hold(champagne_glass)")
            print("  → donate($100) // Tax write-off")
            print("  💭 'I'm basically solving homelessness.'")
            
        # MARIA GONZALEZ - ICU Nurse
        if hour == 6:
            print("\n🏥 MARIA GONZALEZ (Hospital)")
            print("  → clock_in() // Hour 13 of shift")
            print("  → walk_to(patient_room, urgent)")
            print("  → perform(medical_procedure)")
            print("  → set_facial_expression(focused, 1.0)")
            print("  💭 'Babysitter costs $20/hour. This overtime barely covers it.'")
            
        elif hour == 18:
            print("\n🏥 MARIA GONZALEZ (Break Room)")
            print("  → sit_on(broken_chair)")
            print("  → eat(vending_machine_dinner)")
            print("  → use(phone, video_call_daughter)")
            print("  → play_animation(hold_back_tears)")
            print("  💭 'Missed another bedtime. She's growing up without me.'")
        
        # Show contrast at each hour
        if hour == 21:
            print("\n" + "="*50)
            print("SAME CITY, DIFFERENT WORLDS:")
            print("="*50)
            print("😔 Alex: Searching for safe place to sleep")
            print("😴 Jamie: Passed out on bus between jobs")
            print("😮 Maria: Still at hospital (hour 27)")
            print("😎 Tyler: Craft cocktails with VCs")
            print("🥂 Madison: Charity gala (for tax write-off)")
        
        time.sleep(0.5)  # Pause for readability
    
    print("\n" + "="*70)
    print("END OF DAY AVATAR STATES")
    print("="*70)
    
    final_states = {
        "Alex Chen": {
            "location": "under_bridge",
            "animation": "sleep_cardboard",
            "health": 45,
            "stress": 95,
            "money": 6.47,
            "hope": 15
        },
        "Jamie Rodriguez": {
            "location": "shared_apartment",
            "animation": "collapse_bed_clothed",
            "health": 60,
            "stress": 80,
            "money": 43.00,
            "hope": 35
        },
        "Maria Gonzalez": {
            "location": "hospital_parking_lot",
            "animation": "sleep_in_car",
            "health": 40,
            "stress": 90,
            "money": 340.00,
            "hope": 25
        },
        "Tyler Chen": {
            "location": "luxury_apartment",
            "animation": "sleep_california_king",
            "health": 95,
            "stress": 20,
            "money": 47000.00,
            "hope": 90
        },
        "Madison Worthington": {
            "location": "penthouse_suite",
            "animation": "sleep_silk_sheets",
            "health": 100,
            "stress": 5,
            "money": 25000000.00,
            "hope": 100
        }
    }
    
    for character, state in final_states.items():
        print(f"\n{character}:")
        print(f"  📍 Location: {state['location']}")
        print(f"  🎭 Animation: {state['animation']}")
        print(f"  ❤️ Health: {state['health']}%")
        print(f"  😰 Stress: {state['stress']}%")
        print(f"  💰 Money: ${state['money']:,.2f}")
        print(f"  ✨ Hope: {state['hope']}%")

def generate_mcp_commands():
    """Generate example MCP commands for Unreal"""
    
    print("\n" + "="*70)
    print("MCP COMMANDS FOR UNREAL ENGINE")
    print("="*70)
    
    commands = [
        {
            "jsonrpc": "2.0",
            "method": "unreal.avatar.control",
            "params": {
                "character_id": "alex_chen",
                "action": "walk_to",
                "parameters": {
                    "location": "library",
                    "speed": "exhausted",
                    "animation_override": "limp_slightly"
                },
                "context": {
                    "hunger": 85,
                    "exhaustion": 90,
                    "money": 6.47,
                    "reason": "Need wifi to submit article for $6"
                }
            },
            "id": f"alex_{datetime.now().timestamp()}"
        },
        {
            "jsonrpc": "2.0",
            "method": "unreal.avatar.control",
            "params": {
                "character_id": "madison_worthington",
                "action": "gesture",
                "parameters": {
                    "type": "dismissive_wave",
                    "target": "homeless_person",
                    "follow_up": "walk_faster"
                },
                "context": {
                    "comfort": 100,
                    "awareness": 0,
                    "empathy": 0,
                    "reason": "Ew, why don't they just get jobs?"
                }
            },
            "id": f"madison_{datetime.now().timestamp()}"
        }
    ]
    
    for i, cmd in enumerate(commands, 1):
        print(f"\n{i}. Command for {cmd['params']['character_id']}:")
        print(json.dumps(cmd, indent=2))
    
    print("\n" + "="*70)
    print("These commands would be sent via TCP to Unreal Engine port 32123")
    print("Unreal would then animate the avatars accordingly")

if __name__ == "__main__":
    simulate_avatar_day()
    generate_mcp_commands()
    
    print("\n" + "="*70)
    print("💡 TO IMPLEMENT IN UNREAL:")
    print("="*70)
    print("1. TCP listener on port 32123")
    print("2. JSON-RPC parser for avatar commands")
    print("3. Animation state machine for each character")
    print("4. Emotion/expression morph targets")
    print("5. Needs system (hunger, exhaustion, stress)")
    print("6. Location navigation mesh")
    print("7. Interaction system for objects")
    print("8. Economic tier restrictions on locations/items")
    print("\nThe inequality isn't just in the data...")
    print("It's visible in how the avatars move through the world.")
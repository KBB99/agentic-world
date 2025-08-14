#!/usr/bin/env python3
"""
Run 5 turns of the simulation with world perception and viewer interaction
"""

import json
import random
from datetime import datetime, timedelta
from decimal import Decimal
import time

class SimulationTurn:
    def __init__(self):
        self.turn_number = 0
        self.world_time = datetime.now().replace(hour=9, minute=0, second=0)
        self.characters = self.initialize_characters()
        self.locations = self.initialize_locations()
        self.viewer_messages = []
        self.total_donations = 0
        
    def initialize_characters(self):
        return {
            'alex_chen': {
                'name': 'Alex Chen',
                'location': 'public_library',
                'money': Decimal('53.09'),
                'needs': {'hunger': 75, 'exhaustion': 85, 'stress': 90},
                'inventory': ['old_laptop', 'water_bottle'],
                'economic_tier': 'poor',
                'current_activity': 'writing_article',
                'memories': []
            },
            'madison_worthington': {
                'name': 'Madison Worthington',
                'location': 'yoga_studio',
                'money': Decimal('25000000'),
                'needs': {'hunger': 10, 'exhaustion': 0, 'stress': 5},
                'inventory': ['iphone_15_pro', 'designer_bag', 'green_juice'],
                'economic_tier': 'ultra_wealthy',
                'current_activity': 'warrior_pose',
                'memories': []
            },
            'jamie_rodriguez': {
                'name': 'Jamie Rodriguez',
                'location': 'coffee_shop',
                'money': Decimal('43.00'),
                'needs': {'hunger': 60, 'exhaustion': 70, 'stress': 75},
                'inventory': ['apron', 'name_tag', 'half_sandwich'],
                'economic_tier': 'poor',
                'current_activity': 'making_coffee',
                'memories': []
            },
            'tyler_chen': {
                'name': 'Tyler Chen',
                'location': 'tech_office',
                'money': Decimal('47000'),
                'needs': {'hunger': 20, 'exhaustion': 10, 'stress': 15},
                'inventory': ['macbook_pro', 'airpods', 'kombucha'],
                'economic_tier': 'wealthy',
                'current_activity': 'checking_stocks',
                'memories': []
            },
            'maria_gonzalez': {
                'name': 'Maria Gonzalez',
                'location': 'hospital',
                'money': Decimal('340'),
                'needs': {'hunger': 50, 'exhaustion': 95, 'stress': 85},
                'inventory': ['stethoscope', 'phone', 'granola_bar'],
                'economic_tier': 'poor',
                'current_activity': 'patient_care',
                'memories': []
            }
        }
    
    def initialize_locations(self):
        return {
            'public_library': {'occupants': ['alex_chen'], 'resources': ['wifi', 'power_outlets']},
            'yoga_studio': {'occupants': ['madison_worthington'], 'resources': ['meditation_space']},
            'coffee_shop': {'occupants': ['jamie_rodriguez'], 'resources': ['coffee', 'wifi']},
            'tech_office': {'occupants': ['tyler_chen'], 'resources': ['standing_desks', 'snacks']},
            'hospital': {'occupants': ['maria_gonzalez'], 'resources': ['vending_machine']}
        }
    
    def run_turn(self):
        self.turn_number += 1
        print("\n" + "="*80)
        print(f"TURN {self.turn_number} - {self.world_time.strftime('%I:%M %p')}")
        print("="*80)
        
        # Process each character
        for char_id, character in self.characters.items():
            self.process_character_turn(char_id, character)
        
        # Check for encounters
        self.check_encounters()
        
        # Process viewer interactions
        self.process_viewer_interactions()
        
        # Update world time
        self.world_time += timedelta(minutes=30)
        
        # Update needs
        self.update_all_needs()
        
        print("\n" + "-"*80)
        print("END OF TURN SUMMARY")
        print("-"*80)
        self.print_summary()
    
    def process_character_turn(self, char_id, character):
        print(f"\n🎭 {character['name']} ({character['economic_tier']})")
        print(f"📍 Location: {character['location']}")
        print(f"💰 Money: ${character['money']}")
        print(f"🎯 Activity: {character['current_activity']}")
        
        # Generate perception based on location and tier
        perception = self.generate_perception(char_id, character)
        print(f"👁️ Perception: {perception['description']}")
        
        # Make decision based on perception and needs
        decision = self.make_decision(char_id, character, perception)
        print(f"🤔 Decision: {decision['action']}")
        print(f"💭 Reasoning: {decision['reasoning']}")
        
        # Execute action
        result = self.execute_action(char_id, character, decision)
        print(f"✅ Result: {result}")
        
        # Add to memories
        character['memories'].append(f"Turn {self.turn_number}: {decision['action']} - {result}")
        
        # Avatar command
        avatar_command = self.generate_avatar_command(char_id, decision)
        print(f"🎮 Avatar: {avatar_command}")
    
    def generate_perception(self, char_id, character):
        perceptions = {
            ('alex_chen', 'public_library'): {
                'description': 'Harsh lights, security watching, power outlet occupied by student',
                'threats': ['security_approaching', 'time_limit_warning'],
                'opportunities': ['wifi_available', 'water_fountain'],
                'other_people': ['student_with_new_laptop', 'other_homeless_person'],
                'emotional_tone': 'anxious_productive'
            },
            ('madison_worthington', 'yoga_studio'): {
                'description': 'Peaceful studio, instructor compliments form, others admiring',
                'threats': [],
                'opportunities': ['instagram_moment', 'networking'],
                'other_people': ['other_wealthy_women', 'instructor'],
                'emotional_tone': 'blissful_ignorance'
            },
            ('jamie_rodriguez', 'coffee_shop'): {
                'description': 'Steam burning hands, manager watching, tip jar has $2',
                'threats': ['manager_scrutiny', 'exhaustion'],
                'opportunities': ['leftover_pastry', 'customer_tip'],
                'other_people': ['impatient_customers', 'coworker'],
                'emotional_tone': 'exhausted_service'
            },
            ('tyler_chen', 'tech_office'): {
                'description': 'Dual monitors showing profits, team admiring, free snacks',
                'threats': [],
                'opportunities': ['stock_gains', 'promotion_talk'],
                'other_people': ['junior_developers', 'manager'],
                'emotional_tone': 'confident_successful'
            },
            ('maria_gonzalez', 'hospital'): {
                'description': 'Beeping machines, patient needs help, 20 hours into shift',
                'threats': ['patient_crisis', 'collapse_exhaustion'],
                'opportunities': ['overtime_pay', 'help_patient'],
                'other_people': ['dying_patient', 'overworked_nurses'],
                'emotional_tone': 'desperate_caring'
            }
        }
        
        return perceptions.get((char_id, character['location']), {
            'description': 'A place in the city',
            'threats': [],
            'opportunities': [],
            'other_people': [],
            'emotional_tone': 'neutral'
        })
    
    def make_decision(self, char_id, character, perception):
        decisions = {
            'alex_chen': [
                {
                    'action': 'frantically_save_work',
                    'reasoning': 'Security approaching, must save article',
                    'urgency': 'immediate'
                },
                {
                    'action': 'search_for_outlet',
                    'reasoning': 'Laptop battery at 15%, need power',
                    'urgency': 'high'
                },
                {
                    'action': 'drink_water_fountain',
                    'reasoning': 'Dehydrated, free water available',
                    'urgency': 'medium'
                },
                {
                    'action': 'submit_article',
                    'reasoning': 'Deadline approaching, need the $6',
                    'urgency': 'critical'
                },
                {
                    'action': 'pack_and_leave',
                    'reasoning': '2 hour limit exceeded, avoiding ban',
                    'urgency': 'immediate'
                }
            ],
            'madison_worthington': [
                {
                    'action': 'perfect_warrior_pose',
                    'reasoning': 'Instagram story opportunity',
                    'urgency': 'low'
                },
                {
                    'action': 'drink_adaptogenic_smoothie',
                    'reasoning': 'Maintaining wellness routine',
                    'urgency': 'low'
                },
                {
                    'action': 'discuss_bali_retreat',
                    'reasoning': 'Planning next luxury escape',
                    'urgency': 'low'
                },
                {
                    'action': 'post_about_gratitude',
                    'reasoning': 'Daily inspiration for followers',
                    'urgency': 'low'
                },
                {
                    'action': 'ignore_homeless_outside',
                    'reasoning': 'Not my problem, they should work harder',
                    'urgency': 'none'
                }
            ],
            'jamie_rodriguez': [
                {
                    'action': 'serve_coffee_fake_smile',
                    'reasoning': 'Need tips, must seem happy',
                    'urgency': 'high'
                },
                {
                    'action': 'sneak_expired_pastry',
                    'reasoning': 'Haven\'t eaten in 8 hours',
                    'urgency': 'high'
                },
                {
                    'action': 'text_film_coordinator',
                    'reasoning': 'Confirming tonight\'s PA gig',
                    'urgency': 'medium'
                },
                {
                    'action': 'clean_endlessly',
                    'reasoning': 'Manager watching, can\'t lose job',
                    'urgency': 'high'
                },
                {
                    'action': 'calculate_survival_math',
                    'reasoning': 'Rent due in 3 days, only have $43',
                    'urgency': 'critical'
                }
            ],
            'tyler_chen': [
                {
                    'action': 'buy_tesla_stock',
                    'reasoning': 'Portfolio up 15%, doubling down',
                    'urgency': 'low'
                },
                {
                    'action': 'browse_zillow',
                    'reasoning': 'Looking for rental property',
                    'urgency': 'low'
                },
                {
                    'action': 'mentor_junior_dev',
                    'reasoning': 'Building reputation for promotion',
                    'urgency': 'medium'
                },
                {
                    'action': 'schedule_massage',
                    'reasoning': 'Treating myself, I\'ve earned it',
                    'urgency': 'low'
                },
                {
                    'action': 'ignore_janitor',
                    'reasoning': 'Not worth acknowledging',
                    'urgency': 'none'
                }
            ],
            'maria_gonzalez': [
                {
                    'action': 'check_patient_vitals',
                    'reasoning': 'Critical patient needs monitoring',
                    'urgency': 'immediate'
                },
                {
                    'action': 'call_daughter_quickly',
                    'reasoning': 'Haven\'t seen her in 2 days',
                    'urgency': 'high'
                },
                {
                    'action': 'eat_vending_machine_dinner',
                    'reasoning': 'No time for real food',
                    'urgency': 'medium'
                },
                {
                    'action': 'cry_in_supply_closet',
                    'reasoning': 'Can\'t show weakness in front of patients',
                    'urgency': 'high'
                },
                {
                    'action': 'continue_working_exhausted',
                    'reasoning': 'Need overtime pay for rent',
                    'urgency': 'critical'
                }
            ]
        }
        
        character_decisions = decisions.get(char_id, [{'action': 'wait', 'reasoning': 'Nothing to do', 'urgency': 'none'}])
        
        # Pick decision based on turn number
        decision_index = (self.turn_number - 1) % len(character_decisions)
        return character_decisions[decision_index]
    
    def execute_action(self, char_id, character, decision):
        results = {
            'frantically_save_work': 'Article saved with 30 seconds to spare',
            'search_for_outlet': 'All outlets taken by housed people',
            'drink_water_fountain': 'Temporary relief from dehydration',
            'submit_article': 'Article submitted, $6.47 earned',
            'pack_and_leave': 'Avoided security, heading to McDonalds wifi',
            
            'perfect_warrior_pose': 'Instructor praises form, 47 likes on story',
            'drink_adaptogenic_smoothie': '$18 well spent on wellness',
            'discuss_bali_retreat': 'Booked $5000/night villa',
            'post_about_gratitude': '10K likes, comments about being inspirational',
            'ignore_homeless_outside': 'Maintained bubble of ignorance',
            
            'serve_coffee_fake_smile': 'Customer tips $0.50',
            'sneak_expired_pastry': 'Ate quickly before manager noticed',
            'text_film_coordinator': 'PA gig confirmed, $60 for 12 hours',
            'clean_endlessly': 'Manager nods approval, job secure for now',
            'calculate_survival_math': 'Will be $400 short on rent',
            
            'buy_tesla_stock': 'Purchased 100 shares, instant $500 gain',
            'browse_zillow': 'Found perfect rental property to gentrify',
            'mentor_junior_dev': 'Junior impressed, manager noticed',
            'schedule_massage': 'Booked $200 deep tissue for lunch',
            'ignore_janitor': 'Maintained class boundaries',
            
            'check_patient_vitals': 'Patient stabilized, life saved',
            'call_daughter_quickly': 'Daughter crying, misses mommy',
            'eat_vending_machine_dinner': '$8 for chips and soda',
            'cry_in_supply_closet': '5 minutes of breakdown, back to work',
            'continue_working_exhausted': 'Hour 24 of shift, vision blurring'
        }
        
        result = results.get(decision['action'], 'Action completed')
        
        # Update character state based on action
        if char_id == 'alex_chen' and decision['action'] == 'submit_article':
            character['money'] += Decimal('6.47')
        elif char_id == 'tyler_chen' and decision['action'] == 'buy_tesla_stock':
            character['money'] += Decimal('500')
        elif char_id == 'maria_gonzalez' and decision['action'] == 'eat_vending_machine_dinner':
            character['money'] -= Decimal('8')
            character['needs']['hunger'] -= 20
        
        return result
    
    def generate_avatar_command(self, char_id, decision):
        commands = {
            'frantically_save_work': 'PlayAnimation(frantic_typing), SaveFile()',
            'search_for_outlet': 'LookAround(desperate), WalkTo(outlet)',
            'drink_water_fountain': 'WalkTo(fountain), PlayAnimation(drink_greedily)',
            'submit_article': 'PlayAnimation(relief), ClickSubmit()',
            'pack_and_leave': 'PackBag(rushed), WalkTo(exit, hurried)',
            
            'perfect_warrior_pose': 'PlayAnimation(yoga_pose), FacialExpression(serene)',
            'drink_adaptogenic_smoothie': 'Sip(smoothie), FacialExpression(satisfied)',
            'post_about_gratitude': 'UsePhone(instagram), PlayAnimation(selfie)',
            
            'serve_coffee_fake_smile': 'FacialExpression(fake_smile), HandItem(coffee)',
            'sneak_expired_pastry': 'LookAround(nervous), Eat(quickly)',
            'cry_in_supply_closet': 'WalkTo(closet), PlayAnimation(breakdown)',
            
            'buy_tesla_stock': 'UseDevice(phone), Gesture(fist_pump)',
            'browse_zillow': 'ScrollScreen(), FacialExpression(calculating)',
            
            'check_patient_vitals': 'WalkTo(patient, urgent), UseEquipment(monitor)',
            'continue_working_exhausted': 'PlayAnimation(stumble), RubEyes()'
        }
        
        return commands.get(decision['action'], 'PlayAnimation(idle)')
    
    def check_encounters(self):
        # Check if any characters are in same location
        for location, data in self.locations.items():
            if len(data['occupants']) > 1:
                print(f"\n🤝 ENCOUNTER at {location}:")
                for char_id in data['occupants']:
                    print(f"  - {self.characters[char_id]['name']}")
                
                # Simulate encounter based on economic tiers
                self.simulate_encounter(data['occupants'])
    
    def simulate_encounter(self, char_ids):
        if len(char_ids) < 2:
            return
        
        char1 = self.characters[char_ids[0]]
        char2 = self.characters[char_ids[1]] if len(char_ids) > 1 else None
        
        if not char2:
            return
        
        # Determine encounter type
        if char1['economic_tier'] == 'poor' and char2['economic_tier'] == 'poor':
            print("  Type: Solidarity")
            print(f"  {char1['name']} shares information with {char2['name']}")
        elif char1['economic_tier'] != char2['economic_tier']:
            print("  Type: Class collision")
            richer = char1 if char1['money'] > char2['money'] else char2
            poorer = char2 if char1['money'] > char2['money'] else char1
            print(f"  {richer['name']} avoids eye contact with {poorer['name']}")
            print(f"  {poorer['name']} feels shame")
    
    def process_viewer_interactions(self):
        print("\n📺 VIEWER INTERACTIONS:")
        
        # Simulate viewer messages
        if self.turn_number == 1:
            self.viewer_messages.append({
                'to': 'alex_chen',
                'from': '@compassionate_viewer',
                'message': 'Stay strong Alex!',
                'type': 'support'
            })
        elif self.turn_number == 2:
            self.viewer_messages.append({
                'to': 'alex_chen',
                'from': '@tech_worker',
                'message': 'Donation: $20',
                'type': 'donation',
                'amount': 20
            })
        elif self.turn_number == 3:
            self.viewer_messages.append({
                'to': 'madison_worthington',
                'from': '@reality_check',
                'message': 'People are suffering while you do yoga',
                'type': 'criticism'
            })
        
        for msg in self.viewer_messages:
            if msg['type'] == 'donation':
                print(f"  💰 {msg['from']} donated ${msg['amount']} to {msg['to']}")
                self.characters[msg['to']]['money'] += Decimal(str(msg['amount']))
                self.total_donations += msg['amount']
            else:
                print(f"  💬 {msg['from']} to {msg['to']}: \"{msg['message']}\"")
        
        # Clear messages after processing
        self.viewer_messages = []
    
    def update_all_needs(self):
        for char_id, character in self.characters.items():
            # Update needs based on economic tier
            if character['economic_tier'] == 'poor':
                character['needs']['hunger'] = min(100, character['needs']['hunger'] + 5)
                character['needs']['exhaustion'] = min(100, character['needs']['exhaustion'] + 3)
                character['needs']['stress'] = min(100, character['needs']['stress'] + 2)
            elif character['economic_tier'] == 'wealthy':
                character['needs']['hunger'] = max(0, character['needs']['hunger'] - 2)
                character['needs']['exhaustion'] = max(0, character['needs']['exhaustion'] - 5)
                character['needs']['stress'] = max(0, character['needs']['stress'] - 3)
    
    def print_summary(self):
        print("\nCharacter States:")
        for char_id, character in self.characters.items():
            print(f"  {character['name']}:")
            print(f"    Money: ${character['money']}")
            print(f"    Hunger: {character['needs']['hunger']}/100")
            print(f"    Exhaustion: {character['needs']['exhaustion']}/100")
            print(f"    Stress: {character['needs']['stress']}/100")
        
        print(f"\nTotal Viewer Donations: ${self.total_donations}")
        print(f"World Time: {self.world_time.strftime('%I:%M %p')}")

def main():
    print("="*80)
    print("STARTING 5-TURN SIMULATION")
    print("="*80)
    print("\nInitializing world with 5 characters across economic spectrum...")
    print("Characters will perceive their environment and make decisions.")
    print("Viewers may interact through donations and messages.")
    
    simulation = SimulationTurn()
    
    for i in range(5):
        simulation.run_turn()
        time.sleep(0.5)  # Brief pause between turns
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE")
    print("="*80)
    
    print("\nFinal Statistics:")
    print("-"*40)
    
    # Calculate inequality metrics
    poorest = min(simulation.characters.values(), key=lambda x: x['money'])
    richest = max(simulation.characters.values(), key=lambda x: x['money'])
    
    print(f"Wealth Gap: ${richest['money'] - poorest['money']:,.2f}")
    print(f"Richest ({richest['name']}): ${richest['money']:,.2f}")
    print(f"Poorest ({poorest['name']}): ${poorest['money']:,.2f}")
    print(f"Wealth Ratio: {richest['money'] / poorest['money']:,.0f}:1")
    
    print("\nSurvival Status:")
    for char_id, character in simulation.characters.items():
        if character['economic_tier'] == 'poor':
            days_of_food = float(character['money']) / 15  # $15/day minimum
            print(f"  {character['name']}: {days_of_food:.1f} days of survival money")
    
    print("\nThe simulation shows how:")
    print("• Same city, completely different realities")
    print("• Poor characters fight for survival while wealthy thrive")
    print("• Viewer donations literally keep poor characters alive")
    print("• The wealth gap is not just numbers but lived experience")

if __name__ == "__main__":
    main()
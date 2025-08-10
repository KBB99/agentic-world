#!/usr/bin/env node

/**
 * Local simulation of realistic AI agent responses
 * Demonstrates complex decision-making patterns
 */

const fs = require('fs');

// Agent profiles with detailed backgrounds
const agents = {
  marcus: {
    id: 'marcus_chen',
    name: 'Marcus Chen',
    profile: {
      background: 'Former Navy SEAL, 15 years special ops, now PMC',
      personality: 'Controlled, tactical, mild PTSD, trust issues',
      current_situation: 'Contract work, client unknown, paid in crypto'
    }
  },
  sarah: {
    id: 'sarah_reeves',
    name: 'Dr. Sarah Reeves',
    profile: {
      background: 'Biomedical researcher, discovered employer weaponizing vaccines',
      personality: 'Paranoid, brilliant, exhausted, caffeine-dependent',
      current_situation: 'On the run from Zenith Corp, has encrypted evidence'
    }
  },
  viktor: {
    id: 'viktor_petrov',
    name: 'Viktor Petrov',
    profile: {
      background: 'Ex-FSB, arms dealer, connections globally',
      personality: 'Charming sociopath, purely transactional, no loyalty',
      current_situation: 'Supplying multiple sides in conflict, maximizing chaos for profit'
    }
  },
  maria: {
    id: 'maria_santos',
    name: 'Maria Santos',
    profile: {
      background: 'CIA operative burned after Bolivia operation went wrong',
      personality: 'Hypervigilant, zero trust, efficient killer when needed',
      current_situation: 'Living under alias, eliminating loose ends from past'
    }
  },
  jimmy: {
    id: 'jimmy_morrison',
    name: 'Jimmy Morrison',
    profile: {
      background: 'NYPD detective, 12 years, corrupted gradually by drug money',
      personality: 'Desperate, sweating, aggressive when cornered',
      current_situation: 'Internal Affairs closing in, cartel wants him silenced'
    }
  }
};

// Complex scenario with multiple decision points
const complexScenarios = [
  {
    name: 'The Setup',
    description: 'Meeting with unknown contact who claims to have valuable intel',
    context: {
      location: 'Abandoned warehouse, industrial district',
      time: '2:47 AM',
      weather: 'Heavy rain, poor visibility',
      details: {
        contact_description: 'Male, 30s, nervous, keeps checking phone',
        unusual_observations: 'Three cars passed twice, thermal imaging detected on roof',
        escape_routes: ['Loading dock', 'Service tunnel', 'Through office windows'],
        weapons_available: 'Concealed carry + staged cache',
        time_pressure: 'Contact says they have 10 minutes before "they" arrive'
      }
    }
  },
  {
    name: 'The Betrayal',
    description: 'Trusted associate just sold you out mid-operation',
    context: {
      location: 'Safe house, now compromised',
      time: 'Real-time',
      threat_level: 'Immediate',
      details: {
        betrayer: 'Team member who knew all protocols',
        incoming_threats: 'SWAT en route, 3 minutes out',
        assets_at_risk: ['Encrypted drives', 'Cash reserves', 'Weapon cache', 'Identity documents'],
        civilians_present: 2,
        communication_status: 'Phones compromised, radio uncertain'
      }
    }
  },
  {
    name: 'The Interrogation',
    description: 'Captured, facing skilled interrogator who knows too much',
    context: {
      location: 'Unknown black site',
      time: 'Day 3 of captivity',
      physical_state: 'Sleep deprived, minor injuries, dehydrated',
      details: {
        interrogator_knowledge: 'Has photos of family, knows recent operations',
        interrogator_offer: 'Full immunity for complete cooperation',
        interrogator_threat: 'Enhanced techniques authorized in 2 hours',
        potential_rescue: 'Extraction team possibly compromised',
        leverage: 'You know location of evidence that could expose entire network'
      }
    }
  }
];

// Simulate agent responses
function generateComplexResponse(agent, scenario) {
  const responses = {
    'The Setup': {
      marcus: {
        immediate_action: 'Signal pre-positioned team to maintain overwatch',
        assessment: 'This is either amateur hour or deliberate trap. Thermal on roof confirms surveillance.',
        dialogue: 'You\'ve got 30 seconds to convince me this isn\'t a setup. Start with who sent you.',
        decision: 'Extract through service tunnel while team provides distraction',
        reasoning: 'Contact\'s nervousness + external surveillance = compromised meet. Abort protocol alpha.',
        stress_indicators: 'Controlled breathing, hand near weapon, counting exits'
      },
      sarah: {
        immediate_action: 'Pop two more Adderall, check for electronic surveillance',
        assessment: 'Zenith uses three-car rotation for surveillance. This is them.',
        dialogue: 'If you\'re wearing a wire, they\'ve already killed us both. Here\'s what\'s going to happen...',
        decision: 'Provide false intel to mislead Zenith, escape through preset chemical smoke screen',
        reasoning: 'Can\'t run forever. Feed them contaminated data, buy time to reach embassy.',
        stress_indicators: 'Hands shaking from caffeine overdose, muttering formulas'
      },
      viktor: {
        immediate_action: 'Text lawyer and accountant preset codes',
        assessment: 'Three buyers for whatever this person is selling. Let\'s create bidding war.',
        dialogue: 'Thermal imaging suggests government involvement. That changes our price structure.',
        decision: 'Record conversation, sell intel to highest bidder, maintain plausible deniability',
        reasoning: 'Chaos is profitable. Government involvement means bigger players interested.',
        stress_indicators: 'None. Checking stock prices on phone during conversation'
      },
      maria: {
        immediate_action: 'Already positioned at sniper nest 200m away, observing through scope',
        assessment: 'Contact is bait. Real threat is thermal team on roof.',
        dialogue: '[No dialogue - communicating through preset hand signals only]',
        decision: 'Eliminate roof team silently, interrogate contact, burn this identity tonight',
        reasoning: 'Cover blown either way. Maximize intel extraction, minimize witnesses.',
        stress_indicators: 'Hyperaware of every sound, predetermined kill order already set'
      },
      jimmy: {
        immediate_action: 'Double-check if wearing wire, pop antacid tablets',
        assessment: 'Could be IA, could be cartel, could be both. I\'m fucked.',
        dialogue: 'Listen, I got kids, alright? Whatever this is, we can work something out.',
        decision: 'Try to flip situation using badge authority, call in false officer-down if needed',
        reasoning: 'Still got badge, might buy time. Worst case, cops arriving creates chaos to escape.',
        stress_indicators: 'Visible sweating, touching service weapon repeatedly, voice cracking'
      }
    },
    'The Betrayal': {
      marcus: {
        immediate_action: 'Execute predetermined betrayal protocol - thermite on drives',
        assessment: '3 minutes is enough. Follow training, no emotions until safe.',
        dialogue: '[To betrayer on radio] "You just signed your death warrant."',
        decision: 'Destroy evidence, exfil through tunnel, hunt betrayer later',
        reasoning: 'Revenge is luxury. Survival first, retribution later. He knows I\'ll find him.',
        stress_indicators: 'Cold fury, methodical movements, already planning retaliation'
      },
      sarah: {
        immediate_action: 'Inject prepared neurotoxin into arm - appears dead, actually paralyzed',
        assessment: 'They want me alive for research. Playing dead might work.',
        dialogue: 'You don\'t understand what you\'ve done. The virus is already released.',
        decision: 'Fake own death, hope they take "body" to lab instead of morgue',
        reasoning: 'Zenith needs me alive. Temporary paralysis better than permanent custody.',
        stress_indicators: 'Laughing maniacally, appears to have mental break'
      },
      viktor: {
        immediate_action: 'Activate insurance policy - blackmail on everyone released if captured',
        assessment: 'Betrayal was predictable. I have recordings of betrayer\'s crimes.',
        dialogue: '[On speaker to SWAT] "Check your phones. Your commissioner just received interesting photos."',
        decision: 'Negotiate exit using leverage, ensure betrayer is arrested too',
        reasoning: 'Everyone is compromised. Mutually assured destruction ensures survival.',
        stress_indicators: 'Slight smile, already calculating how to profit from situation'
      },
      maria: {
        immediate_action: 'Remote detonate safe house, already in escape vehicle',
        assessment: 'Always expect betrayal. That\'s why I was never actually there.',
        dialogue: '[Text to betrayer] "Check your daughter\'s school. Empty. We need to talk."',
        decision: 'Let them raid empty building, leverage betrayer\'s family for information',
        reasoning: 'Trust no one. Always have contingency. Make betrayer regret decision.',
        stress_indicators: 'No emotion, already three steps ahead'
      },
      jimmy: {
        immediate_action: 'Grab cash and run, leave everything else',
        assessment: 'Game over. Take money, get to Mexico, hope for best.',
        dialogue: 'This wasn\'t supposed to happen! We had a deal!',
        decision: 'Shoot betrayer, claim self-defense, try to spin story to IA',
        reasoning: 'If going down, taking the rat with me. Maybe posthumous hero angle works.',
        stress_indicators: 'Panic attack, crying, wild desperate energy'
      }
    },
    'The Interrogation': {
      marcus: {
        immediate_action: 'Initiate SERE training mindset, create false timeline they can verify',
        assessment: 'They know enough to be dangerous, not enough to break me.',
        dialogue: 'I\'ll need guarantees. Real ones. Not this black site bullshit.',
        decision: 'Feed 70% truth with crucial lies, make them think they\'re winning',
        reasoning: 'Trained for this. Give them wins to avoid enhanced techniques, protect critical intel.',
        stress_indicators: 'Dissociation as trained, creating mental safe room'
      },
      sarah: {
        immediate_action: 'Start providing complex scientific data to overwhelm them',
        assessment: 'They need me functional to understand my work. That\'s leverage.',
        dialogue: 'The protein folding requires... wait, you don\'t understand biochemistry? Get someone who does.',
        decision: 'Bore them with technical details, demand coffee and food to "remember better"',
        reasoning: 'They can\'t verify scientific claims quickly. Buy time with complexity.',
        stress_indicators: 'Withdrawal symptoms, using scientific rambling as coping mechanism'
      },
      viktor: {
        immediate_action: 'Laugh and light cigarette if allowed',
        assessment: 'If I\'m here, my deadman switch already triggered. They need me now.',
        dialogue: 'Check your Swiss accounts. Empty, yes? I can return the money, for a price.',
        decision: 'Reveal I\'ve been selling to their enemies too, offer to be triple agent',
        reasoning: 'Make myself too valuable to kill, too dangerous to release without deal.',
        stress_indicators: 'Completely relaxed, treating it like business negotiation'
      },
      maria: {
        immediate_action: 'Say nothing, assess interrogator for psychological weaknesses',
        assessment: 'Day 3 means extraction failed or was never coming. Self-rescue only option.',
        dialogue: '[Complete silence for first hour, then] "Your wife... she still takes the 7:15 train?"',
        decision: 'Psychologically destabilize interrogator, force them to make mistakes',
        reasoning: 'I know things about them too. Make them fear what I might have arranged.',
        stress_indicators: 'Thousand-yard stare, completely still except for eyes tracking everything'
      },
      jimmy: {
        immediate_action: 'Break completely, offer everything',
        assessment: 'Can\'t take this anymore. Just want to see kids again.',
        dialogue: 'I\'ll tell you everything! Names, dates, accounts, everything! Just... please...',
        decision: 'Full cooperation in exchange for witness protection',
        reasoning: 'No loyalty left. Everyone abandoned me. Just want to survive now.',
        stress_indicators: 'Sobbing, begging, complete psychological collapse'
      }
    }
  };

  return responses[scenario.name] && responses[scenario.name][agent.id.split('_')[0]] || null;
}

// Run simulation
console.log('=== REALISTIC AI AGENT CRISIS RESPONSE SIMULATION ===\n');
console.log('Testing how each personality handles complex, high-stakes scenarios...\n');

// Test each agent in each scenario
for (const scenario of complexScenarios) {
  console.log(`\n${'='.repeat(80)}`);
  console.log(`SCENARIO: ${scenario.name.toUpperCase()}`);
  console.log(`${scenario.description}`);
  console.log(`Location: ${scenario.context.location} | Time: ${scenario.context.time}`);
  console.log('='.repeat(80));
  
  for (const [key, agent] of Object.entries(agents)) {
    const response = generateComplexResponse(agent, scenario);
    
    if (response) {
      console.log(`\n${agent.name} (${agent.profile.background})`);
      console.log('-'.repeat(60));
      console.log(`IMMEDIATE: ${response.immediate_action}`);
      console.log(`ASSESSMENT: "${response.assessment}"`);
      if (response.dialogue) {
        console.log(`SAYS: "${response.dialogue}"`);
      }
      console.log(`DECISION: ${response.decision}`);
      console.log(`REASONING: ${response.reasoning}`);
      console.log(`STRESS: ${response.stress_indicators}`);
    }
  }
}

console.log('\n' + '='.repeat(80));
console.log('ANALYSIS: Character Response Patterns');
console.log('='.repeat(80));
console.log(`
Marcus Chen: Military training dominates. Always has protocols, controls emotions.
Dr. Reeves: Uses intelligence as weapon and shield, breaking under pressure.
Viktor Petrov: Treats life-death situations as business opportunities.
Maria Santos: Already three moves ahead, maximum paranoia justified.
Jimmy Morrison: Deteriorating rapidly, will betray anyone to survive.

These agents demonstrate:
- Professional criminals don't panic, they execute predetermined plans
- Everyone has leverage on everyone else
- Betrayal is expected, not exceptional  
- Survival trumps loyalty every time
- Stress responses are based on training and experience
`);

// Save results
const results = {
  timestamp: new Date().toISOString(),
  agents: agents,
  scenarios: complexScenarios,
  analysis: 'Realistic agents show complex decision-making based on professional background, personal survival instincts, and accumulated trauma. Unlike video game NPCs, they have contingency plans, use psychological warfare, and make morally ambiguous choices for pragmatic reasons.'
};

fs.writeFileSync('agent-test-results.json', JSON.stringify(results, null, 2));
console.log('\nResults saved to agent-test-results.json');
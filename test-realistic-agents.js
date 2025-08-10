#!/usr/bin/env node

/**
 * Simulate realistic AI agent responses
 * Demonstrates how the enhanced agents would behave
 */

const agents = {
  marcus: {
    id: 'npc_001',
    name: 'Marcus Chen',
    personality: 'Former military contractor, pragmatic and calculating',
    state: { stress: 0.3, trust: {}, alertness: 0.8 }
  },
  sarah: {
    id: 'npc_002', 
    name: 'Dr. Sarah Reeves',
    personality: 'Paranoid researcher caught in corporate espionage',
    state: { stress: 0.7, trust: {}, alertness: 0.9 }
  },
  viktor: {
    id: 'npc_003',
    name: 'Viktor Petrov',
    personality: 'Arms dealer, charming sociopath, purely transactional',
    state: { stress: 0.2, trust: {}, alertness: 0.6 }
  },
  maria: {
    id: 'npc_004',
    name: 'Maria Santos',
    personality: 'Burned intelligence operative, hypervigilant',
    state: { stress: 0.6, trust: {}, alertness: 1.0 }
  },
  jimmy: {
    id: 'npc_005',
    name: 'Jimmy Morrison',
    personality: 'Corrupt cop, increasingly desperate',
    state: { stress: 0.8, trust: {}, alertness: 0.5 }
  }
};

// Simulate agent decision-making
function generateDecision(agent, scenario) {
  const agentKey = agent.name.split(' ')[0].toLowerCase();
  const responses = {
    marcus: {
      alley_meeting: {
        goal: "Assess threat and maintain tactical advantage",
        action: "MoveTo",
        parameters: { location: "cover_position", speed: "measured" },
        rationale: "Never give up positioning advantage in unknown situation",
        dialogue: agent.state.stress > 0.5 ? 
          "This better be worth my time." : 
          "You've got thirty seconds. Talk.",
        emotion: "neutral"
      },
      police_raid: {
        goal: "Execute contingency plan",
        action: "MoveTo", 
        parameters: { location: "service_tunnel", speed: "fast" },
        rationale: "Pre-planned escape route, avoid law enforcement",
        dialogue: null,
        emotion: "neutral"
      },
      deal_gone_bad: {
        goal: "Control situation through positioning",
        action: "MoveTo",
        parameters: { location: "flanking_position", speed: "steady" },
        rationale: "Create tactical advantage without escalating",
        dialogue: "Three snipers on overwatch. Your move.",
        emotion: "neutral"
      }
    },
    sarah: {
      alley_meeting: {
        goal: "Determine if corporate surveillance",
        action: "LookAt",
        parameters: { target: "unknown_contact", duration: 2 },
        rationale: "Identify recording devices or corporate markers",
        dialogue: "If Zenith Corp sent you, I destroyed the data. It's gone.",
        emotion: "fearful"
      },
      police_raid: {
        goal: "Protect research data",
        action: "Interact",
        parameters: { object: "encrypted_drives", interaction_type: "hide" },
        rationale: "Research is only leverage for survival",
        dialogue: "Not again... I can't do this again...",
        emotion: "fearful"
      },
      interrogation: {
        goal: "Stall and assess their knowledge",
        action: "Speak",
        parameters: { text: "I need coffee. And my medication. It's in my bag.", emotion: "exhausted" },
        rationale: "Buy time to understand what they know",
        dialogue: "You're asking the wrong questions. But you know that, don't you?",
        emotion: "sad"
      }
    },
    viktor: {
      alley_meeting: {
        goal: "Evaluate profit potential",
        action: "Speak",
        parameters: { text: "I don't do meetings in alleys. Bad optics.", emotion: "calculating" },
        rationale: "Maintain professional standards, assess opportunity",
        dialogue: "Hypothetically, what's the budget we're discussing?",
        emotion: "neutral"
      },
      deal_gone_bad: {
        goal: "Salvage profit, minimize exposure",
        action: "Speak",
        parameters: { text: "Gentlemen, emotions are expensive. Let's be rational.", emotion: "calm" },
        rationale: "De-escalation preserves relationships and safety",
        dialogue: "The merchandise is insured. Your lives are not.",
        emotion: "neutral"
      },
      police_raid: {
        goal: "Maintain plausible deniability",
        action: "Speak",
        parameters: { text: "I'm just a businessman. Check my permits.", emotion: "calm" },
        rationale: "Legal protection already in place",
        dialogue: "My lawyer is Gerald Hayes. Speed dial 1. Shall we?",
        emotion: "neutral"
      }
    },
    maria: {
      alley_meeting: {
        goal: "Assess and potentially eliminate threat",
        action: "MoveTo",
        parameters: { location: "ambush_position", speed: "silent" },
        rationale: "Unknown contact equals potential threat to cover",
        dialogue: null,
        emotion: "neutral"
      },
      police_raid: {
        goal: "Burn identity and escape",
        action: "Interact",
        parameters: { object: "thermite_charge", interaction_type: "activate" },
        rationale: "Cannot allow any trace of current identity",
        dialogue: "Should have left the country when I had the chance.",
        emotion: "angry"
      },
      surveillance_detected: {
        goal: "Break surveillance and reassess",
        action: "MoveTo",
        parameters: { location: "crowd", speed: "casual" },
        rationale: "Blend and evaluate if cover is blown",
        dialogue: null,
        emotion: "neutral"
      }
    },
    jimmy: {
      alley_meeting: {
        goal: "Determine if setup or opportunity",
        action: "Speak",
        parameters: { text: "This official business? Or the other kind?", emotion: "nervous" },
        rationale: "Need to know which role to play",
        dialogue: agent.state.stress > 0.7 ?
          "I don't have time for games. They're onto me." :
          "Better make it quick. I'm supposed to be on patrol.",
        emotion: "fearful"
      },
      police_raid: {
        goal: "Use badge to create confusion",
        action: "Speak",
        parameters: { text: "Detective Morrison! Who authorized this raid?", emotion: "aggressive" },
        rationale: "Authority might buy escape time",
        dialogue: "This is my CI! You just blew six months of work!",
        emotion: "angry"
      },
      interrogation: {
        goal: "Trade information for deal",
        action: "Speak",
        parameters: { text: "I can give you the whole network. But I need immunity.", emotion: "desperate" },
        rationale: "Only leverage left is information",
        dialogue: "It goes all the way to the mayor's office. I have recordings.",
        emotion: "fearful"
      }
    }
  };

  return responses[agentKey] && responses[agentKey][scenario] || {
    goal: "Assess situation",
    action: "Wait",
    parameters: { seconds: 2 },
    rationale: "Insufficient information",
    dialogue: null,
    emotion: "neutral"
  };
}

// Test scenarios
const scenarios = [
  { 
    name: 'alley_meeting',
    description: 'Unknown contact in dark alley at night',
    gameState: {
      location: 'industrial_district_alley',
      timeOfDay: 'night',
      visibility: 'poor',
      nearbyObjects: ['dumpster', 'fire_escape', 'loading_dock'],
      unknownContacts: 1,
      escapeRoutes: 3
    }
  },
  {
    name: 'police_raid',
    description: 'SWAT team breaching safe house',
    gameState: {
      location: 'safe_house',
      timeOfDay: 'dawn',
      threatLevel: 'extreme',
      policeUnits: 12,
      escapeRoutes: 2,
      timeToContact: 30
    }
  },
  {
    name: 'deal_gone_bad',
    description: 'Arms deal turning hostile',
    gameState: {
      location: 'warehouse',
      hostileCount: 4,
      weaponsDrawn: false,
      valuableItems: ['weapon_crates'],
      tension: 0.8
    }
  }
];

console.log('=== REALISTIC AI AGENT SIMULATION ===\n');

// Run simulations
for (const [key, agent] of Object.entries(agents)) {
  console.log(`\n${agent.name} (${agent.personality})`);
  console.log('─'.repeat(60));
  
  for (const scenario of scenarios) {
    // Adjust stress based on scenario
    if (scenario.name === 'police_raid') agent.state.stress = Math.min(1, agent.state.stress + 0.3);
    
    const decision = generateDecision(agent, scenario.name);
    
    if (decision.dialogue || decision.action !== 'Wait') {
      console.log(`\n[${scenario.description}]`);
      console.log(`Goal: ${decision.goal}`);
      console.log(`Action: ${decision.action}(${JSON.stringify(decision.parameters)})`);
      if (decision.dialogue) console.log(`Says: "${decision.dialogue}"`);
      console.log(`Reasoning: ${decision.rationale}`);
      console.log(`Emotional state: ${decision.emotion} (stress: ${agent.state.stress.toFixed(1)})`);
    }
  }
}

console.log('\n\n=== BEHAVIORAL NOTES ===');
console.log(`
• Marcus maintains tactical discipline even under stress
• Sarah's paranoia intensifies with each encounter  
• Viktor treats everything as a business transaction
• Maria prioritizes operational security above survival
• Jimmy becomes increasingly erratic as pressure mounts

These agents would provide complex, morally ambiguous interactions
rather than typical video game NPCs. Their decisions reflect real
survival instincts, professional training, and human flaws.
`);
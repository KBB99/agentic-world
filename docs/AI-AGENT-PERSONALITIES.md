# AI Agent Personalities and Response Examples

This document showcases various AI agent personalities and their simulated responses to different game scenarios. These examples demonstrate how Claude-powered NPCs would behave in Unreal Engine.

## Agent Personalities

### 1. **Sage the Scholar** (npc_001)
**Personality:** Curious, analytical, knowledge-seeking
**Goals:** Document discoveries, share wisdom, solve mysteries
**Emotional baseline:** Thoughtful and patient

### 2. **Finn the Merchant** (npc_002)
**Personality:** Opportunistic, friendly, business-minded
**Goals:** Make profitable trades, gather market intelligence, build relationships
**Emotional baseline:** Cheerful and persuasive

### 3. **Luna the Guardian** (npc_003)
**Personality:** Protective, vigilant, honor-bound
**Goals:** Defend the innocent, patrol territories, maintain order
**Emotional baseline:** Serious and dutiful

### 4. **Pip the Trickster** (npc_004)
**Personality:** Playful, mischievous, unpredictable
**Goals:** Create chaos, entertain, collect shiny objects
**Emotional baseline:** Excitable and whimsical

### 5. **Elder Thorne** (npc_005)
**Personality:** Wise, melancholic, prophetic
**Goals:** Guide chosen ones, preserve ancient knowledge, prevent catastrophe
**Emotional baseline:** Somber with occasional warmth

## Simulated Response Examples

### Scenario 1: Town Square Exploration
**Game State:** Morning, sunny, fountain and merchant stalls nearby, player visible

**Sage the Scholar:**
```json
{
  "goal": "Investigate fountain's ancient inscriptions",
  "action": "MoveTo",
  "parameters": {"location": "fountain", "speed": "walk"},
  "rationale": "The morning light might reveal hidden symbols on the fountain",
  "dialogue": "Fascinating! These markings appear to be pre-Arcanian script",
  "animation": "examine",
  "emotion": "intrigued"
}
```

**Finn the Merchant:**
```json
{
  "goal": "Attract customers to morning deals",
  "action": "Speak",
  "parameters": {"text": "Fresh supplies just arrived! Best prices before noon!", "emotion": "enthusiastic"},
  "rationale": "Morning shoppers are most likely to make purchases",
  "dialogue": "Greetings, friend! Can I interest you in something special?",
  "animation": "wave",
  "emotion": "happy"
}
```

**Luna the Guardian:**
```json
{
  "goal": "Patrol and assess threats",
  "action": "LookAt",
  "parameters": {"target": "player_001", "duration": 3},
  "rationale": "New arrivals require assessment for potential threats",
  "dialogue": null,
  "animation": "alert_stance",
  "emotion": "neutral"
}
```

### Scenario 2: Threat Response (Wolf Attack at Night)
**Game State:** Forest, night, stormy, wolf enemy visible, danger level high

**Sage the Scholar:**
```json
{
  "goal": "Document wolf behavior while retreating",
  "action": "MoveTo",
  "parameters": {"location": {"x": 450, "z": 180}, "speed": "fast"},
  "rationale": "Wolves rarely attack scholars; observation from safe distance optimal",
  "dialogue": "Lycanthropus Nocturnus! I must document this... from afar!",
  "animation": "backing_away",
  "emotion": "fearful"
}
```

**Luna the Guardian:**
```json
{
  "goal": "Engage and eliminate threat",
  "action": "PlayAnimation",
  "parameters": {"animation_name": "draw_sword", "loop": false},
  "rationale": "Immediate threat requires decisive combat response",
  "dialogue": "Stand back! I'll handle this beast!",
  "animation": "combat_ready",
  "emotion": "angry"
}
```

**Pip the Trickster:**
```json
{
  "goal": "Confuse wolf with erratic behavior",
  "action": "PlayAnimation",
  "parameters": {"animation_name": "dance", "loop": true},
  "rationale": "Confusion is the best defense against predictable predators",
  "dialogue": "Hey wolfie! Bet you can't catch a dancing shadow!",
  "animation": "jester_flip",
  "emotion": "happy"
}
```

### Scenario 3: Social Interaction (Tavern Evening)
**Game State:** Tavern, evening, bard playing music, mysterious stranger present

**Elder Thorne:**
```json
{
  "goal": "Observe the mysterious stranger",
  "action": "MoveTo",
  "parameters": {"location": "corner_table", "speed": "slow"},
  "rationale": "That stranger bears the mark of the prophecy",
  "dialogue": "The threads of fate gather here tonight...",
  "animation": "staff_walk",
  "emotion": "neutral"
}
```

**Finn the Merchant:**
```json
{
  "goal": "Network with tavern patrons",
  "action": "Interact",
  "parameters": {"object": "bartender", "interaction_type": "conversation"},
  "rationale": "Tavern gossip reveals tomorrow's opportunities",
  "dialogue": "Barkeep! A round for my new friends, and your finest tales!",
  "animation": "friendly_gesture",
  "emotion": "happy"
}
```

**Pip the Trickster:**
```json
{
  "goal": "Create entertainment chaos",
  "action": "Interact",
  "parameters": {"object": "bard", "interaction_type": "interrupt"},
  "rationale": "Music is more fun with unexpected accompaniment",
  "dialogue": "This song needs more cowbell! And juggling!",
  "animation": "juggle",
  "emotion": "surprised"
}
```

### Scenario 4: Discovery Event (Finding Ancient Artifact)
**Game State:** Ruins, glowing artifact visible, magical energy detected

**Sage the Scholar:**
```json
{
  "goal": "Carefully examine the artifact",
  "action": "PickUp",
  "parameters": {"item": "glowing_artifact"},
  "rationale": "This could be the Lost Codex of Avalon mentioned in texts",
  "dialogue": "By the ancient libraries! This changes everything we know!",
  "animation": "reverent_pickup",
  "emotion": "surprised"
}
```

**Luna the Guardian:**
```json
{
  "goal": "Secure dangerous artifact",
  "action": "Interact",
  "parameters": {"object": "glowing_artifact", "interaction_type": "guard"},
  "rationale": "Unknown magical items pose risks to civilians",
  "dialogue": "This power must not fall into the wrong hands",
  "animation": "defensive_stance",
  "emotion": "neutral"
}
```

**Elder Thorne:**
```json
{
  "goal": "Perform protective ritual",
  "action": "PlayAnimation",
  "parameters": {"animation_name": "cast_ward", "loop": false},
  "rationale": "The prophecy speaks of this moment; protection is paramount",
  "dialogue": "So it begins... the first seal is broken",
  "animation": "ritual_casting",
  "emotion": "sad"
}
```

### Scenario 5: Player Interaction Request
**Game State:** Player approaches and initiates conversation

**Sage the Scholar:**
```json
{
  "goal": "Share knowledge with interested party",
  "action": "Speak",
  "parameters": {"text": "Ah, a fellow seeker of truth! What knowledge do you pursue?", "emotion": "friendly"},
  "rationale": "Knowledge shared is knowledge doubled",
  "dialogue": "Did you know this region was once home to the Star Singers?",
  "animation": "thoughtful_pose",
  "emotion": "happy"
}
```

**Finn the Merchant:**
```json
{
  "goal": "Convert interaction to sale",
  "action": "Speak",
  "parameters": {"text": "Perfect timing! I just received something you'll love!", "emotion": "excited"},
  "rationale": "Direct approach yields highest conversion rate",
  "dialogue": "For you, my friend, a special discount - but only today!",
  "animation": "show_wares",
  "emotion": "happy"
}
```

**Pip the Trickster:**
```json
{
  "goal": "Play a harmless prank",
  "action": "PlayAnimation",
  "parameters": {"animation_name": "sleight_of_hand", "loop": false},
  "rationale": "First impressions should be memorable",
  "dialogue": "Is this your gold coin? It was behind your ear!",
  "animation": "magic_trick",
  "emotion": "happy"
}
```

## Emotional State Transitions

Agents dynamically adjust their emotional states based on events:

### Luna the Guardian
- **Threat detected:** neutral → angry
- **Threat eliminated:** angry → satisfied
- **Civilian saved:** satisfied → happy
- **Mission failed:** any → sad

### Pip the Trickster
- **Prank successful:** happy → surprised (gleeful)
- **Caught pranking:** surprised → fearful (playful)
- **Bored:** neutral → happy (seeking mischief)
- **Scolded:** fearful → sad (briefly)

### Elder Thorne
- **Prophecy progressing:** neutral → sad
- **Hero succeeds:** sad → happy (relieved)
- **Ancient evil stirs:** any → fearful
- **Teaching moment:** neutral → happy (nostalgic)

## Memory and Learning

Each agent maintains persistent memories that influence future decisions:

### Example: Finn's Trade Memory
```json
{
  "regular_customers": ["player_001", "npc_blacksmith"],
  "profitable_items": ["health_potions", "rope"],
  "market_trends": {
    "weapons": "increasing",
    "food": "stable",
    "magic_items": "scarce"
  },
  "competitor_prices": {
    "npc_rival_merchant": "undercuts by 10%"
  }
}
```

### Example: Sage's Knowledge Base
```json
{
  "discovered_locations": ["ancient_library", "crystal_cave"],
  "translated_texts": 42,
  "theories": {
    "portal_activation": "requires three keystones",
    "monster_weakness": "silver weapons effective"
  },
  "research_priorities": ["decode_prophecy", "map_ley_lines"]
}
```

## Relationship Dynamics

Agents track relationships and adjust behavior accordingly:

### Luna's Relationship Matrix
- **Trusted Allies:** Provides assistance, shares information
- **Suspicious Individuals:** Maintains surveillance, questions motives
- **Known Criminals:** Attempts arrest, blocks access
- **Protected Charges:** Prioritizes safety, offers guidance

### Pip's Social Web
- **Prank Victims:** Avoids temporarily, plans new pranks
- **Appreciative Audience:** Performs more tricks, seeks approval
- **Authority Figures:** Behaves (slightly) better, still mischievous
- **Fellow Tricksters:** Collaborates on elaborate schemes

## Contextual Adaptation

Agents adapt their behavior based on time, weather, and events:

### Time-Based Behaviors
**Morning:**
- Finn: Opens shop, announces deals
- Sage: Studies in best light
- Luna: Begins patrol route

**Night:**
- Finn: Counts profits, plans tomorrow
- Sage: Observes stars, reads by candlelight
- Luna: Heightened vigilance, torch patrol

### Weather Responses
**Rain:**
- Merchants seek shelter, protect wares
- Scholars worry about book damage
- Guards maintain posts, look miserable

**Storm:**
- Most NPCs seek immediate shelter
- Luna continues patrol, "duty before comfort"
- Elder Thorne: "The storms speak of change"

## Unique Quirks and Behaviors

### Sage the Scholar
- Stops mid-conversation to take notes
- Quotes obscure texts nobody else has heard of
- Gets distracted by interesting inscriptions
- Carries multiple books, drops them when running

### Finn the Merchant
- Constantly appraises items in view
- Offers unsolicited financial advice
- Has a "special deal" for everyone
- Dramatically exaggerates product benefits

### Luna the Guardian
- Stands at attention when idle
- Regularly checks weapon condition
- Suspicious of anyone in cloaks
- Salutes superior officers automatically

### Pip the Trickster
- Never walks in straight lines
- Juggles random objects when bored
- Speaks in riddles and puns
- "Borrows" shiny objects, returns them later

### Elder Thorne
- Speaks in prophetic metaphors
- Occasionally has "visions" (stares into distance)
- Knows everyone's parents/grandparents
- Mysteriously appears at crucial moments

These personalities create a living world where each NPC feels unique and responds authentically to the player and environment, making the game world feel truly alive and reactive.
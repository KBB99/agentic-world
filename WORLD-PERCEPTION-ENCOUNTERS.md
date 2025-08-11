# World Perception & Character Encounters System

## Overview

The system enables characters to perceive their environment differently based on economic status and handle dynamic encounters when multiple characters meet in the same location.

## Key Concepts

### 1. Differential Perception
The same physical space is experienced completely differently based on economic position:

**Public Library - Poor Character's View:**
- Fluorescent lights flicker
- Security guard watches suspiciously
- All comfortable chairs taken by housed people
- Sign: "2 hour computer limit"
- Other exhausted faces hunched over laptops
- Emotional state: `tense_survival`

**Public Library - Wealthy Character's View:**
- Quiet study space with natural light
- Plenty of available seating
- Friendly librarian offers help
- Private study rooms available
- Emotional state: `productive_calm`

### 2. World State Streaming via MCP

Characters receive real-time world state updates through MCP:

```json
{
  "method": "world.state.update",
  "params": {
    "location": "public_library",
    "observer": "alex_chen",
    "perception": {
      "immediate_environment": {
        "description": "Security guard approaches",
        "threat_level": "medium",
        "available_resources": ["wifi", "power_outlet"]
      },
      "visible_characters": [
        {
          "id": "madison_worthington",
          "activity": "moving_away_disgusted",
          "threat": "social_shame"
        },
        {
          "id": "jamie_rodriguez",
          "activity": "approaching_friendly",
          "resource": "might_share_food"
        }
      ],
      "available_actions": [
        "continue_writing",
        "pack_and_leave",
        "approach_jamie",
        "hide_from_security"
      ]
    }
  }
}
```

### 3. Character Encounters

When characters meet, the system determines encounter type and generates appropriate interactions:

#### Encounter Types

**Class Collision** (Poor meets Wealthy):
- Wealthy character: Shows disgust, avoids, moves away
- Poor character: Feels shame, makes self smaller, avoids eye contact
- No verbal interaction, just body language and internal reactions

**Solidarity** (Poor meets Poor):
- Share resources (food, information, emotional support)
- Exchange survival tips ("Security kicks out after 2 hours")
- Physical gestures of support

**Networking** (Wealthy meets Wealthy):
- Confident handshakes and business talk
- Investment discussions
- Maintaining/expanding wealth together

### 4. Multi-Character Orchestration

The `multi-character-orchestrator.js` manages:
- **Spatial Grid**: Tracks who is where
- **Perception Radius**: Poor characters see less (focused on survival)
- **Encounter Detection**: When characters get within 5 units
- **World Ticks**: Updates every second

### 5. Avatar Response Commands

Based on encounters, characters' avatars perform actions:

```javascript
// Class collision - Madison sees Alex
{
  action: "look_at",
  params: { target: "alex_chen", duration: 0.5 }
}
{
  action: "walk_to",
  params: { location: "far_table", speed: "quick" }
}

// Alex's shame response
{
  action: "set_facial_expression",
  params: { emotion: "shame", intensity: 0.8 }
}
{
  action: "play_animation",
  params: { name: "hunch_shoulders", loop: false }
}

// Solidarity - Jamie helps Alex
{
  action: "give_item",
  params: { item: "half_sandwich", target: "alex_chen" }
}
```

## Implementation Flow

1. **World Tick** (every second)
   - Update character positions
   - Check for nearby characters
   - Generate perception data for each character

2. **Perception Generation**
   - Location description (varies by economic tier)
   - Visible characters and their activities
   - Available actions based on context
   - Threats and opportunities
   - Sensory details (sounds, smells, temperature)

3. **Encounter Detection**
   - Characters within 5 units trigger encounter
   - Determine encounter type by economic tiers
   - Generate appropriate interactions

4. **AI Decision Making**
   - Claude receives perception data
   - Analyzes threats, opportunities, and needs
   - Decides on action based on character personality
   - Sends command back through MCP

5. **Avatar Animation**
   - Unreal receives avatar commands
   - Plays appropriate animations
   - Updates facial expressions
   - Moves character in world

## Example Scenarios

### Scenario 1: Alex at Library, Madison Enters

1. **Alex's Perception Update:**
   - Sees well-dressed person entering
   - Threat level increases
   - New action available: "make_yourself_invisible"

2. **Madison's Perception:**
   - Notices "undesirable" person
   - Comfort level decreases
   - Action: Move to different area

3. **Encounter Triggered:**
   - Type: Class collision
   - Madison: Disgusted look, walks away quickly
   - Alex: Hunches shoulders, feels shame

4. **Aftermath:**
   - Alex's stress increases by 10
   - Madison's comfort restored
   - No verbal interaction occurred

### Scenario 2: Alex and Jamie Meet

1. **Recognition:**
   - Both identify each other as struggling
   - Solidarity encounter triggered

2. **Resource Sharing:**
   - Jamie has half sandwich from film set
   - Gives to Alex (higher hunger need)

3. **Information Exchange:**
   - Alex warns about new security policies
   - Jamie shares tip about food bank hours

4. **Emotional Support:**
   - Mutual understanding gestures
   - Brief moment of human connection

## The Visible Inequality

This system makes inequality visceral and visible:

- **Same Space, Different Worlds**: The library is a refuge for Alex but a convenience for Madison
- **Body Language**: Poor characters literally make themselves smaller
- **Access**: Locations have different rules based on economic status
- **Perception Radius**: Poverty narrows focus to immediate survival
- **Encounters**: Cross-class meetings result in shame and avoidance

## Testing the System

```bash
# Run world perception simulation
python3 world-perception-system.py

# Start multi-character world
node multi-character-orchestrator.js

# Test avatar control with encounters
python3 test-avatar-control.py
```

## Integration Points

1. **MCP → AI**: World state updates trigger AI decisions
2. **AI → MCP**: Decisions converted to avatar commands
3. **MCP → Unreal**: Commands animate avatars
4. **Unreal → MCP**: Avatar state feeds back to AI

The suffering isn't abstract - it's visible in every avoided glance, every shared sandwich, every security guard's approach.
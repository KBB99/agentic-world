# Unreal Engine Avatar Control via MCP

## Overview

Characters in the simulation control their Unreal Engine avatars through MCP (Model Context Protocol) commands. The AI agents make decisions based on their economic situation, and these decisions are translated into avatar animations, movements, and interactions in the 3D world.

## Architecture

```
Claude AI (Decision) → MCP Bridge → TCP Socket → Unreal Engine → Avatar Animation
                          ↑                           ↓
                    WebSocket API ← Game State ← World Feedback
```

## Command Flow

### 1. AI Decision Phase
The AI agent (powered by Claude) analyzes the character's situation and decides on an action:

```python
# Alex Chen's AI decides they need to find food
decision = {
    "character": "alex_chen",
    "goal": "survive_hunger",
    "action": "go_to_food_bank",
    "rationale": "Haven't eaten in 18 hours, $0.47 won't buy food",
    "urgency": "high"
}
```

### 2. MCP Translation
The decision is translated into avatar control commands:

```json
{
    "jsonrpc": "2.0",
    "method": "unreal.avatar.control",
    "params": {
        "character_id": "alex_chen",
        "action": "walk_to",
        "parameters": {
            "location": "food_bank",
            "speed": "weak",
            "animation_override": "hunger_walk"
        }
    }
}
```

### 3. Unreal Execution
Unreal Engine receives the command and:
- Navigates the avatar to the food bank
- Plays hunger/exhaustion animations
- Updates facial expressions
- Triggers need-based behaviors

## Avatar Commands

### Movement Commands
```javascript
walk_to(location, speed)        // Navigate to location
run_to(location)                 // Run (uses more energy)
turn_to(degrees)                 // Rotate avatar
look_at(target, duration)        // Focus on object/character
sit_on(object)                   // Sit on furniture/ground
stand_up()                       // Stand from sitting
```

### Interaction Commands
```javascript
pickup(object)                   // Pick up item
drop(object)                     // Drop held item
use(object, action)              // Use object (laptop, phone, etc.)
open(object)                     // Open door/container
talk_to(character, message)      // Speak to NPC
gesture(type)                    // Perform gesture
```

### Expression Commands
```javascript
set_facial_expression(emotion, intensity)  // Change face
play_animation(name, loop)                 // Play animation
set_posture(type)                         // Body language
```

### Need-Based Commands
```javascript
eat(food_item)                   // Consume food
drink(drink_item)                // Drink
sleep(location, duration)        // Rest
work(activity, duration)         // Perform work
```

## Character-Specific Behaviors

### Economic Tier Restrictions

**Poor Characters (Alex, Jamie, Maria)**
- Cannot enter: luxury stores, private offices, expensive restaurants
- Limited animations: exhausted, stressed, desperate
- Restricted items: only free/cheap objects
- Movement: slower due to exhaustion/hunger

**Wealthy Characters (Tyler, Madison)**
- Full access to all locations
- Confident animations and postures
- Premium items and interactions
- Fast, purposeful movement

### Example: Alex Chen's Day

```python
# 6 AM - Wake up rough
mcp.send("play_animation", {"name": "wake_up_cardboard", "loop": false})
mcp.send("stand_up", {})
mcp.send("set_facial_expression", {"emotion": "exhausted", "intensity": 0.9})

# 9 AM - Rush to library for power outlet
mcp.send("run_to", {"location": "library"})  # Despite exhaustion
mcp.send("sit_on", {"object": "floor"})  # All chairs taken
mcp.send("use", {"object": "old_laptop", "action": "write"})

# 12 PM - Hunger kicks in
mcp.send("play_animation", {"name": "stomach_clutch", "loop": false})
mcp.send("check_pockets", {})  # Finds $0.47

# 3 PM - Food bank
mcp.send("walk_to", {"location": "food_bank", "speed": "weak"})
mcp.send("stand_in_line", {"duration": 45})
mcp.send("receive", {"items": ["canned_beans", "stale_bread"]})
mcp.send("eat", {"food_item": "bread", "urgency": "immediate"})
```

### Example: Madison Worthington's Day

```python
# 10 AM - Morning routine
mcp.send("wake_up", {"location": "king_bed"})
mcp.send("walk_to", {"location": "marble_bathroom", "speed": "graceful"})
mcp.send("use", {"object": "phone", "action": "check_instagram"})

# 12 PM - Yoga class
mcp.send("walk_to", {"location": "yoga_studio", "speed": "elegant"})
mcp.send("play_animation", {"name": "warrior_pose", "loop": true})
mcp.send("drink", {"drink_item": "adaptogenic_smoothie_18_dollars"})

# See homeless person
mcp.send("look_at", {"target": "homeless_person", "duration": 0.5})
mcp.send("gesture", {"type": "dismissive_wave"})
mcp.send("walk_faster", {})
mcp.send("use", {"object": "phone", "action": "donate_5_dollars_for_tax_writeoff"})
```

## Emotional States & Animations

### Stress Responses by Economic Tier

**High Stress (Poor)**
- `head_in_hands`
- `nervous_pace`
- `bite_nails`
- `exhausted_slouch`

**Low Stress (Wealthy)**
- `confident_stance`
- `casual_stretch`
- `check_watch`
- `satisfied_smile`

## Implementation in Unreal

### 1. TCP Listener Blueprint
```cpp
// Listen on port 32123 for MCP commands
FSocket* ListenerSocket = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM)
    ->CreateSocket(NAME_Stream, TEXT("MCP_Listener"), false);
    
FIPv4Endpoint Endpoint(FIPv4Address::Any, 32123);
ListenerSocket->Bind(*Endpoint.ToInternetAddr());
ListenerSocket->Listen(8);
```

### 2. Command Parser
```cpp
void ParseMCPCommand(const FString& JSONCommand) {
    TSharedPtr<FJsonObject> ParsedCommand;
    if (FJsonSerializer::Deserialize(Reader, ParsedCommand)) {
        FString CharacterID = ParsedCommand->GetStringField("character_id");
        FString Action = ParsedCommand->GetStringField("action");
        
        // Route to appropriate character controller
        if (ACharacterAvatar* Avatar = FindAvatar(CharacterID)) {
            Avatar->ExecuteCommand(Action, ParsedCommand->GetObjectField("parameters"));
        }
    }
}
```

### 3. Animation State Machine
Each character has animation states based on:
- Economic tier
- Current needs (hunger, exhaustion, stress)
- Location permissions
- Available resources

### 4. Need System Integration
```cpp
class UCharacterNeeds : public UActorComponent {
    float Hunger = 50.0f;
    float Exhaustion = 30.0f;
    float Stress = 70.0f;
    
    void UpdateAnimation() {
        if (Hunger > 80) PlayAnimation("stomach_clutch");
        if (Exhaustion > 90) SetMovementSpeed(0.3f);
        if (Stress > 85) PlayAnimation("anxiety_fidget");
    }
};
```

## Testing the System

### 1. Start MCP Bridge
```bash
node mcp-to-unreal-bridge.js \
  --character alex_chen \
  --tier poor \
  --wss wss://your-api-gateway/prod
```

### 2. Send Test Commands
```bash
# Test Alex walking to library
curl -X POST http://localhost:32123 \
  -d '{"method":"walk_to","params":{"location":"library","speed":"tired"}}'

# Test Madison's dismissive gesture
curl -X POST http://localhost:32123 \
  -d '{"method":"gesture","params":{"type":"dismissive_wave"}}'
```

### 3. Monitor Avatar Response
- Avatar should navigate to specified location
- Appropriate animations should play
- Facial expressions should update
- Need meters should change

## WebSocket Telemetry

Avatar states are streamed back through WebSocket:

```json
{
    "type": "avatar_state",
    "character_id": "alex_chen",
    "state": {
        "location": "library",
        "animation": "typing_frantically",
        "needs": {
            "hunger": 85,
            "exhaustion": 90,
            "stress": 95
        },
        "held_items": ["old_laptop"],
        "money": 6.47
    }
}
```

## The Visible Inequality

The avatar control system makes economic inequality viscerally visible:

- **Alex's avatar**: Slow, exhausted animations, restricted from most locations
- **Tyler's avatar**: Confident stride, access everywhere, casual gestures
- **Madison's avatar**: Graceful movements, oblivious to suffering around her
- **Maria's avatar**: Hurried between work and childcare, visibly stressed
- **Jamie's avatar**: Switching between fake customer service smile and exhaustion

The same city, rendered in Unreal Engine, is experienced completely differently based on economic position. The avatars don't just have different stats - they move through the world in fundamentally different ways.

## Next Steps

1. Implement TCP listener in Unreal Engine
2. Create animation blueprints for each economic tier
3. Build location-based access control
4. Add need system with visual feedback
5. Connect WebSocket for state streaming
6. Implement multiplayer to see inequality in real-time

The suffering isn't just data. It's visible in every animation, every restricted door, every exhausted step.
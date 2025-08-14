# Unreal Engine Character Control System - Implementation Plan

## Overview
Enable AI characters from the web simulation to control physical bodies in Unreal Engine, creating a living world where economic decisions translate to visible actions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Interface                           │
│  [Character Decisions] → [Action Commands] → [WebSocket]        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MCP Bridge (Enhanced)                        │
│  • Translate AI decisions to Unreal commands                    │
│  • Queue actions for execution                                  │
│  • Handle perception data from Unreal                          │
└────────────────────────┬────────────────────────────────────────┘
                         │ TCP/JSON-RPC
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Unreal Engine MCP Server                       │
│  • Receive commands via MCP protocol                            │
│  • Execute character actions                                    │
│  • Send world state back to AI                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│              Unreal Engine Character System                     │
│  • Character Controllers (one per AI)                           │
│  • Animation State Machines                                     │
│  • Physics & Collision                                          │
│  • Perception Components                                        │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: MCP Command Protocol

### Character Control Commands

```typescript
// Movement Commands
MoveTo(location: Vector3, speed: float)
LookAt(target: Vector3 | ActorId, duration: float)
StopMoving()
Turn(degrees: float)

// Animation Commands
PlayAnimation(animName: string, loop: bool, blendTime: float)
SetAnimationState(state: "idle" | "walking" | "running" | "sitting")
PlayGesture(gesture: "wave" | "nod" | "shake_head" | "point")

// Interaction Commands
Interact(objectId: string, interactionType: string)
PickUp(itemId: string)
Drop(itemId: string)
Use(itemId: string)

// Communication Commands
Speak(text: string, emotion: string, duration: float)
ShowEmotion(emotion: string, intensity: float)
DisplayThought(thought: string, duration: float)

// Perception Queries
GetVisibleActors() → Actor[]
GetNearbyItems() → Item[]
GetCurrentLocation() → Vector3
GetCharacterState() → CharacterState
```

### Implementation File: `mcp-unreal-commands.js`

```javascript
const UNREAL_COMMANDS = {
  // Movement
  MOVE_TO: 'character.moveTo',
  LOOK_AT: 'character.lookAt',
  STOP: 'character.stop',
  
  // Animation
  PLAY_ANIM: 'character.playAnimation',
  SET_STATE: 'character.setState',
  
  // Interaction
  INTERACT: 'character.interact',
  PICK_UP: 'character.pickUp',
  DROP: 'character.drop',
  
  // Communication
  SPEAK: 'character.speak',
  EMOTE: 'character.emote',
  
  // Perception
  GET_PERCEPTION: 'character.getPerception'
};
```

## Phase 2: Unreal Engine Blueprint System

### Character Controller Blueprint

```
ACharacterController
├── Components
│   ├── CharacterMovement
│   ├── AnimationController
│   ├── PerceptionComponent
│   ├── InteractionComponent
│   └── MCPInterface
├── Properties
│   ├── CharacterID (string)
│   ├── CurrentState (struct)
│   ├── Memories (array)
│   └── Personality (struct)
└── Functions
    ├── ExecuteCommand(command)
    ├── UpdatePerception()
    ├── SendStateToMCP()
    └── ProcessDecision(decision)
```

### Location System in Unreal

Map real-world inspired locations:

```
Level: UrbanInequality
├── Locations
│   ├── PublicLibrary
│   │   ├── WiFiZone (trigger volume)
│   │   ├── Tables (interactable)
│   │   ├── PowerOutlets (interactable)
│   │   └── Security (NPC)
│   ├── CoffeeShop
│   │   ├── Counter (work location)
│   │   ├── Seating (interactable)
│   │   └── WiFiZone
│   ├── FoodBank
│   │   ├── Queue (nav points)
│   │   ├── FoodPickup (interactable)
│   │   └── WaitArea
│   ├── LuxuryApartment
│   │   ├── Penthouse
│   │   ├── Gym
│   │   └── PrivateOffice
│   └── Streets
│       ├── Sidewalks (nav mesh)
│       ├── Benches (rest points)
│       └── ATMs (interactable)
```

## Phase 3: Character Movement & Animation

### Animation State Machine

```
States:
├── Idle
│   ├── Standing
│   ├── Sitting
│   └── Lying
├── Locomotion
│   ├── Walk
│   ├── Run
│   └── Sneak
├── Work
│   ├── Typing
│   ├── Serving
│   └── Cleaning
├── Social
│   ├── Talking
│   ├── Listening
│   └── Gesturing
└── Emotional
    ├── Desperate (slouched, slow)
    ├── Stressed (fidgeting, pacing)
    ├── Happy (upright, energetic)
    └── Exhausted (dragging, stumbling)
```

### Movement System

```cpp
// CharacterMovementComponent.cpp
void ExecuteMoveTo(FVector Destination) {
    // Use Unreal's built-in pathfinding
    UAIBlueprintHelperLibrary::SimpleMoveToLocation(
        Controller, 
        Destination
    );
    
    // Adjust speed based on character state
    float Speed = CalculateSpeedFromNeeds();
    GetCharacterMovement()->MaxWalkSpeed = Speed;
}

float CalculateSpeedFromNeeds() {
    // Exhausted characters move slower
    float Exhaustion = CharacterState.Needs.Exhaustion;
    float BaseSpeed = 600.0f;
    return BaseSpeed * (1.0f - (Exhaustion / 100.0f) * 0.5f);
}
```

## Phase 4: Perception System

### What Characters Can See

```cpp
struct FCharacterPerception {
    TArray<AActor*> VisibleCharacters;
    TArray<AInteractable*> NearbyObjects;
    FLocationInfo CurrentLocation;
    float AvailableWiFiStrength;
    bool SecurityPresent;
    int32 CrowdDensity;
};

FCharacterPerception GatherPerception() {
    FCharacterPerception Perception;
    
    // Use Unreal's perception component
    GetPerceptionComponent()->GetCurrentlyPerceivedActors(
        SightConfig->GetSenseClass(), 
        Perception.VisibleCharacters
    );
    
    // Check for interactables in range
    GetWorld()->OverlapMultiByChannel(...);
    
    // Determine location context
    Perception.CurrentLocation = GetLocationContext();
    
    return Perception;
}
```

### Sending Perception to AI

```javascript
// In MCP bridge
async function sendPerceptionToAI(characterId, perception) {
    const enrichedPerception = {
        ...perception,
        interpretation: interpretPerception(perception),
        opportunities: findOpportunities(perception),
        threats: identifyThreats(perception)
    };
    
    // Send to AI for decision making
    await updateCharacterPerception(characterId, enrichedPerception);
}
```

## Phase 5: Action Execution System

### Mapping AI Decisions to Unreal Actions

```javascript
// decision-to-action-mapper.js

function mapDecisionToUnrealCommands(decision) {
    const commands = [];
    
    switch(decision.action) {
        case 'search_for_food':
            commands.push({
                type: 'MOVE_TO',
                params: { location: 'FoodBank' }
            });
            commands.push({
                type: 'PLAY_ANIM',
                params: { anim: 'desperate_walk' }
            });
            break;
            
        case 'work_shift':
            commands.push({
                type: 'MOVE_TO',
                params: { location: 'CoffeeShop.Counter' }
            });
            commands.push({
                type: 'PLAY_ANIM',
                params: { anim: 'working_barista', loop: true }
            });
            break;
            
        case 'stream_for_donations':
            commands.push({
                type: 'INTERACT',
                params: { object: 'Laptop', action: 'use' }
            });
            commands.push({
                type: 'SPEAK',
                params: { 
                    text: "Hey everyone, thanks for watching...",
                    emotion: decision.emotion 
                }
            });
            break;
            
        case 'ask_for_help':
            commands.push({
                type: 'LOOK_AT',
                params: { target: 'NearestCharacter' }
            });
            commands.push({
                type: 'PLAY_GESTURE',
                params: { gesture: 'plead' }
            });
            commands.push({
                type: 'SPEAK',
                params: { 
                    text: decision.dialogue,
                    emotion: 'desperate'
                }
            });
            break;
    }
    
    return commands;
}
```

## Phase 6: Bidirectional Communication

### Enhanced MCP Bridge

```javascript
// mcp-bridge-unreal.js

class UnrealMCPBridge {
    constructor() {
        this.characterQueues = new Map(); // Commands per character
        this.perceptionCache = new Map();  // Latest perception per character
    }
    
    // From AI to Unreal
    async sendCommandToUnreal(characterId, command) {
        const message = {
            jsonrpc: '2.0',
            method: command.type,
            params: {
                characterId,
                ...command.params
            },
            id: generateId()
        };
        
        await this.tcpClient.send(message);
    }
    
    // From Unreal to AI
    async handleUnrealUpdate(message) {
        if (message.method === 'perception.update') {
            const { characterId, perception } = message.params;
            
            // Cache perception
            this.perceptionCache.set(characterId, perception);
            
            // Trigger AI decision
            await this.requestAIDecision(characterId, perception);
        }
        
        if (message.method === 'action.completed') {
            const { characterId, action, result } = message.params;
            
            // Log completion
            console.log(`${characterId} completed ${action}: ${result}`);
            
            // Process next queued action
            this.processNextAction(characterId);
        }
    }
    
    async requestAIDecision(characterId, perception) {
        // Get character state from DynamoDB
        const character = await getCharacterState(characterId);
        
        // Get AI decision
        const decision = await getAIDecision(character, perception);
        
        // Map to Unreal commands
        const commands = mapDecisionToUnrealCommands(decision);
        
        // Queue and execute
        this.queueCommands(characterId, commands);
    }
}
```

## Phase 7: Visual Feedback System

### Character State Visualization

```cpp
// Show character state above their head
class UCharacterStateWidget : public UUserWidget {
    UPROPERTY(meta = (BindWidget))
    UTextBlock* NameText;
    
    UPROPERTY(meta = (BindWidget))
    UTextBlock* MoneyText;
    
    UPROPERTY(meta = (BindWidget))
    UProgressBar* HungerBar;
    
    UPROPERTY(meta = (BindWidget))
    UProgressBar* ExhaustionBar;
    
    UPROPERTY(meta = (BindWidget))
    UTextBlock* CurrentActionText;
    
    void UpdateDisplay(FCharacterState State) {
        NameText->SetText(FText::FromString(State.Name));
        MoneyText->SetText(FText::Format(
            LOCTEXT("Money", "${0}"),
            FText::AsNumber(State.Money)
        ));
        HungerBar->SetPercent(State.Needs.Hunger / 100.0f);
        ExhaustionBar->SetPercent(State.Needs.Exhaustion / 100.0f);
        CurrentActionText->SetText(FText::FromString(State.CurrentAction));
    }
};
```

### Emotion & Speech Bubbles

```cpp
// Display speech and thoughts
void ShowSpeechBubble(FString Text, FString Emotion) {
    // Create widget component
    USpeechBubbleWidget* Bubble = CreateWidget<USpeechBubbleWidget>();
    Bubble->SetText(Text);
    Bubble->SetEmotion(Emotion);
    
    // Position above character
    Bubble->AddToViewport();
    Bubble->SetPositionInViewport(
        GetCharacterScreenPosition() + FVector2D(0, -100)
    );
    
    // Auto-hide after duration
    GetWorld()->GetTimerManager().SetTimer(
        HideTimer, 
        [Bubble]() { Bubble->RemoveFromParent(); },
        3.0f, 
        false
    );
}
```

## Phase 8: Testing & Integration

### Test Scenarios

1. **Basic Movement Test**
   ```
   Alex Chen: "Go to library" → Character walks to library in Unreal
   ```

2. **Interaction Test**
   ```
   Jamie: "Make coffee" → Character moves to machine, plays animation
   ```

3. **Social Interaction Test**
   ```
   Two characters meet → Face each other, play conversation animations
   ```

4. **Economic Action Test**
   ```
   Character streams → Sits at computer, typing animation, speech bubbles
   ```

5. **Emotional State Test**
   ```
   Exhausted character → Slow walk, slouched posture, stumbling
   ```

## Implementation Timeline

### Week 1: Foundation
- [ ] Set up Unreal project with basic level
- [ ] Create character Blueprint with movement
- [ ] Implement MCP server in Unreal (C++ or Blueprint)
- [ ] Test basic TCP communication

### Week 2: Character Control
- [ ] Implement movement commands
- [ ] Add animation state machine
- [ ] Create perception component
- [ ] Test command execution

### Week 3: World Building
- [ ] Build library, coffee shop, food bank locations
- [ ] Add interactable objects
- [ ] Implement navigation mesh
- [ ] Create location-based triggers

### Week 4: AI Integration
- [ ] Connect MCP bridge to Unreal
- [ ] Map AI decisions to commands
- [ ] Test full pipeline
- [ ] Add visual feedback (UI, speech bubbles)

### Week 5: Polish & Testing
- [ ] Refine animations
- [ ] Add particle effects (stress, exhaustion)
- [ ] Test multi-character scenarios
- [ ] Performance optimization

## Required Unreal Assets

### Characters
- Base human character mesh
- Clothing variations (poor, middle, wealthy)
- Animation sets (locomotion, work, social, emotional)

### Environment
- Urban environment kit
- Interior sets (library, coffee shop, apartment)
- Props (laptops, coffee machines, benches, books)

### UI
- Character state widgets
- Speech bubble system
- Interaction prompts

## Technical Requirements

### Unreal Engine
- Version: 5.3+
- Plugins:
  - AI/Navigation
  - HTTP/WebSocket
  - JSON parsing

### Networking
- TCP server for MCP protocol
- JSON-RPC message handling
- Async command processing

### Performance
- Level-of-detail (LOD) for characters
- Occlusion culling for interiors
- Efficient perception updates (tick rate limiting)

## Success Metrics

1. **Response Time**: < 100ms from decision to action start
2. **Animation Quality**: Smooth transitions, no glitches
3. **Perception Accuracy**: Characters see what they should
4. **Command Success Rate**: > 95% execution success
5. **Multi-Character**: Support 20+ simultaneous characters

## Next Steps

1. **Create Unreal Project**
   ```bash
   # Create new project
   UnrealEngine/Engine/Binaries/Win64/UnrealEditor.exe -CreateProject
   ```

2. **Install Required Plugins**
   - MCP Server Plugin (custom)
   - WebSocket Client
   - JSON Blueprint

3. **Import Base Assets**
   - Character models
   - Animation packs
   - Environment kit

4. **Begin Implementation**
   - Start with Phase 1: MCP Protocol
   - Test with single character
   - Gradually add complexity

This system will bring the economic simulation to life, making inequality visible and visceral as characters physically navigate their world based on their economic circumstances.
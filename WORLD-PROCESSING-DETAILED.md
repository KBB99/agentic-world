# Detailed World & Scene Processing Architecture

## Overview: The Data Flow

```
UNREAL ENGINE (Ground Truth) → MCP Bridge → AI Processing → Decision → Avatar Command → UNREAL ENGINE
        ↑                                                                                      ↓
        └──────────────────────── World State Feedback Loop ─────────────────────────────────┘
```

## Layer 1: Unreal Engine - The Ground Truth

### What Unreal Knows (The Actual World State)

```cpp
// In Unreal, this is the authoritative world state
class AWorldManager : public AActor {
    TMap<FString, FCharacterState> Characters;
    TMap<FString, FLocationState> Locations;
    TArray<FInteractableObject> Objects;
    
    struct FCharacterState {
        FVector Position;           // Exact 3D coordinates
        FRotator Rotation;          // Where they're facing
        FString CurrentAnimation;   // What animation is playing
        TArray<AActor*> VisibleActors;  // What's in their view frustum
        float Health, Hunger, Stress;   // Internal stats
    };
};
```

### Unreal's Scene Query System

```cpp
// Unreal performs scene queries to determine what each character can see
void UpdateCharacterPerception(ACharacter* Character) {
    // 1. Sphere trace for nearby objects
    TArray<FHitResult> HitResults;
    GetWorld()->SweepMultiByChannel(
        HitResults,
        Character->GetActorLocation(),
        Character->GetActorLocation(),
        FQuat::Identity,
        ECC_Visibility,
        FCollisionShape::MakeSphere(PerceptionRadius)
    );
    
    // 2. Line-of-sight checks
    for (auto& Hit : HitResults) {
        if (IsInFieldOfView(Character, Hit.GetActor())) {
            // This actor is visible to the character
            VisibleActors.Add(Hit.GetActor());
        }
    }
    
    // 3. Ray casting for detailed environment
    FHitResult GroundHit;
    GetWorld()->LineTraceSingleByChannel(
        GroundHit,
        Character->GetActorLocation(),
        Character->GetActorLocation() - FVector(0, 0, 1000),
        ECC_Visibility
    );
    // Determines if standing on carpet, concrete, etc.
}
```

## Layer 2: MCP Bridge - Translation & Enrichment

### Raw Data from Unreal

The MCP bridge receives raw scene data from Unreal:

```javascript
// Raw message from Unreal Engine
{
    "type": "scene_update",
    "character_id": "alex_chen",
    "raw_perception": {
        "position": { "x": 1247.3, "y": 892.1, "z": 0.0 },
        "rotation": { "pitch": 0, "yaw": 127.5, "roll": 0 },
        "visible_actors": [
            { "id": "madison_worthington", "type": "Character", "distance": 8.2 },
            { "id": "library_chair_042", "type": "Furniture", "distance": 2.1 },
            { "id": "security_guard_01", "type": "NPC", "distance": 15.7 },
            { "id": "power_outlet_03", "type": "Interactable", "distance": 0.5, "occupied": false }
        ],
        "location_volume": "library_main_floor",
        "ambient_sound_level": 35,  // decibels
        "lighting_lux": 320,         // lux value
        "temperature": 18            // celsius
    }
}
```

### MCP Bridge Processing

The bridge enriches this raw data with semantic meaning:

```javascript
class SceneProcessor {
    processRawPerception(rawData, characterProfile) {
        // 1. Location Context
        const location = this.getLocationContext(rawData.location_volume);
        
        // 2. Social Context
        const socialDynamics = this.analyzeSocialSituation(
            rawData.visible_actors,
            characterProfile.economic_tier
        );
        
        // 3. Threat Assessment (for poor characters)
        const threats = this.assessThreats(rawData, characterProfile);
        
        // 4. Opportunity Detection
        const opportunities = this.findOpportunities(rawData, characterProfile);
        
        // 5. Emotional Coloring
        const emotionalContext = this.applyEmotionalFilter(
            rawData,
            characterProfile.current_stress
        );
        
        return this.constructPerceptionPackage(
            rawData,
            location,
            socialDynamics,
            threats,
            opportunities,
            emotionalContext
        );
    }
    
    analyzeSocialSituation(visibleActors, economicTier) {
        const analysis = {
            higher_status_present: false,
            lower_status_present: false,
            peer_present: false,
            authority_present: false,
            social_pressure: 0
        };
        
        for (const actor of visibleActors) {
            if (actor.type === 'Character') {
                const otherTier = this.getCharacterTier(actor.id);
                
                if (economicTier === 'poor' && otherTier === 'wealthy') {
                    analysis.higher_status_present = true;
                    analysis.social_pressure += 30;  // Intense pressure
                }
                
                if (actor.id.includes('security')) {
                    analysis.authority_present = true;
                    if (economicTier === 'poor') {
                        analysis.social_pressure += 50;  // Threat of eviction
                    }
                }
            }
        }
        
        return analysis;
    }
    
    assessThreats(rawData, profile) {
        const threats = [];
        
        if (profile.economic_tier === 'poor') {
            // Security guard approaching
            const security = rawData.visible_actors.find(a => a.id.includes('security'));
            if (security && security.distance < 20) {
                threats.push({
                    type: 'eviction',
                    source: security.id,
                    severity: security.distance < 10 ? 'immediate' : 'approaching',
                    time_to_impact: security.distance / 2.0  // seconds
                });
            }
            
            // Time limit in location
            const timeInLocation = Date.now() - profile.entered_location_at;
            if (timeInLocation > 7200000) {  // 2 hours
                threats.push({
                    type: 'time_limit_exceeded',
                    severity: 'high',
                    action_required: 'leave_soon'
                });
            }
            
            // Social rejection
            const wealthy = rawData.visible_actors.filter(a => 
                this.getCharacterTier(a.id) === 'wealthy'
            );
            if (wealthy.length > 0) {
                threats.push({
                    type: 'social_rejection',
                    severity: 'medium',
                    source: wealthy.map(w => w.id)
                });
            }
        }
        
        return threats;
    }
}
```

## Layer 3: Semantic Interpretation

### Converting Physical Space to Meaning

```javascript
class SemanticInterpreter {
    interpretScene(processedPerception, characterMemory) {
        // Transform raw spatial data into meaningful context
        
        return {
            // Physical becomes emotional
            "location_meaning": this.getLocationMeaning(
                processedPerception.location,
                characterMemory.past_experiences_here
            ),
            
            // Distance becomes social dynamics  
            "social_topology": this.mapSocialSpace(
                processedPerception.visible_actors,
                processedPerception.character_tier
            ),
            
            // Objects become resources or obstacles
            "affordances": this.identifyAffordances(
                processedPerception.visible_objects,
                processedPerception.character_needs
            ),
            
            // Time becomes urgency
            "temporal_pressure": this.calculateTemporalPressure(
                processedPerception.threats,
                processedPerception.opportunities
            )
        };
    }
    
    getLocationMeaning(location, memories) {
        // Same library, different meanings
        if (location === 'library') {
            if (memories.includes('kicked_out_by_security')) {
                return {
                    meaning: 'dangerous_refuge',
                    emotional_tone: 'anxious',
                    behavioral_tendency: 'hypervigilant'
                };
            }
            if (memories.includes('wrote_successful_article')) {
                return {
                    meaning: 'productivity_island',
                    emotional_tone: 'determined',
                    behavioral_tendency: 'focused'
                };
            }
        }
    }
    
    mapSocialSpace(actors, tier) {
        // Convert Euclidean distance to social distance
        const socialMap = {
            safe_zones: [],
            danger_zones: [],
            neutral_zones: [],
            escape_routes: []
        };
        
        actors.forEach(actor => {
            const socialDistance = this.calculateSocialDistance(actor, tier);
            
            if (tier === 'poor' && actor.tier === 'wealthy') {
                // Wealthy person creates danger zone around them
                socialMap.danger_zones.push({
                    center: actor.position,
                    radius: 10,  // meters of social discomfort
                    intensity: actor.attention_on_you ? 'high' : 'medium'
                });
            }
            
            if (tier === 'poor' && actor.tier === 'poor') {
                // Other poor person creates safe zone
                socialMap.safe_zones.push({
                    center: actor.position,
                    radius: 5,
                    type: 'potential_ally'
                });
            }
        });
        
        return socialMap;
    }
}
```

## Layer 4: AI Decision Processing (Claude)

### What Claude Receives

```python
# The enriched, interpreted world state
perception_package = {
    "raw_sensory": {
        "location": "library_main_floor",
        "exact_position": [1247.3, 892.1, 0.0],
        "visible_characters": ["madison_worthington", "security_guard_01"],
        "available_objects": ["power_outlet_03", "library_chair_042"]
    },
    
    "interpreted_meaning": {
        "situation": "precarious_productivity",
        "social_dynamic": "unwelcome_presence",
        "immediate_threats": [
            {"type": "security_approaching", "eta": 15},
            {"type": "social_rejection", "source": "madison_worthington"}
        ],
        "opportunities": [
            {"type": "free_power", "availability": "now"},
            {"type": "wifi_access", "quality": "good"}
        ]
    },
    
    "emotional_context": {
        "your_state": {
            "stress": 85,
            "hunger": 70,
            "exhaustion": 80,
            "shame": 60
        },
        "atmosphere": {
            "hostility": 65,
            "safety": 20,
            "productivity_potential": 40
        }
    },
    
    "action_space": {
        "immediate_actions": [
            "continue_working",
            "pack_up_slowly",
            "pack_up_quickly",
            "approach_outlet",
            "avoid_eye_contact",
            "pretend_studying"
        ],
        "social_actions": [
            "make_yourself_smaller",
            "look_busy",
            "move_away_from_madison"
        ],
        "survival_actions": [
            "save_work",
            "grab_water",
            "plan_exit_route"
        ]
    },
    
    "historical_context": {
        "time_at_location": 95,  # minutes
        "previous_evictions": 3,
        "successful_work_sessions": 12,
        "calories_consumed_today": 400
    }
}
```

### Claude's Processing

```python
def process_world_state(perception, character_profile, goals):
    """
    Claude processes the enriched world state to make decisions
    """
    
    # 1. Situation Assessment
    situation = assess_situation(perception)
    # "I'm in danger but need 20 more minutes to submit article"
    
    # 2. Priority Calculation
    priorities = calculate_priorities(
        perception['emotional_context'],
        perception['immediate_threats'],
        character_profile['goals']
    )
    # 1. Avoid eviction (security in 15 seconds)
    # 2. Submit article (need $6)
    # 3. Maintain dignity (Madison watching)
    
    # 3. Action Selection
    action = select_action(
        perception['action_space'],
        priorities,
        character_profile['personality']
    )
    
    # 4. Generate response
    return {
        "decision": "save_and_pack",
        "reasoning": "Security approaching, can't risk losing work",
        "emotional_response": "frustrated_resignation",
        "actions": [
            {"type": "save_work", "urgency": "immediate"},
            {"type": "pack_up_slowly", "reason": "don't look suspicious"},
            {"type": "avoid_eye_contact", "target": "madison_worthington"},
            {"type": "plan_exit_route", "destination": "mcdonalds_wifi"}
        ]
    }
```

## Layer 5: Command Generation & Execution

### Translating Decision to Avatar Commands

```javascript
// MCP Bridge converts AI decision to Unreal commands
class CommandTranslator {
    translateDecision(aiDecision) {
        const commands = [];
        
        for (const action of aiDecision.actions) {
            switch(action.type) {
                case 'save_work':
                    commands.push({
                        type: 'PlayAnimation',
                        animation: 'FranticTyping',
                        duration: 2.0
                    });
                    commands.push({
                        type: 'InteractWith',
                        object: 'Laptop',
                        action: 'SaveFile'
                    });
                    break;
                    
                case 'pack_up_slowly':
                    commands.push({
                        type: 'PlayAnimationSequence',
                        sequence: [
                            'CloseL laptop',
                            'PackBackpack',
                            'StandUpTired'
                        ],
                        timing: 'deliberate'  // Not rushed, avoiding suspicion
                    });
                    break;
                    
                case 'avoid_eye_contact':
                    commands.push({
                        type: 'SetGazeTarget',
                        target: 'Floor',
                        avoidTarget: action.target
                    });
                    commands.push({
                        type: 'SetFacialExpression',
                        expression: 'Shame',
                        intensity: 0.7
                    });
                    break;
            }
        }
        
        return commands;
    }
}
```

### Back to Unreal

```cpp
// Unreal receives and executes commands
void ACharacterController::ProcessMCPCommand(FString JSONCommand) {
    TSharedPtr<FJsonObject> Command;
    FJsonSerializer::Deserialize(Reader, Command);
    
    FString Type = Command->GetStringField("type");
    
    if (Type == "PlayAnimation") {
        FString AnimName = Command->GetStringField("animation");
        float Duration = Command->GetNumberField("duration");
        
        // Play the actual animation on the character mesh
        UAnimInstance* AnimInstance = GetMesh()->GetAnimInstance();
        AnimInstance->Montage_Play(AnimationMap[AnimName], 1.0f);
        
        // Update world state
        CurrentAnimation = AnimName;
        BroadcastStateChange();
    }
    else if (Type == "SetGazeTarget") {
        // Use Unreal's look-at system
        FVector TargetLocation = GetTargetLocation(Command->GetStringField("target"));
        
        // Procedural look-at using IK
        AnimInstance->SetLookAtTarget(TargetLocation);
        
        // Avoid looking at specific actor
        FString AvoidTarget = Command->GetStringField("avoidTarget");
        if (!AvoidTarget.IsEmpty()) {
            AvoidanceTargets.Add(AvoidTarget);
        }
    }
}
```

## The Complete Loop

### Frame-by-Frame Processing

```
Frame 0: Unreal detects Madison enters library
Frame 1: Scene query shows Madison in Alex's view frustum  
Frame 2: MCP receives update, enriches with "wealthy person present"
Frame 3: Claude receives "social threat detected"
Frame 4: Claude decides "make yourself smaller"
Frame 5: MCP translates to "PlayAnimation: HunchShoulders"
Frame 6: Unreal plays animation on Alex's avatar
Frame 7: Madison's scene query shows "poor person hunching"
Frame 8: Madison's AI decides "move away"
Frame 9: Both avatars now physically responding to social dynamics
```

## Performance Considerations

### Optimization Strategies

1. **Perception Culling**: Only process what's relevant
```cpp
// Don't process entire world, just perception radius
if (DistanceTo(Actor) > PerceptionRadius * 1.5) {
    continue;  // Skip distant actors
}
```

2. **Level of Detail (LOD) for Perception**
```javascript
// Distant characters get less detailed perception
if (distance > 30) {
    return { basic: "person", tier: "unknown" };
} else if (distance > 10) {
    return { detailed: "wealthy_person", activity: "walking" };
} else {
    return { full: "madison_worthington", expression: "disgusted", ... };
}
```

3. **Temporal Batching**
```javascript
// Not every character needs updates every frame
updateSchedule = {
    "alex_chen": { frequency: "every_frame", priority: "high" },  // Player character
    "background_npc_01": { frequency: "every_10_frames", priority: "low" }
};
```

## The Reality of Processing

The key insight is that **the same physical data creates different realities**:

1. **Unreal** knows: "Character A is 8.2 meters from Character B"
2. **MCP** interprets: "Poor person near wealthy person = social threat"
3. **Claude** understands: "I need to make myself invisible or risk eviction"
4. **Avatar** performs: Hunched shoulders, avoided eye contact, shame expression

The processing pipeline transforms objective physical reality into subjective lived experience, making inequality visible not just in statistics but in every frame of animation.
# MetaHuman AI Character Integration Plan

## Overview
Using Epic's MetaHuman Creator for photorealistic AI-controlled characters that physically embody economic inequality through facial expressions, body language, and appearance.

## MetaHuman Advantages for Economic Simulation

### Facial Expression System
- **59 facial control points** for nuanced emotions
- Exhaustion visible in eye bags, drooping eyelids
- Stress shown through jaw tension, furrowed brows
- Desperation in micro-expressions
- Hope/defeat in eye movements

### Appearance Customization by Economic Class

#### Poor Characters (Alex Chen, Maria Gonzalez)
```
Appearance:
- Tired eyes with dark circles
- Unkempt hair (hasn't seen barber in months)
- Stubble/ungroomed facial hair
- Worn, ill-fitting clothes
- Slouched posture rig adjustments
- Skin: Stress breakouts, pallor from poor nutrition

Animations:
- Exhausted idle (swaying slightly)
- Slow, dragging walk cycle
- Nervous fidgeting gestures
- Protective body language (arms crossed)
```

#### Middle Class (Ashley Kim)
```
Appearance:
- Neat but tired appearance
- Professional but affordable clothing
- Maintained grooming
- Some stress indicators (slight bags under eyes)
- Alert but weary expression

Animations:
- Purposeful walk
- Checking phone frequently
- Professional gestures
- Occasional stress habits (neck rubbing)
```

#### Wealthy (Victoria Sterling, Madison Worthington)
```
Appearance:
- Perfect grooming (salon hair, manicured)
- Designer clothing with proper fit
- Healthy skin tone
- Confident posture
- Relaxed facial expression

Animations:
- Confident stride
- Smooth, unhurried movements
- Dismissive gestures
- Phone checking (leisure not anxiety)
```

## MetaHuman Control System Architecture

```
┌────────────────────────────────────────────────┐
│         AI Decision Layer (Web/Cloud)          │
│    Character personality + Economic state      │
└────────────────────┬───────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────┐
│           MetaHuman Control Interface          │
│         (Custom MCP-to-MetaHuman Bridge)       │
├─────────────────────────────────────────────────┤
│ • Face Control Rig (ARKit compatible)          │
│ • Body Control Rig (Full IK)                   │
│ • Groom System (hair/beard states)             │
│ • Clothing System (LOD variants)               │
└────────────────────┬───────────────────────────┘
                     │
                     ↓
┌────────────────────────────────────────────────┐
│          Unreal Engine 5.3+ Runtime            │
│            MetaHuman Components                │
├─────────────────────────────────────────────────┤
│ • Face Animation Blueprint                     │
│ • Body Animation Blueprint                     │
│ • Live Link Face Integration                   │
│ • Chaos Cloth Simulation                       │
│ • Lumen/Nanite Rendering                       │
└────────────────────────────────────────────────┘
```

## MetaHuman Emotion Mapping

### AI Emotion to Facial Expression

```cpp
// MetaHumanEmotionController.cpp

void SetEmotionalState(FString Emotion, float Intensity) {
    FMetaHumanFaceParams Params;
    
    if (Emotion == "desperate") {
        Params.BrowInnerUp = 0.7f * Intensity;
        Params.BrowOuterDown = 0.3f * Intensity;
        Params.EyeWideLeft = 0.4f * Intensity;
        Params.EyeWideRight = 0.4f * Intensity;
        Params.MouthFrownLeft = 0.6f * Intensity;
        Params.MouthFrownRight = 0.6f * Intensity;
        Params.JawOpen = 0.1f * Intensity;
        // Add micro-tremor
        Params.AddNoise(0.05f * Intensity);
    }
    else if (Emotion == "exhausted") {
        Params.EyeBlinkLeft = 0.3f;
        Params.EyeBlinkRight = 0.35f; // Asymmetric for realism
        Params.EyeLookDown = 0.4f * Intensity;
        Params.BrowOuterDown = 0.5f * Intensity;
        Params.MouthOpen = 0.1f; // Slight mouth breathing
        Params.HeadTilt = -5.0f * Intensity; // Head droops
    }
    else if (Emotion == "stressed") {
        Params.JawClench = 0.6f * Intensity;
        Params.BrowDown = 0.4f * Intensity;
        Params.EyeSquintLeft = 0.3f * Intensity;
        Params.EyeSquintRight = 0.3f * Intensity;
        Params.NoseSneer = 0.2f * Intensity;
        // Add jaw grinding animation
        Params.JawSideToSide = FMath::Sin(GetTime()) * 0.1f * Intensity;
    }
    else if (Emotion == "hopeful") {
        Params.BrowInnerUp = 0.2f * Intensity;
        Params.MouthSmileLeft = 0.3f * Intensity;
        Params.MouthSmileRight = 0.3f * Intensity;
        Params.EyeWideLeft = 0.2f * Intensity;
        Params.EyeWideRight = 0.2f * Intensity;
    }
    
    ApplyFaceParams(Params);
}
```

## Speech & Lip Sync System

### MetaHuman Speech Integration

```cpp
// Using Unreal's Audio2Face or OVR Lipsync
class UMetaHumanSpeechController : public UActorComponent {
public:
    UFUNCTION(BlueprintCallable)
    void Speak(FString Text, FString Emotion) {
        // Generate audio from text (using cloud TTS)
        USoundWave* Audio = GenerateSpeech(Text, Emotion);
        
        // Generate phoneme data for lip sync
        FPhonemeSequence Phonemes = AnalyzePhonemes(Audio);
        
        // Apply to MetaHuman face rig
        ApplyLipSync(Phonemes);
        
        // Layer emotion on top
        SetEmotionalState(Emotion, 0.7f);
        
        // Play audio
        UAudioComponent->Play(Audio);
    }
    
private:
    void ApplyLipSync(FPhonemeSequence& Phonemes) {
        for (auto& Phoneme : Phonemes) {
            // Map phonemes to MetaHuman visemes
            FMetaHumanFaceParams VisemeParams = GetVisemeParams(Phoneme.Type);
            
            // Blend with current expression
            BlendFaceParams(VisemeParams, Phoneme.Weight);
            
            // Queue for correct timing
            QueueFaceUpdate(VisemeParams, Phoneme.Timestamp);
        }
    }
};
```

## Body Language System

### Economic Status Reflected in Posture

```cpp
class UMetaHumanPostureController : public UActorComponent {
private:
    void UpdatePostureFromEconomicStatus(float Money, FCharacterNeeds Needs) {
        FPostureParams Posture;
        
        if (Money < 100) {
            // Poor posture
            Posture.SpineCurve = -15.0f; // Slouched
            Posture.ShoulderDrop = 10.0f; // Defeated shoulders
            Posture.HeadForward = 5.0f;  // Tired head position
            
            // Add exhaustion effects
            if (Needs.Exhaustion > 80) {
                Posture.SwayAmount = 2.0f; // Swaying from tiredness
                Posture.KneesBend = 5.0f;  // Legs struggling
            }
        }
        else if (Money < 10000) {
            // Middle class posture
            Posture.SpineCurve = 0.0f;   // Neutral
            Posture.ShoulderDrop = 0.0f;  // Alert
            Posture.HeadForward = 0.0f;   // Attentive
        }
        else {
            // Wealthy posture
            Posture.SpineCurve = 5.0f;    // Straight, confident
            Posture.ShoulderDrop = -5.0f;  // Shoulders back
            Posture.ChestOut = 5.0f;       // Confident chest
            Posture.ChinUp = 3.0f;         // Looking above others
        }
        
        ApplyPostureToRig(Posture);
    }
};
```

## Clothing & Appearance Degradation

### Dynamic Clothing System

```cpp
class UMetaHumanClothingManager : public UActorComponent {
public:
    void UpdateClothingCondition(float Money, int DaysSinceWash) {
        if (Money < 100) {
            // Poor clothing state
            ClothingMaterial->SetScalarParameter("DirtLevel", 0.7f);
            ClothingMaterial->SetScalarParameter("WearLevel", 0.8f);
            ClothingMaterial->SetVectorParameter("ColorFade", FLinearColor(0.8f, 0.8f, 0.8f));
            
            // Wrinkled cloth simulation
            ChaosClothConfig.Stiffness = 0.3f; // Loose, worn fabric
            ChaosClothConfig.Damping = 0.8f;   // Heavy from dirt
        }
        else if (Money > 100000) {
            // Wealthy clothing
            ClothingMaterial->SetScalarParameter("DirtLevel", 0.0f);
            ClothingMaterial->SetScalarParameter("WearLevel", 0.0f);
            ClothingMaterial->SetVectorParameter("ColorFade", FLinearColor(1.0f, 1.0f, 1.0f));
            
            // Crisp cloth simulation
            ChaosClothConfig.Stiffness = 0.9f; // Pressed, new fabric
            ChaosClothConfig.Damping = 0.2f;   // Light, clean
        }
    }
};
```

## MetaHuman Character Presets

### Creating Economic Diversity

```javascript
// metahuman-character-presets.js

const CHARACTER_PRESETS = {
    'alex_chen': {
        metahumanBase: 'AsianMale_02',
        age: 28,
        modifications: {
            face: {
                eyeBags: 0.8,
                wrinkles: { stress: 0.6, smile: 0.2 },
                skinTone: { saturation: -0.2 }, // Pallor
                eyeRedness: 0.4
            },
            hair: {
                style: 'medium_unkempt',
                greyPercentage: 0.1, // Stress graying
                greasiness: 0.6
            },
            body: {
                weight: -0.2, // Underweight from poor diet
                muscleTone: -0.3
            }
        }
    },
    
    'victoria_sterling': {
        metahumanBase: 'CaucasianFemale_01',
        age: 42,
        modifications: {
            face: {
                eyeBags: 0.0,
                wrinkles: { smile: 0.3, forehead: 0.1 },
                skinTone: { glow: 0.7 }, // Healthy glow
                makeup: 'professional_full'
            },
            hair: {
                style: 'professional_bob',
                highlights: true,
                glossiness: 0.9
            },
            body: {
                weight: 0.0, // Ideal weight
                muscleTone: 0.4 // Gym membership
            }
        }
    }
};
```

## Performance Optimization

### MetaHuman LOD System

```cpp
// Adjust quality based on camera distance and importance
void UpdateMetaHumanLOD(float DistanceToCamera, bool IsMainCharacter) {
    if (IsMainCharacter || DistanceToCamera < 500) {
        // Highest quality - all face controls active
        SetFaceLOD(0);
        SetBodyLOD(0);
        EnableStrandHair(true);
        EnableWrinkleMaps(true);
    }
    else if (DistanceToCamera < 2000) {
        // Medium quality - reduced face controls
        SetFaceLOD(1);
        SetBodyLOD(1);
        EnableStrandHair(false); // Use cards
        EnableWrinkleMaps(false);
    }
    else {
        // Low quality - basic animation only
        SetFaceLOD(2);
        SetBodyLOD(2);
        UseSimplifiedRig(true);
    }
}
```

## Crowd Diversity System

### Generating Background Characters

```cpp
// Create variety in background MetaHumans
void GenerateCrowdDiversity() {
    TArray<FMetaHumanPreset> Presets = {
        LoadPreset("LowIncome_Variant_01"),
        LoadPreset("LowIncome_Variant_02"),
        LoadPreset("MiddleClass_Variant_01"),
        LoadPreset("Wealthy_Variant_01")
    };
    
    for (int i = 0; i < NumCrowdCharacters; i++) {
        FMetaHumanPreset Base = Presets[FMath::RandRange(0, Presets.Num()-1)];
        
        // Add variation
        Base.SkinTone += FMath::RandRange(-0.2f, 0.2f);
        Base.Height += FMath::RandRange(-10.0f, 10.0f);
        Base.Weight += FMath::RandRange(-0.1f, 0.1f);
        
        SpawnMetaHuman(Base);
    }
}
```

## Integration with Existing System

### MCP Commands for MetaHuman

```javascript
// Enhanced commands for MetaHuman control
const METAHUMAN_COMMANDS = {
    // Facial expressions
    SET_EXPRESSION: 'metahuman.setExpression',
    SET_VISEME: 'metahuman.setViseme',
    BLINK: 'metahuman.blink',
    
    // Eye control
    LOOK_AT: 'metahuman.lookAt',
    EYE_DART: 'metahuman.eyeDart', // Nervous glancing
    
    // Full body
    SET_POSTURE: 'metahuman.setPosture',
    GESTURE: 'metahuman.gesture',
    
    // Appearance
    UPDATE_CLOTHING: 'metahuman.updateClothing',
    SET_GROOM: 'metahuman.setGroom', // Hair/beard state
    
    // Speech with emotion
    SPEAK_WITH_LIPSYNC: 'metahuman.speakWithLipsync'
};
```

## Testing MetaHuman Integration

### Character Showcase Scenarios

1. **Exhaustion Test**
   - Alex after 48 hours awake
   - Micro-sleeps (eyes closing briefly)
   - Head nodding forward
   - Stumbling walk

2. **Stress Test**
   - Maria during eviction
   - Jaw clenching
   - Hand wringing
   - Rapid breathing (chest movement)

3. **Class Contrast**
   - Victoria and Alex in same frame
   - Visible health differences
   - Posture contrast
   - Clothing quality difference

4. **Emotional Range**
   - Joy: Jamie gets a gig
   - Despair: Alex loses last dollar
   - Hope: Maria finds help
   - Contempt: Victoria sees homeless

## MetaHuman Benefits for Your Simulation

1. **Visceral Inequality**: Poverty literally visible on faces
2. **Emotional Authenticity**: Real human expressions
3. **Viewer Empathy**: Photorealistic characters create connection
4. **Social Commentary**: Visual metaphor for economic violence
5. **Streaming Integration**: Characters can "look at camera" when streaming

The MetaHuman system will make your economic simulation incredibly powerful—viewers won't just see statistics, they'll see real human faces struggling, surviving, and embodying the reality of inequality.
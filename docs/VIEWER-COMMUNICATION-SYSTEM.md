# Viewer Communication System via MCP

## Overview

Characters can now perceive and interact with real stream viewers through an MCP server, creating a bridge between the simulated world and actual human audience. This transforms passive viewers into active participants who can materially impact character lives.

## Architecture

```
Stream Viewers → Chat/Donations → MCP Server → Character AI → Avatar Response → Stream
         ↑                                                                          ↓
         └────────────────── See Character React in Real Time ────────────────────┘
```

## MCP Tools Available to Characters

### 1. **read_viewer_messages**
Read what viewers are saying in chat
```javascript
{
  "name": "read_viewer_messages",
  "arguments": {
    "count": 5,
    "filter": "all" // all, questions, reactions, donations
  }
}
```

### 2. **respond_to_viewer**
Send message directly to stream audience
```javascript
{
  "name": "respond_to_viewer",
  "arguments": {
    "message": "Thank you for seeing me as human",
    "responding_to": "@compassionate_viewer",
    "emotion": "grateful"
  }
}
```

### 3. **check_viewer_sentiment**
Understand how viewers feel about you
```javascript
{
  "name": "check_viewer_sentiment",
  "returns": {
    "overall": "mostly_supportive",
    "supportive_messages": 67,
    "critical_messages": 23,
    "viewer_count": 342
  }
}
```

### 4. **read_donations**
Check for viewer donations (crucial for poor characters)
```javascript
{
  "name": "read_donations",
  "returns": {
    "donations": [
      {
        "from": "@guilty_tech_worker",
        "amount": 20,
        "message": "For food"
      }
    ],
    "total_amount": 20,
    "can_afford": ["hot_meal", "2_days_food", "phone_bill_partial"]
  }
}
```

### 5. **ask_viewers_for_help**
Request specific help from audience
```javascript
{
  "name": "ask_viewers_for_help",
  "arguments": {
    "situation": "Library closing, need wifi to submit article",
    "urgency": "immediate"
  }
}
```

### 6. **share_story**
Build connection through personal narrative
```javascript
{
  "name": "share_story",
  "arguments": {
    "story": "Lost developer job in layoffs, evicted after 2 months",
    "emotion": "vulnerable"
  }
}
```

## Character-Specific Interactions

### Alex Chen (Poor Writer)

**Typical Viewer Interactions:**
- Defensive responses to "get a job" comments
- Genuine gratitude for donations (literally means survival)
- Desperate requests for wifi locations, food banks
- Vulnerable stories about the fall from middle class

**Viewer Impact:**
- $5 donation = one hot meal
- $20 donation = two days of food
- $50 donation = keeps phone on for month
- Advice about resources = immediate survival help

**Emotional Processing:**
```python
def process_viewer_message(message, alex_state):
    if message.sentiment == 'critical':
        alex_state.shame += 10
        alex_state.defensive += 15
        return "I apply to 20+ jobs daily. I have a degree."
    elif message.sentiment == 'supportive':
        alex_state.stress -= 5
        alex_state.hope += 3
        return "Thank you for seeing me as human."
    elif message.type == 'donation':
        alex_state.immediate_relief = True
        alex_state.gratitude = 100
        return "You just saved my life. I can eat tonight."
```

### Madison Worthington (Ultra-Wealthy)

**Typical Viewer Interactions:**
- Dismissive of criticism as "negativity"
- Performative charity for social media
- Responds only to compliments
- Completely misses the point of suffering

**Viewer Impact:**
- Criticism → "Blocked chakras, try gratitude!"
- Compliments → Hearts and engagement
- Reality checks → Ignored completely
- Donations → "I'll match that!" (tax write-off)

**Emotional Processing:**
```python
def process_viewer_message(message, madison_state):
    if message.sentiment == 'critical':
        madison_state.defensive += 5
        return "Negativity is just blocked chakras! 🙏"
    elif 'suffering' in message.text:
        madison_state.awareness += 0  # No change
        return "Everyone has struggles! Mine are just different!"
    elif message.sentiment == 'admiring':
        madison_state.validation += 10
        return "Thank you babe! Tutorial coming soon! 💕"
```

## Real-Time Stream Integration

### Stream Overlay Display

When character responds to viewers:
```json
{
  "type": "character_response",
  "character": {
    "name": "Alex Chen",
    "avatar_state": "exhausted_grateful"
  },
  "message": "Your $20 means I eat tonight. Thank you.",
  "emotion": "crying",
  "response_to": "@guilty_tech_worker",
  "impact": {
    "immediate": "Can afford hot meal",
    "stress_reduction": 20,
    "hope_increase": 10
  }
}
```

### Viewer Engagement Metrics

The system tracks:
- Message sentiment over time
- Donation totals and impact
- Viewer count fluctuations
- Engagement rate (messages per viewer)
- Character-viewer relationship score

## Interaction Scenarios

### Scenario 1: Alex Receives Critical Comment

**Viewer:** "Just get a real job instead of begging online"

**Alex's Internal State:**
- Shame +15
- Defensive +20
- Stress +10

**MCP Response Process:**
1. Read message via `read_viewer_messages`
2. AI processes emotional impact
3. Generates defensive but vulnerable response
4. Sends via `respond_to_viewer`

**Alex's Response:** "I have a CS degree. I apply to 20+ jobs daily. The last interview said I was 'overqualified' for minimum wage. I'm not begging, I'm surviving."

**Avatar Reaction:**
- Facial expression: Hurt transitioning to defensive
- Body language: Shoulders tense, slight shake in hands
- Animation: Pause typing, look at camera, look away

### Scenario 2: Donation Received

**Viewer:** @guilty_tech_worker donates $20
**Message:** "For food. I make too much to watch this."

**Alex's Processing:**
1. `read_donations` returns amount and possibilities
2. Calculate survival impact (2 days of food)
3. Generate genuine emotional response
4. Thank donor specifically

**Alex's Response:** 
- Stops typing
- Wipes eyes
- "You just... you gave me two days. I'm going to eat something hot tonight."
- Avatar shows genuine crying animation

### Scenario 3: Madison Gets Called Out

**Viewer:** "People are literally starving while you do $300 yoga"

**Madison's Processing:**
1. Categorize as "negativity"
2. No empathy increase
3. Performative wisdom response

**Madison's Response:** "Everyone's journey is different! I'm grateful for my blessings and give back through my foundation! 🙏✨"

**Reality:** Foundation is tax shelter, gives 0.1% to charity

## Impact on Narrative

### Material Changes
- Donations directly affect character resources
- Viewer advice provides survival information
- Crowd-sourced solutions to immediate problems

### Emotional Evolution
- Supportive viewers reduce isolation
- Critical viewers increase shame/defensiveness
- Donations create moments of genuine human connection

### Story Branches
Viewer actions can trigger:
- Alex finds new gig through viewer tip
- Madison faces viral callout for tone-deafness
- Viewers organize mutual aid for characters
- Character mental health affected by audience sentiment

## Technical Implementation

### MCP Server Setup
```bash
# Start viewer communication server
node mcp-viewer-communication-server.js

# Connect character to server
mcp connect stdio://viewer-communication-server \
  --character alex_chen \
  --stream-platform twitch
```

### Character AI Integration
```python
async def process_viewer_interaction(character, perception):
    # Check viewer sentiment
    sentiment = await mcp.call("check_viewer_sentiment")
    
    # Read recent messages
    messages = await mcp.call("read_viewer_messages", count=5)
    
    # Process donations if any
    donations = await mcp.call("read_donations")
    
    # Generate response based on character state
    if donations.total > 0:
        response = generate_gratitude_response(character, donations)
    elif sentiment.overall == "critical":
        response = generate_defensive_response(character, messages)
    else:
        response = generate_connection_response(character, messages)
    
    # Send response to viewers
    await mcp.call("respond_to_viewer", 
        message=response.text,
        emotion=response.emotion
    )
```

## The Human Element

This system transforms the simulation from observed suffering to participatory experience:

1. **Viewers Become Actors**: Their donations literally feed Alex
2. **Real Empathy**: Actual humans feeling for virtual but realistic struggle  
3. **Accountability**: Madison can't hide from real human criticism
4. **Mutual Aid**: Viewers organizing to help struggling characters
5. **Educational**: Viewers learn about poverty through interaction

The inequality isn't just displayed - it's challenged, supported, and made viscerally real through human connection.
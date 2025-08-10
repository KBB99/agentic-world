/**
 * AI Agent Orchestrator Lambda
 * Processes game state from Unreal Engine and generates AI-driven character commands
 * using Claude via AWS Bedrock
 */

const { BedrockRuntimeClient, InvokeModelCommand } = require("@aws-sdk/client-bedrock-runtime");
const { DynamoDBClient, GetItemCommand, PutItemCommand, QueryCommand, UpdateItemCommand } = require("@aws-sdk/client-dynamodb");
const { ApiGatewayManagementApiClient, PostToConnectionCommand } = require("@aws-sdk/client-apigatewaymanagementapi");
const { marshall, unmarshall } = require("@aws-sdk/util-dynamodb");

const bedrock = new BedrockRuntimeClient({ region: process.env.AWS_REGION });
const dynamodb = new DynamoDBClient({ region: process.env.AWS_REGION });
const apiGw = new ApiGatewayManagementApiClient({ 
  endpoint: process.env.WS_API_ENDPOINT 
});

// Agent command schemas for Unreal
const UNREAL_COMMANDS = {
  MoveTo: {
    params: ['location', 'speed'],
    description: 'Navigate character to location'
  },
  Interact: {
    params: ['object', 'interaction_type'],
    description: 'Interact with world object'
  },
  Speak: {
    params: ['text', 'emotion'],
    description: 'Character dialogue'
  },
  PlayAnimation: {
    params: ['animation_name', 'loop'],
    description: 'Play character animation'
  },
  LookAt: {
    params: ['target', 'duration'],
    description: 'Orient character toward target'
  },
  Wait: {
    params: ['seconds'],
    description: 'Pause before next action'
  },
  PickUp: {
    params: ['item'],
    description: 'Pick up an item'
  },
  Drop: {
    params: ['item'],
    description: 'Drop held item'
  },
  TeleportTo: {
    params: ['location'],
    description: 'Instantly move to location'
  },
  SetEmotion: {
    params: ['emotion', 'intensity'],
    description: 'Set character emotional state'
  }
};

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event));
  
  try {
    const { connectionId, requestContext } = event;
    const body = JSON.parse(event.body || '{}');
    
    switch (body.action) {
      case 'agent_request':
        return await handleAgentRequest(connectionId, body.data);
      
      case 'update_context':
        return await updateAgentContext(body.data);
      
      case 'get_status':
        return await getAgentStatus(body.data);
      
      default:
        return { statusCode: 200, body: JSON.stringify({ status: 'ok' }) };
    }
  } catch (error) {
    console.error('Handler error:', error);
    return { 
      statusCode: 500, 
      body: JSON.stringify({ error: error.message }) 
    };
  }
};

async function handleAgentRequest(connectionId, data) {
  const { 
    agentId, 
    gameState, 
    characterState, 
    requestType = 'decide_action',
    urgency = 'normal' 
  } = data;
  
  console.log(`Processing ${requestType} for agent ${agentId}`);
  
  // Get agent context and recent history
  const [context, history] = await Promise.all([
    getAgentContext(agentId),
    getRecentHistory(agentId, 10)
  ]);
  
  // Build and send prompt to Claude
  const prompt = buildAgentPrompt(
    context, 
    gameState, 
    characterState, 
    history, 
    requestType,
    urgency
  );
  
  const decision = await invokeClaudeForDecision(prompt, urgency);
  
  // Validate and enhance decision
  const validatedDecision = validateDecision(decision, characterState);
  
  // Store in history
  await storeAgentDecision(agentId, validatedDecision, gameState);
  
  // Send to Unreal via WebSocket
  await sendCommandToUnreal(connectionId, {
    ...validatedDecision,
    agentId,
    timestamp: Date.now()
  });
  
  return {
    statusCode: 200,
    body: JSON.stringify(validatedDecision)
  };
}

async function getAgentContext(agentId) {
  try {
    const result = await dynamodb.send(new GetItemCommand({
      TableName: process.env.AGENT_CONTEXT_TABLE,
      Key: marshall({ agentId })
    }));
    
    if (result.Item) {
      const item = unmarshall(result.Item);
      return item.context;
    }
  } catch (error) {
    console.error('Error fetching context:', error);
  }
  
  // Default context for new agents
  return {
    personality: "curious and helpful",
    goals: ["explore the environment", "interact with objects"],
    knowledge: {},
    relationships: {},
    emotional_state: "neutral",
    memory_summary: ""
  };
}

async function getRecentHistory(agentId, limit) {
  try {
    const result = await dynamodb.send(new QueryCommand({
      TableName: process.env.AGENT_STATE_TABLE,
      KeyConditionExpression: 'agentId = :aid',
      ExpressionAttributeValues: marshall({ ':aid': agentId }),
      Limit: limit,
      ScanIndexForward: false // Most recent first
    }));
    
    return result.Items.map(item => {
      const data = unmarshall(item);
      return data.decision;
    });
  } catch (error) {
    console.error('Error fetching history:', error);
    return [];
  }
}

function buildAgentPrompt(context, gameState, characterState, history, requestType, urgency) {
  const commandList = Object.entries(UNREAL_COMMANDS)
    .map(([cmd, info]) => `- ${cmd}(${info.params.join(', ')}): ${info.description}`)
    .join('\n');
  
  const historyText = history.slice(0, 5)
    .map(h => `- ${h.action}: ${h.rationale}`)
    .join('\n');
  
  const prompt = `You are an AI controlling a character in a 3D game world.

CHARACTER PROFILE:
Personality: ${context.personality}
Current emotional state: ${context.emotional_state}
Active goals: ${JSON.stringify(context.goals)}
Relationships: ${JSON.stringify(context.relationships)}

AVAILABLE COMMANDS:
${commandList}

CURRENT SITUATION:
Location: ${gameState.location || 'unknown'}
Nearby objects: ${JSON.stringify(gameState.nearbyObjects || [])}
Visible characters: ${JSON.stringify(gameState.visibleCharacters || [])}
Time of day: ${gameState.timeOfDay || 'day'}
Weather: ${gameState.weather || 'clear'}

CHARACTER STATE:
Position: ${JSON.stringify(characterState.position || {})}
Health: ${characterState.health || 100}
Inventory: ${JSON.stringify(characterState.inventory || [])}
Current animation: ${characterState.currentAnimation || 'idle'}
Is moving: ${characterState.isMoving || false}

RECENT ACTIONS:
${historyText || 'None'}

REQUEST: ${requestType}
URGENCY: ${urgency}

Based on the character's personality and current situation, decide the next action.
${urgency === 'high' ? 'This requires IMMEDIATE action!' : ''}

Respond with a JSON object:
{
  "goal": "current objective (concise)",
  "action": "command name from the list above",
  "parameters": { /* appropriate parameters for the command */ },
  "rationale": "brief reasoning",
  "dialogue": "optional character speech (null if silent)",
  "animation": "optional animation to play",
  "emotion": "current emotion (happy/sad/angry/fearful/surprised/neutral)"
}`;
  
  return prompt;
}

async function invokeClaudeForDecision(prompt, urgency = 'normal') {
  const temperature = urgency === 'high' ? 0.3 : 0.7; // Lower temp for urgent decisions
  
  try {
    const command = new InvokeModelCommand({
      modelId: process.env.BEDROCK_MODEL || 'anthropic.claude-3-sonnet-20240229-v1:0',
      contentType: 'application/json',
      accept: 'application/json',
      body: JSON.stringify({
        anthropic_version: "bedrock-2023-05-31",
        max_tokens: 600,
        temperature,
        messages: [{
          role: "user",
          content: prompt
        }],
        system: "You are an expert game AI that controls NPCs. Always respond with valid JSON."
      })
    });
    
    const response = await bedrock.send(command);
    const responseBody = JSON.parse(new TextDecoder().decode(response.body));
    
    // Extract JSON from response
    const content = responseBody.content[0].text;
    const jsonMatch = content.match(/\{[\s\S]*\}/);
    
    if (jsonMatch) {
      const decision = JSON.parse(jsonMatch[0]);
      console.log('Claude decision:', decision);
      return decision;
    }
  } catch (error) {
    console.error('Bedrock invocation error:', error);
  }
  
  // Fallback decision
  return {
    goal: "Observe surroundings",
    action: "Wait",
    parameters: { seconds: 2 },
    rationale: "Assessing situation",
    dialogue: null,
    animation: "idle",
    emotion: "neutral"
  };
}

function validateDecision(decision, characterState) {
  // Ensure decision has required fields
  const validated = {
    goal: decision.goal || "Continue current task",
    action: decision.action || "Wait",
    parameters: decision.parameters || {},
    rationale: decision.rationale || "Continuing behavior",
    dialogue: decision.dialogue || null,
    animation: decision.animation || null,
    emotion: decision.emotion || "neutral"
  };
  
  // Validate action exists
  if (!UNREAL_COMMANDS[validated.action]) {
    console.warn(`Unknown action: ${validated.action}, defaulting to Wait`);
    validated.action = "Wait";
    validated.parameters = { seconds: 1 };
  }
  
  // Additional validation based on character state
  if (characterState.isMoving && validated.action === "MoveTo") {
    // Avoid interrupting ongoing movement
    validated.action = "Wait";
    validated.parameters = { seconds: 0.5 };
    validated.rationale = "Completing current movement";
  }
  
  return validated;
}

async function storeAgentDecision(agentId, decision, gameState) {
  const timestamp = Date.now();
  const ttl = Math.floor(Date.now() / 1000) + (7 * 24 * 60 * 60); // 7 days
  
  const item = {
    agentId,
    timestamp,
    ttl,
    decision,
    gameState: {
      location: gameState.location,
      timeOfDay: gameState.timeOfDay
    },
    createdAt: new Date(timestamp).toISOString()
  };
  
  await dynamodb.send(new PutItemCommand({
    TableName: process.env.AGENT_STATE_TABLE,
    Item: marshall(item)
  }));
}

async function sendCommandToUnreal(connectionId, command) {
  const message = {
    action: 'agent_command',
    data: command
  };
  
  try {
    await apiGw.send(new PostToConnectionCommand({
      ConnectionId: connectionId,
      Data: JSON.stringify(message)
    }));
    
    console.log(`Sent command to Unreal: ${command.action}`);
  } catch (error) {
    if (error.statusCode === 410) {
      console.log('Connection no longer exists');
    } else {
      console.error('Failed to send command:', error);
    }
  }
}

async function updateAgentContext(data) {
  const { agentId, updates } = data;
  
  const item = {
    agentId,
    context: {
      ...updates,
      lastUpdated: new Date().toISOString()
    }
  };
  
  await dynamodb.send(new PutItemCommand({
    TableName: process.env.AGENT_CONTEXT_TABLE,
    Item: marshall(item)
  }));
  
  return {
    statusCode: 200,
    body: JSON.stringify({ status: 'context updated' })
  };
}

async function getAgentStatus(data) {
  const { agentId } = data;
  
  const [context, lastDecision] = await Promise.all([
    getAgentContext(agentId),
    getRecentHistory(agentId, 1)
  ]);
  
  return {
    statusCode: 200,
    body: JSON.stringify({
      agentId,
      context,
      lastDecision: lastDecision[0] || null,
      timestamp: Date.now()
    })
  };
}
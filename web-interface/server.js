#!/usr/bin/env node
/**
 * Web API Server for Agentic World Simulation
 * Provides HTTP endpoints to control the simulation from a web interface
 */

const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const AWS = require('aws-sdk');

// Configure AWS
AWS.config.update({ region: 'us-east-1' });
const dynamodb = new AWS.DynamoDB.DocumentClient();

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname)));
// Serve generated content
app.use('/content', express.static(path.join(__dirname, 'public', 'content')));

// Store current simulation state
let simulationState = {
    worldState: {},
    characters: {},
    turnNumber: 0,
    lastUpdate: null,
    isRunning: false
};

// DynamoDB table names
const AGENTS_TABLE = 'agentic-demo-agent-contexts';
const WORLD_TABLE = 'agentic-demo-world-state';
const MEMORIES_TABLE = 'agentic-demo-character-memories';
const MESSAGES_TABLE = 'agentic-demo-messages';

// Store active messages for characters
let characterMessages = {};

// Content generation tracking
let generatedContent = {
    blogs: [],
    stories: [],
    code: [],
    social: [],
    art: []
};

/**
 * Load world state from DynamoDB
 */
async function loadWorldState() {
    try {
        const worldResponse = await dynamodb.get({
            TableName: WORLD_TABLE,
            Key: { worldId: 'main' }
        }).promise();
        
        const agentsResponse = await dynamodb.scan({
            TableName: AGENTS_TABLE
        }).promise();
        
        const characters = {};
        for (const item of agentsResponse.Items || []) {
            const agentId = item.agentId;
            
            // Determine money based on background
            let money = 100;
            const background = item.background || '';
            if (background.includes('trust fund') || background.includes('$25M')) {
                money = 25000000;
            } else if (background.includes('$500K')) {
                money = 500000;
            } else if (background.includes('$47K') || background.includes('tech')) {
                money = 47000;
            } else if (background.includes('writer') || background.includes('couch')) {
                money = 53.09;
            } else if (background.includes('barista') || background.includes('film')) {
                money = 43;
            }
            
            characters[agentId] = {
                id: agentId,
                money: money,
                location: item.location || 'public_library',
                needs: item.needs || {
                    hunger: money > 10000 ? 10 : 75,
                    exhaustion: money > 10000 ? 0 : 85,
                    stress: money > 10000 ? 5 : 90
                },
                personality: item.personality,
                background: item.background,
                current_situation: item.current_situation,
                last_action: item.last_action || null
            };
        }
        
        simulationState = {
            worldState: worldResponse.Item || { worldId: 'main', turn_number: 0 },
            characters: characters,
            turnNumber: worldResponse.Item?.turn_number || 0,
            lastUpdate: new Date().toISOString(),
            isRunning: false
        };
        
        return simulationState;
    } catch (error) {
        console.error('Error loading world state:', error);
        throw error;
    }
}

/**
 * Execute simulation turn
 */
async function executeTurn(useAI = false, turns = 1) {
    return new Promise((resolve, reject) => {
        if (simulationState.isRunning) {
            return reject(new Error('Simulation already running'));
        }
        
        simulationState.isRunning = true;
        
        // Use MCP-enabled version if it exists, otherwise fallback
        const mcpScript = path.join(__dirname, '..', 'execute-simulation-turn-with-mcp.py');
        const regularScript = path.join(__dirname, '..', 'execute-simulation-turn.py');
        const scriptPath = fs.existsSync(mcpScript) ? mcpScript : regularScript;
        
        const args = [
            scriptPath,
            '--turns', turns.toString()
        ];
        
        if (useAI) {
            args.push('--use-bedrock');
        }
        
        const pythonProcess = spawn('python3', args);
        
        let output = '';
        let errorOutput = '';
        const turnLog = [];
        
        const interactions = [];
        
        pythonProcess.stdout.on('data', (data) => {
            output += data.toString();
            
            // Parse turn events from output
            const lines = data.toString().split('\n');
            lines.forEach(line => {
                if (line.includes('🎭')) {
                    const match = line.match(/🎭 (.+)/);
                    if (match) {
                        const character = match[1];
                        turnLog.push({
                            character,
                            timestamp: new Date().toLocaleTimeString(),
                            type: 'character_turn'
                        });
                    }
                } else if (line.includes('🤔 Decision:')) {
                    const match = line.match(/🤔 Decision: (.+)/);
                    if (match && turnLog.length > 0) {
                        turnLog[turnLog.length - 1].action = match[1];
                    }
                } else if (line.includes('✅ Result:')) {
                    const match = line.match(/✅ Result: (.+)/);
                    if (match && turnLog.length > 0) {
                        turnLog[turnLog.length - 1].result = match[1];
                    }
                } else if (line.includes('🤝')) {
                    // Parse character interactions
                    const match = line.match(/🤝 (.+) meets (.+) at (.+)/);
                    if (match) {
                        const currentInteraction = {
                            participants: [match[1], match[2]],
                            location: match[3],
                            type: 'unknown',
                            outcome: ''
                        };
                        interactions.push(currentInteraction);
                    }
                } else if (line.includes('Interaction type:')) {
                    const match = line.match(/Interaction type: (.+)/);
                    if (match && interactions.length > 0) {
                        interactions[interactions.length - 1].type = match[1];
                    }
                } else if (line.includes('💰') && line.includes('shares')) {
                    const match = line.match(/💰 (.+) shares \$(.+) with (.+)/);
                    if (match && interactions.length > 0) {
                        interactions[interactions.length - 1].resource_exchange = `${match[1]} shared $${match[2]} with ${match[3]}`;
                    }
                } else if (line.includes('💝') && line.includes('gives')) {
                    const match = line.match(/💝 (.+) gives \$(.+) to (.+)/);
                    if (match && interactions.length > 0) {
                        interactions[interactions.length - 1].resource_exchange = `${match[1]} gave $${match[2]} to ${match[3]}`;
                    }
                } else if (line.includes('💬')) {
                    if (interactions.length > 0) {
                        interactions[interactions.length - 1].outcome = 'Sharing survival tips and support';
                    }
                } else if (line.includes('😣')) {
                    if (interactions.length > 0) {
                        interactions[interactions.length - 1].outcome = 'Tense class-based encounter';
                    }
                }
            });
        });
        
        pythonProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
            console.error('Python error:', data.toString());
        });
        
        pythonProcess.on('close', async (code) => {
            simulationState.isRunning = false;
            
            if (code !== 0) {
                console.error('Python process exited with code:', code);
                console.error('Error output:', errorOutput);
                return reject(new Error(`Simulation failed: ${errorOutput}`));
            }
            
            try {
                // Reload state from DynamoDB
                await loadWorldState();
                
                resolve({
                    success: true,
                    output,
                    turnLog,
                    interactions,
                    ...simulationState
                });
            } catch (error) {
                reject(error);
            }
        });
    });
}

// API Routes

/**
 * GET /world-state
 * Get current world state
 */
app.get('/world-state', async (req, res) => {
    try {
        const state = await loadWorldState();
        res.json(state);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /run-turn
 * Execute one or more simulation turns
 */
app.post('/run-turn', async (req, res) => {
    try {
        const { useAI = false, turns = 1 } = req.body;
        
        console.log(`Running ${turns} turn(s) with AI: ${useAI}`);
        
        const result = await executeTurn(useAI, turns);
        res.json(result);
    } catch (error) {
        console.error('Turn execution error:', error);
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

/**
 * POST /reset-world
 * Reset the simulation to initial state
 */
app.post('/reset-world', async (req, res) => {
    try {
        // Run Python script with reset flag
        const resetProcess = spawn('python3', [
            path.join(__dirname, '..', 'execute-simulation-turn.py'),
            '--reset',
            '--turns', '0'
        ]);
        
        resetProcess.on('close', async (code) => {
            if (code === 0) {
                await loadWorldState();
                res.json({ 
                    success: true, 
                    message: 'World reset complete' 
                });
            } else {
                res.status(500).json({ 
                    success: false, 
                    error: 'Reset failed' 
                });
            }
        });
    } catch (error) {
        res.status(500).json({ 
            success: false, 
            error: error.message 
        });
    }
});

/**
 * GET /characters/:id
 * Get specific character details
 */
app.get('/characters/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const response = await dynamodb.get({
            TableName: AGENTS_TABLE,
            Key: { agentId: id }
        }).promise();
        
        if (response.Item) {
            // Get memories
            const memoriesResponse = await dynamodb.get({
                TableName: MEMORIES_TABLE,
                Key: { characterId: id }
            }).promise();
            
            const character = {
                ...response.Item,
                memories: memoriesResponse.Item?.memories || []
            };
            
            res.json(character);
        } else {
            res.status(404).json({ error: 'Character not found' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /characters-with-memories
 * Get all characters with their memories and full profiles
 */
app.get('/characters-with-memories', async (req, res) => {
    try {
        // Get all agents
        const agentsResponse = await dynamodb.scan({
            TableName: AGENTS_TABLE
        }).promise();
        
        // Get all memories
        const memoriesResponse = await dynamodb.scan({
            TableName: MEMORIES_TABLE
        }).promise();
        
        // Create a map of memories by character ID
        const memoriesMap = {};
        for (const item of memoriesResponse.Items || []) {
            memoriesMap[item.characterId] = item.memories || [];
        }
        
        // Combine agents with their memories
        const charactersWithMemories = {};
        for (const agent of agentsResponse.Items || []) {
            const agentId = agent.agentId;
            
            // Determine money based on background
            let money = 100;
            const background = agent.background || '';
            if (background.includes('trust fund') || background.includes('$25M')) {
                money = 25000000;
            } else if (background.includes('$500K')) {
                money = 500000;
            } else if (background.includes('$47K') || background.includes('tech')) {
                money = 47000;
            } else if (background.includes('writer') || background.includes('couch')) {
                money = 53.09;
            } else if (background.includes('barista') || background.includes('film')) {
                money = 43;
            }
            
            charactersWithMemories[agentId] = {
                id: agentId,
                money: money,
                location: agent.location || 'public_library',
                needs: agent.needs || {
                    hunger: money > 10000 ? 10 : 75,
                    exhaustion: money > 10000 ? 0 : 85,
                    stress: money > 10000 ? 5 : 90
                },
                personality: agent.personality || '',
                background: agent.background || '',
                current_situation: agent.current_situation || '',
                goals: agent.goals || [],
                current_state: agent.current_state || 'normal',
                stress_response: agent.stress_response || '',
                memories: memoriesMap[agentId] || [],
                last_action: agent.last_action || null,
                stream_followers: agent.stream_followers || 0,
                social_media_followers: agent.social_media_followers || 0,
                last_mcp_action: agent.last_mcp_action || null,
                viewer_interactions: agent.viewer_interactions || []
            };
        }
        
        res.json(charactersWithMemories);
    } catch (error) {
        console.error('Error fetching characters with memories:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /locations
 * Get all location states
 */
app.get('/locations', async (req, res) => {
    try {
        const worldResponse = await dynamodb.get({
            TableName: WORLD_TABLE,
            Key: { worldId: 'main' }
        }).promise();
        
        const locations = worldResponse.Item?.locations || {};
        
        // Add character counts to each location
        for (const [locId, locData] of Object.entries(locations)) {
            const charactersHere = Object.values(simulationState.characters)
                .filter(char => char.location === locId)
                .map(char => char.id);
            
            locations[locId] = {
                ...locData,
                occupants: charactersHere,
                occupant_count: charactersHere.length
            };
        }
        
        res.json(locations);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /send-message
 * Send a message to a character and get AI response
 */
app.post('/send-message', async (req, res) => {
    try {
        const { characterId, message, senderName = 'Viewer' } = req.body;
        
        if (!characterId || !message) {
            return res.status(400).json({ error: 'Character ID and message required' });
        }
        
        // Get character details
        const characterResponse = await dynamodb.get({
            TableName: AGENTS_TABLE,
            Key: { agentId: characterId }
        }).promise();
        
        if (!characterResponse.Item) {
            return res.status(404).json({ error: 'Character not found' });
        }
        
        const character = characterResponse.Item;
        
        // Store the incoming message
        const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const timestamp = new Date().toISOString();
        
        const incomingMessage = {
            messageId,
            characterId,
            sender: senderName,
            message,
            timestamp,
            type: 'viewer_to_character'
        };
        
        // Save to DynamoDB
        try {
            await dynamodb.put({
                TableName: MESSAGES_TABLE,
                Item: incomingMessage
            }).promise();
        } catch (e) {
            console.log('Messages table does not exist yet, storing locally');
        }
        
        // Store locally for immediate access
        if (!characterMessages[characterId]) {
            characterMessages[characterId] = [];
        }
        characterMessages[characterId].push(incomingMessage);
        
        // Get AI response using Bedrock
        const response = await getCharacterResponse(character, message, senderName);
        
        // Store the response
        const responseMessage = {
            messageId: `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            characterId,
            sender: characterId,
            message: response.message,
            timestamp: new Date().toISOString(),
            type: 'character_to_viewer',
            emotion: response.emotion
        };
        
        // Save response to DynamoDB
        try {
            await dynamodb.put({
                TableName: MESSAGES_TABLE,
                Item: responseMessage
            }).promise();
        } catch (e) {
            console.log('Messages table does not exist yet');
        }
        
        characterMessages[characterId].push(responseMessage);
        
        res.json({
            success: true,
            response: responseMessage,
            characterState: {
                emotion: response.emotion,
                money: character.money,
                needs: character.needs
            }
        });
        
    } catch (error) {
        console.error('Error sending message:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /messages/:characterId
 * Get message history for a character
 */
app.get('/messages/:characterId', async (req, res) => {
    try {
        const { characterId } = req.params;
        const limit = parseInt(req.query.limit) || 50;
        
        // Try to get from DynamoDB first
        try {
            const response = await dynamodb.query({
                TableName: MESSAGES_TABLE,
                KeyConditionExpression: 'characterId = :id',
                ExpressionAttributeValues: {
                    ':id': characterId
                },
                Limit: limit,
                ScanIndexForward: false // Most recent first
            }).promise();
            
            res.json(response.Items || []);
        } catch (e) {
            // Fallback to local storage
            res.json(characterMessages[characterId] || []);
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * Helper function to get AI response from character
 */
async function getCharacterResponse(character, message, senderName) {
    const AWS = require('aws-sdk');
    const bedrock = new AWS.BedrockRuntime({ region: 'us-east-1' });
    
    try {
        // Build character context
        const prompt = `You are ${character.agentId}, with this personality: ${character.personality}

Your background: ${character.background}
Current situation: ${character.current_situation}
Your emotional state: ${character.current_state}
Your goals: ${character.goals?.join(', ')}

A viewer named "${senderName}" sent you this message: "${message}"

Respond as this character would, staying true to their personality and current situation. Keep your response under 100 words. Also indicate your emotional state.

Respond in JSON format:
{
  "message": "your response",
  "emotion": "your current emotion"
}`;
        
        const response = await bedrock.invokeModel({
            modelId: 'anthropic.claude-3-sonnet-20240229-v1:0',
            body: JSON.stringify({
                anthropic_version: 'bedrock-2023-05-31',
                max_tokens: 200,
                messages: [{
                    role: 'user',
                    content: prompt
                }]
            })
        }).promise();
        
        const responseBody = JSON.parse(response.body.toString());
        const aiResponse = responseBody.content[0].text;
        
        // Parse JSON from response
        const jsonMatch = aiResponse.match(/\{[^}]+\}/s);
        if (jsonMatch) {
            return JSON.parse(jsonMatch[0]);
        }
        
        // Fallback response
        return {
            message: "Thanks for your message. Things are tough but I'm getting by.",
            emotion: character.current_state || 'tired'
        };
        
    } catch (error) {
        console.error('Bedrock error:', error);
        
        // Fallback response based on character situation
        const money = parseFloat(character.money || 0);
        if (money < 100) {
            return {
                message: `Thanks for reaching out, ${senderName}. Every bit of support helps when you're struggling like I am.`,
                emotion: 'grateful but exhausted'
            };
        } else if (money < 10000) {
            return {
                message: `Hey ${senderName}, thanks for the message! Just trying to make it work, you know?`,
                emotion: 'cautiously optimistic'
            };
        } else {
            return {
                message: `Hello ${senderName}, thank you for your interest. Life has been quite comfortable lately.`,
                emotion: 'content'
            };
        }
    }
}

/**
 * GET /content-hub
 * Get all generated content metadata from LOCAL and S3
 */
app.get('/content-hub', async (req, res) => {
    try {
        const fsSync = require('fs');
        const fsPromises = require('fs').promises;
        const contentDir = path.join(__dirname, 'public', 'content', 'metadata');
        
        const content = {
            blogs: [],
            stories: [],
            code: [],
            social: [],
            s3Content: {}
        };
        
        // Read LOCAL metadata files if they exist
        try {
            const blogsPath = path.join(contentDir, 'blogs.json');
            if (fsSync.existsSync(blogsPath)) {
                content.blogs = JSON.parse(await fsPromises.readFile(blogsPath, 'utf-8'));
            }
        } catch (e) {}
        
        try {
            const storiesPath = path.join(contentDir, 'stories.json');
            if (fsSync.existsSync(storiesPath)) {
                content.stories = JSON.parse(await fsPromises.readFile(storiesPath, 'utf-8'));
            }
        } catch (e) {}
        
        try {
            const codePath = path.join(contentDir, 'code.json');
            if (fsSync.existsSync(codePath)) {
                content.code = JSON.parse(await fsPromises.readFile(codePath, 'utf-8'));
            }
        } catch (e) {}
        
        try {
            const socialPath = path.join(contentDir, 'social.json');
            if (fsSync.existsSync(socialPath)) {
                content.social = JSON.parse(await fsPromises.readFile(socialPath, 'utf-8'));
            }
        } catch (e) {}
        
        // Also fetch S3 content if configured
        try {
            const s3Content = await fetchS3Content();
            content.s3Content = s3Content;
        } catch (e) {
            console.log('Could not fetch S3 content:', e.message);
        }
        
        res.json(content);
    } catch (error) {
        console.error('Error fetching content hub:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * Fetch content from S3
 */
async function fetchS3Content() {
    const AWS = require('aws-sdk');
    const s3 = new AWS.S3({ region: 'us-east-1' });
    
    // Read stack outputs to get bucket name and CloudFront domain
    const stackOutputs = require('../aws/out/stack-outputs.json');
    const bucketName = stackOutputs.viewerBucketName;
    const cloudfrontDomain = stackOutputs.cloudfrontDomainName;
    
    const s3Content = {
        characters: {},
        cloudfrontDomain: cloudfrontDomain
    };
    
    // List all character content indices
    const characters = ['alex_chen', 'jamie_rodriguez', 'ashley_kim', 'victoria_sterling'];
    
    for (const characterId of characters) {
        try {
            // Fetch character's index.json from S3
            const indexKey = `content/${characterId}/index.json`;
            const data = await s3.getObject({
                Bucket: bucketName,
                Key: indexKey
            }).promise();
            
            const index = JSON.parse(data.Body.toString());
            s3Content.characters[characterId] = index;
            
            // Add CloudFront URLs
            if (index.content) {
                for (const contentType in index.content) {
                    index.content[contentType] = index.content[contentType].map(item => ({
                        ...item,
                        cloudfrontUrl: item.url || `https://${cloudfrontDomain}/${item.s3_key}`
                    }));
                }
            }
        } catch (e) {
            // Character hasn't published anything yet
            s3Content.characters[characterId] = {
                character_id: characterId,
                content: {}
            };
        }
    }
    
    return s3Content;
}

/**
 * GET /s3-content/:character
 * Get S3 content for a specific character
 */
app.get('/s3-content/:character', async (req, res) => {
    try {
        const AWS = require('aws-sdk');
        const s3 = new AWS.S3({ region: 'us-east-1' });
        
        const stackOutputs = require('../aws/out/stack-outputs.json');
        const bucketName = stackOutputs.viewerBucketName;
        const cloudfrontDomain = stackOutputs.cloudfrontDomainName;
        
        const characterId = req.params.character;
        const indexKey = `content/${characterId}/index.json`;
        
        try {
            const data = await s3.getObject({
                Bucket: bucketName,
                Key: indexKey
            }).promise();
            
            const index = JSON.parse(data.Body.toString());
            
            // Add CloudFront URLs
            if (index.content) {
                for (const contentType in index.content) {
                    index.content[contentType] = index.content[contentType].map(item => ({
                        ...item,
                        cloudfrontUrl: `https://${cloudfrontDomain}/${item.s3_key}`
                    }));
                }
            }
            
            res.json(index);
        } catch (e) {
            res.json({
                character_id: characterId,
                content: {},
                message: 'No content published yet'
            });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /generate-content
 * Trigger content generation for a character
 */
app.post('/generate-content', async (req, res) => {
    try {
        const { characterId, contentType, params } = req.body;
        
        // Get character details
        const characterResponse = await dynamodb.get({
            TableName: AGENTS_TABLE,
            Key: { agentId: characterId }
        }).promise();
        
        if (!characterResponse.Item) {
            return res.status(404).json({ error: 'Character not found' });
        }
        
        const character = characterResponse.Item;
        
        // Run content generation Python script
        const contentProcess = spawn('python3', [
            path.join(__dirname, '..', 'content-generation-system.py'),
            '--character', characterId,
            '--type', contentType,
            '--topic', params.topic || 'general'
        ]);
        
        let output = '';
        let errorOutput = '';
        
        contentProcess.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        contentProcess.stderr.on('data', (data) => {
            errorOutput += data.toString();
        });
        
        contentProcess.on('close', (code) => {
            if (code !== 0) {
                return res.status(500).json({ 
                    error: 'Content generation failed',
                    details: errorOutput 
                });
            }
            
            // Parse output for created content URL
            const urlMatch = output.match(/Created: (.+)/);
            if (urlMatch) {
                res.json({
                    success: true,
                    url: urlMatch[1],
                    characterId,
                    contentType
                });
            } else {
                res.json({
                    success: true,
                    message: 'Content generated',
                    output
                });
            }
        });
        
    } catch (error) {
        console.error('Error generating content:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /stats
 * Get simulation statistics
 */
app.get('/stats', async (req, res) => {
    try {
        await loadWorldState();
        
        const characters = Object.values(simulationState.characters);
        const poorest = characters.reduce((min, char) => 
            char.money < min.money ? char : min
        );
        const richest = characters.reduce((max, char) => 
            char.money > max.money ? char : max
        );
        
        const stats = {
            total_characters: characters.length,
            turn_number: simulationState.turnNumber,
            wealth_gap: richest.money - poorest.money,
            wealth_ratio: richest.money / Math.max(poorest.money, 0.01),
            richest: {
                id: richest.id,
                money: richest.money
            },
            poorest: {
                id: poorest.id,
                money: poorest.money
            },
            average_needs: {
                hunger: characters.reduce((sum, c) => sum + (c.needs?.hunger || 0), 0) / characters.length,
                exhaustion: characters.reduce((sum, c) => sum + (c.needs?.exhaustion || 0), 0) / characters.length,
                stress: characters.reduce((sum, c) => sum + (c.needs?.stress || 0), 0) / characters.length
            }
        };
        
        res.json(stats);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * WebSocket support for real-time updates (future enhancement)
 */
const server = app.listen(PORT, () => {
    console.log(`🌍 Agentic World API Server running on port ${PORT}`);
    console.log(`📊 Web interface available at http://localhost:${PORT}`);
    console.log('\nEndpoints:');
    console.log('  GET  /world-state    - Get current world state');
    console.log('  POST /run-turn       - Execute simulation turn');
    console.log('  POST /reset-world    - Reset simulation');
    console.log('  GET  /characters/:id - Get character details');
    console.log('  GET  /characters-with-memories - Get all characters with memories');
    console.log('  GET  /locations      - Get all locations');
    console.log('  GET  /stats          - Get simulation statistics');
    console.log('  POST /send-message   - Send message to character');
    console.log('  GET  /messages/:id   - Get character message history');
    console.log('\nPress Ctrl+C to stop the server');
    
    // Load initial state
    loadWorldState().then(() => {
        console.log('\n✅ Initial world state loaded');
        console.log(`   ${Object.keys(simulationState.characters).length} characters`);
        console.log(`   Turn ${simulationState.turnNumber}`);
    }).catch(err => {
        console.error('❌ Failed to load initial state:', err.message);
    });
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});
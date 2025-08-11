#!/usr/bin/env node
/**
 * MCP to Unreal Engine Avatar Control Bridge
 * Receives character decisions from AI agents and sends avatar commands to Unreal
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
const WebSocket = require('ws');
const net = require('net');

class UnrealAvatarBridge {
  constructor(config) {
    this.config = {
      unrealHost: config.unrealHost || '127.0.0.1',
      unrealPort: config.unrealPort || 32123,
      websocketUrl: config.websocketUrl,
      characterId: config.characterId,
      economicTier: config.economicTier || 'poor'
    };
    
    this.unrealSocket = null;
    this.websocket = null;
    this.mcpClient = null;
    this.commandQueue = [];
    this.characterState = {
      location: 'unknown',
      animation: 'idle',
      heldObjects: [],
      needs: {
        hunger: 50,
        thirst: 50,
        exhaustion: 30,
        stress: 70
      }
    };
  }

  async connect() {
    console.log('🌉 Starting MCP to Unreal Avatar Bridge...\n');
    
    // Connect to Unreal Engine
    await this.connectToUnreal();
    
    // Connect to WebSocket for AI decisions
    if (this.config.websocketUrl) {
      await this.connectToWebSocket();
    }
    
    // Connect to MCP servers for character tools
    await this.connectToMCP();
    
    console.log('✅ All connections established\n');
  }

  async connectToUnreal() {
    return new Promise((resolve, reject) => {
      console.log(`📡 Connecting to Unreal Engine at ${this.config.unrealHost}:${this.config.unrealPort}...`);
      
      this.unrealSocket = new net.Socket();
      
      this.unrealSocket.connect(this.config.unrealPort, this.config.unrealHost, () => {
        console.log('   ✓ Connected to Unreal Engine');
        
        // Send initial character registration
        this.sendToUnreal({
          type: 'register_character',
          character_id: this.config.characterId,
          economic_tier: this.config.economicTier,
          initial_state: this.characterState
        });
        
        resolve();
      });
      
      this.unrealSocket.on('data', (data) => {
        this.handleUnrealResponse(data);
      });
      
      this.unrealSocket.on('error', (err) => {
        console.error('❌ Unreal connection error:', err.message);
        reject(err);
      });
    });
  }

  async connectToWebSocket() {
    console.log(`🌐 Connecting to WebSocket at ${this.config.websocketUrl}...`);
    
    this.websocket = new WebSocket(this.config.websocketUrl);
    
    this.websocket.on('open', () => {
      console.log('   ✓ Connected to AI decision WebSocket');
    });
    
    this.websocket.on('message', (data) => {
      this.handleAIDecision(JSON.parse(data));
    });
  }

  async connectToMCP() {
    console.log('🔧 Connecting to MCP filesystem server...');
    
    // Only filesystem for poor characters
    if (this.config.economicTier === 'poor') {
      const transport = new StdioClientTransport({
        command: 'npx',
        args: ['-y', '@modelcontextprotocol/server-filesystem', process.cwd()]
      });
      
      this.mcpClient = new Client({
        name: `${this.config.characterId}-avatar-client`,
        version: '1.0.0'
      });
      
      await this.mcpClient.connect(transport);
      console.log('   ✓ Connected to MCP filesystem (only free tool available)');
    }
  }

  handleAIDecision(decision) {
    console.log(`\n🤖 AI Decision for ${this.config.characterId}:`);
    console.log(`   Goal: ${decision.goal}`);
    console.log(`   Action: ${decision.action}`);
    
    // Translate AI decision to avatar command
    const avatarCommand = this.translateToAvatarCommand(decision);
    
    if (avatarCommand) {
      this.sendToUnreal(avatarCommand);
    }
  }

  translateToAvatarCommand(decision) {
    // Map AI decisions to avatar actions
    const commandMap = {
      'go_to_library': {
        action: 'walk_to',
        params: { location: 'public_library', speed: 'tired' }
      },
      'write_article': {
        action: 'use',
        params: { object: 'laptop', action: 'type' }
      },
      'look_for_food': {
        action: 'walk_to',
        params: { location: 'food_bank', speed: 'hungry' }
      },
      'express_stress': {
        action: 'play_animation',
        params: { animation_name: 'stressed_idle', loop: true }
      },
      'check_phone': {
        action: 'use',
        params: { object: 'phone', action: 'check_gigs' }
      },
      'sleep_rough': {
        action: 'sleep',
        params: { location: 'park_bench', duration: 4 }
      }
    };
    
    const mapping = commandMap[decision.action];
    if (!mapping) return null;
    
    return {
      type: 'avatar_command',
      character_id: this.config.characterId,
      action: mapping.action,
      parameters: mapping.params,
      reason: decision.rationale,
      timestamp: new Date().toISOString()
    };
  }

  sendToUnreal(command) {
    const message = JSON.stringify(command) + '\n';
    
    console.log(`\n➡️  Sending to Unreal:`);
    console.log(`   Action: ${command.action || command.type}`);
    if (command.parameters) {
      console.log(`   Params:`, command.parameters);
    }
    
    if (this.unrealSocket && this.unrealSocket.writable) {
      this.unrealSocket.write(message);
    } else {
      console.log('   ⚠️  Queuing command (Unreal not connected)');
      this.commandQueue.push(command);
    }
  }

  handleUnrealResponse(data) {
    try {
      const response = JSON.parse(data.toString());
      
      if (response.type === 'state_update') {
        // Update character state based on Unreal feedback
        this.characterState = {
          ...this.characterState,
          ...response.state
        };
        
        console.log(`\n📊 State Update from Unreal:`);
        console.log(`   Location: ${this.characterState.location}`);
        console.log(`   Animation: ${this.characterState.animation}`);
        console.log(`   Needs:`, this.characterState.needs);
        
        // Send state to AI for next decision
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
          this.websocket.send(JSON.stringify({
            type: 'state_update',
            character_id: this.config.characterId,
            state: this.characterState
          }));
        }
      }
    } catch (err) {
      // Handle non-JSON responses
      console.log(`\n📨 Unreal says: ${data.toString().trim()}`);
    }
  }

  // Character-specific behaviors
  async performCharacterAction(action) {
    console.log(`\n🎮 Performing: ${action.description}`);
    
    switch(this.config.characterId) {
      case 'alex_chen':
        await this.alexBehavior(action);
        break;
      case 'tyler_chen':
        await this.tylerBehavior(action);
        break;
      case 'madison_worthington':
        await this.madisonBehavior(action);
        break;
      default:
        await this.defaultBehavior(action);
    }
  }

  async alexBehavior(action) {
    // Alex's desperate survival actions
    const commands = [
      { action: 'set_facial_expression', params: { emotion: 'exhausted', intensity: 0.9 }},
      { action: 'walk_to', params: { location: 'library', speed: 'slow' }},
      { action: 'sit_on', params: { object: 'floor' }}, // Can't always get a chair
      { action: 'use', params: { object: 'old_laptop', action: 'write' }},
      { action: 'play_animation', params: { animation_name: 'rub_eyes', loop: false }}
    ];
    
    // Send commands with delays to simulate realistic pacing
    for (const cmd of commands) {
      this.sendToUnreal({
        type: 'avatar_command',
        character_id: 'alex_chen',
        ...cmd,
        timestamp: new Date().toISOString()
      });
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }

  async tylerBehavior(action) {
    // Tyler's confident tech bro actions
    const commands = [
      { action: 'walk_to', params: { location: 'standing_desk', speed: 'confident' }},
      { action: 'gesture', params: { type: 'point_at_screen' }},
      { action: 'use', params: { object: 'macbook_pro', action: 'code' }},
      { action: 'drink', params: { drink_item: 'kombucha' }}
    ];
    
    for (const cmd of commands) {
      this.sendToUnreal({
        type: 'avatar_command',
        character_id: 'tyler_chen',
        ...cmd,
        timestamp: new Date().toISOString()
      });
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }

  async madisonBehavior(action) {
    // Madison's oblivious wealthy actions
    const commands = [
      { action: 'walk_to', params: { location: 'yoga_studio', speed: 'graceful' }},
      { action: 'play_animation', params: { animation_name: 'yoga_pose', loop: true }},
      { action: 'use', params: { object: 'iphone_15_pro', action: 'instagram' }},
      { action: 'gesture', params: { type: 'air_kiss' }}
    ];
    
    for (const cmd of commands) {
      this.sendToUnreal({
        type: 'avatar_command', 
        character_id: 'madison_worthington',
        ...cmd,
        timestamp: new Date().toISOString()
      });
      await new Promise(resolve => setTimeout(resolve, 2500));
    }
  }

  async defaultBehavior(action) {
    // Generic avatar behavior
    this.sendToUnreal({
      type: 'avatar_command',
      character_id: this.config.characterId,
      action: 'idle',
      parameters: {},
      timestamp: new Date().toISOString()
    });
  }
}

// Main execution
async function main() {
  const args = process.argv.slice(2);
  
  // Parse command line arguments
  const config = {
    unrealHost: '127.0.0.1',
    unrealPort: 32123,
    websocketUrl: null,
    characterId: 'alex_chen',
    economicTier: 'poor'
  };
  
  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--unreal-host') config.unrealHost = args[++i];
    if (args[i] === '--unreal-port') config.unrealPort = parseInt(args[++i]);
    if (args[i] === '--wss') config.websocketUrl = args[++i];
    if (args[i] === '--character') config.characterId = args[++i];
    if (args[i] === '--tier') config.economicTier = args[++i];
  }
  
  console.log('🎮 MCP TO UNREAL AVATAR BRIDGE');
  console.log('================================\n');
  console.log('Configuration:');
  console.log(`  Character: ${config.characterId} (${config.economicTier} tier)`);
  console.log(`  Unreal: ${config.unrealHost}:${config.unrealPort}`);
  console.log(`  WebSocket: ${config.websocketUrl || 'Not configured'}`);
  console.log();
  
  const bridge = new UnrealAvatarBridge(config);
  
  try {
    await bridge.connect();
    
    // Example: Send initial avatar setup
    setTimeout(() => {
      console.log('\n🎬 Sending initial avatar commands...\n');
      bridge.performCharacterAction({
        description: 'Initial character setup'
      });
    }, 2000);
    
    // Keep process alive
    process.on('SIGINT', () => {
      console.log('\n\n👋 Shutting down bridge...');
      if (bridge.unrealSocket) bridge.unrealSocket.end();
      if (bridge.websocket) bridge.websocket.close();
      if (bridge.mcpClient) bridge.mcpClient.close();
      process.exit(0);
    });
    
  } catch (err) {
    console.error('❌ Failed to start bridge:', err);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { UnrealAvatarBridge };
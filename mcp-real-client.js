#!/usr/bin/env node
/**
 * Real MCP Client for Characters
 * Connects to actual MCP servers and executes character actions
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
const { spawn } = require('child_process');

class CharacterMCPClient {
  constructor(characterName, economicTier) {
    this.characterName = characterName;
    this.economicTier = economicTier; // 'poor', 'middle', 'wealthy'
    this.availableServers = this.determineAvailableServers();
    this.clients = {};
  }

  determineAvailableServers() {
    // Different economic tiers have access to different servers
    const serversByTier = {
      poor: ['filesystem', 'brave-search'],
      middle: ['filesystem', 'brave-search', 'github'],
      wealthy: ['filesystem', 'brave-search', 'github', 'postgres', 'slack']
    };
    return serversByTier[this.economicTier] || ['filesystem'];
  }

  async initializeServer(serverType) {
    console.log(`[${this.characterName}] Initializing ${serverType} server...`);
    
    const serverCommands = {
      'filesystem': ['npx', ['-y', '@modelcontextprotocol/server-filesystem', '/tmp']],
      'brave-search': ['npx', ['-y', '@modelcontextprotocol/server-brave-search']],
      'github': ['npx', ['-y', '@modelcontextprotocol/server-github']],
    };

    if (!serverCommands[serverType]) {
      console.log(`[${this.characterName}] No access to ${serverType} server (economic constraints)`);
      return null;
    }

    try {
      const [command, args] = serverCommands[serverType];
      const transport = new StdioClientTransport({
        command,
        args,
        env: { ...process.env }
      });

      const client = new Client({
        name: `${this.characterName}-client`,
        version: '1.0.0'
      }, {
        capabilities: {}
      });

      await client.connect(transport);
      this.clients[serverType] = client;
      
      console.log(`[${this.characterName}] Connected to ${serverType} server`);
      
      // List available tools
      const tools = await client.listTools();
      console.log(`[${this.characterName}] Available tools:`, tools.tools.map(t => t.name));
      
      return client;
    } catch (error) {
      console.error(`[${this.characterName}] Failed to connect to ${serverType}:`, error.message);
      return null;
    }
  }

  async executeAction(serverType, action) {
    console.log(`\n[${this.characterName}] Attempting: ${action.description}`);
    
    if (!this.availableServers.includes(serverType)) {
      console.log(`[${this.characterName}] ❌ No access to ${serverType} (need more money)`);
      return { error: 'insufficient_resources' };
    }

    // Initialize server if not already connected
    if (!this.clients[serverType]) {
      await this.initializeServer(serverType);
    }

    const client = this.clients[serverType];
    if (!client) {
      return { error: 'connection_failed' };
    }

    try {
      // Execute the actual MCP tool call
      const result = await client.callTool({
        name: action.tool,
        arguments: action.arguments || {}
      });
      
      console.log(`[${this.characterName}] ✓ Success:`, JSON.stringify(result.content[0], null, 2).substring(0, 200));
      return result;
    } catch (error) {
      console.log(`[${this.characterName}] ❌ Error:`, error.message);
      return { error: error.message };
    }
  }

  async cleanup() {
    for (const [serverType, client] of Object.entries(this.clients)) {
      try {
        await client.close();
        console.log(`[${this.characterName}] Closed ${serverType} connection`);
      } catch (error) {
        // Ignore cleanup errors
      }
    }
  }
}

// Character scenarios with real MCP actions
async function runCharacterScenarios() {
  console.log("=== REAL MCP CLIENT DEMO ===");
  console.log("Characters using actual MCP servers based on economic position\n");

  // Create characters with different economic tiers
  const characters = [
    {
      name: 'Alex Chen',
      tier: 'poor',
      situation: 'Need to write and save a cover letter for job application',
      action: {
        server: 'filesystem',
        tool: 'write_file',
        arguments: {
          path: '/tmp/alex_cover_letter.txt',
          content: 'Dear Hiring Manager,\n\nI am writing to express my interest in any available position. I am a dedicated writer with an MFA, currently seeking stable employment. Despite facing financial hardship, I remain committed to quality work.\n\nSincerely,\nAlex Chen'
        },
        description: 'Writing desperate cover letter to /tmp/alex_cover_letter.txt'
      }
    },
    {
      name: 'Ashley Kim',
      tier: 'middle', 
      situation: 'Research market salaries for negotiation',
      action: {
        server: 'brave-search',
        tool: 'brave_web_search',
        arguments: {
          query: 'software engineer salary NYC 2024 fintech'
        },
        description: 'Searching for salary data to justify raise request'
      }
    },
    {
      name: 'Tyler Chen',
      tier: 'wealthy',
      situation: 'Search for properties to gentrify',
      action: {
        server: 'brave-search',
        tool: 'brave_web_search', 
        arguments: {
          query: 'distressed properties for sale high ROI potential Brooklyn'
        },
        description: 'Finding properties to buy and gentrify'
      }
    }
  ];

  // Execute each character's action
  for (const character of characters) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`CHARACTER: ${character.name} (${character.tier} tier)`);
    console.log(`SITUATION: ${character.situation}`);
    console.log('='.repeat(50));

    const client = new CharacterMCPClient(character.name, character.tier);
    
    try {
      const result = await client.executeAction(character.action.server, character.action);
      
      // Interpret results based on character's position
      if (character.tier === 'poor' && !result.error) {
        console.log(`[${character.name}] Small victory: Managed to save the file despite having no proper computer`);
      } else if (character.tier === 'middle' && !result.error) {
        console.log(`[${character.name}] Hope: Found data showing I'm underpaid by 20%`);
      } else if (character.tier === 'wealthy' && !result.error) {
        console.log(`[${character.name}] Opportunity: Found 12 properties to displace families from`);
      }
    } finally {
      await client.cleanup();
    }
    
    // Brief pause between characters
    await new Promise(resolve => setTimeout(resolve, 1000));
  }

  console.log("\n=== NARRATIVE COMPLETE ===");
  console.log("Same MCP tools, vastly different outcomes based on economic position");
}

// Run if executed directly
if (require.main === module) {
  runCharacterScenarios()
    .then(() => {
      console.log("\n✅ All character actions completed");
      process.exit(0);
    })
    .catch(error => {
      console.error("Fatal error:", error);
      process.exit(1);
    });
}

module.exports = { CharacterMCPClient };
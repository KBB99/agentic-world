#!/usr/bin/env node
/**
 * REAL MCP Server Connection
 * Actually connects to and executes on MCP servers
 */

const { Client } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');

async function executeRealMCPAction(characterName, decision) {
  console.log(`\n=== ${characterName.toUpperCase()} CONNECTING TO REAL MCP ===`);
  
  // Determine which server to connect to
  const serverConfig = {
    'filesystem': {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', process.cwd()]
    },
    'brave-search': {
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-brave-search'],
      env: { BRAVE_API_KEY: process.env.BRAVE_API_KEY || 'demo-key' }
    }
  };

  const config = serverConfig[decision.mcp_server];
  if (!config) {
    console.log(`❌ No configuration for server: ${decision.mcp_server}`);
    return null;
  }

  console.log(`\n1. SPAWNING MCP SERVER: ${decision.mcp_server}`);
  console.log(`   Command: ${config.command} ${config.args.join(' ')}`);

  try {
    // Create transport to spawn the server
    const transport = new StdioClientTransport({
      command: config.command,
      args: config.args,
      env: { ...process.env, ...config.env }
    });

    // Create client
    const client = new Client({
      name: `${characterName}-client`,
      version: '1.0.0'
    }, {
      capabilities: {}
    });

    console.log(`\n2. CONNECTING TO SERVER...`);
    await client.connect(transport);
    console.log(`   ✓ Connected successfully`);

    // List available tools
    console.log(`\n3. LISTING AVAILABLE TOOLS:`);
    const tools = await client.listTools();
    console.log(`   Found ${tools.tools.length} tools:`);
    tools.tools.forEach(tool => {
      console.log(`   - ${tool.name}: ${tool.description || 'No description'}`);
    });

    // Execute the actual tool
    console.log(`\n4. EXECUTING TOOL: ${decision.mcp_tool}`);
    console.log(`   Arguments:`, JSON.stringify(decision.mcp_arguments, null, 2));
    
    const result = await client.callTool({
      name: decision.mcp_tool,
      arguments: decision.mcp_arguments || {}
    });

    console.log(`\n5. RESULT FROM MCP SERVER:`);
    if (result.content && result.content[0]) {
      const content = result.content[0];
      if (content.type === 'text') {
        console.log(`   ${content.text.substring(0, 500)}`);
      } else {
        console.log(`   Result type: ${content.type}`);
      }
    }

    // Clean up
    await client.close();
    console.log(`\n6. CONNECTION CLOSED`);
    
    return result;

  } catch (error) {
    console.log(`\n❌ ERROR: ${error.message}`);
    return null;
  }
}

// Export for use by Python
if (require.main === module) {
  // Get decision from command line arguments
  const args = process.argv.slice(2);
  if (args.length < 1) {
    console.log('Usage: node real-mcp-connection.js <decision-json>');
    process.exit(1);
  }

  const decision = JSON.parse(args[0]);
  const characterName = decision.character || 'unknown';
  
  executeRealMCPAction(characterName, decision)
    .then(result => {
      console.log('\n✅ MCP ACTION COMPLETE');
      if (result) {
        // Output result as JSON for Python to parse
        console.log('JSON_RESULT:', JSON.stringify(result));
      }
      process.exit(0);
    })
    .catch(error => {
      console.error('Fatal error:', error);
      process.exit(1);
    });
}

module.exports = { executeRealMCPAction };
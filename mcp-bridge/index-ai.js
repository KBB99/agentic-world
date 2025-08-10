/**
 * Enhanced MCP Bridge with AI Agent Support
 * Bidirectional bridge between Unreal MCP Server and AWS AI Agent Orchestrator
 * 
 * Features:
 * - Forwards Unreal game state to cloud AI agents
 * - Receives AI-generated commands and forwards to Unreal
 * - Maintains telemetry overlay updates
 * - Handles connection resilience and message queuing
 * 
 * Usage:
 *   node index-ai.js --wss wss://api-gateway.amazonaws.com/prod \
 *                     --agent-id npc_001 \
 *                     [--mcp-host 127.0.0.1] [--mcp-port 32123]
 */

'use strict';

const net = require('net');
const WebSocket = require('ws');

// ---------- Configuration ----------
function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--wss' && i + 1 < argv.length) { out.wss = argv[++i]; continue; }
    if (a === '--agent-id' && i + 1 < argv.length) { out.agentId = argv[++i]; continue; }
    if (a === '--mcp-host' && i + 1 < argv.length) { out.mcpHost = argv[++i]; continue; }
    if (a === '--mcp-port' && i + 1 < argv.length) { out.mcpPort = parseInt(argv[++i], 10); continue; }
    if (a === '--verbose') { out.verbose = true; continue; }
  }
  return out;
}

const args = parseArgs(process.argv);

const TELEMETRY_WSS = args.wss || process.env.TELEMETRY_WSS;
const AGENT_ID = args.agentId || process.env.AGENT_ID || 'agent_001';
const MCP_HOST = args.mcpHost || process.env.MCP_HOST || '127.0.0.1';
const MCP_PORT = Number.isFinite(args.mcpPort) ? args.mcpPort : (process.env.MCP_PORT ? parseInt(process.env.MCP_PORT, 10) : 32123);
const VERBOSE = Boolean(args.verbose || process.env.VERBOSE);

if (!TELEMETRY_WSS) {
  console.error('[mcp-bridge-ai] Missing required --wss or TELEMETRY_WSS');
  process.exit(2);
}

console.log('[mcp-bridge-ai] Starting enhanced bridge with AI support');
console.log(`[mcp-bridge-ai] MCP TCP: ${MCP_HOST}:${MCP_PORT}`);
console.log(`[mcp-bridge-ai] WSS:     ${TELEMETRY_WSS}`);
console.log(`[mcp-bridge-ai] Agent:   ${AGENT_ID}`);

// ---------- WebSocket Manager (Bidirectional) ----------
class AIAgentWebSocket {
  constructor(url, agentId) {
    this.url = url;
    this.agentId = agentId;
    this.ws = null;
    this.connecting = false;
    this.backoffMs = 1000;
    this.maxBackoffMs = 15000;
    this.ready = false;
    this.commandHandlers = new Map();
    this.messageQueue = [];
    
    this._connect();
  }
  
  _connect() {
    if (this.connecting) return;
    this.connecting = true;
    
    const ws = new WebSocket(this.url);
    this.ws = ws;
    
    ws.on('open', () => {
      this.ready = true;
      this.connecting = false;
      this.backoffMs = 1000;
      console.log('[ai-websocket] Connected to API Gateway');
      
      // Register agent
      this.send({
        action: 'register_agent',
        data: { agentId: this.agentId }
      });
      
      // Flush queued messages
      while (this.messageQueue.length > 0) {
        const msg = this.messageQueue.shift();
        this._sendRaw(msg);
      }
    });
    
    ws.on('message', (data) => {
      try {
        const msg = JSON.parse(data.toString());
        this._handleMessage(msg);
      } catch (e) {
        console.error('[ai-websocket] Parse error:', e.message);
      }
    });
    
    ws.on('close', () => {
      this.ready = false;
      this.ws = null;
      console.warn('[ai-websocket] Disconnected');
      this._scheduleReconnect();
    });
    
    ws.on('error', (err) => {
      console.warn('[ai-websocket] Error:', err.message);
    });
  }
  
  _handleMessage(msg) {
    if (VERBOSE) console.log('[ai-websocket] Received:', JSON.stringify(msg));
    
    // Handle AI agent commands
    if (msg.action === 'agent_command') {
      this._handleAgentCommand(msg.data);
    }
    // Handle telemetry broadcasts (for overlay)
    else if (msg.action === 'telemetry') {
      // This is handled by the telemetry state manager
    }
  }
  
  _handleAgentCommand(command) {
    console.log(`[ai-command] Received: ${command.action} for ${command.agentId}`);
    
    // Notify registered handlers
    this.commandHandlers.forEach(handler => {
      try {
        handler(command);
      } catch (e) {
        console.error('[ai-command] Handler error:', e);
      }
    });
  }
  
  onCommand(handler) {
    const id = Date.now();
    this.commandHandlers.set(id, handler);
    return () => this.commandHandlers.delete(id);
  }
  
  _scheduleReconnect() {
    if (this.connecting) return;
    setTimeout(() => {
      this.backoffMs = Math.min(this.backoffMs * 1.6, this.maxBackoffMs);
      this.connecting = false;
      this._connect();
    }, this.backoffMs);
  }
  
  send(message) {
    const data = JSON.stringify(message);
    if (this.ready && this.ws) {
      this._sendRaw(data);
    } else {
      this.messageQueue.push(data);
      if (this.messageQueue.length > 100) {
        this.messageQueue.shift(); // Drop oldest if queue too large
      }
    }
  }
  
  _sendRaw(data) {
    try {
      this.ws.send(data);
    } catch (e) {
      console.error('[ai-websocket] Send error:', e.message);
    }
  }
  
  // Request AI decision for game state
  requestAgentDecision(gameState, characterState, requestType = 'decide_action') {
    this.send({
      action: 'agent_request',
      data: {
        agentId: this.agentId,
        gameState,
        characterState,
        requestType,
        timestamp: Date.now()
      }
    });
  }
  
  // Send telemetry update
  sendTelemetry(update) {
    const envelope = { action: 'telemetry', data: {} };
    
    if (update.goal) envelope.data.goal = update.goal;
    if (update.action) envelope.data.action = update.action;
    if (update.rationale) envelope.data.rationale = update.rationale;
    if (update.result) envelope.data.result = update.result;
    
    this.send(envelope);
  }
}

// ---------- Enhanced MCP TCP Client ----------
class EnhancedMcpClient {
  constructor(host, port, aiWebSocket) {
    this.host = host;
    this.port = port;
    this.aiWebSocket = aiWebSocket;
    this.sock = null;
    this.parser = new JsonRpcStreamParser(this._onMessage.bind(this));
    this.backoffMs = 1000;
    this.maxBackoffMs = 15000;
    this.connecting = false;
    this.pendingRequests = new Map();
    this.nextId = 1;
    
    this._connect();
    this._setupAICommandHandler();
  }
  
  _connect() {
    if (this.connecting) return;
    this.connecting = true;
    
    const s = net.createConnection({ host: this.host, port: this.port }, () => {
      console.log(`[mcp-enhanced] Connected to ${this.host}:${this.port}`);
      this.sock = s;
      this.connecting = false;
      this.backoffMs = 1000;
      
      // Send initialization
      this.sendRequest('initialize', {
        bridge: 'ai-enhanced',
        agentId: AGENT_ID
      });
    });
    
    s.on('data', (chunk) => {
      this.parser.feed(chunk);
    });
    
    s.on('error', (err) => {
      console.warn('[mcp-enhanced] TCP error:', err.message);
    });
    
    s.on('close', () => {
      console.warn('[mcp-enhanced] Disconnected from MCP server');
      this.sock = null;
      this._scheduleReconnect();
    });
  }
  
  _scheduleReconnect() {
    if (this.connecting) return;
    setTimeout(() => {
      this.backoffMs = Math.min(this.backoffMs * 1.6, this.maxBackoffMs);
      this.connecting = false;
      this._connect();
    }, this.backoffMs);
  }
  
  _onMessage(msg) {
    if (VERBOSE) console.log('[mcp-enhanced] Received:', JSON.stringify(msg));
    
    // Handle responses to our requests
    if (msg.id && this.pendingRequests.has(msg.id)) {
      const handler = this.pendingRequests.get(msg.id);
      this.pendingRequests.delete(msg.id);
      handler(msg);
    }
    
    // Handle notifications from Unreal
    if (msg.method && !msg.id) {
      this._handleNotification(msg);
    }
    
    // Handle requests from Unreal
    if (msg.method && msg.id) {
      this._handleRequest(msg);
    }
  }
  
  _handleNotification(msg) {
    const method = msg.method.toLowerCase();
    const params = msg.params || {};
    
    // Game state updates trigger AI decisions
    if (method.includes('game_state') || method.includes('world_update')) {
      this.aiWebSocket.requestAgentDecision(
        params.gameState || params,
        params.characterState || {},
        'periodic_update'
      );
    }
    
    // Character events
    if (method.includes('character_event')) {
      if (params.event === 'collision' || params.event === 'interaction_available') {
        this.aiWebSocket.requestAgentDecision(
          params.gameState || {},
          params.characterState || {},
          'react_to_event'
        );
      }
    }
    
    // Update telemetry overlay
    const telemetryUpdate = this._extractTelemetry(msg);
    if (telemetryUpdate) {
      this.aiWebSocket.sendTelemetry(telemetryUpdate);
    }
  }
  
  _handleRequest(msg) {
    // Respond to Unreal requests
    const response = {
      jsonrpc: '2.0',
      id: msg.id
    };
    
    switch (msg.method) {
      case 'get_agent_info':
        response.result = {
          agentId: AGENT_ID,
          status: 'connected',
          aiEnabled: true
        };
        break;
        
      default:
        response.error = {
          code: -32601,
          message: 'Method not found'
        };
    }
    
    this.send(response);
  }
  
  _extractTelemetry(msg) {
    const params = msg.params || {};
    const method = msg.method || '';
    
    // Extract telemetry based on message type
    if (method.includes('action_complete')) {
      return {
        result: params.result || 'Completed',
        action: params.action || method
      };
    }
    
    if (method.includes('goal_update')) {
      return {
        goal: params.goal || params.objective
      };
    }
    
    return null;
  }
  
  _setupAICommandHandler() {
    // Handle commands from AI agent
    this.aiWebSocket.onCommand((command) => {
      console.log(`[mcp-enhanced] Forwarding AI command to Unreal: ${command.action}`);
      
      // Convert AI command to Unreal JSON-RPC
      const unrealMsg = {
        jsonrpc: '2.0',
        method: 'agent.execute_command',
        params: {
          agentId: command.agentId || AGENT_ID,
          command: command.action,
          parameters: command.parameters || {},
          dialogue: command.dialogue,
          animation: command.animation,
          emotion: command.emotion,
          goal: command.goal,
          rationale: command.rationale
        },
        id: this.nextId++
      };
      
      this.sendRequest(unrealMsg.method, unrealMsg.params, (response) => {
        // Update telemetry with command result
        const result = response.result || response.error || 'Unknown';
        this.aiWebSocket.sendTelemetry({
          action: command.action,
          result: typeof result === 'object' ? JSON.stringify(result) : result
        });
      });
    });
  }
  
  send(msg) {
    if (!this.sock) return;
    
    const data = JSON.stringify(msg) + '\n';
    try {
      this.sock.write(data);
    } catch (e) {
      console.error('[mcp-enhanced] Send error:', e.message);
    }
  }
  
  sendRequest(method, params, callback) {
    const id = this.nextId++;
    const msg = {
      jsonrpc: '2.0',
      method,
      params,
      id
    };
    
    if (callback) {
      this.pendingRequests.set(id, callback);
    }
    
    this.send(msg);
    return id;
  }
}

// ---------- JSON-RPC Stream Parser ----------
class JsonRpcStreamParser {
  constructor(onMessage) {
    this.buf = Buffer.alloc(0);
    this.onMessage = onMessage;
  }
  
  feed(chunk) {
    if (!chunk || chunk.length === 0) return;
    this.buf = Buffer.concat([this.buf, chunk]);
    
    // Try LSP-style framing first
    while (true) {
      const headerEnd = this._indexOfSub(this.buf, Buffer.from('\r\n\r\n'));
      if (headerEnd >= 0) {
        const headersBuf = this.buf.slice(0, headerEnd).toString('utf8');
        const clMatch = headersBuf.match(/Content-Length:\s*(\d+)/i);
        if (clMatch) {
          const bodyLen = parseInt(clMatch[1], 10);
          const totalNeeded = headerEnd + 4 + bodyLen;
          if (this.buf.length >= totalNeeded) {
            const bodyBuf = this.buf.slice(headerEnd + 4, totalNeeded);
            this._safeParse(bodyBuf.toString('utf8'));
            this.buf = this.buf.slice(totalNeeded);
            continue;
          } else {
            return;
          }
        }
      }
      break;
    }
    
    // Fallback: NDJSON
    const str = this.buf.toString('utf8');
    if (str.indexOf('\n') !== -1) {
      const parts = str.split(/\r?\n/);
      const last = parts.pop();
      for (const line of parts) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        this._safeParse(trimmed);
      }
      this.buf = Buffer.from(last, 'utf8');
    }
  }
  
  _safeParse(s) {
    try {
      const obj = JSON.parse(s);
      this.onMessage(obj);
    } catch (e) {
      if (VERBOSE) console.warn('[parser] JSON parse error:', e.message);
    }
  }
  
  _indexOfSub(buf, sub) {
    for (let i = 0; i <= buf.length - sub.length; i++) {
      let ok = true;
      for (let j = 0; j < sub.length; j++) {
        if (buf[i + j] !== sub[j]) { ok = false; break; }
      }
      if (ok) return i;
    }
    return -1;
  }
}

// ---------- Initialize System ----------
const aiWebSocket = new AIAgentWebSocket(TELEMETRY_WSS, AGENT_ID);
const mcpClient = new EnhancedMcpClient(MCP_HOST, MCP_PORT, aiWebSocket);

// Periodic game state request (optional)
setInterval(() => {
  if (mcpClient.sock) {
    mcpClient.sendRequest('get_game_state', {}, (response) => {
      if (response.result) {
        aiWebSocket.requestAgentDecision(
          response.result.gameState || {},
          response.result.characterState || {},
          'periodic_check'
        );
      }
    });
  }
}, 30000); // Every 30 seconds

console.log('[mcp-bridge-ai] AI-enhanced bridge initialized');
console.log('[mcp-bridge-ai] Waiting for connections...');
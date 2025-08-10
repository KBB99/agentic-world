'use strict';

const net = require('net');
const WebSocket = require('ws');
const { spawn } = require('child_process');
const path = require('path');

function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--wss' && i + 1 < argv.length) { out.wss = argv[++i]; continue; }
    if (a === '--host' && i + 1 < argv.length) { out.host = argv[++i]; continue; }
    if (a === '--port' && i + 1 < argv.length) { out.port = parseInt(argv[++i], 10); continue; }
  }
  return out;
}

const args = parseArgs(process.argv);
const WSS = args.wss || process.env.TELEMETRY_WSS || 'wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod';
const MCP_HOST = args.host || '127.0.0.1';
const MCP_PORT = Number.isFinite(args.port) ? args.port : 32123;

console.log('[e2e] Using WSS:', WSS);
console.log('[e2e] Mock MCP at:', MCP_HOST + ':' + MCP_PORT);

let ws, srv, bridge;
let received = [];
let pass = false;

function done(ok) {
  try { if (ws && ws.readyState === 1) ws.close(); } catch {}
  try { if (srv) srv.close(); } catch {}
  try { if (bridge) bridge.kill(); } catch {}
  setTimeout(() => process.exit(ok ? 0 : 1), 300);
}

// 1) Start a mock MCP TCP server that emits a few JSON-RPC messages
srv = net.createServer((socket) => {
  console.log('[mock-mcp] client connected');
  // Send a goal update
  setTimeout(() => {
    const msg = { jsonrpc: '2.0', method: 'set_goal', params: { goal: 'Explore foyer' } };
    socket.write(JSON.stringify(msg) + '\n');
    console.log('[mock-mcp] --> set_goal');
  }, 300);

  // Send an action (editor console command)
  setTimeout(() => {
    const msg = { jsonrpc: '2.0', method: 'editor_console_command', params: { command: 'stat fps' } };
    socket.write(JSON.stringify(msg) + '\n');
    console.log('[mock-mcp] --> editor_console_command');
  }, 700);

  // Send a success result
  setTimeout(() => {
    const msg = { jsonrpc: '2.0', id: 1, result: { status: 'OK' } };
    socket.write(JSON.stringify(msg) + '\n');
    console.log('[mock-mcp] --> result OK');
  }, 1200);

  // Close after a brief interval
  setTimeout(() => {
    try { socket.end(); } catch {}
  }, 2500);
});

srv.listen(MCP_PORT, MCP_HOST, () => {
  console.log(`[mock-mcp] listening on ${MCP_HOST}:${MCP_PORT}`);

  // 2) Connect a WebSocket client to API Gateway (receives broadcast)
  ws = new WebSocket(WSS);

  ws.on('open', () => {
    console.log('[ws-test] connected to WSS');
    // 3) Spawn the bridge which will connect to MCP and publish telemetry to WSS
    const bridgeCwd = path.resolve(__dirname, '..');
    bridge = spawn(process.execPath, [
      'index.js',
      '--wss', WSS,
      '--mcp-host', MCP_HOST,
      '--mcp-port', String(MCP_PORT),
      '--verbose'
    ], { cwd: bridgeCwd, stdio: ['ignore', 'inherit', 'inherit'] });
  });

  ws.on('message', (data) => {
    let s = data.toString();
    console.log('[ws-test] <=', s);
    try {
      const obj = JSON.parse(s);
      received.push(obj);
      // Expect at least one action derived from the console command
      if (obj && typeof obj.action === 'string' && /console/i.test(obj.action) && /stat fps/i.test(obj.action)) {
        pass = true;
      }
    } catch (_) {
      // ignore non-JSON (shouldn't happen)
    }
  });

  ws.on('error', (err) => {
    console.error('[ws-test] error:', err.message);
  });

  ws.on('close', () => {
    console.warn('[ws-test] closed');
  });

  // Decide test result after a short window
  setTimeout(() => {
    if (pass) {
      console.log('[e2e] PASS: Received broadcast with console action from bridge');
      done(true);
    } else {
      console.error('[e2e] FAIL: No matching broadcast received; messages:', JSON.stringify(received));
      done(false);
    }
  }, 8000);
});

srv.on('error', (err) => {
  console.error('[mock-mcp] server error:', err.message);
  done(false);
});
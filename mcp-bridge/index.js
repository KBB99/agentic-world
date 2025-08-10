/**
 * Unreal MCP (TCP JSON-RPC) → API Gateway WebSocket Telemetry Bridge
 * - Connects to a local Unreal MCP Server over TCP JSON-RPC (e.g., 127.0.0.1:32123)
 * - Parses inbound JSON-RPC requests/responses/notifications
 * - Publishes succinct overlay telemetry to your API Gateway WebSocket:
 *     { action: "telemetry", data: { goal, action, rationale, result } }
 *
 * Usage:
 *   node index.js --wss wss://unk0zycq5d.execute-api.us-east-1.amazonaws.com/prod
 *                 [--mcp-host 127.0.0.1] [--mcp-port 32123]
 *
 * Env:
 *   TELEMETRY_WSS, MCP_HOST, MCP_PORT
 *
 * Notes:
 * - This bridge tolerates both NDJSON and LSP-style "Content-Length" framing.
 * - Heuristics map JSON-RPC messages to overlay fields ("goal", "action", etc.).
 * - To avoid route-selection collision in API Gateway, we send an envelope with
 *   action: "telemetry" and the payload in "data: {...}".
 */

'use strict';

const net = require('net');
const WebSocket = require('ws');

// ---------- CLI / ENV ----------
function parseArgs(argv) {
  const out = {};
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--wss' && i + 1 < argv.length) { out.wss = argv[++i]; continue; }
    if (a === '--mcp-host' && i + 1 < argv.length) { out.mcpHost = argv[++i]; continue; }
    if (a === '--mcp-port' && i + 1 < argv.length) { out.mcpPort = parseInt(argv[++i], 10); continue; }
    if (a === '--verbose') { out.verbose = true; continue; }
  }
  return out;
}

const args = parseArgs(process.argv);

const TELEMETRY_WSS = args.wss || process.env.TELEMETRY_WSS;
const MCP_HOST = args.mcpHost || process.env.MCP_HOST || '127.0.0.1';
const MCP_PORT = Number.isFinite(args.mcpPort) ? args.mcpPort : (process.env.MCP_PORT ? parseInt(process.env.MCP_PORT, 10) : 32123);
const VERBOSE = Boolean(args.verbose || process.env.VERBOSE);

if (!TELEMETRY_WSS) {
  console.error('[mcp-bridge] Missing required --wss or TELEMETRY_WSS (API Gateway WebSocket URL)');
  process.exit(2);
}

console.log('[mcp-bridge] Starting');
console.log(`[mcp-bridge] MCP TCP: ${MCP_HOST}:${MCP_PORT}`);
console.log(`[mcp-bridge] WSS:     ${TELEMETRY_WSS}`);

// ---------- WebSocket Publisher (to API GW) ----------
class TelemetryPublisher {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.connecting = false;
    this.backoffMs = 1000;
    this.maxBackoffMs = 15000;
    this.ready = false;

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
      console.log('[telemetry] Connected to API Gateway WebSocket');
    });
    ws.on('close', () => {
      this.ready = false;
      this.ws = null;
      console.warn('[telemetry] Disconnected from API Gateway WebSocket');
      this._scheduleReconnect();
    });
    ws.on('error', (err) => {
      console.warn('[telemetry] WebSocket error:', err.message);
      // error handler fires before close in many cases
    });
    // Optional: respond to pings to keep alive if needed (API GW pings not exposed here)
  }

  _scheduleReconnect() {
    if (this.connecting) return;
    setTimeout(() => {
      this.backoffMs = Math.min(this.backoffMs * 1.6, this.maxBackoffMs);
      this.connecting = false;
      this._connect();
    }, this.backoffMs);
  }

  sendTelemetry(update) {
    // Envelope to avoid route-selection collision with "action" field used by overlay
    const envelope = { action: 'telemetry', data: {} };

    // Only include fields provided
    if (typeof update.goal === 'string' && update.goal.length) envelope.data.goal = update.goal;
    if (typeof update.action === 'string' && update.action.length) {
      // Use actionText to avoid clashing with route-selection "action"
      envelope.data.actionText = update.action;
    }
    if (typeof update.rationale === 'string' && update.rationale.length) envelope.data.rationale = update.rationale;
    if (typeof update.result === 'string' && update.result.length) envelope.data.result = update.result;

    if (!this.ready || !this.ws) return;
    const s = JSON.stringify(envelope);
    try { this.ws.send(s); }
    catch (e) { /* ignore transient send errors */ }
  }
}

// ---------- JSON-RPC Stream Parser (NDJSON + LSP framing) ----------
class JsonRpcStreamParser {
  constructor(onMessage) {
    this.buf = Buffer.alloc(0);
    this.onMessage = onMessage;
  }

  feed(chunk) {
    if (!chunk || chunk.length === 0) return;
    this.buf = Buffer.concat([this.buf, chunk]);

    // Try LSP-style framing first: "Content-Length: N\r\n\r\n{...N bytes...}"
    while (true) {
      const headerEnd = this._indexOfSub(this.buf, Buffer.from('\r\n\r\n'));
      if (headerEnd >= 0) {
        // Inspect headers for Content-Length
        const headersBuf = this.buf.slice(0, headerEnd).toString('utf8');
        const clMatch = headersBuf.match(/Content-Length:\s*(\d+)/i);
        if (clMatch) {
          const bodyLen = parseInt(clMatch[1], 10);
          const totalNeeded = headerEnd + 4 + bodyLen;
          if (this.buf.length >= totalNeeded) {
            const bodyBuf = this.buf.slice(headerEnd + 4, totalNeeded);
            this._safeParse(bodyBuf.toString('utf8'));
            // Consume
            this.buf = this.buf.slice(totalNeeded);
            // Continue parsing; there may be more frames
            continue;
          } else {
            // Wait for more data
            return;
          }
        }
      }
      break; // no LSP frame detected at buffer start
    }

    // Fallback: NDJSON (split on \n)
    // If buf contains at least one newline, split and parse lines except the last incomplete line
    const str = this.buf.toString('utf8');
    if (str.indexOf('\n') !== -1) {
      const parts = str.split(/\r?\n/);
      // Keep the last part (could be partial)
      const last = parts.pop();
      for (const line of parts) {
        const trimmed = line.trim();
        if (!trimmed) continue;
        this._safeParse(trimmed);
      }
      this.buf = Buffer.from(last, 'utf8');
    } else {
      // Not enough data to form a line or frame; wait for more
    }
  }

  _safeParse(s) {
    try {
      const obj = JSON.parse(s);
      this.onMessage(obj);
    } catch (e) {
      // Ignore parse errors (could be partial or non-JSON logs)
      if (VERBOSE) console.warn('[parser] JSON parse error:', e.message);
    }
  }

  _indexOfSub(buf, sub) {
    // Naive search for small header terminator
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

// ---------- Heuristic Mapper: JSON-RPC → {goal, action, rationale, result} ----------
class TelemetryState {
  constructor(publisher) {
    this.pub = publisher;
    this.state = {
      goal: undefined,
      action: undefined,
      rationale: undefined,
      result: undefined,
    };
    this._sendScheduled = false;
  }

  set(partial) {
    let changed = false;
    for (const k of Object.keys(partial)) {
      const v = partial[k];
      if (typeof v === 'string' && v.length > 0 && this.state[k] !== v) {
        this.state[k] = v;
        changed = true;
      }
    }
    if (changed) this._scheduleSend();
  }

  _scheduleSend() {
    if (this._sendScheduled) return;
    this._sendScheduled = true;
    setTimeout(() => {
      this._sendScheduled = false;
      this.pub.sendTelemetry(this.state);
    }, 120); // coalesce bursts
  }
}

function summarizeParams(params) {
  try {
    if (!params || typeof params !== 'object') return '';
    // Special-cases
    if (typeof params.command === 'string') return ` "${truncate(params.command, 80)}"`;
    if (typeof params.name === 'string' && typeof params.class === 'string') return ` ${params.class} ${params.name}`;
    if (typeof params.asset === 'string') return ` ${truncate(params.asset, 60)}`;
    // Generic: show up to 2 key=value pairs with short values
    const pairs = [];
    for (const [k, v] of Object.entries(params)) {
      if (v == null) continue;
      const vs = typeof v === 'string' ? truncate(v, 40) : (typeof v === 'number' ? String(v) : undefined);
      if (vs) pairs.push(`${k}=${vs}`);
      if (pairs.length >= 2) break;
    }
    return pairs.length ? ' ' + pairs.join(' ') : '';
  } catch {
    return '';
  }
}

function truncate(s, n) {
  if (!s || s.length <= n) return s;
  return s.slice(0, n - 1) + '…';
}

function mapJsonRpcToTelemetry(msg, t) {
  // msg may be request, response, or notification
  try {
    // 1) Responses
    if (Object.prototype.hasOwnProperty.call(msg, 'result')) {
      const res = msg.result;
      let rs = 'Success';
      if (typeof res === 'string') rs = truncate(res, 100);
      else if (res && typeof res === 'object') {
        if (typeof res.status === 'string') rs = truncate(res.status, 100);
        else if (typeof res.message === 'string') rs = truncate(res.message, 100);
        else rs = 'OK';
      }
      t.set({ result: rs });
      return;
    }
    if (Object.prototype.hasOwnProperty.call(msg, 'error')) {
      const err = msg.error || {};
      const rs = `Error ${err.code ?? ''} ${err.message ? truncate(err.message, 100) : ''}`.trim();
      t.set({ result: rs });
      return;
    }

    // 2) Requests/Notifications
    const method = typeof msg.method === 'string' ? msg.method : undefined;
    const params = (msg.params && typeof msg.params === 'object') ? msg.params : undefined;
    if (!method) return;

    const m = method.toLowerCase();

    // Goal heuristics
    if (m.includes('set_goal') || m.includes('goal.set') || m.endsWith('.goal') || m.includes('agent.set_goal')) {
      const g = (params && (params.goal || params.text || params.message || params.plan)) || undefined;
      if (typeof g === 'string') t.set({ goal: truncate(g, 140), result: 'Goal updated' });
      return;
    }
    if (m.includes('plan') && params && typeof params.text === 'string') {
      t.set({ goal: truncate(params.text, 140), rationale: 'Planning' });
      return;
    }

    // Rationale heuristics
    const rat = params && (params.rationale || params.reason || params.why || params.explanation);
    if (typeof rat === 'string') t.set({ rationale: truncate(rat, 160) });

    // Action heuristics (Unreal/editor/tool invocations)
    if (m.startsWith('editor_') || m.startsWith('tool') || m.includes('console') || m.includes('create_') || m.includes('update_') || m.includes('delete_')) {
      const act = `${method}${summarizeParams(params)}`;
      t.set({ action: truncate(act, 140), result: 'Initiated' });
      return;
    }

    // Generic fallback: show method as action if clearly an operation verb
    if (/^(run|exec|do|move|navigate|search|open|take|screenshot|teleport|spawn|destroy|play|pause|stop|save|load)\b/i.test(m)) {
      const act = `${method}${summarizeParams(params)}`;
      t.set({ action: truncate(act, 140), result: 'Initiated' });
      return;
    }

    // Console command explicit
    if (m.includes('console') && params && typeof params.command === 'string') {
      t.set({ action: `console ${truncate(params.command, 120)}`, result: 'Initiated' });
      return;
    }
  } catch (e) {
    if (VERBOSE) console.warn('[mapper] error:', e.message);
  }
}

// ---------- TCP Client (to Unreal MCP) ----------
class McpTcpClient {
  constructor(host, port, onRpc) {
    this.host = host;
    this.port = port;
    this.onRpc = onRpc;
    this.sock = null;
    this.parser = new JsonRpcStreamParser(this._onMessage.bind(this));
    this.backoffMs = 1000;
    this.maxBackoffMs = 15000;
    this.connecting = false;

    this._connect();
  }

  _connect() {
    if (this.connecting) return;
    this.connecting = true;

    const s = net.createConnection({ host: this.host, port: this.port }, () => {
      console.log(`[mcp] Connected to ${this.host}:${this.port}`);
      this.sock = s;
      this.connecting = false;
      this.backoffMs = 1000;
    });

    s.on('data', (chunk) => {
      this.parser.feed(chunk);
    });
    s.on('error', (err) => {
      console.warn('[mcp] TCP error:', err.message);
    });
    s.on('close', () => {
      console.warn('[mcp] Disconnected from MCP server');
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

  _onMessage(obj) {
    if (VERBOSE) {
      try {
        console.log('[mcp] <--', truncate(JSON.stringify(obj), 300));
      } catch {}
    }
    this.onRpc(obj);
  }
}

// ---------- Wire it up ----------
const publisher = new TelemetryPublisher(TELEMETRY_WSS);
const telemetry = new TelemetryState(publisher);
const mcp = new McpTcpClient(MCP_HOST, MCP_PORT, (msg) => mapJsonRpcToTelemetry(msg, telemetry));

// Optional: keep process alive and log basic heartbeat
setInterval(() => {
  // no-op heartbeat
}, 30000);
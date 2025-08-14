#!/usr/bin/env node
'use strict';

/**
 * Local control plane for the multi-character world:
 * - Serves the viewer UI (viewer/)
 * - Exposes HTTP APIs:
 *    GET  /api/characters
 *    POST /api/run-turn  { count?: number }
 *    POST /api/interact  { characterId: string, type: "set_goal"|"message"|"nudge_action", payload: object }
 * - Provides SSE at /telemetry/stream for:
 *    event: telemetry  { goal, action, rationale, result }
 *    event: characters { characters: [...] }
 *
 * No external deps (Express/ws) to keep friction low.
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');
const { MultiCharacterWorld } = require('../multi-character-orchestrator.js');

const PORT = Number(process.env.PORT || 8081);
const viewerDir = path.resolve(__dirname, '../viewer');
const sseClients = new Set();

let world;
let tickCount = 0;

const config = {
  aiWebSocketUrl: null, // not used in local control plane
  initialCharacters: [
    {
      id: 'alex_chen',
      name: 'Alex Chen',
      economicTier: 'poor',
      startLocation: 'public_library',
      money: 53.09,
      inventory: ['old_laptop', 'water_bottle'],
      initialNeeds: { hunger: 75, thirst: 40, exhaustion: 85, stress: 90 }
    },
    {
      id: 'madison_worthington',
      name: 'Madison Worthington',
      economicTier: 'ultra_wealthy',
      startLocation: 'public_library',
      money: 25000000,
      inventory: ['iphone_15_pro', 'designer_bag', 'credit_cards'],
      initialNeeds: { hunger: 10, thirst: 0, exhaustion: 0, stress: 5 }
    },
    {
      id: 'jamie_rodriguez',
      name: 'Jamie Rodriguez',
      economicTier: 'poor',
      startLocation: 'coffee_shop',
      money: 43,
      inventory: ['apron', 'name_tag', 'half_sandwich'],
      initialNeeds: { hunger: 60, thirst: 30, exhaustion: 70, stress: 75 }
    }
  ]
};

async function initWorld() {
  world = new MultiCharacterWorld(config);
  await world.initialize();
  // Do NOT start auto-ticking; we step via REST
  console.log('World initialized. Characters:', Array.from(world.characters.keys()).join(', '));
}

function getCharactersSnapshot() {
  return Array.from(world.characters.values()).map(c => ({
    id: c.id,
    name: c.name,
    economicTier: c.economicTier,
    location: c.location,
    state: c.state
  }));
}

function sseWriteEvent(res, event, data) {
  try {
    res.write(`event: ${event}\n`);
    res.write(`data: ${JSON.stringify(data)}\n\n`);
  } catch (_) {
    // ignore write errors; connection likely closed
  }
}

function sseBroadcast(event, data) {
  for (const res of Array.from(sseClients)) {
    sseWriteEvent(res, event, data);
  }
}

function makeTelemetry(origin = 'manual') {
  const chars = Array.from(world.characters.values());
  const chosen =
    chars
      .slice()
      .sort((a, b) => (b.state?.stress || 0) - (a.state?.stress || 0))[0] || chars[0];

  const who = chosen ? `${chosen.name}` : 'World';
  return {
    goal: chosen?.state?.goal || `Maintain simulation realism`,
    action: 'world_tick',
    rationale: origin === 'manual' ? 'Step executed from web control' : 'Automatic progression',
    result: `Tick ${tickCount} processed for ${who}`
  };
}

function runOneTick(origin = 'manual') {
  world.worldTick();
  tickCount += 1;

  const telemetry = makeTelemetry(origin);
  sseBroadcast('telemetry', telemetry);
  sseBroadcast('characters', { characters: getCharactersSnapshot() });
}

function parseBody(req) {
  return new Promise((resolve, reject) => {
    let buf = '';
    req.on('data', chunk => (buf += chunk));
    req.on('end', () => {
      if (!buf) return resolve({});
      try {
        resolve(JSON.parse(buf));
      } catch (e) {
        reject(new Error('Invalid JSON'));
      }
    });
  });
}

function setCORS(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
}

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url, true);
  const pathname = parsed.pathname || '/';
  const method = req.method || 'GET';

  // CORS + preflight
  setCORS(res);
  if (method === 'OPTIONS') {
    res.writeHead(204);
    return res.end();
  }

  // SSE Telemetry Stream
  if (method === 'GET' && pathname === '/telemetry/stream') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
      'X-Accel-Buffering': 'no'
    });
    res.write('retry: 5000\n\n'); // reconnection delay
    sseClients.add(res);

    // On disconnect
    req.on('close', () => {
      sseClients.delete(res);
    });

    // Push initial state
    sseWriteEvent(res, 'characters', { characters: getCharactersSnapshot() });
    sseWriteEvent(res, 'telemetry', makeTelemetry('connect'));
    return;
  }

  // API: List characters
  if (pathname === '/api/characters' && method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ characters: getCharactersSnapshot() }));
  }

  // API: Run N ticks
  if (pathname === '/api/run-turn' && method === 'POST') {
    try {
      const body = await parseBody(req);
      let count = Number(body?.count || 1);
      if (!Number.isFinite(count) || count < 1) count = 1;
      if (count > 100) count = 100; // safety cap

      for (let i = 0; i < count; i += 1) {
        runOneTick('manual');
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: true, ran: count, totalTicks: tickCount }));
    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: e.message }));
    }
  }

  // API: Interact with character
  if (pathname === '/api/interact' && method === 'POST') {
    try {
      const body = await parseBody(req);
      const { characterId, type, payload } = body || {};
      if (!characterId || !type) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: 'characterId and type are required' }));
      }

      const character = world.characters.get(characterId);
      if (!character) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        return res.end(JSON.stringify({ ok: false, error: `Character ${characterId} not found` }));
      }

      // Ensure some internal fields exist
      character.state = character.state || {};
      character.state.messages = character.state.messages || [];
      character.state.goals = character.state.goals || [];

      let summary = '';

      switch (type) {
        case 'set_goal': {
          const goalText = String(payload?.goal || '').slice(0, 200);
          if (!goalText) throw new Error('payload.goal is required');
          character.state.goal = goalText;
          character.state.goals.push({ text: goalText, at: Date.now() });
          summary = `Set goal to "${goalText}"`;
          break;
        }
        case 'message': {
          const text = String(payload?.text || '').slice(0, 500);
          if (!text) throw new Error('payload.text is required');
          character.state.messages.push({ from: 'viewer', text, at: Date.now() });
          summary = `Viewer message: ${text}`;
          break;
        }
        case 'nudge_action': {
          const act = String(payload?.action || '').slice(0, 100);
          if (!act) throw new Error('payload.action is required');
          character.state.animation = act;
          summary = `Nudged animation/action to "${act}"`;
          break;
        }
        default:
          throw new Error(`Unsupported interact type: ${type}`);
      }

      // Broadcast state and a small telemetry line
      sseBroadcast('characters', { characters: getCharactersSnapshot() });
      sseBroadcast('telemetry', {
        goal: character.state.goal || 'Follow viewer guidance',
        action: 'viewer_interact',
        rationale: `Interaction: ${type}`,
        result: `${character.name}: ${summary}`
      });

      res.writeHead(200, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: true, summary }));
    } catch (e) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      return res.end(JSON.stringify({ ok: false, error: e.message }));
    }
  }

  // Static: serve viewer
  if (method === 'GET') {
    // Map URL to viewer/ directory
    const rel = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
    const filePath = path.resolve(viewerDir, rel);

    if (!filePath.startsWith(viewerDir)) {
      res.writeHead(403);
      return res.end('Forbidden');
    }

    fs.stat(filePath, (err, st) => {
      if (err || !st.isFile()) {
        res.writeHead(404);
        return res.end('Not found');
      }

      const ext = path.extname(filePath).toLowerCase();
      const types = {
        '.html': 'text/html; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.m3u8': 'application/vnd.apple.mpegurl',
        '.ts': 'video/mp2t',
        '.mp4': 'video/mp4',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.jpg': 'image/jpeg'
      };
      const ctype = types[ext] || 'application/octet-stream';

      res.writeHead(200, { 'Content-Type': ctype });
      fs.createReadStream(filePath).pipe(res);
    });
    return;
  }

  res.writeHead(404);
  res.end('Not found');
});

// Heartbeat for SSE connections (comments)
setInterval(() => {
  for (const res of Array.from(sseClients)) {
    try {
      res.write(':\n\n');
    } catch (_) {
      sseClients.delete(res);
    }
  }
}, 15000);

initWorld()
  .then(() => {
    server.listen(PORT, () => {
      console.log(`Control plane server listening on http://localhost:${PORT}`);
      console.log(`Viewer UI: http://localhost:${PORT}/  (append ?api=http://localhost:${PORT} when serving viewer elsewhere)`);
    });
  })
  .catch(err => {
    console.error('Failed to initialize world', err);
    process.exit(1);
  });
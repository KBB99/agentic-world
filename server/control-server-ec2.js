#!/usr/bin/env node
'use strict';

/**
 * Minimal Control Plane for EC2 (port 80)
 * - HTTP API:
 *    GET  /api/characters
 *    POST /api/run-turn  { count?: number }   // capped to 100
 *    POST /api/interact  { characterId, type: "set_goal"|"message"|"nudge_action", payload }
 * - SSE:
 *    GET /telemetry/stream
 *
 * No external dependencies. Contains a small, self-contained "world" simulation.
 */

const http = require('http');
const url = require('url');

// World state
const world = {
  tick: 0,
  characters: [
    {
      id: 'alex_chen',
      name: 'Alex Chen',
      economicTier: 'poor',
      location: 'public_library',
      state: {
        animation: 'idle',
        needs: { hunger: 75, thirst: 40, exhaustion: 85, stress: 90 },
        money: 53.09,
        inventory: ['old_laptop', 'water_bottle'],
        goal: 'Find free wifi to submit article',
        messages: []
      }
    },
    {
      id: 'madison_worthington',
      name: 'Madison Worthington',
      economicTier: 'ultra_wealthy',
      location: 'public_library',
      state: {
        animation: 'idle',
        needs: { hunger: 10, thirst: 0, exhaustion: 0, stress: 5 },
        money: 25000000,
        inventory: ['iphone_15_pro', 'designer_bag', 'credit_cards'],
        goal: 'Increase engagement',
        messages: []
      }
    },
    {
      id: 'jamie_rodriguez',
      name: 'Jamie Rodriguez',
      economicTier: 'poor',
      location: 'coffee_shop',
      state: {
        animation: 'idle',
        needs: { hunger: 60, thirst: 30, exhaustion: 70, stress: 75 },
        money: 43,
        inventory: ['apron', 'name_tag', 'half_sandwich'],
        goal: 'Get through the shift',
        messages: []
      }
    }
  ]
};

// SSE client set
const sseClients = new Set();

function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

function telemetryLine(origin, who, extra) {
  return {
    goal: who?.state?.goal || 'Maintain simulation realism',
    action: origin,
    rationale: origin === 'world_tick' ? 'Automatic progression' : 'Viewer interaction',
    result: extra || `Tick ${world.tick} processed${who ? ' for ' + who.name : ''}`
  };
}

function broadcast(event, data) {
  for (const res of Array.from(sseClients)) {
    try {
      res.write(`event: ${event}\n`);
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    } catch (_) {
      try { res.end(); } catch {}
      sseClients.delete(res);
    }
  }
}

function snapshot() {
  return { characters: world.characters.map(c => ({
    id: c.id,
    name: c.name,
    economicTier: c.economicTier,
    location: c.location,
    state: c.state
  }))};
}

function pickCharacter() {
  // Pick highest stress or first
  const sorted = world.characters.slice().sort((a,b) => (b.state.needs.stress||0) - (a.state.needs.stress||0));
  return sorted[0] || world.characters[0];
}

// Simple world tick: needs drift; poor worsen faster
function runTick() {
  world.tick += 1;
  for (const c of world.characters) {
    const poorFactor = (c.economicTier === 'poor') ? 1.2 : 0.6;
    const n = c.state.needs;
    n.hunger = clamp(n.hunger + (Math.random() * 2 + 0.5) * poorFactor, 0, 100);
    n.thirst = clamp(n.thirst + (Math.random() * 2 + 0.5) * poorFactor, 0, 100);
    n.exhaustion = clamp(n.exhaustion + (Math.random() * 1.5 + 0.2) * poorFactor, 0, 100);
    // stress reacts to hunger/exhaustion
    const stressDrift = ((n.hunger - 50) + (n.exhaustion - 50)) / 200; // ~[-0.5, 0.5]
    n.stress = clamp(n.stress + stressDrift * 5, 0, 100);

    // very basic context-driven animation
    if (n.hunger > 80) c.state.animation = 'look_for_food';
    else if (n.exhaustion > 85) c.state.animation = 'rest';
    else c.state.animation = 'idle';
  }

  const who = pickCharacter();
  broadcast('telemetry', telemetryLine('world_tick', who));
  broadcast('characters', snapshot());
}

function respondJSON(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end(body);
}

function handleOPTIONS(res) {
  res.writeHead(204, {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type'
  });
  res.end();
}

function getBody(req) {
  return new Promise((resolve, reject) => {
    let buf = '';
    req.on('data', c => buf += c);
    req.on('end', () => {
      if (!buf) return resolve({});
      try { resolve(JSON.parse(buf)); }
      catch (e) { reject(e); }
    });
  });
}

const server = http.createServer(async (req, res) => {
  const parsed = url.parse(req.url || '/', true);
  const pathname = parsed.pathname || '/';
  const method = req.method || 'GET';

  if (method === 'OPTIONS') return handleOPTIONS(res);

  // SSE stream
  if (method === 'GET' && pathname === '/telemetry/stream') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
      'Access-Control-Allow-Origin': '*'
    });
    res.write('retry: 5000\n\n');
    sseClients.add(res);
    // Initial burst
    const who = pickCharacter();
    res.write(`event: telemetry\n`);
    res.write(`data: ${JSON.stringify(telemetryLine('connect', who, 'Client connected'))}\n\n`);
    res.write(`event: characters\n`);
    res.write(`data: ${JSON.stringify(snapshot())}\n\n`);

    req.on('close', () => { sseClients.delete(res); });
    return;
  }

  if (method === 'GET' && pathname === '/api/characters') {
    return respondJSON(res, 200, snapshot());
  }

  if (method === 'POST' && pathname === '/api/run-turn') {
    try {
      const body = await getBody(req);
      let count = Number(body?.count || 1);
      if (!Number.isFinite(count) || count < 1) count = 1;
      if (count > 100) count = 100;
      for (let i=0; i<count; i++) runTick();
      return respondJSON(res, 200, { ok: true, ran: count, totalTicks: world.tick });
    } catch (e) {
      return respondJSON(res, 400, { ok: false, error: e.message });
    }
  }

  if (method === 'POST' && pathname === '/api/interact') {
    try {
      const body = await getBody(req);
      const { characterId, type, payload } = body || {};
      if (!characterId || !type) return respondJSON(res, 400, { ok: false, error: 'characterId and type are required' });
      const c = world.characters.find(x => x.id === characterId);
      if (!c) return respondJSON(res, 404, { ok: false, error: `Character ${characterId} not found` });

      let summary = '';
      switch (type) {
        case 'set_goal': {
          const goal = String(payload?.goal || '').slice(0, 200);
          if (!goal) return respondJSON(res, 400, { ok: false, error: 'payload.goal required' });
          c.state.goal = goal;
          summary = `Set goal to "${goal}"`;
          break;
        }
        case 'message': {
          const text = String(payload?.text || '').slice(0, 500);
          if (!text) return respondJSON(res, 400, { ok: false, error: 'payload.text required' });
          c.state.messages.push({ from: 'viewer', text, at: Date.now() });
          summary = `Viewer message: ${text}`;
          break;
        }
        case 'nudge_action': {
          const act = String(payload?.action || '').slice(0, 100);
          if (!act) return respondJSON(res, 400, { ok: false, error: 'payload.action required' });
          c.state.animation = act;
          summary = `Nudged animation/action to "${act}"`;
          break;
        }
        default:
          return respondJSON(res, 400, { ok: false, error: `Unsupported interact type: ${type}` });
      }

      // Small immediate telemetry push
      broadcast('characters', snapshot());
      broadcast('telemetry', {
        goal: c.state.goal || 'Follow viewer guidance',
        action: 'viewer_interact',
        rationale: `Interaction: ${type}`,
        result: `${c.name}: ${summary}`
      });

      return respondJSON(res, 200, { ok: true, summary });
    } catch (e) {
      return respondJSON(res, 400, { ok: false, error: e.message });
    }
  }

  // Default 404
  res.writeHead(404, {
    'Content-Type': 'text/plain',
    'Access-Control-Allow-Origin': '*'
  });
  res.end('Not found');
});

// Keep SSE alive with periodic comment
setInterval(() => {
  for (const res of Array.from(sseClients)) {
    try { res.write(':\n\n'); } catch (_) { sseClients.delete(res); }
  }
}, 15000);

const PORT = Number(process.env.PORT || 80);
server.listen(PORT, () => {
  console.log(`EC2 Control plane listening on port ${PORT}`);
});
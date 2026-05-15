/**
 * gss-matcher-proxy — Cloudflare Worker
 *
 * Three endpoints:
 *   POST /          Form submission → generate sessionId → fire Cassidy → return {sessionId}
 *   POST /receive   Cassidy callback → store results in KV
 *   GET  /results/:sessionId  Frontend polling → return KV value
 */

const ALLOWED_ORIGINS = [
  'https://gss-matcher.pages.dev',
  'https://82fa0f1c.gss-matcher.pages.dev',
  'http://localhost:5173',
  'http://127.0.0.1:5173',
  'null', // file:// local HTML testing
];

const RATE_LIMIT_MAX   = 20;   // submissions per IP per hour
const SESSION_TTL_SEC  = 7200; // 2 hours

// ── CORS helpers ──────────────────────────────────────────────────────────────

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin':  allowed,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
  };
}

function respond(body, status, origin, extra = {}) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...corsHeaders(origin),
      ...extra,
    },
  });
}

// ── Rate limiting (simple IP-based counter in KV) ─────────────────────────────

async function checkRateLimit(ip, kv) {
  const key  = `rl:${ip}`;
  const raw  = await kv.get(key);
  const count = raw ? parseInt(raw, 10) : 0;
  if (count >= RATE_LIMIT_MAX) return false;
  await kv.put(key, String(count + 1), { expirationTtl: 3600 });
  return true;
}

// ── Main handler ──────────────────────────────────────────────────────────────

export default {
  async fetch(request, env, ctx) {
    const url    = new URL(request.url);
    const origin = request.headers.get('Origin') || 'null';
    const method = request.method;

    // Pre-flight
    if (method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders(origin) });
    }

    // ── POST / — form submission ─────────────────────────────────────────────
    if (method === 'POST' && url.pathname === '/') {

      // Rate limit
      const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
      const allowed = await checkRateLimit(ip, env.RESULTS_KV);
      if (!allowed) {
        return respond({ error: 'Rate limit exceeded. Please try again later.' }, 429, origin);
      }

      // Parse payload
      let payload;
      try {
        payload = await request.json();
      } catch {
        return respond({ error: 'Invalid JSON payload.' }, 400, origin);
      }

      // Generate sessionId and inject into payload
      const sessionId = crypto.randomUUID();
      payload['session-id'] = sessionId;

      // Store pending state + form_data so results screen can personalise hero
      await env.RESULTS_KV.put(
        `session:${sessionId}`,
        JSON.stringify({
          status: 'pending',
          form_data: {
            first_name:          payload['student-first-name']        || '',
            research_interests:  payload['intake-research-interests'] || [],
            degree:              payload['intake-degree-goal']         || '',
            career_goal:         payload['intake-career-goal']         || '',
          },
        }),
        { expirationTtl: SESSION_TTL_SEC }
      );

      // Fire Cassidy webhook non-blocking
      const cassidyPromise = fetch(env.CASSIDY_WEBHOOK_URL, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify(payload),
      }).catch(err => console.error('Cassidy webhook error:', err));

      // ctx.waitUntil keeps the Worker alive until Cassidy webhook completes
      ctx.waitUntil(cassidyPromise);

      return respond({ sessionId }, 202, origin);
    }

    // ── POST /receive — Cassidy callback ─────────────────────────────────────
    if (method === 'POST' && url.pathname === '/receive') {

      // Auth
      const auth = request.headers.get('Authorization') || '';
      if (auth !== `Bearer ${env.RECEIVE_API_KEY}`) {
        return respond({ error: 'Unauthorized.' }, 401, origin);
      }

      let body;
      try {
        body = await request.json();
      } catch {
        return respond({ error: 'Invalid JSON.' }, 400, origin);
      }

      // Cassidy sometimes wraps output as a JSON-encoded string — unwrap if needed
      let data = body;
      if (typeof data === 'string') {
        try { data = JSON.parse(data); } catch { /* leave as-is */ }
      }

      // Extract sessionId — Cassidy sends as 'session_id' (underscore)
      const sessionId = data.session_id || data['session-id'] || data.sessionId;
      if (!sessionId) {
        return respond({ error: 'Missing session-id in Cassidy response.' }, 400, origin);
      }

      // Preserve form_data stored at submission time
      const existing = await env.RESULTS_KV.get(`session:${sessionId}`);
      const prev = existing ? JSON.parse(existing) : {};

      // Store ready state
      await env.RESULTS_KV.put(
        `session:${sessionId}`,
        JSON.stringify({ status: 'ready', data, form_data: prev.form_data || null }),
        { expirationTtl: SESSION_TTL_SEC }
      );

      return respond({ ok: true }, 200, origin);
    }

    // ── GET /results/:sessionId — frontend polling ────────────────────────────
    const pollMatch = url.pathname.match(/^\/results\/([^/]+)$/);
    if (method === 'GET' && pollMatch) {
      const sessionId = pollMatch[1];
      const raw = await env.RESULTS_KV.get(`session:${sessionId}`);

      if (!raw) {
        return respond({ status: 'not_found' }, 404, origin);
      }

      const result = JSON.parse(raw);
      return respond(result, 200, origin);
    }

    // ── 404 ───────────────────────────────────────────────────────────────────
    return respond({ error: 'Not found.' }, 404, origin);
  },
};

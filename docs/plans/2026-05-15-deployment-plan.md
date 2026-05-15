# GSS AI Matcher — Deployment Plan
**Date:** 2026-05-15 (start of session)  
**Owner:** Mack Wallace / Enterprise Commons  
**Goal:** Working end-to-end demo: intake form → Cloudflare Worker → Cassidy AI → results screen

---

## Overview

| Phase | Task | Est. Time | Owner |
|-------|------|-----------|-------|
| 1 | Push prototype to GitHub | 20 min | Claude |
| 2 | Deploy frontend to Cloudflare Pages | 15 min | Claude |
| 3 | Write & deploy Cloudflare Worker | 60 min | Claude |
| 4 | Configure secrets, KV, and CORS | 20 min | Mack + Claude |
| 5 | Wire frontend to Worker (Items 5–7) | 45 min | Claude |
| 6 | End-to-end test & debug | 30 min | Mack + Claude |

**Total estimate: ~3–3.5 hours**

---

## Pre-flight checklist (Mack to confirm before session starts)

- [ ] Cloudflare account credentials available (or already logged in via `wrangler login`)
- [ ] Cassidy GSS workflow webhook URL on hand (needed as Worker secret)
- [ ] GitHub account `mackwallace` — confirm repo name: `gss-matcher` (or choose alternate)
- [ ] `wrangler` CLI installed? Check: `wrangler --version`. If not, Claude will install.

---

## Phase 1 — GitHub Repository

**Files to push:**

| File | Notes |
|------|-------|
| `gss-matcher-intake-v4.0.html` | Working intake form |
| `gss-matcher-loader-v3.0.html` | Working loader |
| `gss-matcher-results-v2.0.html` | Working results (merge layer embedded) |
| `ec-logo.png` | EC icon for page header |
| `ec-logo-full.png` | EC full logo for footer |
| `gss_display_v2.json` | Display lookup (also embedded in results v2.0) |
| `cf-worker/worker.js` | Cloudflare Worker (to be written in Phase 3) |
| `cf-worker/wrangler.toml` | Worker config (to be written in Phase 3) |
| `.gitignore` | Standard Node + Python ignores |

**Steps:**
1. Create repo `mackwallace/gss-matcher` via `gh repo create`
2. Init git, add files, commit, push to main

---

## Phase 2 — Cloudflare Pages

**Config:**
- Build command: *(none — static HTML files)*
- Output directory: `/` (root)
- Branch: `main` → auto-deploy on push

**Steps:**
1. In Cloudflare dashboard → Pages → Create project → Connect to Git
2. Select `mackwallace/gss-matcher` repo
3. Set output directory to `/` (no build step)
4. Deploy — Pages URL will be `gss-matcher.pages.dev` or similar
5. Note the Pages URL — needed for Worker CORS allowlist

---

## Phase 3 — Cloudflare Worker (`gss-matcher-proxy`)

**Worker responsibilities:**

| Endpoint | Method | What it does |
|----------|--------|--------------|
| `POST /` | Form submit | Generate sessionId → store `{status:'pending'}` in KV → fire Cassidy webhook (non-blocking) → return `{sessionId}` |
| `POST /receive` | Cassidy callback | Auth with Bearer token → parse Cassidy output → store `{status:'ready', data:{...}}` in KV |
| `GET /results/:sessionId` | Frontend poll | Return KV value (`pending` or `ready` with data) |

**Worker to be written by Claude:** `cf-worker/worker.js` — modeled on the Career Navigator proxy.

**wrangler.toml config:**
```toml
name = "gss-matcher-proxy"
main = "worker.js"
compatibility_date = "2024-01-01"

[[kv_namespaces]]
binding = "RESULTS_KV"
id = "PASTE_KV_ID_HERE"  # filled after Step 3b
```

**Steps:**
1. Claude writes `cf-worker/worker.js` and `cf-worker/wrangler.toml`
2. `wrangler kv:namespace create RESULTS_KV` → paste the returned ID into `wrangler.toml`
3. `cd cf-worker && wrangler deploy`
4. Note the Worker URL (e.g., `gss-matcher-proxy.mackwallace.workers.dev`)

---

## Phase 4 — Secrets, KV, CORS

**Secrets to set (Mack provides values, Claude runs commands):**
```bash
wrangler secret put CASSIDY_WEBHOOK_URL   # Mack's Cassidy GSS workflow webhook
wrangler secret put RECEIVE_API_KEY       # shared secret for /receive auth — generate a UUID
```

**CORS update:**  
Once Pages URL is known, update Worker CORS `allowedOrigins` to include:
- `https://gss-matcher.pages.dev` (or whatever Pages URL is)
- `http://localhost:5173` (for future React dev)
- `http://127.0.0.1:5173`

---

## Phase 5 — Frontend Wiring (Items 5–7 from delta)

Three targeted JS changes across the 3 HTML files:

### Item 5 — Intake form: POST to Worker (not mock)

**File:** `gss-matcher-intake-v4.0.html`  
**Change:** In the form submit handler, replace the mock loading overlay trigger with a real `fetch()` POST to the Worker URL. On 202 response, extract `sessionId` and navigate to the loader.

```js
// Current (mock):
showLoading();

// Replace with:
fetch('https://gss-matcher-proxy.mackwallace.workers.dev/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify(payload)
})
.then(r => r.json())
.then(data => {
  window.location.href = 'gss-matcher-loader-v3.0.html?session=' + data.sessionId;
})
.catch(() => { /* show error state */ });
```

### Item 6 — Loader: poll Worker for results

**File:** `gss-matcher-loader-v3.0.html`  
**Change:** On load, read `?session=` from URL params. Replace the `simTimer` demo mode trigger with real polling via `startLoaderLive(sessionId)` (function already exists in the loader — just needs to be called with the real sessionId instead of the demo timer).

```js
// On page load:
var params = new URLSearchParams(window.location.search);
var sessionId = params.get('session');
if (sessionId) {
  startLoaderLive(sessionId);  // real polling — already written
} else {
  startLoader(DEMO_DURATION);  // fallback to demo mode
}
```

**Also update:** `goToResults()` function to navigate to `gss-matcher-results-v2.0.html?session=` + sessionId.

### Item 7 — Results screen: accept Cassidy output

**File:** `gss-matcher-results-v2.0.html`  
**Change:** On load, read `?session=` from URL params. If present, fetch from Worker `GET /results/:sessionId`, pass `data.matches` through `mergeWithDisplay()`, then `renderCards()`. If no session param, fall back to mock RESULTS (demo mode).

```js
window.addEventListener('load', function() {
  renderHero();
  var params = new URLSearchParams(window.location.search);
  var sessionId = params.get('session');
  if (sessionId) {
    // Production: fetch real results from Worker
    fetch('https://gss-matcher-proxy.mackwallace.workers.dev/results/' + sessionId)
      .then(r => r.json())
      .then(function(response) {
        if (response.status === 'ready') {
          var merged = response.data.matches.map(mergeWithDisplay);
          merged.forEach(function(m){ SLUG_MAP[toSlug(m.school_name)] = m.school_name; });
          var sorted = merged.slice().sort(function(a,b){ return b.overall_score - a.overall_score; });
          renderHero(response.data.form_data); // if Worker passes form_data through
          renderCards(sorted);
          renderSummary(sorted);
        }
      });
  } else {
    // Demo mode: use mock RESULTS
    var merged = RESULTS.map(mergeWithDisplay);
    merged.forEach(function(m){ SLUG_MAP[toSlug(m.school_name)] = m.school_name; });
    var sorted = merged.slice().sort(function(a,b){ return b.overall_score - a.overall_score; });
    renderCards(sorted);
    renderSummary(sorted);
  }
});
```

**Note on formData:** The Worker should store `form_data` (first_name, research_interests, degree, career_goal) in the KV alongside the session so it can be returned with the results and used to personalize the hero section. If Worker doesn't store it, `formData` stays hardcoded as "Alex" for now.

---

## Phase 6 — End-to-End Test

**Test flow:**
1. Open `gss-matcher-intake-v4.0.html` (via Pages URL, not file://)
2. Fill and submit the form
3. Loader appears, shows pipeline animation
4. Cassidy processes → calls `/receive` → Worker stores results in KV
5. Loader poll detects `status: 'ready'` → navigates to results screen
6. Results screen shows real AI matches from Cassidy

**If Cassidy isn't ready for end-to-end testing:**  
Use the Worker's `/receive` endpoint manually to inject mock Cassidy output and test the full frontend flow independently.

```bash
curl -X POST https://gss-matcher-proxy.mackwallace.workers.dev/receive \
  -H "Authorization: Bearer <RECEIVE_API_KEY>" \
  -H "Content-Type: application/json" \
  -d @test-cassidy-response.json
```

---

## Key URLs (fill in during session)

| Item | URL |
|------|-----|
| GitHub repo | `https://github.com/mackwallace/gss-matcher` |
| Cloudflare Pages | TBD |
| Cloudflare Worker | TBD |
| Cassidy webhook | TBD (Mack provides) |

---

## Worker CORS allowed origins (update after Phase 2)

```js
var ALLOWED_ORIGINS = [
  'https://TBD.pages.dev',       // Cloudflare Pages URL (fill in)
  'http://localhost:5173',        // Vite dev (future React)
  'http://127.0.0.1:5173',
  'null',                         // file:// protocol for local HTML testing
];
```

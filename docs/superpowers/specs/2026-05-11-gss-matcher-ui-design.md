# GSS AI Matcher — v1 UI Design Spec

**Date:** 2026-05-11  
**Owner:** Mack Wallace / Enterprise Commons  
**Status:** Intake form complete at v3.0 · Results + Compare screens pending  
**Last updated:** 2026-05-11

## Build Status

| Screen | File | Status |
|--------|------|--------|
| Intake form | `gss-matcher-intake-v3.0.html` | ✅ Complete — approved |
| Loading overlay | Embedded in intake form | ✅ Complete |
| Results screen | `gss-matcher-results-v1.0.html` | 🔲 Not yet built |
| Compare view | Embedded in results screen | 🔲 Not yet built |
| Cloudflare Worker | `cf-worker/worker.js` | 🔲 Not yet deployed |

## Intake Form Change Log

**v1.0 → v2.0:**
Section labels humanized (Tell Us About You / Your Research & Goals / Strengthen Your Match / What Matters Most to You). Career goal moved to 2nd field in S2. Profile enrichment (LinkedIn/CV) moved before sliders. Google Scholar URL added. "Must stay local" reveals city/state fields. Location label updated. "No preference" approach locks others. Confidentiality banner added. CTA timing updated to "up to 2 minutes". Step indicator added. Hero text widened.

**v2.0 → v3.0:**
EC logo (open book) replaces navy EC block — loaded from local `ec-logo.png`. GSS logo replaced with SVG wordmark (session-gated external URL doesn't load from file://). Hover interactions added throughout (cards lift, option cards lift with shadow, step dots scale/fill, inputs steel border on hover, slider thumbs scale). "Still exploring / Other" career goal reveals free-text detail box. CV helper text moved above textarea. Sliders made fully interactive with live color-coded labels. Confidentiality notice moved below CTA (lighter styling). Footer added (EC navy, © 2026 Enterprise Commons, Privacy Notice, Terms of Use).

**Reference docs:**
- `Intake Form Fields - v1.md` — 14-field form spec (field IDs, validation, Cassidy wiring)
- `design-system-prototype-2026-05-06.md` — brand tokens, component specs, do/don't
- `GSS_Prototype_PRD_v0.1.md` — product requirements, scoring engine, match card wireframes
- `kb/` — 113 school markdown files (Cassidy knowledge base, already built)

---

## 1. Goal

Build a v1 prototype web app that:
1. Collects a student's physics grad program preferences via a 14-field intake form
2. POSTs the payload to a Cloudflare Worker, which fires the Cassidy AI matching engine
3. Displays ranked match results with scores, AI explanations, and program data in-browser
4. Allows side-by-side comparison of 2–4 programs
5. Supports a live client demo of the GradSchoolShopper AI Matcher concept

Cassidy handles email delivery of results independently. The frontend is display-only.

---

## 2. Architecture & Data Flow

```
┌─────────────────┐     POST /          ┌──────────────────────┐
│  Cloudflare     │ ─────────────────── │  Cloudflare Worker   │
│  Pages (React)  │ ◄── {sessionId} ─── │  gss-matcher-proxy   │
│                 │                     │                      │
│  polls every 3s │ ── GET /results/:id │  KV: RESULTS_KV      │
│                 │ ◄── {status,data} ── │                      │
└─────────────────┘                     └──────────┬───────────┘
                                                   │ ctx.waitUntil (non-blocking)
                                                   ▼
                                         ┌─────────────────┐
                                         │  Cassidy        │
                                         │  AI Workflow    │
                                         │                 │
                                         │  POST /receive  │
                                         │  (on complete)  │
                                         └─────────────────┘
```

**Request lifecycle:**
1. User submits form → frontend POSTs to Worker `POST /`
2. Worker generates `sessionId`, stores `{status: 'pending'}` in KV (2hr TTL), fires Cassidy webhook non-blocking via `ctx.waitUntil`, returns `{sessionId}` (202)
3. Frontend transitions to Loading screen, begins polling `GET /results/:sessionId` every 3 seconds
4. Cassidy workflow completes → POSTs results to Worker `POST /receive` (Bearer auth)
5. Worker stores `{status: 'ready', data: {...}}` in KV
6. Frontend poll detects `status: 'ready'` → transitions to Results screen
7. Cassidy sends email to student independently (no frontend involvement)
8. Poll timeout: 3 minutes → show error state with retry option

**Payload note:** Field 13 (`intake-school-data`) sends the full `gss_programs.json` (~277KB serialized) in every request. This is intentional per the PRD — Agent 1 scores all 113 schools from this payload. If Cassidy imposes payload size limits, this field should be migrated to a Cassidy-side knowledge base reference in a future iteration.

---

## 3. Tech Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | React 18 + Vite | Component model handles complex UI state; Vite gives fast DX |
| Styling | Tailwind CSS v3 | Utility-first; rapid prototyping; aligns with Career Navigator precedent |
| State | React `useState` / `useEffect` | No Redux needed — state is shallow and local to App |
| API proxy | Cloudflare Worker (new) | Same proven pattern as Career Navigator; same ecosystem as Pages |
| Hosting | Cloudflare Pages | Auto-deploys from GitHub; zero config with Vite; same account as Worker |
| Fonts | Google Fonts (Rubik + Roboto) | Per design system |

---

## 4. Repository & File Structure

**GitHub repo:** `mackwallace/gss-matcher` (new, public)

```
gss-matcher/
├── index.html
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
├── package.json
├── .gitignore
├── public/
│   ├── favicon.ico               ← GSS favicon (from design system assets)
│   └── gss-logo.png              ← GSS logo (from design system assets)
├── src/
│   ├── main.jsx                  ← React root, mounts App
│   ├── App.jsx                   ← Screen state machine + polling logic
│   ├── api.js                    ← submitForm() and pollResults() fetch wrappers
│   ├── data/
│   │   └── gss_programs.json     ← Imported at build time; injected into form payload
│   ├── screens/
│   │   ├── IntakeScreen.jsx      ← 14-field form, 4 sections
│   │   ├── LoadingScreen.jsx     ← Polling UI, pipeline visualization
│   │   ├── ResultsScreen.jsx     ← Filter sidebar + match card list
│   │   └── CompareScreen.jsx     ← Side-by-side comparison table
│   └── components/
│       ├── SpecialtyChips.jsx    ← Chip grid from JSON taxonomy (show 20 / show all)
│       ├── MatchCard.jsx         ← Collapsed + expanded states
│       ├── ScoreBadge.jsx        ← Circular score (count-up animation on load)
│       ├── ReachBadge.jsx        ← Reach / Match / Safety pill
│       ├── ScoreBar.jsx          ← Horizontal score bar for expanded card breakdown
│       ├── FilterSidebar.jsx     ← Filter controls for results screen
│       └── CompareTable.jsx      ← Full-width sticky-column comparison table
└── cf-worker/
    ├── worker.js                 ← Cloudflare Worker (gss-matcher-proxy)
    └── wrangler.toml
```

---

## 5. App State (App.jsx)

Single top-level state object managed with `useState`. No routing — screen transitions are state changes.

```js
// Screen state machine
screen: 'intake' | 'loading' | 'results' | 'compare'

// Form submission
sessionId: string | null   // null pre-submit; set from Worker's 202 response body {sessionId}
                           // Worker generates sessionId server-side (same as Career Navigator)
formData: object           // Captured on submit; used to display context line on results screen

// Results
results: Match[]           // Array of match objects from Cassidy (see Section 8)
pollError: string | null   // Set if poll times out or returns error

// Results screen controls
filters: {
  reachTypes: string[]     // ['Reach', 'Match', 'Safety'] — all on by default
  campusSetting: string[]  // ['Urban', 'Suburban', 'Rural'] — all on by default
  degreeType: string       // 'Any' | 'PhD' | 'Masters'
  specialty: string        // Free-text filter against matching_specialties
}
sortBy: 'score' | 'research_fit' | 'acceptance_rate'

// Compare
compareList: string[]      // school_names selected for compare; max 4
```

---

## 6. Cloudflare Worker — `gss-matcher-proxy`

New worker, modeled exactly on Career Navigator's `cn-career-navigator-proxy`. Three endpoints:

### POST /
Accepts the form payload. Generates `sessionId`, injects it, stores `pending` in KV, fires Cassidy non-blocking, returns `{sessionId}`.

CORS allowed origins:
- Cloudflare Pages URL (set once Pages is deployed)
- `http://localhost:5173` (Vite dev server)
- `http://127.0.0.1:5173`

Rate limit: 20 submissions / IP / hour (same as Career Navigator).

### POST /receive
Cassidy calls this when the workflow completes. Requires `Authorization: Bearer <RECEIVE_API_KEY>`. Parses the response body (handles Cassidy's JSON-encoded-string wrapping), writes `{status: 'ready', data}` to KV keyed by `session-id`.

### GET /results/:sessionId
Frontend polling endpoint. Returns KV value directly (`{status: 'pending'}` or `{status: 'ready', data: {...}}`). Returns `{status: 'not_found'}` (404) if session expired or never created.

**Worker secrets (set via Wrangler):**
- `CASSIDY_WEBHOOK_URL` — Mack's Cassidy GSS workflow webhook URL
- `RECEIVE_API_KEY` — shared secret for `/receive` auth

**KV binding:** `RESULTS_KV` (new namespace, created via Wrangler)

---

## 7. Screen-by-Screen Specification

### Screen 1 — Intake Form (`IntakeScreen.jsx`)

**Layout:** Centered single column, max-width 600px. Mint gradient header strip (`linear-gradient(180deg, #F0FAF5 0%, #FFFFFF 120px)`).

**Header:**
- GSS logo (top-left)
- H1 (Rubik bold, 40px): "Find your physics program."
- Subhead (Roboto, slate, 18px): "Answer a few questions and we'll match you to programs where you'll thrive."
- Progress hint: "Takes about 2 minutes"

**Section 1 — Identity**
- First Name (text input, required)
- Last Name (text input, required)
- Email (email input, required) — labeled "Your results will be sent here"

**Section 2 — Core Matching**
- **Degree goal** (Field 4): Three option cards (pill buttons) — PhD / Master's / Either. Inactive: border only. Active: `--color-mint-light` fill + `--color-primary` border.
- **Research interests** (Field 5): `<SpecialtyChips />` — renders top 20 most common specialties as selectable chips by default, "Show all specialties (+180)" expansion. Multi-select. Minimum 1 required. Chip values read directly from `gss_programs.json` `specialty_taxonomy` array — never hardcoded. Selected chips use mint fill.
- **Research approach** (Field 6): Four checkboxes — Experimental / Theoretical / Computational / No preference. Optional.
- **Location flexibility** (Field 7): Three radio options. "Specific region" reveals a second-level radio: Northeast / Southeast / Midwest / Southwest / West Coast / Pacific Northwest.
- **Student status** (Field 8): Three radio options.
- **Career goal** (Field 9): Dropdown, 6 options.

**Section 3 — Preferences (decorative)**
Five sliders (1–5). Labeled with: *"In the full system, these drive your personalized weights."* Grayed out visually to signal non-interactive intent. Not included in API payload.

**Section 4 — Profile Enrichment (optional)**
- LinkedIn URL (text input, optional) — hint: "https://www.linkedin.com/in/yourname"
- CV / Resume (textarea, optional) — hint: "Paste plain text. Max ~3,000 words." Character counter shown.

**CTA:** Full-width primary button — "Find My Programs →" (disabled until required fields complete).

**On submit:**
1. Validate required fields client-side. Show inline errors on missing.
2. Build payload per intake form spec. Inject `gss_programs.json` as JSON string (`intake-school-data`). Do NOT include `session-id` — Worker generates it server-side and injects it before forwarding to Cassidy.
3. POST to Worker. On 202 response, store `sessionId` from response body in state. Transition to Loading screen.

---

### Screen 2 — Loading (`LoadingScreen.jsx`)

**Layout:** Centered, vertically centered in viewport.

**Content:**
- GSS logo
- H2 (Rubik): "Finding your matches..."
- Animated 3-stage pipeline (same pattern as Career Navigator):
  - Stage 1: "Building your profile" → active → complete
  - Stage 2: "Scoring 113 programs" → active → complete
  - Stage 3: "Writing your explanations" → active → complete
- Stages auto-advance on a timer (15s / 30s / remainder) regardless of actual Cassidy progress — purely cosmetic
- Subtle "This usually takes 30–60 seconds" note

**Polling:** `useEffect` starts interval (3s) on mount. On `status: 'ready'` → transition to Results. On 3-minute timeout → show error state: "Something took longer than expected. [Try again]" (resets to Intake with form data preserved).

---

### Screen 3 — Results (`ResultsScreen.jsx`)

**Layout:** Two-column desktop. `FilterSidebar` fixed left (240px). Match cards scrollable right column.

**Header bar:**
- Left: "Your Top Matches" (Rubik, 28px)
- Context line: "Matching for: [research interests] · [degree] · [career goal]" — built from `formData`
- Right: Sort tabs — "Best Match | Research Fit | Acceptance Rate"

**Filter Sidebar (`FilterSidebar.jsx`):**
- Section: Admissions Fit — Reach / Match / Safety toggles (all on by default, mint when active)
- Section: Campus Setting — Urban / Suburban / Rural checkboxes
- Section: Degree Type — Any / PhD / Master's radio
- Section: Specialty — text input that filters against each card's `matching_specialties`
- "Clear filters" link at bottom

**Match Card list:**
- Rendered from `results` array, filtered and sorted per active state
- 16px gap between cards
- Top 3 cards get `--shadow-sm` elevation treatment
- "+ Add to Compare" checkbox on each card (disabled + tooltip "Max 4 programs" when compareList.length === 4)
- Floating "Compare Selected (N) →" button appears when compareList.length >= 2

**`MatchCard.jsx` — Collapsed state:**
```
┌─────────────────────────────────────────────────────┐
│  [ScoreBadge 87]  Brown University    [● Match]      │
│                   Physics · Providence, RI · Urban   │
│                                                      │
│  Condensed Matter · Biophysics · High Energy (+2)   │
│                                                      │
│  "Strong match for condensed matter research with   │
│   both experimental and theoretical tracks..."      │
│                                                      │
│  Acceptance: 15% · Deadline: Dec 15 · PhDs/yr: 18  │
│                                                      │
│  [☐ Add to Compare]              [View Details ▼]   │
└─────────────────────────────────────────────────────┘
```

**`MatchCard.jsx` — Expanded state (clicking "View Details"):**
```
Score Breakdown:
  Research Fit          92  ████████████░
  Admissions Feasibility 70  █████████░░░
  Program Activity       85  ███████████░
  Location Match         80  ██████████░░
  Degree Structure Fit   95  ████████████

Why This Matches You:
  [AI-generated 2–3 sentence explanation from Cassidy]

Faculty:
  [Placeholder block — "Faculty data not yet available.
   View department website for current faculty listings."]

Funding:
  [Placeholder block — "Funding data not yet available.
   See program page for stipend and funding details."]

[View Program on GradSchoolShopper →]   (opens in new tab)
```

---

### Screen 4 — Compare (`CompareScreen.jsx`)

**Trigger:** "Compare Selected (N) →" floating button.

**Layout:** Full-width. Programs as columns (2–4), attributes as sticky-left-column rows.

**Header:** "← Back to Results" link (top-left). "Compare Programs" title.

**Table rows:**

| Attribute | School A | School B | School C |
|-----------|---------|---------|---------|
| Overall Score | 87/100 | 91/100 | 78/100 |
| Reach/Match/Safety | Match | Reach | Match |
| Matching Specialties | Condensed Matter, Biophysics | Condensed Matter, Quantum | Condensed Matter |
| Research Approach | Both | Both | Experimental |
| Acceptance Rate | 15% | 4% | 12% |
| Application Deadline | Dec 15 | Dec 15 | Dec 1 |
| Campus Setting | Urban | Urban | Suburban |
| PhD Granted (2024) | 18 | — | 12 |
| First Year Enrollment | 11 | — | 9 |
| Faculty | Placeholder | Placeholder | Placeholder |
| Funding | Placeholder | Placeholder | Placeholder |
| GSS Profile | [Link] | [Link] | [Link] |

Best value per row: subtle mint left-border highlight.

Note at bottom: *"Faculty and funding data will be populated in the full system."*

---

## 8. Cassidy Output Schema (expected)

Per PRD Section 8.3. Frontend expects `data.matches` — array of objects:

```json
{
  "matches": [
    {
      "school_name": "Brown University",
      "department": "Physics",
      "location": "Providence, RI",
      "campus_setting": "Urban",
      "overall_score": 87,
      "reach_match_safety": "Match",
      "matching_specialties": ["Condensed Matter Physics", "Biophysics"],
      "score_breakdown": {
        "research_fit": 92,
        "admissions_feasibility": 70,
        "program_activity": 85,
        "location_match": 80,
        "degree_structure_fit": 95
      },
      "explanation": "...",
      "acceptance_rate": "15%",
      "phd_granted_2024": 18,
      "application_deadline": "Dec 15",
      "school_profile_url": "https://gradschoolshopper.com/browse/brown-university.html"
    }
  ]
}
```

If Cassidy's actual output schema differs, `api.js` should normalize the response to this shape before setting state.

---

## 9. Deployment

### Cloudflare Worker
1. `cd cf-worker && wrangler deploy`
2. Set secrets: `wrangler secret put CASSIDY_WEBHOOK_URL` and `wrangler secret put RECEIVE_API_KEY`
3. Create KV namespace: `wrangler kv:namespace create RESULTS_KV` → paste binding ID into `wrangler.toml`
4. Update Worker CORS allowed origins once Pages URL is known

### Cloudflare Pages
1. Connect GitHub repo `mackwallace/gss-matcher` in Cloudflare Pages dashboard
2. Build command: `npm run build`
3. Build output directory: `dist`
4. Auto-deploys on every push to `main`

### Environment variables
No environment variables needed in the React app — the Worker URL is the only external dependency. Hardcode the Worker URL as a constant in `api.js` (not an env var) for prototype simplicity.

---

## 10. Design System Reference

All visual decisions follow `design-system-prototype-2026-05-06.md`. Key tokens:

| Token | Value | Use |
|-------|-------|-----|
| `--color-primary` | `#77C999` | CTAs, active chips, score badges, match badge |
| `--color-text-primary` | `#3E455E` | All body text |
| `--color-surface` | `#F7F9FC` | Card backgrounds |
| `--color-reach` | `#F59E0B` | Reach badge |
| `--color-safety` | `#A1B3C9` | Safety badge |
| `--font-heading` | Rubik | H1–H4, score badge number |
| `--font-body` | Roboto | All other text |
| Button radius | 4px | Square — matches GSS brand |
| Card radius | 12px | Match cards, panels |

Animations: score badge count-up (600ms), card staggered entrance (50ms delay each), card hover `translateY(-2px)`. No looping animations.

---

## 11. Out of Scope (v1)

- User accounts or saved lists
- Email delivery (Cassidy handles this)
- Mobile optimization (desktop demo only)
- Adaptive preference refinement
- Real faculty or funding data (placeholder blocks only)
- URL routing / deep links to results
- PDF export of compare view
- Analytics or event tracking

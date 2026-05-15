# GSS AI Engine — Output Schema & Results Population Guide
**Version:** 1.2  
**Owner:** Mack Wallace / Enterprise Commons  
**For:** Cassidy AI engine builder + Claude Code frontend  
**Last updated:** 2026-05-15

### Changelog
| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-05-14 | Initial document |
| 1.1 | 2026-05-14 | Added merge layer, frontend wiring |
| 1.2 | 2026-05-15 | Location match now dynamic (Agent 1 v1.2); added two-JSON-file section; added form_data source; added coverage numbers; updated scoring weights |

---

## Governing Principle

> **Factual data must come directly from the university KB markdown files whenever available. AI-generated content is reserved for scored outputs and narrative explanations only.**

Fabricating factual data (acceptance rates, faculty, stipends, deadlines) is not acceptable. If a field is not in the KB file, surface the absence explicitly rather than inferring a value.

---

## The Two JSON Files

Two separate JSON files power the results screen. They serve different purposes and are read by different systems.

| File | Read by | Purpose |
|------|---------|---------|
| `gss_scoring_v2.json` | **Cassidy Agent 1** (inside workflow) | Scoring input — contains all fields Agent 1 needs to compute scores: `acceptance_rate_decimal`, `offers_phd`, `offers_masters`, `specialties`, `specialty_details`, `phd_granted_2024`, `first_year_enrollment_fall2024`, `region`, `city`, `state` |
| `gss_display_v2.json` | **Results screen frontend** (embedded inline as `GSS_DISPLAY`) | Display lookup — contains all fields the results screen needs to render cards: `department`, `location`, `region`, `campus_setting`, `acceptance_rate` (string), `application_deadline`, `faculty_count`, all URL fields |

**These files do not overlap in the frontend.** `gss_scoring_v2.json` never touches the browser. `gss_display_v2.json` is embedded directly in `gss-matcher-results-v2.0.html` and never sent to Cassidy.

**`gss_display_v2.json` field coverage (113 schools total):**

| Field | Coverage |
|-------|----------|
| `department`, `location`, `region`, `campus_setting`, `faculty_count` | 113/113 |
| `faculty_url` | 99/113 |
| `grad_url` | 86/113 |
| `gss_url` | 83/113 |
| `dept_url` | 60/113 |
| `funding_url` | 20/113 |

---

## Full Data Flow

```
[Intake Form]
    │ POST payload (student profile only — no school data)
    ▼
[Cloudflare Worker — gss-matcher-proxy]
    │ generates sessionId, stores form_data in KV, fires Cassidy webhook
    ▼
[Cassidy Workflow]
    │
    ├─ Agent 1 (GSS Match Scorer v1.2)
    │    reads: student_profile + gss_scoring_v2.json
    │    outputs: ranked_schools (scores + matching_specialties per school)
    │
    ├─ Agent 2 (Match Explainer)
    │    reads: student_profile + Agent 1 output + KB markdown files
    │    outputs: why field per school
    │
    └─ Response Assembler
         outputs: matches array + metadata
         POSTs to Worker /receive with session_id
              │
              ▼
[Cloudflare Worker — /receive]
    │ stores {status:'ready', data, form_data} in KV
    ▼
[Results Screen — polling GET /results/:sessionId]
    │
    ├─ response.form_data → hero section (Jordan's name, interests, degree, career goal)
    │
    └─ response.data.matches → mergeWithDisplay()
         ├─ AI fields from Cassidy: overall_score, score_breakdown, matching_specialties, why
         └─ Display fields from GSS_DISPLAY (gss_display_v2.json): all factual/link fields
              │
              ▼
         renderCards() + renderSummary()
              │
              ▼
         Frontend derives: selectivity badge, qualitative labels, Summary & Next Steps
```

---

## Source Map — Every Field on the Results Screen

### Source 1 — Cassidy AI output (`response.data.matches`)

| Field | Agent | Notes |
|-------|-------|-------|
| `overall_score` | Agent 1 | Weighted composite 0–100, rounded to nearest integer |
| `matching_specialties` | Agent 1 | Intersection of student interests + school specialties array |
| `score_breakdown.research_fit` | Agent 1 | Specialty overlap + approach bonus (max +10) |
| `score_breakdown.admissions_feasibility` | Agent 1 | Derived from `acceptance_rate_decimal` in `gss_scoring_v2.json` |
| `score_breakdown.program_activity` | Agent 1 | Derived from `phd_granted_2024` + `first_year_enrollment_fall2024` |
| `score_breakdown.location_match` | Agent 1 | **Dynamic as of v1.2** — scores against `region`/`city`/`state` in `gss_scoring_v2.json` vs student's `intake-location-flexibility` |
| `score_breakdown.degree_structure_fit` | Agent 1 | `offers_phd` / `offers_masters` vs student's `intake-degree-goal` |
| `why` | Agent 2 | 2–3 sentence explanation. Also sent as `match_explanation` — frontend normalises via `mergeWithDisplay()` |

### Source 2 — `gss_display_v2.json` (embedded as `GSS_DISPLAY`, looked up by `school_name`)

Display lookup takes priority over any Cassidy-supplied value for these fields in `mergeWithDisplay()`.

| Field | KB Source | Coverage |
|-------|-----------|----------|
| `school_name` | KB frontmatter: `school_name` | 113/113 |
| `abbr` | Known abbreviations map (build script) | Partial |
| `department` | KB body: `**Department:**` | 113/113 |
| `location` | KB frontmatter: `city` + `state` → `"City, ST"` | 113/113 |
| `region` | KB frontmatter: `region` | 113/113 |
| `campus_setting` | KB frontmatter: `campus_setting` | 113/113 |
| `acceptance_rate` | KB frontmatter: `acceptance_rate_decimal` → `"N%"` string | 113/113 |
| `application_deadline` | KB frontmatter: `application_deadline` | 113/113 |
| `phd_granted_2024` | KB frontmatter: `phd_granted_2024` | 113/113 |
| `ms_granted_2024` | KB frontmatter: `ms_granted_2024` | 113/113 |
| `faculty_count` | KB frontmatter: `faculty_count_research` (prefer) or `faculty_count_total` | 113/113 |
| `gss_url` | KB Key Links: `[GSS Profile]` | 83/113 |
| `grad_url` | KB Key Links: `[Graduate Studies Overview]` / `[Application Process]` | 86/113 |
| `dept_url` | KB Key Links: `[Department Website]` | 60/113 |
| `faculty_url` | KB Key Links: `[Faculty Directory]` | 99/113 |
| `funding_url` | KB Key Links: `[Financial Assistance]` | 20/113 |

### Source 3 — Worker session `form_data` (`response.form_data`)

Stored at form submission time, returned alongside match results. Used only to personalise the hero section of the results screen.

| Field | Used for |
|-------|----------|
| `first_name` | Hero heading: "Jordan's Top Matches" |
| `research_interests` | Context chips row |
| `degree` | Context chips row |
| `career_goal` | Context chips row |

### Derived by frontend (no external source)

| Field | How |
|-------|-----|
| Selectivity badge | `selectivity(acceptance_rate)` — JS thresholds (< 8% → Highly Selective, etc.) |
| Score qualitative labels | `qualLabel(key, value)` — e.g. 92 → "Exceptional" |
| Summary & Next Steps | `generateSummary()` — synthesises full merged results array using GSS brand voice |

---

## Cassidy Output Structure (what arrives at Worker `/receive`)

```json
{
  "event_type": "match_results_generated",
  "session_id": "UUID",
  "generated_at": "ISO timestamp",
  "workflow_run_id": "string",
  "matches": [ ...array of match objects... ],
  "metadata": { ... }
}
```

The Worker stores `response.data = full body` in KV. The frontend reads `response.data.matches`.

**Note on field name:** Cassidy may return the explanation as `match_explanation`. `mergeWithDisplay()` normalises this: `record.why = match.why || match.match_explanation || ''`

---

## Agent 1 Output Schema (per school in `ranked_schools`)

Agent 1 returns `ranked_schools`. The Response Assembler renames this to `matches` and enriches with Agent 2 output. Each school object from Agent 1 contains:

| Field | Type | Notes |
|-------|------|-------|
| `school_name` | string | |
| `acceptance_rate_decimal` | float or null | Raw decimal from `gss_scoring_v2.json` |
| `phd_granted_2024` | integer or null | |
| `first_year_enrollment_fall2024` | integer or null | |
| `offers_phd` | boolean | |
| `offers_masters` | boolean | |
| `specialties` | string[] | All specialties for the school |
| `overall_score` | integer 0–100 | |
| `matching_specialties` | string[] | Subset that matched student interests |
| `score_breakdown` | object | 5 dimension scores |
| `data_flags.missing_acceptance_rate` | boolean | |
| `data_flags.missing_enrollment_data` | boolean | |

Display fields (`department`, `campus_setting`, `acceptance_rate` string, `application_deadline`, URLs) are **not** in Agent 1 output — they come from `gss_display_v2.json` via the frontend merge layer.

---

## Scoring Weights (Agent 1 v1.2 — fixed)

| Dimension | Weight | Scoring Input (`gss_scoring_v2.json`) | Status |
|-----------|--------|---------------------------------------|--------|
| Research Fit | 35% | `specialties`, `specialty_details` | ✅ Dynamic |
| Admissions Feasibility | 20% | `acceptance_rate_decimal` | ✅ Dynamic |
| Program Activity | 15% | `phd_granted_2024`, `first_year_enrollment_fall2024` | ✅ Dynamic |
| Location Match | 15% | `region`, `city`, `state` vs `intake-location-flexibility` | ✅ Dynamic as of v1.2 |
| Degree Structure Fit | 15% | `offers_phd`, `offers_masters` | ✅ Dynamic |

**Note:** `preferences-weights` from the intake form are passed through in the payload but **explicitly ignored by Agent 1 v1.2**. Fixed weights apply to all students.

---

## Qualitative Label Mapping (Frontend Display)

### Research Fit, Program Activity, Location Match, Degree Fit

| Score | Label |
|-------|-------|
| 90–100 | Exceptional |
| 80–89 | Very Strong |
| 70–79 | Strong |
| 60–69 | Good |
| < 60 | Developing |

### Admissions Feasibility (higher = more accessible)

| Score | Label |
|-------|-------|
| 80+ | Accessible |
| 65–79 | Competitive |
| 45–64 | Highly Competitive |
| < 45 | Most Selective |

---

## Selectivity Badge (Frontend Display)

Derived from `acceptance_rate` string at render time. Not a field from Cassidy.

| Acceptance Rate | Badge |
|-----------------|-------|
| < 8% | Highly Selective |
| 8–14% | Selective |
| 15–21% | Moderately Selective |
| 22%+ | Accessible |
| null / not listed | Not Listed |

---

## KB Coverage Tiers

| Tier | Count | What's Available |
|------|-------|-----------------|
| Full profile | 41 schools | All frontmatter + About text + Program Requirements + Faculty table + Funding + International Students + Key Links |
| Directory-only | 67 schools | Frontmatter fields only — no About text, no GRE data |
| No URL | 5 schools | Frontmatter only; no GSS URL |

For directory-only schools: `why` must rely on structured frontmatter fields only — do not invent department descriptions. `faculty_url`, `funding_url`, `dept_url` will typically be `null`.

**Placeholder text in results UI:**
- Faculty (null): *"Faculty listings not yet available. View the department website for current faculty."*
- Funding (null): *"Funding information not yet available. See the program page for stipend and fellowship details."*

---

## Summary & Next Steps (Frontend-Generated)

The "Summary & Next Steps" section is generated entirely by `generateSummary()` in the results screen JS. The engine does not return this — it is synthesised from the full merged `matches` array using the GSS brand voice (neutral, direct, data-grounded, no hype). No AI generation required.

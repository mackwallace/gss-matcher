# GradSchoolShopper AI Matching Engine — Prototype PRD
**Version:** 0.1 (Prototype Scope)
**Date:** 2026-05-06
**Owner:** Mack Wallace / Enterprise Commons
**Audience:** Claude Code (front-end build), Cassidy AI agent (matching engine)
**Purpose:** Internal reference for building an illustrative prototype to support a client pitch. This is NOT a production PRD. It is a scaffolded demo that shows the full UX flow using available data, with clearly marked placeholders for data that would be populated in a production build.

---

## 1. PROTOTYPE GOAL

Build a single-page web application that demonstrates an AI-powered graduate program matching engine layered on top of GradSchoolShopper's existing directory. The prototype must show:

1. A **student intake form** (preference collection)
2. A **ranked results screen** with AI-generated match scores and explanations
3. An **expandable match card** with key program data + placeholder faculty/funding data
4. A **compare view** for side-by-side program comparison

The prototype does NOT need to be production-ready. It needs to be convincing enough to let a client executive say "I get it — I want this."

---

## 2. DATA MODEL

### 2.1 Available Data (from GSS Advanced Program Details spreadsheet)

Each row in the spreadsheet is a **program-specialty combination** for a given school. Multiple rows per school = multiple specialties. The following fields are available and usable in the prototype:

| Field | Column Name | Notes |
|-------|-------------|-------|
| School name | `School Name` | e.g., "Brown University" |
| Department | `Department` | e.g., "Physics", "Physics & Astronomy" |
| Specialty | `Program Specialty` | e.g., "Condensed Matter Physics" — this is the subfield |
| PhD type | `PhD (Theoretical/Experimental)` | Values: Both, Theoretical, Experimental, None |
| Master's type | `Master (Final Degree/Enroute to PhD)` | Values: Both, Final Degree, Enroute to PHD, None |
| Campus setting | `Campus Setting` | Values: Urban, Suburban, Rural |
| Acceptance rate | `Overall Acceptance Rate` | e.g., "15%", "33%", "N/A" |
| Application deadline | `Application Due Date` | e.g., "15-Dec" |
| MS granted 2024 | `Prof/Term MS Granted Class of 2024` | integer or blank |
| PhD granted 2024 | `PhD Granted Class of 2024` | integer or blank |
| First year enrollment | `First Year GS Enroll Fall 2024` | integer |
| Total enrollment | `Total GS Enroll Fall 2024` | integer |
| School profile URL | `School Profile` | Link to gradschoolshopper.com program page |

**Pre-processing note for Claude Code:** The spreadsheet has multiple rows per school (one per specialty). Before rendering match cards, aggregate rows by school so each match card = one school with a list of its matching specialties.

### 2.2 Placeholder Data (not in spreadsheet — would be scraped/queried in production)

The following fields are NOT in the spreadsheet. In the prototype, render them as styled placeholder blocks with a tooltip or footnote explaining how they'd be populated:

| Field | Placeholder Text | Production Source |
|-------|-----------------|-------------------|
| Annual stipend | `$[Stipend data — scraped from program page]` | Scraped from gradschoolshopper.com program page or department website |
| Cost-of-living adjusted stipend | `[CoL-adjusted value — calculated]` | Stipend + city CoL index (e.g., MIT/BLS data) |
| Funding type | `[TA / RA / Fellowship — scraped]` | Program page |
| Faculty matches | `[Faculty data — retrieved via web query]` | Web search: "[School] [Department] [Subfield] faculty" |
| Advisor availability | `[Advisor availability — not yet available]` | Future: crowdsourced or scraped from faculty pages |
| International student % | `[International student data — scraped]` | Program page |
| Time to degree (median) | `[Time-to-degree — scraped]` | Program page |
| Career outcomes | `[Placement data — scraped]` | Program page |

---

## 3. STUDENT INTAKE FORM

The intake form is the first screen. It collects the minimum required inputs to run a match. Keep it to 6 fields for the prototype.

### 3.1 Required Fields

| # | Field Label | Input Type | Options / Notes |
|---|-------------|------------|-----------------|
| 1 | What degree are you pursuing? | Radio | PhD / Master's / Either |
| 2 | What are your primary research interests? | Multi-select chips | Use the GSS specialty taxonomy — show top 20 most common, with "show more" option. Pre-populated list from spreadsheet specialties. |
| 3 | What research approach do you prefer? | Multi-select checkbox | Experimental / Theoretical / Computational / No preference |
| 4 | Where are you located or willing to relocate? | Radio + optional region picker | Anywhere in US / Specific region / Must stay local |
| 5 | Are you a domestic or international student? | Radio | US Citizen/Permanent Resident / International Student / Prefer not to say |
| 6 | What is your primary career goal? | Single select dropdown | Academic research / National lab / Industry R&D / Data science/Tech / Teaching / Exploring |

### 3.2 Optional (prototype can show but not require)

| # | Field Label | Input Type |
|---|-------------|------------|
| 7 | Importance sliders | Sliders (1–5) for: Research fit / Funding / Location / Prestige / Career outcomes |

### 3.3 Intake UX Notes

- Show a progress indicator (e.g., "Step 1 of 1 — takes about 60 seconds")
- Use a clean card-based layout, one question per visual block
- CTA button: "Find My Programs →"
- On submit, show a loading state: "Matching you to programs..." (even if instant — this signals AI)

---

## 4. MATCHING ENGINE

### 4.1 How Matching Works (for the Cassidy AI agent)

The matching engine receives the student's intake form responses and the program dataset, and returns a ranked, scored list of schools with explanations.

**Input to agent:**
```json
{
  "degree_goal": "PhD",
  "research_interests": ["Condensed Matter Physics", "Quantum Information"],
  "research_approach": ["Experimental"],
  "location_flexibility": "Anywhere in US",
  "student_status": "Domestic",
  "career_goal": "Academic research",
  "weights": {
    "research_fit": 5,
    "funding": 3,
    "location": 2,
    "prestige": 2,
    "career_outcomes": 3
  }
}
```

**Data context passed to agent:**
The aggregated program dataset (by school), with each school's specialties, PhD/MS availability, campus setting, acceptance rate, enrollment size, and deadline.

### 4.2 Scoring Dimensions (Simplified for Prototype)

The prototype uses 5 scoring dimensions. Each is scored 0–100. Final score = weighted average.

| Dimension | Weight (default PhD) | How Scored in Prototype |
|-----------|---------------------|------------------------|
| Research Fit | 35% | # of matching specialties / total specialties offered; bonus if research approach (exp/theory) aligns |
| Admissions Feasibility | 20% | Acceptance rate → Low (<15% = Reach), Mid (15–35% = Match), High (>35% = Safety) |
| Program Size & Activity | 15% | PhD granted 2024 + first year enrollment as proxy for program vitality |
| Location Match | 15% | Campus setting (Urban/Suburban/Rural) vs. preference; region match if specified |
| Degree Structure Fit | 15% | PhD available + type (Both/Theo/Exp) matches student preference |

**Note for Cassidy agent:** Use the above scoring logic to compute a 0–100 composite score per school, then rank. Also generate a 2–3 sentence natural language explanation of why each school matches — this is the "Why this matches you" text shown on the match card.

### 4.3 Reach / Match / Safety Classification

Based on acceptance rate only (prototype simplification):
- **Reach:** < 15% acceptance rate
- **Match:** 15%–35% acceptance rate
- **Safety:** > 35% acceptance rate (or N/A = unclassified)

In production, this would be a multi-dimensional feasibility score. Indicate this with a footnote: "In the full system, Reach/Match/Safety is calculated across 5 dimensions including advisor availability and research fit strength."

---

## 5. RESULTS SCREEN

### 5.1 Layout

- Header: "Your Top Matches" + student name/subfield as context line (e.g., "Matching for: PhD in Condensed Matter Physics")
- Show top 10–15 ranked match cards
- Filters sidebar (optional for prototype): Filter by Reach/Match/Safety, Campus Setting, Degree Type
- Sort toggle: Best Match (default) | Acceptance Rate | Program Size

### 5.2 Match Card (Collapsed State)

Each card shows:

```
┌─────────────────────────────────────────────────────────┐
│  [Reach / Match / Safety badge]          Score: 87/100  │
│                                                         │
│  Brown University                                       │
│  Department of Physics                                  │
│  Providence, RI · Urban                                 │
│                                                         │
│  Matching specialties: Condensed Matter, Biophysics,    │
│  High Energy Physics (+3 more)                          │
│                                                         │
│  Acceptance Rate: 15%  |  PhD Granted 2024: 18          │
│  Application Deadline: Dec 15                           │
│                                                         │
│  "Strong match for condensed matter research with       │
│   both experimental and theoretical tracks available."  │
│                                                         │
│  [+ Add to Compare]        [View Details ▼]             │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Match Card (Expanded State)

Clicking "View Details" expands the card to show:

```
Score Breakdown:
  Research Fit:          92/100  ████████████░
  Admissions Feasibility: 70/100  █████████░░░
  Program Activity:       85/100  ███████████░
  Location Match:         80/100  ██████████░░
  Degree Structure Fit:   95/100  ████████████

Why This Matches You:
  [AI-generated 3-sentence explanation]
  e.g., "Brown's Physics department offers strong condensed matter and
  biophysics research tracks aligned with your interests. The experimental
  PhD track is available, matching your preferred approach. With 18 PhDs
  awarded in 2024, this is an active research program."

Faculty Highlights:
  [PLACEHOLDER — Faculty data not yet loaded]
  In the full system, this would show 2–3 faculty members in your
  subfield with links to their research profiles and an advisor
  availability indicator.

Funding:
  Stipend: [PLACEHOLDER — scraped from program page]
  CoL-Adjusted Value: [PLACEHOLDER — calculated]
  Funding Type: [PLACEHOLDER — TA/RA/Fellowship]
  Note: "In the full system, funding is normalized by city cost-of-living
  to enable true apples-to-apples comparison."

International Support:
  [PLACEHOLDER — scraped from program page]

  [View Program on GradSchoolShopper →]   (link to School Profile URL)
```

---

## 6. COMPARE VIEW

### 6.1 Trigger

User clicks "+ Add to Compare" on 2–4 cards, then clicks "Compare Selected" floating button.

### 6.2 Compare Table Layout

Side-by-side table. Rows = attributes. Columns = selected schools.

| Attribute | Brown University | MIT | UC Berkeley |
|-----------|-----------------|-----|-------------|
| Overall Score | 87/100 | 91/100 | 78/100 |
| Reach/Match/Safety | Match | Reach | Match |
| Matching Specialties | Condensed Matter, Biophysics | Condensed Matter, Quantum Info | Condensed Matter, Materials |
| Research Approach | Both | Both | Experimental |
| Acceptance Rate | 15% | 4% | 12% |
| PhD Granted 2024 | 18 | [data] | [data] |
| Campus Setting | Urban | Urban | Urban |
| Application Deadline | Dec 15 | Dec 15 | Dec 1 |
| Stipend | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| Faculty Highlights | [PLACEHOLDER] | [PLACEHOLDER] | [PLACEHOLDER] |
| GSS Profile | [Link] | [Link] | [Link] |

### 6.3 UX Notes

- Highlight the "best" value per row with a subtle green background
- Show a note at the bottom: "Funding and faculty data would be populated from program pages and live web queries in the production system."

---

## 7. TECH STACK (PROTOTYPE ONLY)

| Component | Tool | Notes |
|-----------|------|-------|
| Front-end | React (via Claude Code) | Single-page app; clean, minimal UI |
| Data | GSS Advanced Program Details.xlsx | Pre-process into JSON for the app |
| AI matching engine | Cassidy agent | Receives intake + data, returns ranked scores + explanations |
| Styling | Tailwind CSS | Fast, clean, mobile-friendly |
| Hosting | Cloudflare Pages or GitHub Pages | Static deploy, shareable URL |
| Faculty/funding lookup | Not built — placeholder UI only | In production: web search agent or scraped KB |

---

## 8. CASSIDY AI AGENT SPEC

### 8.1 Agent Role

**Name:** GSS Match Engine
**Purpose:** Given a student preference profile and a program dataset, return a ranked list of matched schools with scores and natural language explanations.

### 8.2 Input Schema

```
STUDENT PROFILE:
- degree_goal: [PhD | Master's | Either]
- research_interests: [list of specialties from GSS taxonomy]
- research_approach: [Experimental | Theoretical | Computational | No preference]
- location_flexibility: [Anywhere | Region: X | Local only]
- student_status: [Domestic | International]
- career_goal: [string]
- weights: {research_fit, funding, location, prestige, career_outcomes} — each 1–5

PROGRAM DATA: [JSON array of aggregated school records from spreadsheet]
```

### 8.3 Output Schema

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
      "explanation": "Brown's Physics department offers strong condensed matter and biophysics research tracks aligned with your interests. The experimental PhD track is available, matching your preferred approach. With 18 PhDs awarded in 2024, this is an active research program.",
      "acceptance_rate": "15%",
      "phd_granted_2024": 18,
      "application_deadline": "Dec 15",
      "school_profile_url": "https://gradschoolshopper.com/browse/brown-university.html"
    }
  ]
}
```

### 8.4 Agent Instructions Summary

- Score each school on 5 dimensions using available data fields
- Aggregate specialty rows per school before scoring
- Rank by overall_score descending
- Generate a 2–3 sentence plain-English explanation per school that references specific matching reasons
- Classify Reach/Match/Safety based on acceptance rate
- Return top 15 matches
- For missing data fields (acceptance rate = "N/A"), handle gracefully: omit that dimension from scoring and note in output

---

## 9. PROTOTYPE SCOPE BOUNDARIES

### In Scope (build this)
- Intake form (6 questions)
- Results screen with ranked match cards (collapsed + expanded)
- Compare view (2–4 schools)
- Placeholder blocks for faculty, funding, and other scraped data (styled, not blank)
- AI-generated match explanation text per card
- Reach/Match/Safety badge

### Out of Scope (do NOT build for prototype)
- User accounts or login
- Saved lists / application tracking
- Funding normalization (CoL calculation)
- Real faculty data or web scraping
- Adaptive preference refinement
- Mobile optimization (desktop demo is fine)
- Collaborative filtering
- Any backend database — use static JSON

---

## 10. PLACEHOLDER LANGUAGE GUIDE

Use this exact language for placeholder blocks in the prototype UI so it's clear to demo viewers what is scaffolded vs. live:

| Section | Placeholder Label | Tooltip / Footnote Text |
|---------|-------------------|------------------------|
| Faculty | "Faculty data not yet loaded" | "In the full system, 2–3 faculty in your subfield would appear here with research areas and advisor availability status — retrieved via live web query." |
| Stipend | "Stipend data — scraped from program page" | "In the full system, stipend data is scraped from each program's GSS profile page and normalized by city cost-of-living." |
| CoL-Adjusted Funding | "Cost-of-living adjusted value — calculated" | "Raw stipend divided by city cost-of-living index to enable true apples-to-apples comparison across programs." |
| International Support | "International student data — scraped from program page" | "In the full system, this field is populated from the program's GSS profile and department website." |
| Time to Degree | "Time-to-degree median — scraped" | "Median time to PhD completion for this program, drawn from program page or AIP data." |
| Career Outcomes | "Placement data — scraped from program page" | "Where graduates go: academia, national labs, industry R&D, etc." |

---

## 11. DEMO SCRIPT ALIGNMENT

The prototype must support this demo walk-through sequence (from demo-strategy doc):

1. **Step 1:** Show intake form — fill out "Alex" persona (Condensed Matter, PhD, West Coast, experimental, industry R&D)
2. **Step 2:** Submit → show ranked results screen with match cards
3. **Step 3:** Expand top result — show score breakdown + AI explanation + placeholder blocks
4. **Step 4:** Add 2–3 programs to compare view
5. **Step 5 (optional):** Hand control to client — let them change a subfield or preference and rerun

The prototype must be fast enough to re-run live without noticeable delay.

---
*End of Prototype PRD v0.1*
*Next step: Use this PRD with Claude Code to build the front-end. Use Section 8 to configure the Cassidy AI matching agent.*

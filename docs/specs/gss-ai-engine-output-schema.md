# GSS AI Engine — Output Schema & Results Population Guide
**Version:** 1.0  
**Owner:** Mack Wallace / Enterprise Commons  
**For:** Cassidy AI engine builder  
**Last updated:** 2026-05-14

---

## Purpose

This document defines what information the Cassidy AI matching engine must return per matched program, and specifies **where each field should come from**. The governing principle:

> **Factual data must come directly from the university KB markdown files whenever available. AI-generated content is reserved for scored outputs and narrative explanations only.**

Fabricating factual data (acceptance rates, faculty, stipends, deadlines) is not acceptable. If a field is not in the KB file, surface the absence explicitly rather than inferring a value.

---

## Output Structure

The engine returns a JSON object with a `matches` array. Each element represents one matched program, ranked by `overall_score` descending.

```json
{
  "matches": [
    { ...match object... },
    { ...match object... }
  ]
}
```

**Number of results:** 5–10 programs (variable; engine decides based on scoring threshold). The frontend renders whatever count is returned.

---

## Match Object — Full Schema

```json
{
  "school_name": "string",
  "abbr": "string | null",
  "department": "string",
  "location": "string",
  "region": "string",
  "campus_setting": "string",

  "overall_score": "integer (0–100)",
  "matching_specialties": ["string"],
  "score_breakdown": {
    "research_fit": "integer (0–100)",
    "admissions_feasibility": "integer (0–100)",
    "program_activity": "integer (0–100)",
    "location_match": "integer (0–100)",
    "degree_structure_fit": "integer (0–100)"
  },

  "why": "string",

  "acceptance_rate": "string",
  "phd_granted_2024": "integer | null",
  "application_deadline": "string",
  "faculty_count": "integer | null",

  "gss_url": "string",
  "grad_url": "string",
  "dept_url": "string | null",
  "faculty_url": "string | null",
  "funding_url": "string | null"
}
```

---

## Field-by-Field Guide

### Identification

| Field | Source | Notes |
|-------|--------|-------|
| `school_name` | KB frontmatter: `school_name` | Full legal name. e.g. `"University of Illinois Urbana-Champaign"` |
| `abbr` | KB frontmatter or known convention | Common abbreviation if one exists. `"UIUC"`, `"MIT"`, `"UCSB"`. `null` if none. |
| `department` | KB header block: `Department:` | Typically `"Physics"` for this dataset |
| `location` | KB frontmatter: `city` + `state` | Format: `"Cambridge, MA"` |
| `region` | KB frontmatter: `region` | One of: `Northeast`, `Mid-Atlantic`, `Southeast`, `Midwest`, `Southwest`, `Mountain West`, `West Coast`, `Pacific Northwest` |
| `campus_setting` | KB frontmatter: `campus_setting` | One of: `Urban`, `Suburban`, `College Town`, `Rural` |

---

### Scores (AI-Generated)

| Field | Source | Notes |
|-------|--------|-------|
| `overall_score` | Agent 1 computed | Weighted composite: Research Fit 35%, Admissions 20%, Program Activity 15%, Location 15%, Degree Fit 15% |
| `matching_specialties` | Agent 1 computed | Intersection of student's `intake-research-interests` and KB `specialties` array. Return only matched values. |
| `score_breakdown.research_fit` | Agent 1 computed | 0–100. Based on specialty overlap + approach bonus |
| `score_breakdown.admissions_feasibility` | Agent 1 computed | 0–100. Higher = more accessible. Derived from `acceptance_rate` in KB |
| `score_breakdown.program_activity` | Agent 1 computed | 0–100. Based on `phd_granted_2024`, `faculty_count_research`, `total_enrollment_2024` |
| `score_breakdown.location_match` | Agent 1 computed | 0–100. Prototype v0.1: flat 85 for all. Future: driven by `intake-location-flexibility` |
| `score_breakdown.degree_structure_fit` | Agent 1 computed | 0–100. Based on `offers_phd` / `offers_masters` vs student's `intake-degree-goal` |

---

### AI Explanation

| Field | Source | Notes |
|-------|--------|-------|
| `why` | Agent 2 generated | 2–3 sentence explanation of why this program matches this specific student. Must reference student's research interests and career goal by name. Must be grounded in KB data — do not invent department descriptions. For directory-only schools (no About text in KB), rely on structured fields only. |

**Agent 2 tone:** Follow GSS brand voice — neutral, authoritative, data-grounded. No hype, no superlatives without data, no exclamation points. See `BRAND VOICE SNIPPET — GradSchoolShopper.md`.

---

### Program Facts (KB Source — Do Not Fabricate)

| Field | KB Source | If Missing |
|-------|-----------|------------|
| `acceptance_rate` | KB frontmatter: `acceptance_rate` (stored as decimal e.g. `0.4`). Convert to `"40%"` string for display. | `"Not listed"` |
| `phd_granted_2024` | KB frontmatter: `phd_granted_2024` | `null` |
| `application_deadline` | KB frontmatter: `application_deadline` | `"See program website"` |
| `faculty_count` | KB frontmatter: `faculty_count_research` (prefer) or `faculty_count_total` | `null` |

---

### Links (KB Source — Verify Before Including)

| Field | KB Source | Fallback |
|-------|-----------|---------|
| `gss_url` | KB **Key Links** section: `[GSS Profile](url)` | Construct from slug pattern: `https://gradschoolshopper.com/browse/[school-slug].html`. Verify the URL does not 404 before including. |
| `grad_url` | KB **Key Links** section: `[Graduate Studies Overview](url)` or `[Application Process](url)` | Use department website as fallback. Never omit — the results UI uses this as a primary CTA ("Visit Admissions"). |
| `dept_url` | KB header block: `Department Website:` | `null` if not in KB |
| `faculty_url` | KB **Key Links** section: `[Faculty Directory](url)` | `null` if not in KB |
| `funding_url` | KB **Key Links** section: `[Financial Assistance](url)` | `null` if not in KB |

---

## How the Results Screen Uses Each Field

| Field | Used In |
|-------|---------|
| `school_name` + `abbr` | Card heading: `"University of Illinois Urbana-Champaign (UIUC)"` |
| `location` + `campus_setting` + `region` | Card subtitle: `"Urbana, IL · College Town · Midwest"` |
| `overall_score` | Stat pill: `"Match Score 88/100"` |
| `score_breakdown.research_fit` | Stat pill: qualitative label (Exceptional / Very Strong / Strong...) |
| `acceptance_rate` | Stat pill: `"Acceptance 10%"` |
| `matching_specialties` | Research Strengths chips on card |
| `why` | "Why This Matches You" — collapsed teaser (2 lines) and full text on expand |
| `score_breakdown` (all 5) | Expanded card: horizontal score breakdown bars with qualitative labels |
| `faculty_count` + `faculty_url` | Expanded: "This program has N faculty members. View the faculty directory." |
| `funding_url` | Expanded: "View the program's funding and financial support page." |
| `application_deadline` | Card footer: `"Deadline: Dec 15"` |
| `phd_granted_2024` | Card footer: `"PhDs/yr: 24"` |
| `grad_url` | Expanded card primary CTA: `"Visit [School] Admissions →"` |
| `gss_url` | Expanded card secondary CTA: `"View on GradSchoolShopper →"` |
| `why` + all fields | Summary & Next Steps section (bottom of results page) — generated by front-end JS from full results JSON |

---

## Handling Missing KB Data

The KB has two tiers of coverage (see `University KB/_KB_METADATA.md`):

| KB Coverage Tier | Schools | What's Available |
|------------------|---------|------------------|
| **Full profile** | 41 schools | All factual fields + About text + Program Requirements |
| **Directory-only** | 67 schools | Frontmatter fields only (specialties, deadline, acceptance rate, enrollment) |
| **No URL** | 5 schools | Frontmatter only; no GSS URL |

**For directory-only schools:**
- `why` must be grounded in frontmatter fields only. Do not invent About text.
- `faculty_url`, `funding_url`, `dept_url` will typically be `null`
- `grad_url` may not be in KB — construct from known institutional patterns or omit if uncertain

**Placeholder text for missing links (shown in results UI):**
- Faculty: *"Faculty listings not yet available. View the department website for current faculty."*
- Funding: *"Funding information not yet available. See the program page for stipend and fellowship details."*

---

## Scoring Weights Reference (Agent 1 v0.1)

| Dimension | Weight | Key KB Fields Used |
|-----------|--------|-------------------|
| Research Fit | 35% | `specialties`, student's `intake-research-interests` + `intake-research-approach` |
| Admissions Feasibility | 20% | `acceptance_rate` |
| Program Activity | 15% | `phd_granted_2024`, `faculty_count_research`, `total_enrollment_2024` |
| Location Match | 15% | Prototype: flat 85. Future: `city`, `state`, `region` vs `intake-location-flexibility` |
| Degree Structure Fit | 15% | `offers_phd`, `offers_masters` vs `intake-degree-goal` |

---

## Qualitative Label Mapping (Frontend Display)

The frontend converts raw scores to qualitative labels. The engine returns raw integers (0–100) and the frontend displays these labels:

**Research Fit, Program Activity, Location Match, Degree Fit:**
| Score | Label |
|-------|-------|
| 90–100 | Exceptional |
| 80–89 | Very Strong |
| 70–79 | Strong |
| 60–69 | Good |
| < 60 | Developing |

**Admissions Feasibility (higher = more accessible):**
| Score | Label |
|-------|-------|
| 80+ | Accessible |
| 65–79 | Competitive |
| 45–64 | Highly Competitive |
| < 45 | Most Selective |

---

## Selectivity Badge (Frontend Display)

The frontend derives a selectivity badge from `acceptance_rate` (not from a separate field):

| Acceptance Rate | Badge |
|-----------------|-------|
| < 8% | Highly Selective |
| 8–14% | Selective |
| 15–21% | Moderately Selective |
| 22%+ | Accessible |

---

## Summary & Next Steps (Frontend-Generated)

The "Summary & Next Steps" section at the bottom of the results page is generated entirely by front-end JavaScript from the full `matches` array. The engine does not need to return a separate summary. The JS function:

1. Identifies the top match by `overall_score`
2. Identifies the match with highest `score_breakdown.research_fit`
3. Finds the earliest `application_deadline` (accounting for academic year cycle: Dec before Jan)
4. Counts programs with shared deadlines
5. Identifies the most and least selective programs by `acceptance_rate`
6. Generates a structured paragraph + bulleted next steps in the GSS brand voice (neutral, direct, data-grounded)

No AI generation required for this section.

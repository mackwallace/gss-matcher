# Test Case 001 — Jordan Lee
**Purpose:** Stress-test scoring dimensions with a profile distinct from mock data (Alex). Validates multi-specialty HEP matching, West Coast location filtering, CV enrichment via Profile Builder, and overall pipeline integrity from form → Worker → Cassidy → results screen.  
**Status:** Ready to run  
**Date:** 2026-05-15

---

## Test Persona

| Field | Value |
|-------|-------|
| Name | Jordan Lee |
| Background | Strong domestic undergrad, University of Oregon Physics, May 2025 graduate |
| Research | Experimental high energy physics — ATLAS/CERN detector work, Belle II at SLAC |
| Profile strength | Full CV, GRE scores, NSF GRFP Honorable Mention, co-authored ATLAS note |

---

## Session ID Note

> **The Worker auto-generates a UUID session ID** on every POST / submission. The value `test-jordan-lee-001` is a reference label for this document only — it is NOT passed to the Worker.
>
> After submitting the form, **capture the session ID from the loader URL**:
> `https://gss-matcher.pages.dev/gss-matcher-loader-v3.0.html?session=<UUID>`
>
> Record it here for debugging: `session_id: ______________________________`

---

## Form Inputs

### Required Fields

| Field ID | Value |
|----------|-------|
| `student-first-name` | `Jordan` |
| `student-last-name` | `Lee` |
| `student-email` | `jordan.lee@testgss.com` |
| `intake-degree-goal` | `PhD` |
| `intake-career-goal` | `Academic research (tenure-track faculty)` |
| `intake-research-interests` | `High Energy Physics`, `Particles and Fields`, `Quantum Optics and Quantum Information` |
| `intake-research-approach` | `Experimental` |
| `intake-location-flexibility` | `Specific region — West Coast` |
| `intake-student-status` | `U.S. Citizen` |
| `intake-marketing-consent` | ✅ checked |

### Optional Fields

| Field ID | Value |
|----------|-------|
| `enhance-linkedin-url` | *(leave empty)* |
| `enhance-scholar-url` | *(leave empty)* |
| `enhance-researchgate-url` | *(leave empty)* |
| `enhance-cv-text` | See below |
| `preferences-weights` | `research_fit: 5, funding: 3, location: 4, prestige: 4, career_outcomes: 3` |

### CV Text (`enhance-cv-text`)

```
B.S. Physics, University of Oregon, 2025. GPA: 3.85/4.0.
GRE: 167V / 170Q.

Research Experience:
- 2 years in the UO High Energy Physics lab under Prof. David Strom.
  Worked on detector calibration for the ATLAS experiment at CERN.
  Co-authored one internal ATLAS note on track reconstruction efficiency.
- Summer 2024 REU at SLAC National Accelerator Laboratory. Contributed
  to data quality monitoring for the Belle II experiment.

Awards: Dean's List all semesters. NSF GRFP Honorable Mention 2025.

Skills: Python, ROOT, C++, statistical analysis, detector simulation.

Career goal: Tenure-track faculty at a research university, with a focus
on experimental particle physics and future collider experiments.
```

---

## Full JSON Payload (for reference / direct API testing)

This is what the intake form submits to the Worker. `intake-school-data` is injected automatically by the form — shown truncated here.

```json
{
  "student-first-name": "Jordan",
  "student-last-name": "Lee",
  "student-email": "jordan.lee@testgss.com",
  "intake-degree-goal": "PhD",
  "intake-career-goal": "Academic research (tenure-track faculty)",
  "intake-research-interests": [
    "High Energy Physics",
    "Particles and Fields",
    "Quantum Optics and Quantum Information"
  ],
  "intake-research-approach": ["Experimental"],
  "intake-location-flexibility": "Specific region — West Coast",
  "intake-student-status": "U.S. Citizen",
  "enhance-linkedin-url": "",
  "enhance-scholar-url": "",
  "enhance-researchgate-url": "",
  "enhance-cv-text": "B.S. Physics, University of Oregon, 2025. GPA: 3.85/4.0.\nGRE: 167V / 170Q.\n\nResearch Experience:\n- 2 years in the UO High Energy Physics lab under Prof. David Strom.\n  Worked on detector calibration for the ATLAS experiment at CERN.\n  Co-authored one internal ATLAS note on track reconstruction efficiency.\n- Summer 2024 REU at SLAC National Accelerator Laboratory. Contributed\n  to data quality monitoring for the Belle II experiment.\n\nAwards: Dean's List all semesters. NSF GRFP Honorable Mention 2025.\n\nSkills: Python, ROOT, C++, statistical analysis, detector simulation.\n\nCareer goal: Tenure-track faculty at a research university, with a focus\non experimental particle physics and future collider experiments.",
  "preferences-weights": {
    "research_fit": 5,
    "funding": 3,
    "location": 4,
    "prestige": 4,
    "career_outcomes": 3
  },
  "intake-marketing-consent": true,
  "intake-school-data": "[...full gss_programs.json stringified — auto-injected by form...]"
}
```

---

## What This Test Exercises

| Scoring Dimension | What to Watch |
|-------------------|---------------|
| **Research Fit (35%)** | 3 HEP-adjacent interests — multi-specialty matching + Experimental approach bonus (+5 to +10 pts) |
| **Admissions Feasibility (20%)** | West Coast schools (Caltech ~4%, Stanford ~4%, UCSB ~9%, UW ~11%) — expect Reach programs to appear; feasibility scores will be low but research fit should still rank them highly |
| **Program Activity (15%)** | Large R1 HEP programs (Caltech, UW, UCSB, UC Santa Cruz, UC Davis) should score highly on faculty count + PhDs granted |
| **Location Match (15%)** | Flat 85 in v0.1 — confirm the value `"Specific region — West Coast"` passes through correctly in the payload |
| **Degree Fit (15%)** | PhD only — schools that offer PhD should score max; Master's-only filtered out |
| **CV Enrichment** | Profile Builder should surface: SLAC REU, ATLAS/CERN detector work, NSF GRFP HM, ROOT/C++ skills, 2026 graduation timeline |

---

## Expected Behavior

### Agent 1 — Program Scoring

**Schools likely to appear in top matches (West Coast HEP):**
- University of Washington (strong HEP, manageable acceptance)
- UC Santa Barbara (Particles & Fields, HEP)
- Stanford (strong HEP reach — low acceptance but high research fit)
- Caltech (extreme reach — 4% — but highest HEP research fit)
- UC Santa Cruz (Santa Cruz Institute for Particle Physics — SCIPP)
- UC Davis (HEP experimental)
- Oregon State University (in-state familiarity, HEP)

**Scores to watch:**
- Research Fit: should be 85–97 for schools with active HEP experimental programs
- Admissions Feasibility: Caltech and Stanford will be 30–40 range (correctly low)
- Degree Structure Fit: should be 90–95 for PhD-offering programs

### Agent 2 — Match Explanation (`why` field)

Each `why` field should reference Jordan specifically. Look for:
- ✅ "High Energy Physics" or "experimental particle physics" named explicitly
- ✅ ATLAS / CERN or SLAC mentioned if Profile Builder enrichment worked
- ✅ Career goal ("academic research" or "faculty") reflected
- ✅ Experimental approach noted where relevant
- ❌ "Alex" should NOT appear — confirms session isolation

### Metadata to Check

| Field | Expected |
|-------|----------|
| `event_type` | `match_results_generated` |
| `session_id` | UUID matching the loader URL param |
| `matches` | Array of 5–10 objects |
| `metadata.profile_completeness` | `"Full"` (CV provided, GRE scores present) |

---

## Evaluation Checklist

Run through these after results return:

**Pipeline**
- [ ] Form submits without errors
- [ ] Loader appears and pipeline stages animate
- [ ] Loader navigates to results screen (not stuck or timing out)
- [ ] Results screen shows Jordan's name in the hero ("Jordan's Top Matches")
- [ ] Results screen shows correct research interests chips (High Energy Physics, Particles and Fields, Quantum Optics and Quantum Information)

**Scoring quality (check Agent 1 JSON)**
- [ ] 5–10 matches returned
- [ ] At least 1 West Coast school in top 3
- [ ] Caltech and/or Stanford appear (even if low feasibility score) — confirms Reach programs aren't filtered out
- [ ] No `overall_score` above 100 or below 0
- [ ] `score_breakdown` all 5 dimensions present and sum to a weighted composite consistent with `overall_score`

**Explanation quality (check Agent 2 output)**
- [ ] `why` field mentions HEP or experimental particle physics
- [ ] `why` does not contain "Alex" (session isolation)
- [ ] CV enrichment visible: SLAC, ATLAS, or NSF mentioned in at least one explanation

**Display layer (check results UI)**
- [ ] Selectivity badges render correctly (expect Highly Selective for Caltech/Stanford)
- [ ] Score breakdown bars show qualitative labels (Exceptional / Very Strong / etc.)
- [ ] "Visit Admissions" CTA links present on expanded cards
- [ ] Summary & Next Steps section generated at bottom

---

## Debugging Reference

If results don't appear, check in this order:

1. **Worker KV** — confirm session was stored:
   ```bash
   wrangler kv key get "session:<UUID>" --namespace-id 56780ada6c1a4fbda92c901f0dfea771
   ```

2. **Cassidy callback** — check if `/receive` was called by reviewing Worker logs:
   ```bash
   wrangler tail --name gss-matcher-proxy
   ```

3. **Loader timeout** — if loader shows "Something took longer than expected," the `PROD_DURATION` (3 min) elapsed before Cassidy responded. Check if Cassidy is processing.

4. **CORS error** — if form submission fails in browser console, check that `https://gss-matcher.pages.dev` is in the Worker's `ALLOWED_ORIGINS`.

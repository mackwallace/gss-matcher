# Results Screen — Null Fields, Dead Links, Duplicate Selectivity Range
**Date:** 2026-09-18
**Reported by:** Mack Wallace, testing ahead of the AIP GradSchoolShopper & AI discussion (2026-09-18, 11am ET)

## Symptoms
On `gss-matcher-results-v2.0.html` (both a real session and demo mode):
- Acceptance rate, location, region, campus setting showing `null`
- Selectivity badge showing "Not Listed" instead of a real category
- "View program" / "View on GSS" CTA links dead (`href="null"`)
- Summary's selectivity range collapsed to one duplicated value (observed as 17% for both min and max)

## Root cause
`normalizeMatch()` rebuilds each Cassidy match into a fixed-field object and
silently dropped `location`, `region`, `campus_setting`, `abbr`,
`acceptance_rate`, `application_deadline`, `faculty_count`, and every
`*_url` field. `mergeWithDisplay()` is supposed to fall back to those fields
on the raw match when a school isn't found in `gss_display_v2.json` — but
since `normalizeMatch()` already stripped them, that fallback always
resolved to `null`. One dropped-field bug produced all four symptoms above.

**Compounding data issue:** several school names don't exactly match
`gss_display_v2.json`'s punctuation convention (missing comma before
campus, missing campus suffix) — confirmed for Illinois Urbana-Champaign,
Michigan (Ann Arbor), and Colorado Boulder (the exact case in the original
bug report). `DISPLAY_NAME_OVERRIDE` only covered 2 of these; extended to 5.

**Separate, unfixed gap:** MIT, UC Santa Barbara, and University of
Maryland are not in the tracked 113-school `gss_display_v2.json` dataset at
all — not a naming mismatch, a real data-completeness gap. Product decision
needed on whether to add them (the AI recommends them as reach schools
regardless of whether they're tracked).

## Fix
Commit `00b2f60` — `normalizeMatch()` now passes the previously-dropped
fields through as a fallback-of-last-resort; `DISPLAY_NAME_OVERRIDE`
extended with the 3 additional mismatches. See the code comments at the
fix site for detail.

## Deployment note — read before pushing again
This project's Cloudflare Pages **plan** (see `2026-05-15-deployment-plan.md`,
Phase 2) called for Git-integrated auto-deploy on push to `main`. That was
never actually configured — `wrangler pages project list` shows Git
Provider: **No**. A `git push` to GitHub does **not** update
`gss-matcher.pages.dev`. Deploy manually after every change that needs to
go live:

```bash
wrangler pages deploy . --project-name gss-matcher --branch main --commit-dirty=true
```

Requires a fresh `wrangler login` — the stored OAuth token expires
periodically (it had expired as of this fix, last valid 2026-08-13).

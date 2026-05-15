#!/usr/bin/env python3
"""
build_gss_display_v2.py

Regenerates gss_display_v2.json from the 113 University KB markdown files.
Expands the v1 field set to include: abbr, location, region, campus_setting,
faculty_count, phd_granted_2024, and all link fields (gss_url, grad_url,
dept_url, faculty_url, funding_url).

No external dependencies required — uses stdlib only.

Run from the project root:
    python3 build_gss_display_v2.py
"""

import json
import re
from pathlib import Path

KB_DIR     = Path(__file__).parent / "University KB"
OUTPUT     = Path(__file__).parent / "gss_display_v2.json"

# ── State → 2-letter abbreviation ─────────────────────────────────────────────
STATE_ABBREV = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
    "Ontario": "ON", "Quebec": "QC", "British Columbia": "BC",
    "Alberta": "AB", "Saskatchewan": "SK", "Nova Scotia": "NS",
    "Manitoba": "MB", "New Brunswick": "NB",
}

# ── Known common abbreviations ────────────────────────────────────────────────
KNOWN_ABBR = {
    "Massachusetts Institute of Technology": "MIT",
    "University of Illinois Urbana-Champaign": "UIUC",
    "University of Illinois, Urbana-Champaign": "UIUC",
    "University of California, Santa Barbara": "UCSB",
    "University of California Santa Barbara": "UCSB",
    "University of California, Los Angeles": "UCLA",
    "University of California, Berkeley": "UC Berkeley",
    "University of California, San Diego": "UCSD",
    "University of California, Davis": "UC Davis",
    "University of California, Irvine": "UC Irvine",
    "University of California, Santa Cruz": "UC Santa Cruz",
    "University of California, Riverside": "UC Riverside",
    "Georgia Institute of Technology": "Georgia Tech",
    "Carnegie Mellon University": "CMU",
    "Ohio State University": "OSU",
    "Pennsylvania State University": "Penn State",
    "University of Texas at Austin": "UT Austin",
    "Texas A&M University": "Texas A&M",
    "University of Maryland": "UMD",
    "University of Maryland, College Park": "UMD",
    "Michigan State University": "MSU",
    "Florida State University": "FSU",
    "Virginia Tech": "VT",
    "North Carolina State University": "NC State",
    "University of Colorado Boulder": "CU Boulder",
    "University of Colorado, Boulder": "CU Boulder",
    "Arizona State University": "ASU",
    "University of Arizona": "UA",
    "Indiana University Bloomington": "IU",
    "Purdue University": "Purdue",
    "University of Wisconsin-Madison": "UW-Madison",
    "Iowa State University": "ISU",
    "Washington University in St. Louis": "WashU",
    "Case Western Reserve University": "CWRU",
    "University of Pittsburgh": "Pitt",
    "Louisiana State University": "LSU",
    "University of Georgia": "UGA",
    "Georgia State University": "GSU",
    "University of North Carolina at Chapel Hill": "UNC",
    "University of Virginia": "UVA",
    "West Virginia University": "WVU",
    "University of Tennessee": "UT",
    "University of Florida": "UF",
    "University of Central Florida": "UCF",
    "University of South Florida": "USF",
    "Florida International University": "FIU",
    "University of Hawaii at Manoa": "UH Manoa",
    "University of Washington": "UW",
    "Oregon State University": "OSU-Corvallis",
    "University of New Mexico": "UNM",
    "New Mexico State University": "NMSU",
    "University of Nevada, Reno": "UNR",
    "University of Nevada, Las Vegas": "UNLV",
    "University of Utah": "UU",
    "Utah State University": "USU",
    "Montana State University": "MSU-Bozeman",
    "University of Kansas": "KU",
    "Kansas State University": "K-State",
    "University of Nebraska-Lincoln": "UNL",
    "University of Nebraska, Lincoln": "UNL",
    "University of Oklahoma": "OU",
    "Oklahoma State University": "OSU-Stillwater",
    "Louisiana State University and A&M College": "LSU",
    "University of Arkansas": "U of A",
    "University of Alabama": "UA",
    "Auburn University": None,
    "Clemson University": None,
    "Vanderbilt University": None,
    "Stony Brook University": None,
    "Northeastern University": None,
    "Boston University": None,
}


# ── Flat YAML frontmatter parser (no external deps) ───────────────────────────
def _coerce(value: str):
    """Convert a raw YAML scalar string to Python type."""
    v = value.strip().strip('"').strip("'")
    if v.lower() in ("null", "~", ""):
        return None
    if v.lower() == "true":
        return True
    if v.lower() == "false":
        return False
    if v.lower() == "not_available":
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        f = float(v)
        return f
    except ValueError:
        pass
    return v


def parse_frontmatter(text: str) -> dict:
    """Parse flat YAML frontmatter between leading --- delimiters."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.strip().startswith("-"):
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.strip()
        # Skip nested / list-valued keys
        if not key or not rest:
            continue
        fm[key] = _coerce(rest)
    return fm


# ── URL extraction from markdown body ─────────────────────────────────────────
def _find_link(text, *label_patterns):
    """Return the first URL whose markdown label matches any of the patterns."""
    for pat in label_patterns:
        m = re.search(rf'\[{pat}[^\]]*\]\(([^)]+)\)', text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


MONTH_LONG = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
}

def normalize_deadline(val):
    """Convert 'December 15' → 'Dec 15'. Leave complex/multi-deadline strings as-is."""
    if not val:
        return None
    m = re.match(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})$',
        str(val).strip()
    )
    if m:
        return f"{MONTH_LONG[m.group(1)]} {m.group(2)}"
    return str(val).strip()


def extract_department(text: str):
    """Extract department from the markdown body header block."""
    m = re.search(r'\*\*Department:\*\*\s*(.+)', text)
    return m.group(1).strip() if m else None


def extract_links(text: str) -> dict:
    return {
        "gss_url":     _find_link(text, "GSS Profile"),
        "grad_url":    _find_link(text,
                           "Graduate Studies Overview",
                           "Graduate Program",
                           "Prospective Students",
                           "Application Process",
                           "Graduate Admissions",
                           "Admissions"),
        "dept_url":    _find_link(text, "Department Website"),
        "faculty_url": _find_link(text, "Faculty Directory", "Faculty"),
        "funding_url": _find_link(text,
                           "Financial Assist",
                           "Financial Support",
                           "Funding"),
    }


# ── Per-file processor ─────────────────────────────────────────────────────────
def process(path):
    text = path.read_text(encoding="utf-8")
    fm   = parse_frontmatter(text)

    school_name = fm.get("school_name")
    if not school_name or not isinstance(school_name, str):
        return None

    # Location: "City, ST"
    city  = fm.get("city") or ""
    state = fm.get("state") or ""
    abbr  = STATE_ABBREV.get(state, state)
    location = f"{city}, {abbr}".strip(", ") if city else None

    # acceptance_rate decimal → "N%"
    acc = fm.get("acceptance_rate")
    if isinstance(acc, (int, float)):
        acc_str = f"{int(round(acc * 100))}%" if acc <= 1 else f"{int(round(acc))}%"
    elif isinstance(acc, str):
        acc_str = acc
    else:
        acc_str = None

    # faculty_count: prefer research count
    fc = fm.get("faculty_count_research")
    if not isinstance(fc, int):
        fc = fm.get("faculty_count_total")
    faculty_count = fc if isinstance(fc, int) else None

    links = extract_links(text)

    # abbr: use known map; None if no abbreviation or school has no common short form
    known = KNOWN_ABBR.get(school_name, "__missing__")
    school_abbr = None if known in (None, "__missing__") else known

    record = {
        "school_name":           school_name,
        "abbr":                  school_abbr,
        "department":            fm.get("department") or extract_department(text),
        "location":              location,
        "region":                fm.get("region"),
        "campus_setting":        fm.get("campus_setting"),
        "acceptance_rate":       acc_str,
        "application_deadline":  normalize_deadline(fm.get("application_deadline")),
        "phd_granted_2024":      fm.get("phd_granted_2024") if isinstance(fm.get("phd_granted_2024"), int) else None,
        "ms_granted_2024":       fm.get("ms_granted_2024")  if isinstance(fm.get("ms_granted_2024"),  int) else None,
        "total_enrollment_fall2024": fm.get("total_enrollment_2024") if isinstance(fm.get("total_enrollment_2024"), int) else None,
        "faculty_count":         faculty_count,
        "gss_url":               links["gss_url"],
        "grad_url":              links["grad_url"],
        "dept_url":              links["dept_url"],
        "faculty_url":           links["faculty_url"],
        "funding_url":           links["funding_url"],
    }

    return school_name, record


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    md_files = sorted(f for f in KB_DIR.glob("*.md") if not f.name.startswith("_"))
    print(f"Processing {len(md_files)} KB files...")

    display, errors = {}, []
    for path in md_files:
        result = process(path)
        if result:
            display[result[0]] = result[1]
        else:
            errors.append(path.name)

    if errors:
        print(f"  ⚠  No school_name found in: {errors}")

    OUTPUT.write_text(json.dumps(display, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✓  Wrote {len(display)} schools → {OUTPUT.name}\n")

    # Coverage report
    fields = ["gss_url", "grad_url", "dept_url", "faculty_url", "funding_url", "faculty_count", "location", "region"]
    for f in fields:
        n = sum(1 for v in display.values() if v.get(f) is not None)
        print(f"  {f:<28} {n:>3}/{len(display)}")


if __name__ == "__main__":
    main()

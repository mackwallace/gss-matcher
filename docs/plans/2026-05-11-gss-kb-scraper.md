# GSS Knowledge Base Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scrape all 113 GradSchoolShopper program pages and merge with existing spreadsheet JSON data into 113 structured markdown files — one per school — for import into Cassidy as the AI matching engine knowledge base.

**Architecture:** A single Python script (`build_kb.py`) reads `gss_programs.json` (113 schools with structured spreadsheet data), scrapes each school's GSS program page using the Firecrawl API, parses the scraped markdown for About text / program requirements / GRE requirements, then merges both data sources into a well-structured markdown file per school. Output is 113 `.md` files in a `kb/` directory.

**Tech Stack:** Python 3.10+, firecrawl-py v1.x, pytest; no framework, no database

---

## File Structure

```
GradSchoolShopper-Physics-Match/
├── build_kb.py               # Main pipeline: scrape + parse + build markdown
├── requirements.txt          # firecrawl-py, pytest
├── tests/
│   └── test_build_kb.py      # Unit tests for parse and markdown builder
└── kb/                       # Output: 113 .md files (created by script)
    └── auburn-university.md
    └── ...
```

---

## Data Sources & What Each Provides

| Source | Fields Available |
|--------|-----------------|
| `gss_programs.json` | school_name, department, campus_setting, acceptance_rate, application_deadline, ms_granted_2024, phd_granted_2024, first_year_enrollment_fall2024, total_enrollment_fall2024, school_profile_url, offers_phd, offers_masters, specialty_details (specialty + phd_type + masters_type per row) |
| Scraped GSS page | About/description text, Master's requirements, Doctorate requirements, GRE required (Y/N), Physics GRE required (Y/N), TOEFL required (Y/N), phone, full address, contact email, department website URL |

---

## Markdown Output Structure (per school)

```markdown
# Auburn University

**Department:** Physics  
**Campus Setting:** Rural  
**Phone:** (334) 844-4264  
**Address:** Leach Science Center Suite 2158, Auburn, Alabama 36849  
**Contact Email:** landeal@auburn.edu  
**Department Website:** http://www.auburn.edu/...  
**GSS Profile:** https://gradschoolshopper.com/browse/auburn-university.html  

---

## Specialties

- **Atomic, Molecular, & Optical Physics** — PhD: Both | Master's: Both
- **Biophysics** — PhD: Both | Master's: Both
...

---

## Admissions & Program Data

| Field | Value |
|-------|-------|
| Acceptance Rate | 40% |
| Application Deadline | Mar 14 |
| First Year Enrollment (Fall 2024) | 12 |
| Total Enrollment (Fall 2024) | 56 |
| PhDs Granted (2024) | 9 |
| MS Granted (2024) | 0 |

---

## Admissions Requirements

| Requirement | Status |
|-------------|--------|
| GRE | Required |
| Physics GRE | Not Required |
| TOEFL | Required |

---

## About

[department about text scraped from page]

---

## Program Requirements

### Master's

[scraped masters requirements]

### Doctorate / PhD

[scraped doctorate requirements]
```

---

## Task 1: Setup

**Files:**
- Create: `requirements.txt`
- Create: `tests/` directory

- [ ] **Step 1: Create requirements.txt**

```
firecrawl-py>=1.0.0
pytest>=7.0.0
```

- [ ] **Step 2: Create tests directory**

```bash
mkdir -p "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/tests"
touch "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/tests/__init__.py"
```

- [ ] **Step 3: Install dependencies**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
pip install -r requirements.txt
```

Expected: `Successfully installed firecrawl-py-...`

- [ ] **Step 4: Verify FIRECRAWL_API_KEY is set**

```bash
python3 -c "import os; key = os.environ.get('FIRECRAWL_API_KEY'); print('Key found:', bool(key))"
```

Expected: `Key found: True`

If False, the key is in `~/.zshrc` — run `source ~/.zshrc` first (it's managed by Infisical).

- [ ] **Step 5: Verify Firecrawl SDK import and auth**

```bash
python3 -c "
import os
from firecrawl import FirecrawlApp
app = FirecrawlApp(api_key=os.environ['FIRECRAWL_API_KEY'])
result = app.scrape_url('https://gradschoolshopper.com/browse/auburn-university.html', formats=['markdown'])
print('SDK works. Markdown length:', len(result.markdown or ''))
"
```

Expected: `SDK works. Markdown length: [number > 1000]`

If `result.markdown` fails with AttributeError, the SDK uses dict-style access — replace with `result.get('markdown', '')`. Update all SDK calls in Task 4 accordingly.

- [ ] **Step 6: Confirm gss_programs.json structure**

```bash
python3 -c "
import json
with open('gss_programs.json') as f:
    data = json.load(f)
print('Top-level keys:', list(data.keys()))
print('School count:', len(data['schools']))
print('First school name:', data['schools'][0]['school_name'])
print('Sample URL:', data['schools'][0]['school_profile_url'])
"
```

Expected output:
```
Top-level keys: ['_meta', 'specialty_taxonomy', 'schools']
School count: 113
First school name: Arizona State University
Sample URL: https://www.gradschoolshopper.com/browse/arizona-state-university.html
```

---

## Task 2: Write the Parser (with Tests)

**Files:**
- Create: `tests/test_build_kb.py`
- Create: `build_kb.py` (parse functions only)

The GSS program pages have a consistent markdown structure. This task writes and tests the function that extracts structured fields from the scraped markdown.

**Reference page structure** (from Auburn University scrape):
```
#### About

[department description text]

#### Follow Us

[Facebook widget — ignore this section]

#### Program Requirements

Master's:

[master's requirements text]

Doctorate:

[doctorate requirements text]

**GRE Requirements:**
Required

**Physics GRE Requirements:**
Not Required

**TOEFL Requirements:**
Required
```

Contact fields (phone, address, email, website) come from the `metadata` dict returned alongside the markdown, not from the markdown text itself.

- [ ] **Step 1: Write failing tests for parse_program_page**

Create `tests/test_build_kb.py`:

```python
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from build_kb import parse_program_page

AUBURN_SAMPLE = """
#### About

Educating the Next Generation of Scientists

The Auburn Physics is a department of the College of Sciences and Mathematics (COSAM) at Auburn University. Our faculty provide a proven path for students to pursue rewarding careers in Physics.

[Faculty and Staff](https://www.auburn.edu/cosam/departments/physics/physics-faculty/index.htm#tenure)

[Research Specialties](http://www.auburn.edu/cosam/departments/physics/research/index.htm)

#### Follow Us

Facebook

#### Program Requirements

Master's:

Each student must complete 30 hours of course work with a minimum grade average of 3.0/4.0. A thesis option and nonthesis option are available.

Doctorate:

Each student must complete 60 hours of course work including dissertation and research hours. Passage of a general doctoral examination is required.

**GRE Requirements:**
Required

**Physics GRE Requirements:**
Not Required

**TOEFL Requirements:**
Required

#### Follow Us

Facebook
"""

AUBURN_METADATA = {
    "business:contact_data:phone_number": "(334) 844-4264",
    "business:contact_data:street_address": "Leach Science Center Suite 2158",
    "business:contact_data:locality": "Auburn",
    "business:contact_data:region": "Alabama",
    "business:contact_data:postal_code": "36849",
    "business:contact_data:email": "landeal@auburn.edu",
    "business:contact_data:website": "http://www.auburn.edu/academic/cosam/departments/physics/",
}


def test_parse_about_text():
    result = parse_program_page(AUBURN_SAMPLE, AUBURN_METADATA)
    assert 'about_text' in result
    assert 'Educating the Next Generation of Scientists' in result['about_text']
    assert 'Facebook' not in result['about_text']


def test_parse_masters_requirements():
    result = parse_program_page(AUBURN_SAMPLE, AUBURN_METADATA)
    assert 'masters_requirements' in result
    assert '30 hours of course work' in result['masters_requirements']


def test_parse_doctorate_requirements():
    result = parse_program_page(AUBURN_SAMPLE, AUBURN_METADATA)
    assert 'doctorate_requirements' in result
    assert '60 hours of course work' in result['doctorate_requirements']


def test_parse_gre_requirements():
    result = parse_program_page(AUBURN_SAMPLE, AUBURN_METADATA)
    assert result.get('gre_required') == 'Required'
    assert result.get('physics_gre_required') == 'Not Required'
    assert result.get('toefl_required') == 'Required'


def test_parse_contact_from_metadata():
    result = parse_program_page(AUBURN_SAMPLE, AUBURN_METADATA)
    assert result['phone'] == '(334) 844-4264'
    assert result['contact_email'] == 'landeal@auburn.edu'
    assert 'auburn.edu' in result['department_website']
    assert 'Leach Science Center' in result['address']
    assert 'Alabama' in result['address']


def test_parse_missing_about_returns_empty_string():
    result = parse_program_page("No about section here.", {})
    assert result.get('about_text', '') == ''


def test_parse_missing_requirements_returns_empty_string():
    result = parse_program_page("No requirements here.", {})
    assert result.get('masters_requirements', '') == ''
    assert result.get('doctorate_requirements', '') == ''


def test_parse_missing_gre_returns_not_specified():
    result = parse_program_page("No GRE info here.", {})
    assert result.get('gre_required', 'Not specified') == 'Not specified'
```

- [ ] **Step 2: Run tests — expect all to fail**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 -m pytest tests/test_build_kb.py -v 2>&1 | head -30
```

Expected: All tests fail with `ImportError: cannot import name 'parse_program_page' from 'build_kb'`

- [ ] **Step 3: Create build_kb.py with parse_program_page**

Create `build_kb.py`:

```python
import re
import json
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed


def parse_program_page(markdown: str, metadata: dict) -> dict:
    """Extract structured fields from a scraped GSS program page."""
    data = {}

    # About text: between "#### About" and the next "#### " heading
    about_match = re.search(
        r'#### About\n\n(.*?)(?=\n#### )',
        markdown, re.DOTALL
    )
    data['about_text'] = about_match.group(1).strip() if about_match else ''

    # Master's requirements: between "Master's:\n\n" and "Doctorate:" or "**GRE"
    masters_match = re.search(
        r"Master's:\n\n(.*?)(?=\n\nDoctorate:|\n\*\*GRE)",
        markdown, re.DOTALL
    )
    data['masters_requirements'] = masters_match.group(1).strip() if masters_match else ''

    # Doctorate requirements: between "Doctorate:\n\n" and "**GRE" or "#### " or end
    doctorate_match = re.search(
        r"Doctorate:\n\n(.*?)(?=\n\*\*GRE|\n#### |\Z)",
        markdown, re.DOTALL
    )
    data['doctorate_requirements'] = doctorate_match.group(1).strip() if doctorate_match else ''

    # GRE / Physics GRE / TOEFL — each appears on the line immediately after the bold label
    gre_match = re.search(r'\*\*GRE Requirements:\*\*\n+(\w[^\n]+)', markdown)
    data['gre_required'] = gre_match.group(1).strip() if gre_match else ''

    phys_gre_match = re.search(r'\*\*Physics GRE Requirements:\*\*\n+(\w[^\n]+)', markdown)
    data['physics_gre_required'] = phys_gre_match.group(1).strip() if phys_gre_match else ''

    toefl_match = re.search(r'\*\*TOEFL Requirements:\*\*\n+(\w[^\n]+)', markdown)
    data['toefl_required'] = toefl_match.group(1).strip() if toefl_match else ''

    # Contact fields from page metadata (Open Graph / business tags)
    street = metadata.get('business:contact_data:street_address', '')
    city = metadata.get('business:contact_data:locality', '')
    region = metadata.get('business:contact_data:region', '')
    postal = metadata.get('business:contact_data:postal_code', '')
    address_parts = [p for p in [street, city, region, postal] if p]
    data['address'] = ', '.join(address_parts)
    data['phone'] = metadata.get('business:contact_data:phone_number', '')
    data['contact_email'] = metadata.get('business:contact_data:email', '')
    data['department_website'] = metadata.get('business:contact_data:website', '')

    return data
```

- [ ] **Step 4: Run tests — expect all to pass**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 -m pytest tests/test_build_kb.py -v
```

Expected: All 8 tests pass.

If `test_parse_about_text` fails with "Facebook in about_text", the regex needs a tighter boundary — change the lookahead to `(?=\n#### Follow Us|\n#### Program)`.

- [ ] **Step 5: Commit**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
git init  # only if not already a git repo
git add build_kb.py tests/ requirements.txt
git commit -m "feat: add parse_program_page with tests"
```

---

## Task 3: Write the Markdown Builder (with Tests)

**Files:**
- Modify: `tests/test_build_kb.py` (add builder tests)
- Modify: `build_kb.py` (add build_school_markdown and url_to_slug)

- [ ] **Step 1: Write failing tests for build_school_markdown and url_to_slug**

Append to `tests/test_build_kb.py`:

```python
from build_kb import build_school_markdown, url_to_slug

SAMPLE_SCHOOL_JSON = {
    "school_name": "Auburn University",
    "department": "Physics",
    "campus_setting": "Rural",
    "acceptance_rate": "40%",
    "acceptance_rate_decimal": 0.4,
    "application_deadline": "Mar 14",
    "ms_granted_2024": 0,
    "phd_granted_2024": 9,
    "first_year_enrollment_fall2024": 12,
    "total_enrollment_fall2024": 56,
    "school_profile_url": "https://gradschoolshopper.com/browse/auburn-university.html",
    "offers_phd": True,
    "offers_masters": True,
    "specialties": ["Atomic, Molecular, & Optical Physics", "Biophysics"],
    "specialty_details": [
        {"specialty": "Atomic, Molecular, & Optical Physics", "phd_type": "Both", "masters_type": "Both"},
        {"specialty": "Biophysics", "phd_type": "Both", "masters_type": "Both"},
    ]
}

SAMPLE_SCRAPED = {
    "about_text": "A great physics department.",
    "masters_requirements": "Complete 30 hours with 3.0 GPA.",
    "doctorate_requirements": "Complete 60 hours including dissertation.",
    "gre_required": "Required",
    "physics_gre_required": "Not Required",
    "toefl_required": "Required",
    "phone": "(334) 844-4264",
    "address": "380 Duncan Drive, Auburn, Alabama 36849",
    "contact_email": "landeal@auburn.edu",
    "department_website": "http://www.auburn.edu/cosam/departments/physics/",
}


def test_markdown_has_school_name_as_h1():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert md.startswith("# Auburn University")


def test_markdown_contains_specialties():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert 'Atomic, Molecular, & Optical Physics' in md
    assert 'PhD: Both' in md


def test_markdown_contains_admissions_data():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert '40%' in md
    assert 'Mar 14' in md
    assert '12' in md  # first year enrollment


def test_markdown_contains_gre_requirements():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert 'GRE' in md
    assert 'Required' in md
    assert 'Not Required' in md


def test_markdown_contains_about_text():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert 'A great physics department.' in md


def test_markdown_contains_program_requirements():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert '30 hours' in md
    assert '60 hours' in md


def test_markdown_contains_gss_profile_link():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert 'gradschoolshopper.com/browse/auburn-university.html' in md


def test_markdown_no_none_values():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, SAMPLE_SCRAPED)
    assert 'None' not in md


def test_markdown_graceful_with_empty_scraped():
    md = build_school_markdown(SAMPLE_SCHOOL_JSON, {})
    # Should still produce valid markdown with JSON data
    assert '# Auburn University' in md
    assert '40%' in md
    # Missing scraped sections should not crash
    assert 'None' not in md


def test_url_to_slug_standard():
    assert url_to_slug('https://gradschoolshopper.com/browse/auburn-university.html') == 'auburn-university'


def test_url_to_slug_with_www():
    assert url_to_slug('https://www.gradschoolshopper.com/browse/arizona-state-university.html') == 'arizona-state-university'
```

- [ ] **Step 2: Run tests — expect new tests to fail**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 -m pytest tests/test_build_kb.py -v 2>&1 | tail -20
```

Expected: First 8 tests pass, new tests fail with `ImportError: cannot import name 'build_school_markdown'`

- [ ] **Step 3: Add build_school_markdown and url_to_slug to build_kb.py**

Append to `build_kb.py` after the `parse_program_page` function:

```python
def url_to_slug(url: str) -> str:
    """Extract school slug from a GSS profile URL.

    'https://gradschoolshopper.com/browse/auburn-university.html' -> 'auburn-university'
    """
    from urllib.parse import urlparse
    path = urlparse(url).path
    filename = os.path.basename(path)
    return filename.replace('.html', '')


def build_school_markdown(school: dict, scraped: dict) -> str:
    """Build a Cassidy knowledge base markdown document for one school.

    Merges structured spreadsheet data (school dict) with scraped page data (scraped dict).
    All fields fall back gracefully if scraped data is missing.
    """
    lines = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append(f"# {school['school_name']}\n")
    lines.append(f"**Department:** {school['department']}  ")
    lines.append(f"**Campus Setting:** {school['campus_setting']}  ")
    if scraped.get('phone'):
        lines.append(f"**Phone:** {scraped['phone']}  ")
    if scraped.get('address'):
        lines.append(f"**Address:** {scraped['address']}  ")
    if scraped.get('contact_email'):
        lines.append(f"**Contact Email:** {scraped['contact_email']}  ")
    if scraped.get('department_website'):
        lines.append(f"**Department Website:** {scraped['department_website']}  ")
    lines.append(f"**GSS Profile:** {school['school_profile_url']}  ")
    lines.append("")

    # ── Specialties ─────────────────────────────────────────────────────────
    lines.append("---\n")
    lines.append("## Specialties\n")
    for sd in school.get('specialty_details', []):
        phd = sd['phd_type'] if sd['phd_type'] != 'None' else '—'
        ms = sd['masters_type'] if sd['masters_type'] != 'None' else '—'
        lines.append(f"- **{sd['specialty']}** — PhD: {phd} | Master's: {ms}")
    lines.append("")

    # ── Admissions & Program Data ────────────────────────────────────────────
    lines.append("---\n")
    lines.append("## Admissions & Program Data\n")
    lines.append("| Field | Value |")
    lines.append("|-------|-------|")
    lines.append(f"| Acceptance Rate | {school.get('acceptance_rate') or 'N/A'} |")
    lines.append(f"| Application Deadline | {school.get('application_deadline') or 'N/A'} |")
    lines.append(f"| First Year Enrollment (Fall 2024) | {school.get('first_year_enrollment_fall2024') or 'N/A'} |")
    lines.append(f"| Total Enrollment (Fall 2024) | {school.get('total_enrollment_fall2024') or 'N/A'} |")
    lines.append(f"| PhDs Granted (2024) | {school.get('phd_granted_2024') or 'N/A'} |")
    lines.append(f"| MS Granted (2024) | {school.get('ms_granted_2024') or 'N/A'} |")
    lines.append("")

    # ── Admissions Requirements ──────────────────────────────────────────────
    lines.append("---\n")
    lines.append("## Admissions Requirements\n")
    lines.append("| Requirement | Status |")
    lines.append("|-------------|--------|")
    lines.append(f"| GRE | {scraped.get('gre_required') or 'Not specified'} |")
    lines.append(f"| Physics GRE | {scraped.get('physics_gre_required') or 'Not specified'} |")
    lines.append(f"| TOEFL | {scraped.get('toefl_required') or 'Not specified'} |")
    lines.append("")

    # ── About ────────────────────────────────────────────────────────────────
    if scraped.get('about_text'):
        lines.append("---\n")
        lines.append("## About\n")
        lines.append(scraped['about_text'])
        lines.append("")

    # ── Program Requirements ─────────────────────────────────────────────────
    if scraped.get('masters_requirements') or scraped.get('doctorate_requirements'):
        lines.append("---\n")
        lines.append("## Program Requirements\n")
        if scraped.get('masters_requirements'):
            lines.append("### Master's\n")
            lines.append(scraped['masters_requirements'])
            lines.append("")
        if scraped.get('doctorate_requirements'):
            lines.append("### Doctorate / PhD\n")
            lines.append(scraped['doctorate_requirements'])
            lines.append("")

    return "\n".join(lines)
```

- [ ] **Step 4: Run all tests — expect all to pass**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 -m pytest tests/test_build_kb.py -v
```

Expected: All 18 tests pass.

- [ ] **Step 5: Commit**

```bash
git add build_kb.py tests/test_build_kb.py
git commit -m "feat: add build_school_markdown and url_to_slug with tests"
```

---

## Task 4: Write the Scraper and Run the Full Pipeline

**Files:**
- Modify: `build_kb.py` (add scrape_school and main)

- [ ] **Step 1: Add scrape_school and main to build_kb.py**

Append to `build_kb.py` after the `build_school_markdown` function:

```python
def scrape_school(app, school: dict) -> tuple:
    """Scrape one school's GSS page and return parsed data.

    Returns: (school_name, scraped_dict, error_str_or_None)
    error_str_or_None is None on success, an error message string on failure.
    """
    url = school['school_profile_url']
    try:
        result = app.scrape_url(url, formats=['markdown'], only_main_content=True)
        # Handle both Pydantic model (v1 SDK) and dict (v0 SDK) response formats
        if hasattr(result, 'markdown'):
            markdown = result.markdown or ''
            metadata = dict(result.metadata) if result.metadata else {}
        else:
            markdown = result.get('markdown', '')
            metadata = result.get('metadata', {})
        parsed = parse_program_page(markdown, metadata)
        return school['school_name'], parsed, None
    except Exception as e:
        return school['school_name'], {}, str(e)


def main():
    api_key = os.environ.get('FIRECRAWL_API_KEY')
    if not api_key:
        raise SystemExit("ERROR: FIRECRAWL_API_KEY environment variable not set")

    from firecrawl import FirecrawlApp
    app = FirecrawlApp(api_key=api_key)

    json_path = Path(__file__).parent / 'gss_programs.json'
    with open(json_path, encoding='utf-8') as f:
        data = json.load(f)
    schools = data['schools']
    print(f"Loaded {len(schools)} schools from gss_programs.json")

    output_dir = Path(__file__).parent / 'kb'
    output_dir.mkdir(exist_ok=True)

    scraped_results = {}
    failed = []

    print(f"Scraping {len(schools)} pages with 10 concurrent workers...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_school = {
            executor.submit(scrape_school, app, school): school
            for school in schools
        }
        for i, future in enumerate(as_completed(future_to_school), 1):
            school = future_to_school[future]
            name, scraped, error = future.result()
            if error:
                failed.append((name, error))
                print(f"  [{i}/{len(schools)}] FAILED: {name} — {error}")
            else:
                scraped_results[name] = scraped
                print(f"  [{i}/{len(schools)}] OK: {name}")

    print(f"\nBuilding {len(schools)} markdown files...")
    for school in schools:
        name = school['school_name']
        scraped = scraped_results.get(name, {})
        markdown = build_school_markdown(school, scraped)
        slug = url_to_slug(school['school_profile_url'])
        output_path = output_dir / f"{slug}.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

    print(f"\nDone.")
    print(f"  Files written: {len(schools)}")
    print(f"  Output directory: {output_dir}")
    if failed:
        print(f"  Failed scrapes ({len(failed)}):")
        for name, err in failed:
            print(f"    - {name}: {err}")


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run a smoke test with 3 schools**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 -c "
import os, json
from pathlib import Path
from firecrawl import FirecrawlApp
from build_kb import scrape_school, build_school_markdown, url_to_slug

app = FirecrawlApp(api_key=os.environ['FIRECRAWL_API_KEY'])
with open('gss_programs.json') as f:
    data = json.load(f)

test_schools = data['schools'][:3]
Path('kb').mkdir(exist_ok=True)

for school in test_schools:
    name, scraped, error = scrape_school(app, school)
    if error:
        print(f'FAILED {name}: {error}')
        continue
    md = build_school_markdown(school, scraped)
    slug = url_to_slug(school['school_profile_url'])
    Path('kb', f'{slug}.md').write_text(md, encoding='utf-8')
    about_preview = scraped.get('about_text', '')[:80].replace('\n', ' ')
    print(f'OK: {name}')
    print(f'   About preview: {about_preview}...')
    print(f'   GRE: {scraped.get(\"gre_required\", \"missing\")}')
    print()
"
```

Expected: 3 schools scraped and written. Each shows a non-empty about preview and a GRE status.

Verify one file looks correct:
```bash
head -60 "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/arizona-state-university.md"
```

Expected: Clean markdown starting with `# Arizona State University`, containing specialties table, admissions data, and About section.

- [ ] **Step 3: Run the full pipeline**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
python3 build_kb.py
```

Expected output:
```
Loaded 113 schools from gss_programs.json
Scraping 113 pages with 10 concurrent workers...
  [1/113] OK: ...
  ...
  [113/113] OK: ...

Building 113 markdown files...

Done.
  Files written: 113
  Output directory: .../kb
  Failed scrapes (0):
```

This takes approximately 3–5 minutes (113 pages / 10 concurrent = ~12 batches, ~15–20 seconds per batch).

If some schools fail with rate limit errors, re-run — the script overwrites existing files so partial runs are safe.

- [ ] **Step 4: Commit**

```bash
git add build_kb.py
git commit -m "feat: add scraper pipeline, produce 113 KB markdown files"
```

---

## Task 5: Verify Output

- [ ] **Step 1: Count files**

```bash
ls "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/" | wc -l
```

Expected: `113`

- [ ] **Step 2: Check for empty or suspiciously small files**

```bash
find "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/" -name "*.md" -size -500c
```

Expected: No output (all files should be > 500 bytes). If any are listed, those schools likely failed silently — re-run the pipeline for those specific URLs.

- [ ] **Step 3: Spot-check 5 files across different specialties**

```bash
for f in auburn-university mit brown-university university-of-california-berkeley stanford-university; do
  path="/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/${f}.md"
  if [ -f "$path" ]; then
    echo "=== $f ==="
    head -5 "$path"
    grep -c "##" "$path" | xargs echo "  Sections:"
    wc -l "$path" | xargs echo "  Lines:"
    echo ""
  fi
done
```

Expected: Each file starts with `# [School Name]`, has 5–7 `##` sections, and is 40–200 lines.

- [ ] **Step 4: Verify no "None" values leaked into any file**

```bash
grep -rl "None" "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/" | wc -l
```

Expected: `0`

- [ ] **Step 5: Check About section coverage**

```bash
grep -rL "## About" "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match/kb/" | wc -l
```

Expected: `0` or a small number (< 10). Files without an About section are programs where the GSS page had no descriptive text — this is acceptable.

- [ ] **Step 6: Final commit with output summary**

```bash
cd "/Users/mackwallace/Claude Projects/GradSchoolShopper-Physics-Match"
git add kb/
git commit -m "data: add 113 GSS knowledge base markdown files for Cassidy import"
```

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `FIRECRAWL_API_KEY not set` | Env var missing | `source ~/.zshrc` |
| `AttributeError: 'dict' has no attribute 'markdown'` | SDK v0 dict response | Change `result.markdown` → `result.get('markdown', '')` throughout |
| Rate limit 429 | Too many concurrent requests | Reduce `max_workers` from 10 to 5 in `scrape_school` call |
| File count < 113 | Some schools failed | Re-run — pipeline is idempotent, overwrites existing files |
| `## About` missing from many files | Pages have no About text | Acceptable — those programs just won't have this section in Cassidy |

# 🐆 Chui Data Quality Checker

### Upload your data. Find the problems. Fix them before they cost you.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-28%20passing-brightgreen?style=flat-square)

🔗 **[Try it live → chui-quality-checker.streamlit.app](https://chui-quality-checker.streamlit.app)**

---

## What This Does (No Tech Background Needed)

Every business has data — customer lists, M-Pesa exports, inventory spreadsheets. But most of this data has hidden problems: duplicate records, missing amounts, dates written in three different formats, phone numbers with inconsistent spacing. These problems cause wrong reports, failed imports, and bad decisions that cost real money.

This tool reads your CSV or Excel file and tells you exactly what is wrong — in plain English, with a score out of 100, so you know how serious the problems are before you send the data anywhere important. No installation, no account, no technical knowledge required.

## How To Use It

1. Go to **[chui-quality-checker.streamlit.app](https://chui-quality-checker.streamlit.app)**
2. Upload your CSV or Excel file — or click **"Try sample M-Pesa file"** to see it in action immediately
3. Read your quality report across 5 tabs
4. Download a CSV summary of all findings to share with your team

No account needed. No installation. Works on any device with a browser. Your data never leaves your browser session.

## What It Checks

| Check | What It Finds |
|-------|--------------|
| **Missing Values** | Columns with blank or empty cells, ranked by severity (ok / warning / critical) |
| **Duplicates** | Exact repeated rows that inflate counts and totals |
| **Date Formats** | Columns where dates are written inconsistently (DD/MM vs YYYY-MM-DD etc.) |
| **Numeric Issues** | Negative amounts, currency symbols in number fields, statistical outliers |
| **Type Mismatches** | Columns that should be numbers but contain text like "KES 1,200" |
| **String Consistency** | Categorical columns with multiple spellings of the same value (Active / ACTIVE / active) |

---

## For Developers & Technical Reviewers

### Architecture

```
Uploaded File (CSV / Excel / TSV)
        ↓
utils/file_handler.py   ← reads file, detects delimiter + encoding
        ↓
checks/  (6 independent modules — pure functions, independently testable)
    ├── missing_values.py
    ├── duplicates.py
    ├── date_checker.py
    ├── numeric_checker.py
    ├── type_checker.py
    └── string_quality.py
        ↓
reports/quality_score.py  ← aggregates findings into 0-100 score + grade
        ↓
app.py  ← renders 5-tab Streamlit UI + downloadable CSV report
```

**Key design decisions:**
- All check modules are **pure functions**: same input always produces same output — easy to test and easy to reuse outside Streamlit
- Results cached in `st.session_state`: tab switches are instant; checks run once per upload
- Each check module can be imported independently — they work in any Python project
- No database, no server, no credentials: everything runs in memory

### Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Core language |
| Streamlit | 1.35.0 | Web UI framework |
| pandas | 2.2.2 | File reading and data analysis |
| openpyxl | 3.1.2 | Excel file support |
| chardet | 5.2.0 | Encoding detection |
| python-dateutil | 2.9.0 | Date parsing |
| pytest | 8.2.0 | 28 unit tests |

### Running Locally

```bash
git clone https://github.com/[username]/chui_quality_checker
cd chui_quality_checker
pip install -r requirements.txt
streamlit run app.py
# Open http://localhost:8501
```

### Running Tests

```bash
pytest tests/ -v
# Expected: 28 tests pass
```

Tests cover: missing value severity thresholds, duplicate counting and percentage accuracy, date format detection across 6 format patterns, currency symbol detection, outlier flagging, and type mismatch identification.

### Deploying to Streamlit Community Cloud (Free, ~2 minutes)

1. Push this repo to GitHub (public)
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Select this repo + `app.py` as the entry point
5. Click **Deploy**

The sample data file (`sample_data/dirty_mpesa_sample.csv`) is committed to the repo so first-time visitors can try the app immediately without uploading anything.

### Project Structure

```
chui_quality_checker/
├── app.py                          ← Main Streamlit app (run this)
├── requirements.txt
├── .streamlit/
│   └── config.toml                 ← Brand theme (warm ink/paper palette)
├── checks/
│   ├── missing_values.py
│   ├── duplicates.py
│   ├── date_checker.py
│   ├── numeric_checker.py
│   ├── type_checker.py
│   └── string_quality.py
├── reports/
│   └── quality_score.py            ← Weighted 0-100 scoring engine
├── utils/
│   └── file_handler.py             ← File reading + encoding detection
├── sample_data/
│   ├── generate_sample.py          ← Script to regenerate test data
│   └── dirty_mpesa_sample.csv      ← 30,000-row dirty M-Pesa dataset
└── tests/
    ├── test_missing_values.py      ← 7 tests
    ├── test_duplicates.py          ← 8 tests
    ├── test_date_checker.py        ← 6 tests
    └── test_numeric_checker.py     ← 7 tests
```

### Scoring Engine

The quality score (0–100) uses weighted deductions:

| Check | Max Deduction | Scaling |
|-------|:---:|---------|
| Missing values | -30 pts | Scaled by % missing + critical columns |
| Duplicates | -25 pts | Scaled by duplicate % |
| Date inconsistencies | -20 pts | Per inconsistent date column |
| Numeric anomalies | -15 pts | Currency symbols trigger higher penalty |
| Type mismatches | -10 pts | Per mismatched column |

Grades: A (90–100) · B (75–89) · C (60–74) · D (40–59) · F (0–39)

---

## Sample Data

The included `dirty_mpesa_sample.csv` (30,000 rows) is a synthetic M-Pesa transaction file with deliberately injected problems:

| Problem | Count |
|---------|------:|
| Exact duplicate rows | 350 |
| Missing `amount_kes` | 200 |
| Negative `amount_kes` | 150 |
| `"KES "` prefix in amount (text, not number) | 100 |
| Inconsistent phone formats | throughout |
| Inconsistent date formats (DD/MM/YYYY, YYYY-MM-DD, D-Mon-YY) | throughout |
| Mixed transaction_type case (Sale / SALE / sale) | throughout |

Run `python sample_data/generate_sample.py` to regenerate with a new random seed. The script prints a manifest of exactly what was injected.

---

## CV / Portfolio Summary

- Built and deployed a live Streamlit data quality web app performing 6 automated checks (missing values, duplicates, date format consistency, numeric anomalies, type mismatches, string quality) on uploaded CSV/Excel files — accessible at a public URL with zero installation required
- Designed a weighted 0–100 quality scoring engine aggregating findings across all checks into a letter grade with a plain-English summary sentence for non-technical users
- Engineered stateless, pure-function check modules with 28 pytest unit tests, independently importable outside the Streamlit context
- Resolved a Python 3.12 pandas `StringDtype` compatibility issue affecting dtype detection across all check modules; test suite passes on Python 3.10–3.12
- Deployed to Streamlit Community Cloud with Chui Data brand theming; functions as both a portfolio piece and a live lead-generation tool for chuiassistant.com

---

*Built by [Chui Data](https://chuiassistant.com) · [audit@chuidata.com](mailto:audit@chuidata.com) · chuiassistant.com*

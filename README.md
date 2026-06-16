# 🐆 Chui Data Quality Checker

### Upload your data. Find the problems. Fix them before they cost you.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35-red?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
![Tests](https://img.shields.io/badge/Tests-28%20passing-brightgreen?style=flat-square)

🔗 **[Try it live → chui-quality-checker.streamlit.app](https://chui-quality-checker.streamlit.app)**

---

## What This Does

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

---

*Built by [Chui Data](https://chuiassistant.com) · [audit@chuidata.com](mailto:audit@chuidata.com) · chuiassistant.com*

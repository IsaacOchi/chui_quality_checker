"""
app.py — Chui Data Quality Checker
Main Streamlit application. Run with: streamlit run app.py
"""

import io
import os
import pandas as pd
import streamlit as st

from utils.file_handler import read_uploaded_file
from checks.missing_values import check_missing
from checks.duplicates import check_duplicates
from checks.date_checker import detect_date_columns, check_date_formats
from checks.numeric_checker import check_numerics
from checks.type_checker import check_type_consistency
from checks.string_quality import check_string_quality
from reports.quality_score import calculate_score

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Chui Data Quality Checker",
    page_icon="🐆",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    .score-ring {
        font-size: 4rem;
        font-weight: bold;
        text-align: center;
    }
    .kpi-card {
        background: var(--secondary-background-color, #F5E6D3);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        border-left: 4px solid #8B4513;
    }
    .severity-critical { color: #C0392B; font-weight: bold; }
    .severity-warning  { color: #D68910; font-weight: bold; }
    .severity-ok       { color: #1E8449; font-weight: bold; }
    .footer {
        margin-top: 2rem;
        text-align: center;
        color: #888;
        font-size: 0.85rem;
        border-top: 1px solid #e0d0c0;
        padding-top: 0.75rem;
    }
</style>
""", unsafe_allow_html=True)


# ── Helpers ───────────────────────────────────────────────────────────────────

def severity_icon(s: str) -> str:
    return {"critical": "🔴", "warning": "🟡", "ok": "🟢"}.get(s, "⚪")


def grade_color(grade: str) -> str:
    return {"A": "#1E8449", "B": "#2ECC71", "C": "#D68910", "D": "#E67E22", "F": "#C0392B"}.get(grade, "#555")


def run_all_checks(df: pd.DataFrame) -> dict:
    """Run all six check modules. Returns dict of results."""
    missing_result  = check_missing(df)
    dup_result      = check_duplicates(df)
    date_cols       = detect_date_columns(df)
    date_result     = check_date_formats(df, date_cols)
    numeric_result  = check_numerics(df)
    type_result     = check_type_consistency(df)
    string_result   = check_string_quality(df)
    score_result    = calculate_score(
        missing_result, dup_result, date_result,
        numeric_result, type_result, string_result,
    )
    return {
        "missing":  missing_result,
        "dupes":    dup_result,
        "dates":    date_result,
        "numeric":  numeric_result,
        "types":    type_result,
        "strings":  string_result,
        "score":    score_result,
    }


def build_download_csv(results: dict, metadata: dict) -> bytes:
    """Build a flat CSV summary of all findings for download."""
    rows = []

    # Missing values
    for c in results["missing"]["columns"]:
        rows.append({
            "check": "Missing Values",
            "column": c["column"],
            "detail": f"{c['missing_count']} missing ({c['missing_pct']}%)",
            "severity": c["severity"],
        })

    # Duplicates
    rows.append({
        "check": "Duplicates",
        "column": "ALL",
        "detail": f"{results['dupes']['exact_duplicate_rows']} exact duplicate rows ({results['dupes']['duplicate_pct']}%)",
        "severity": results["dupes"]["severity"],
    })

    # Date issues
    for c in results["dates"]["columns"]:
        if not c["is_consistent"]:
            rows.append({
                "check": "Date Formats",
                "column": c["column"],
                "detail": f"Mixed formats: {', '.join(c['formats_found'])}",
                "severity": "warning",
            })

    # Numeric issues
    for c in results["numeric"]["columns"]:
        rows.append({
            "check": "Numeric Issues",
            "column": c["column"],
            "detail": f"Negatives: {c['negative_count']}, Currency symbols: {c['currency_symbol_rows']}, Outliers: {c['outlier_count']}",
            "severity": c["severity"],
        })

    # Type mismatches
    for c in results["types"]["mismatched_columns"]:
        rows.append({
            "check": "Type Mismatch",
            "column": c["column"],
            "detail": f"Stored as {c['pandas_type']}, likely is {c['inferred_type']}",
            "severity": "warning",
        })

    df_out = pd.DataFrame(rows)
    return df_out.to_csv(index=False).encode("utf-8")


# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.shields.io/badge/🐆_Chui_Data-Quality_Checker-8B4513?style=for-the-badge", use_column_width=True)
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload your file",
        type=["csv", "xlsx", "xls", "tsv"],
        help="Supports CSV, Excel (XLSX/XLS), and TSV files",
    )

    sample_path = os.path.join(os.path.dirname(__file__), "sample_data", "dirty_mpesa_sample.csv")
    if os.path.exists(sample_path):
        use_sample = st.button("📂 Try sample M-Pesa file", use_container_width=True)
    else:
        use_sample = False

    st.markdown("---")
    st.markdown("""
**About Chui Data**

We help Kenyan businesses find and fix data quality problems before they affect reports,
imports, and decisions. This tool is a free demonstration of our auditing process.

[🌐 chuiassistant.com](https://chuiassistant.com) · [✉️ audit@chuidata.com](mailto:audit@chuidata.com)
""")


# ── Main ──────────────────────────────────────────────────────────────────────

st.markdown("# 🐆 Chui Data Quality Checker")
st.markdown("**Upload your CSV or Excel file. Get an instant data quality report.**")

# Determine file source
file_source = None
if use_sample and os.path.exists(sample_path):
    file_source = sample_path
    st.info("📂 Using the built-in dirty M-Pesa sample file (30,000 rows). Upload your own file via the sidebar to analyse your data.")
elif uploaded_file is not None:
    file_source = uploaded_file

# Load and run checks
if file_source is not None:
    # Only re-run if the source changed
    source_key = str(getattr(file_source, "name", file_source))
    if st.session_state.get("_source_key") != source_key:
        with st.spinner("Reading file and running quality checks…"):
            try:
                df, metadata = read_uploaded_file(file_source)
                results = run_all_checks(df)
                st.session_state["_df"]          = df
                st.session_state["_metadata"]     = metadata
                st.session_state["_results"]      = results
                st.session_state["_source_key"]   = source_key
            except ValueError as e:
                st.error(f"⚠️ {e}")
                st.stop()
            except Exception as e:
                st.error(f"⚠️ Could not process this file. Please check it is a valid CSV or Excel file. Detail: {e}")
                st.stop()

if "_results" not in st.session_state:
    st.markdown("""
---
### How it works

1. Upload a **CSV, Excel, or TSV file** in the sidebar — or click **Try sample file** to see the checker in action
2. The checker scans your data across six quality dimensions
3. You get a **score out of 100**, a grade, and tab-by-tab findings
4. Download a **CSV summary** of all findings to share with your team

**No account. No installation. Your data never leaves your browser session.**
""")
    st.stop()

# Retrieve from session
df       = st.session_state["_df"]
metadata = st.session_state["_metadata"]
results  = st.session_state["_results"]
score_r  = results["score"]


# ── Show file metadata under sidebar upload ───────────────────────────────────
with st.sidebar:
    st.markdown("---")
    st.markdown(f"""
**File loaded**
- 📄 `{metadata['filename']}`
- Rows: **{metadata['rows']:,}**
- Columns: **{metadata['columns']}**
- Size: **{metadata['file_size_kb']} KB**
- Delimiter: `{metadata['delimiter_detected']}`
""")


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Overview",
    "🔍 Missing Values",
    "👥 Duplicates",
    "📅 Format Issues",
    "🔢 Numeric Issues",
])


# ─── TAB 1: Overview ─────────────────────────────────────────────────────────
with tab1:
    grade  = score_r["grade"]
    label  = score_r["grade_label"]
    score  = score_r["score"]
    color  = grade_color(grade)

    col_score, col_kpis = st.columns([1, 3])

    with col_score:
        st.markdown(f"""
<div style="text-align:center; padding: 1rem;">
    <div style="font-size:5rem; line-height:1; color:{color}; font-weight:bold;">{score}</div>
    <div style="font-size:1.2rem; color:{color}; font-weight:bold;">Grade {grade} — {label}</div>
    <div style="font-size:0.85rem; color:#888; margin-top:0.3rem;">out of 100</div>
</div>
""", unsafe_allow_html=True)

    with col_kpis:
        k1, k2, k3, k4 = st.columns(4)
        total_issues = (
            results["missing"]["total_missing_cells"]
            + results["dupes"]["exact_duplicate_rows"]
            + results["numeric"]["total_numeric_issues"]
            + results["types"]["mismatch_count"]
        )
        k1.metric("Total Rows",       f"{metadata['rows']:,}")
        k2.metric("Total Columns",    f"{metadata['columns']}")
        k3.metric("Issues Found",     f"{total_issues:,}")
        k4.metric("Quality Score",    f"{score}/100")

    st.markdown(f"**{score_r['summary_sentence']}**")
    st.markdown("---")

    # Issues table
    check_rows = [
        {
            "Check":        "Missing Values",
            "Status":       severity_icon(results["missing"]["columns"][0]["severity"] if results["missing"]["columns"] else "ok"),
            "Issues Found": f"{results['missing']['total_missing_cells']:,} missing cells",
            "Severity":     (results["missing"]["columns"][0]["severity"] if results["missing"]["columns"] else "ok").title(),
        },
        {
            "Check":        "Duplicates",
            "Status":       severity_icon(results["dupes"]["severity"]),
            "Issues Found": f"{results['dupes']['exact_duplicate_rows']:,} duplicate rows",
            "Severity":     results["dupes"]["severity"].title(),
        },
        {
            "Check":        "Date Formats",
            "Status":       severity_icon("warning" if any(not c["is_consistent"] for c in results["dates"]["columns"]) else "ok"),
            "Issues Found": f"{sum(1 for c in results['dates']['columns'] if not c['is_consistent'])} inconsistent date columns",
            "Severity":     ("Warning" if any(not c["is_consistent"] for c in results["dates"]["columns"]) else "Ok"),
        },
        {
            "Check":        "Numeric Issues",
            "Status":       severity_icon(results["numeric"]["columns"][0]["severity"] if results["numeric"]["columns"] else "ok"),
            "Issues Found": f"{results['numeric']['total_numeric_issues']:,} total numeric issues",
            "Severity":     (results["numeric"]["columns"][0]["severity"] if results["numeric"]["columns"] else "ok").title(),
        },
        {
            "Check":        "Type Mismatches",
            "Status":       severity_icon("warning" if results["types"]["mismatch_count"] > 0 else "ok"),
            "Issues Found": f"{results['types']['mismatch_count']} mismatched columns",
            "Severity":     ("Warning" if results["types"]["mismatch_count"] > 0 else "Ok"),
        },
        {
            "Check":        "String Quality",
            "Status":       severity_icon("warning" if results["strings"]["total_string_issues"] > 0 else "ok"),
            "Issues Found": f"{results['strings']['total_string_issues']} columns with case/whitespace issues",
            "Severity":     ("Warning" if results["strings"]["total_string_issues"] > 0 else "Ok"),
        },
    ]
    st.dataframe(pd.DataFrame(check_rows), use_container_width=True, hide_index=True)

    # Score breakdown
    with st.expander("Score breakdown"):
        bd = score_r["breakdown"]
        rows_bd = [
            {"Check": k.replace("_", " ").title(), "Points Deducted": v["points_deducted"], "Reason": v["reason"]}
            for k, v in bd.items()
        ]
        st.dataframe(pd.DataFrame(rows_bd), use_container_width=True, hide_index=True)

    # Download button
    csv_bytes = build_download_csv(results, metadata)
    st.download_button(
        label="📥 Download Full Report (CSV)",
        data=csv_bytes,
        file_name=f"chui_quality_report_{metadata['filename'].replace('.', '_')}.csv",
        mime="text/csv",
    )

    st.markdown('<div class="footer">Built by Chui Data · <a href="mailto:audit@chuidata.com">audit@chuidata.com</a> · <a href="https://chuiassistant.com">chuiassistant.com</a></div>', unsafe_allow_html=True)


# ─── TAB 2: Missing Values ────────────────────────────────────────────────────
with tab2:
    mr = results["missing"]
    st.markdown(f"### Missing Values")
    st.markdown(f"**{mr['total_missing_cells']:,}** missing cells across all columns ({mr['missing_pct_overall']}% of all data)")

    if mr["columns_over_threshold"]:
        st.warning(
            f"⚠️ **{len(mr['columns_over_threshold'])} column(s) have more than 20% missing data** — "
            f"these should be investigated before using this file for analysis or reporting: "
            f"`{'`, `'.join(mr['columns_over_threshold'])}`"
        )

    # Bar chart
    cols_with_missing = [c for c in mr["columns"] if c["missing_count"] > 0]
    if cols_with_missing:
        chart_df = pd.DataFrame(cols_with_missing).set_index("column")[["missing_pct"]]
        st.bar_chart(chart_df)
    else:
        st.success("✅ No missing values found in this file.")

    # Table
    table_rows = []
    for c in mr["columns"]:
        table_rows.append({
            "Column":         c["column"],
            "Missing Count":  c["missing_count"],
            "Missing %":      f"{c['missing_pct']}%",
            "Severity":       f"{severity_icon(c['severity'])} {c['severity'].title()}",
        })
    st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    st.markdown('<div class="footer">Built by Chui Data · <a href="mailto:audit@chuidata.com">audit@chuidata.com</a> · <a href="https://chuiassistant.com">chuiassistant.com</a></div>', unsafe_allow_html=True)


# ─── TAB 3: Duplicates ───────────────────────────────────────────────────────
with tab3:
    dr = results["dupes"]
    st.markdown("### Duplicate Rows")

    col_a, col_b = st.columns(2)
    col_a.metric("Duplicate Rows", f"{dr['exact_duplicate_rows']:,}")
    col_b.metric("As % of Total",  f"{dr['duplicate_pct']}%")

    if dr["exact_duplicate_rows"] > 0:
        sev = dr["severity"]
        if sev == "critical":
            st.error(
                f"🔴 **Critical:** {dr['exact_duplicate_rows']:,} rows appear more than once "
                f"({dr['duplicate_pct']}% of your data). "
                f"Duplicate transactions can inflate revenue figures, double-count customers, "
                f"and cause incorrect totals in reports."
            )
        elif sev == "warning":
            st.warning(
                f"🟡 **Warning:** {dr['exact_duplicate_rows']:,} duplicate rows found. "
                f"Investigate whether these are legitimate repeated transactions "
                f"or data entry errors."
            )

        if not dr["duplicate_sample"].empty:
            st.markdown("**Sample duplicate rows (showing first 10 of the duplicated set):**")
            st.dataframe(dr["duplicate_sample"], use_container_width=True)
    else:
        st.success("✅ No exact duplicate rows found.")

    st.markdown('<div class="footer">Built by Chui Data · <a href="mailto:audit@chuidata.com">audit@chuidata.com</a> · <a href="https://chuiassistant.com">chuiassistant.com</a></div>', unsafe_allow_html=True)


# ─── TAB 4: Format Issues ────────────────────────────────────────────────────
with tab4:
    st.markdown("### Format Issues")

    # Date section
    date_cols_results = results["dates"]["columns"]
    st.markdown("#### 📅 Date Columns")
    if not date_cols_results:
        st.info("No date columns detected in this file.")
    else:
        for dc in date_cols_results:
            status = "✅ Consistent" if dc["is_consistent"] else "⚠️ Mixed formats"
            with st.expander(f"{dc['column']} — {status}"):
                st.markdown(f"**Formats detected:** `{'`, `'.join(dc['formats_found']) if dc['formats_found'] else 'none'}`")
                if not dc["is_consistent"] and dc["inconsistent_examples"]:
                    st.markdown("**Examples of mixed formatting:**")
                    for ex in dc["inconsistent_examples"]:
                        st.markdown(f"- `{ex['value']}` → matches `{ex['format']}`")
                st.markdown(f"**Sample values:** `{'`, `'.join(str(v) for v in dc['sample_values'][:5])}`")

    st.markdown("---")

    # Type mismatches section
    type_r = results["types"]
    st.markdown("#### 🔢 Type Mismatches")
    if type_r["mismatch_count"] == 0:
        st.success("✅ All columns have consistent data types.")
    else:
        for col_info in type_r["mismatched_columns"]:
            with st.expander(f"{col_info['column']} — stored as `{col_info['pandas_type']}`, likely `{col_info['inferred_type']}`"):
                st.markdown(
                    f"Column **`{col_info['column']}`** is stored as `{col_info['pandas_type']}` "
                    f"but appears to be `{col_info['inferred_type']}`. "
                    f"This will cause errors in Excel formulas and most analysis tools."
                )
                if col_info["sample_mixed_values"]:
                    st.markdown(f"**Problematic values:** `{'`, `'.join(str(v) for v in col_info['sample_mixed_values'])}`")

    st.markdown("---")

    # String quality section
    str_r = results["strings"]
    st.markdown("#### 🔤 String Consistency")
    if str_r["total_string_issues"] == 0:
        st.success("✅ No whitespace or mixed-case issues found in categorical columns.")
    else:
        for col_info in str_r["columns_with_issues"]:
            with st.expander(f"{col_info['column']}"):
                if col_info["has_leading_trailing_whitespace"]:
                    st.markdown(f"⚠️ **{col_info['whitespace_row_count']} rows** have leading or trailing whitespace — values like `\" Active\"` won't match `\"Active\"` in lookups.")
                if col_info["sample_inconsistencies"]:
                    st.markdown("**Value inconsistencies (same value, different spellings):**")
                    for s in col_info["sample_inconsistencies"]:
                        st.markdown(f"- {s}")

    st.markdown('<div class="footer">Built by Chui Data · <a href="mailto:audit@chuidata.com">audit@chuidata.com</a> · <a href="https://chuiassistant.com">chuiassistant.com</a></div>', unsafe_allow_html=True)


# ─── TAB 5: Numeric Issues ───────────────────────────────────────────────────
with tab5:
    nr = results["numeric"]
    st.markdown("### Numeric Issues")

    if nr["currency_symbols_detected"]:
        st.warning(
            f"⚠️ Currency symbols found in numeric columns: **{', '.join(nr['currency_symbols_detected'])}**. "
            f"Values like `KES 3,200` are stored as text and will break calculations. "
            f"Strip the symbol and convert to a plain number before analysis."
        )

    if not nr["columns"]:
        st.success("✅ No numeric columns with issues found.")
    else:
        for col_info in nr["columns"]:
            sev = col_info["severity"]
            icon = severity_icon(sev)
            with st.expander(f"{icon} {col_info['column']} — {sev.title()}"):
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Negative values",       col_info["negative_count"])
                c2.metric("Currency symbol rows",  col_info["currency_symbol_rows"])
                c3.metric("Outliers (3σ)",         col_info["outlier_count"])
                c4.metric("Non-numeric text rows", col_info["text_in_numeric_rows"])

                if col_info["negative_count"] > 0:
                    st.markdown(
                        f"**{col_info['negative_count']} negative values** ({col_info['negative_pct']}% of rows). "
                        f"Verify whether negatives are intentional (refunds) or data errors."
                    )
                if col_info["currency_symbol_rows"] > 0:
                    st.markdown(
                        f"**{col_info['currency_symbol_rows']} rows** contain currency symbols "
                        f"({', '.join(col_info['currency_symbols_found'])}). "
                        f"These prevent numeric operations like SUM and AVERAGE."
                    )
                if col_info["outlier_count"] > 0:
                    st.markdown(
                        f"**{col_info['outlier_count']} statistical outliers** detected (beyond 3 standard deviations). "
                        f"Review these values — they may be genuine large transactions or data entry errors."
                    )

    st.markdown('<div class="footer">Built by Chui Data · <a href="mailto:audit@chuidata.com">audit@chuidata.com</a> · <a href="https://chuiassistant.com">chuiassistant.com</a></div>', unsafe_allow_html=True)

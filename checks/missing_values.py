"""
checks/missing_values.py
Detects missing/null values across all columns, ranked by severity.
"""

import pandas as pd


def check_missing(df: pd.DataFrame) -> dict:
    """
    Analyse missing values across all columns.

    Returns:
        dict with keys:
            total_missing_cells (int)
            missing_pct_overall (float)
            columns (list of dicts: column, missing_count, missing_pct, severity)
            columns_over_threshold (list of column names with >20% missing)
    """
    total_cells = df.size
    total_missing = int(df.isnull().sum().sum())
    missing_pct_overall = round((total_missing / total_cells * 100), 2) if total_cells > 0 else 0.0

    columns = []
    for col in df.columns:
        missing_count = int(df[col].isnull().sum())
        missing_pct = round((missing_count / len(df) * 100), 2) if len(df) > 0 else 0.0
        severity = _severity(missing_pct)
        columns.append({
            "column": col,
            "missing_count": missing_count,
            "missing_pct": missing_pct,
            "severity": severity,
        })

    # Sort descending by missing_pct
    columns.sort(key=lambda x: x["missing_pct"], reverse=True)

    columns_over_threshold = [c["column"] for c in columns if c["missing_pct"] > 20]

    return {
        "total_missing_cells": total_missing,
        "missing_pct_overall": missing_pct_overall,
        "columns": columns,
        "columns_over_threshold": columns_over_threshold,
    }


def _severity(missing_pct: float) -> str:
    if missing_pct > 50:
        return "critical"
    elif missing_pct >= 10:
        return "warning"
    else:
        return "ok"

"""
checks/duplicates.py
Detects exact duplicate rows in the DataFrame.
"""

import pandas as pd


def check_duplicates(df: pd.DataFrame) -> dict:
    """
    Identify exact duplicate rows.

    Returns:
        dict with keys:
            exact_duplicate_rows (int)
            duplicate_pct (float)
            duplicate_sample (pd.DataFrame — first 5 duplicate pairs)
            severity ("critical" | "warning" | "ok")
    """
    if df.empty:
        return {
            "exact_duplicate_rows": 0,
            "duplicate_pct": 0.0,
            "duplicate_sample": pd.DataFrame(),
            "severity": "ok",
        }

    duplicate_mask = df.duplicated(keep=False)
    duplicate_rows = df[duplicate_mask]

    exact_duplicate_rows = int(df.duplicated(keep="first").sum())
    total_rows = len(df)
    duplicate_pct = round((exact_duplicate_rows / total_rows * 100), 2) if total_rows > 0 else 0.0

    # Sample: show up to 5 duplicate rows for preview
    if not duplicate_rows.empty:
        duplicate_sample = duplicate_rows.head(10)
    else:
        duplicate_sample = pd.DataFrame()

    severity = _severity(duplicate_pct)

    return {
        "exact_duplicate_rows": exact_duplicate_rows,
        "duplicate_pct": duplicate_pct,
        "duplicate_sample": duplicate_sample,
        "severity": severity,
    }


def _severity(duplicate_pct: float) -> str:
    if duplicate_pct > 5:
        return "critical"
    elif duplicate_pct >= 1:
        return "warning"
    else:
        return "ok"

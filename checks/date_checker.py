"""
checks/date_checker.py
Detects date columns and identifies inconsistent date formats.
"""

import re
import pandas as pd
from dateutil import parser as dateutil_parser


# Common date format patterns mapped to regex
DATE_PATTERNS = [
    ("%d/%m/%Y", r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    ("%m/%d/%Y", r"\b\d{1,2}/\d{1,2}/\d{4}\b"),
    ("%Y-%m-%d", r"\b\d{4}-\d{2}-\d{2}\b"),
    ("%d-%m-%Y", r"\b\d{1,2}-\d{1,2}-\d{4}\b"),
    ("%d-%b-%y", r"\b\d{1,2}-[A-Za-z]{3}-\d{2}\b"),
    ("%d-%b-%Y", r"\b\d{1,2}-[A-Za-z]{3}-\d{4}\b"),
    ("%b %d, %Y", r"\b[A-Za-z]{3}\s+\d{1,2},\s*\d{4}\b"),
    ("%d %B %Y", r"\b\d{1,2}\s+[A-Za-z]+\s+\d{4}\b"),
    ("%Y/%m/%d", r"\b\d{4}/\d{2}/\d{2}\b"),
]


def detect_date_columns(df: pd.DataFrame) -> list[str]:
    """
    Return a list of column names that appear to contain date values.
    Uses regex pattern matching on a sample of values.
    """
    date_cols = []

    for col in df.columns:
        # Skip already-parsed datetime columns
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            date_cols.append(col)
            continue

        # Check if column name hints at dates
        col_lower = col.lower()
        name_hint = any(kw in col_lower for kw in ("date", "time", "dt", "dob", "created", "updated", "day"))

        # Sample non-null string values
        sample = df[col].dropna().astype(str).head(100)
        if len(sample) == 0:
            continue

        match_count = sum(1 for val in sample if _looks_like_date(val))
        match_ratio = match_count / len(sample)

        if match_ratio >= 0.6 or (name_hint and match_ratio >= 0.3):
            date_cols.append(col)

    return date_cols


def check_date_formats(df: pd.DataFrame, date_columns: list[str]) -> dict:
    """
    For each detected date column, identify which date formats are present
    and whether the column is consistent (single format).

    Returns:
        dict with key:
            columns: list of dicts with:
                column, formats_found, is_consistent, sample_values, inconsistent_examples
    """
    results = []

    for col in date_columns:
        sample_vals = df[col].dropna().astype(str).head(200).tolist()
        formats_found = _detect_formats_in_values(sample_vals)
        is_consistent = len(formats_found) <= 1

        inconsistent_examples = []
        if not is_consistent:
            # Show a few examples of values matching each format
            for fmt in formats_found[:3]:
                for val in sample_vals[:50]:
                    if _matches_format(val, fmt):
                        inconsistent_examples.append({"value": val, "format": fmt})
                        break

        results.append({
            "column": col,
            "formats_found": formats_found,
            "is_consistent": is_consistent,
            "sample_values": sample_vals[:5],
            "inconsistent_examples": inconsistent_examples,
        })

    return {"columns": results}


def _looks_like_date(value: str) -> bool:
    """Quick check if a string value looks like a date."""
    value = value.strip()
    # Skip pure numbers (could be IDs)
    if re.match(r"^\d+$", value):
        return False
    for _, pattern in DATE_PATTERNS:
        if re.search(pattern, value):
            return True
    # Fallback: try dateutil
    try:
        dateutil_parser.parse(value, fuzzy=False)
        return True
    except Exception:
        return False


def _detect_formats_in_values(values: list[str]) -> list[str]:
    """Return list of date format strings detected across a list of string values."""
    format_hits = {}

    for val in values:
        val = val.strip()
        if not val:
            continue
        for fmt, pattern in DATE_PATTERNS:
            if re.search(pattern, val):
                format_hits[fmt] = format_hits.get(fmt, 0) + 1
                break  # Only count the first matching format per value

    # Return formats that appear in at least 2% of values
    threshold = max(1, len(values) * 0.02)
    return [fmt for fmt, count in format_hits.items() if count >= threshold]


def _matches_format(value: str, fmt: str) -> bool:
    """Check if a value matches a specific date format string."""
    try:
        pd.to_datetime(value, format=fmt)
        return True
    except Exception:
        return False

"""
checks/numeric_checker.py
Detects numeric anomalies: negatives, currency symbols, outliers.
"""

import re
import pandas as pd
import numpy as np


CURRENCY_SYMBOLS = ["KES", "KSh", "Ksh", "USD", "$", "£", "€", "TSh", "UGX"]
CURRENCY_PATTERN = re.compile(r"[KkUuT$£€]", re.IGNORECASE)


def check_numerics(df: pd.DataFrame) -> dict:
    """
    Analyse numeric and potentially-numeric columns for anomalies.

    Returns:
        dict with keys:
            columns (list of dicts per column)
            currency_symbols_detected (list of symbols found globally)
            total_numeric_issues (int)
    """
    columns = []
    global_currency_symbols = set()
    total_issues = 0

    # Include actual numeric columns and object columns that look numeric
    candidate_cols = _get_numeric_candidate_columns(df)

    for col in candidate_cols:
        result = _analyse_column(df, col)
        if result:
            columns.append(result)
            global_currency_symbols.update(result.get("currency_symbols_found", []))
            total_issues += (
                result["negative_count"]
                + result["currency_symbol_rows"]
                + result["outlier_count"]
                + result["text_in_numeric_rows"]
            )

    return {
        "columns": columns,
        "currency_symbols_detected": sorted(global_currency_symbols),
        "total_numeric_issues": total_issues,
    }


def _get_numeric_candidate_columns(df: pd.DataFrame) -> list[str]:
    """Return numeric columns plus object columns that appear mostly numeric."""
    candidates = []

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            candidates.append(col)
        elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col]):
            # Check if column looks mostly numeric (after stripping symbols)
            sample = df[col].dropna().astype(str).head(100)
            if len(sample) == 0:
                continue
            # Also include if column has currency symbols regardless of numeric ratio
            has_currency = bool(sample.apply(_has_currency_symbol).any())
            cleaned = sample.apply(_strip_currency)
            numeric_count = sum(1 for v in cleaned if _is_numeric_string(v))
            if has_currency or numeric_count / len(sample) >= 0.4:
                candidates.append(col)

    return candidates


def _analyse_column(df: pd.DataFrame, col: str) -> dict | None:
    """Analyse a single column for numeric anomalies."""
    series = df[col]

    # Convert to numeric where possible
    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        str_series = series.dropna().astype(str)
        currency_symbol_rows = int(str_series.apply(_has_currency_symbol).sum())
        currency_symbols_found = _find_currency_symbols(str_series)
        text_in_numeric_rows = int(str_series.apply(lambda v: not _is_numeric_string(_strip_currency(v))).sum())

        numeric_series = pd.to_numeric(str_series.apply(_strip_currency), errors="coerce")
    else:
        currency_symbol_rows = 0
        currency_symbols_found = []
        text_in_numeric_rows = 0
        numeric_series = pd.to_numeric(series, errors="coerce")

    if numeric_series.dropna().empty:
        return None

    negative_count = int((numeric_series < 0).sum())
    negative_pct = round(negative_count / len(df) * 100, 2) if len(df) > 0 else 0.0

    # Outliers: beyond 3 standard deviations from mean
    mean = numeric_series.mean()
    std = numeric_series.std()
    if std and std > 0:
        outlier_count = int(((numeric_series - mean).abs() > 3 * std).sum())
    else:
        outlier_count = 0

    severity = _severity(negative_count, currency_symbol_rows, outlier_count, text_in_numeric_rows)

    return {
        "column": col,
        "negative_count": negative_count,
        "negative_pct": negative_pct,
        "outlier_count": outlier_count,
        "currency_symbol_rows": currency_symbol_rows,
        "currency_symbols_found": currency_symbols_found,
        "text_in_numeric_rows": text_in_numeric_rows,
        "severity": severity,
    }


def _severity(negative_count, currency_rows, outliers, text_rows) -> str:
    total = negative_count + currency_rows + outliers + text_rows
    if total == 0:
        return "ok"
    elif currency_rows > 0 or text_rows > 5:
        return "critical"
    elif negative_count > 0 or total > 10:
        return "warning"
    return "ok"


def _strip_currency(value: str) -> str:
    """Remove common currency prefixes and formatting."""
    for sym in CURRENCY_SYMBOLS:
        value = value.replace(sym, "").replace(sym.lower(), "")
    return value.replace(",", "").replace(" ", "").strip()


def _is_numeric_string(value: str) -> bool:
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def _has_currency_symbol(value: str) -> bool:
    for sym in CURRENCY_SYMBOLS:
        if sym in value:
            return True
    return False


def _find_currency_symbols(series: pd.Series) -> list[str]:
    found = set()
    for val in series.head(500):
        for sym in CURRENCY_SYMBOLS:
            if sym in str(val):
                found.add(sym)
    return sorted(found)

"""
checks/string_quality.py
Detects string quality issues: whitespace, mixed case categories, value variants.
"""

import pandas as pd
from collections import Counter


def check_string_quality(df: pd.DataFrame) -> dict:
    """
    Check string/object columns for whitespace and mixed-case category variants.

    Returns:
        dict with key:
            columns: list of dicts per object column with:
                column, has_leading_trailing_whitespace, whitespace_row_count,
                mixed_case_categories, unique_value_variants, sample_inconsistencies
    """
    columns = []

    for col in df.columns:
        if not (pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])):
            continue

        non_null = df[col].dropna()
        if len(non_null) == 0:
            continue

        str_series = non_null.astype(str)

        # Whitespace check
        has_ws = bool(str_series.str.contains(r"^\s+|\s+$", regex=True).any())
        whitespace_row_count = int(str_series.str.contains(r"^\s+|\s+$", regex=True).sum())

        # Mixed case / variant detection (only for low-cardinality columns)
        unique_count = str_series.nunique()
        mixed_case_categories = []
        unique_value_variants = {}
        sample_inconsistencies = []

        if unique_count <= 100:  # Only check categorical-ish columns
            variants = _find_case_variants(str_series)
            if variants:
                mixed_case_categories = list(variants.keys())
                unique_value_variants = variants
                sample_inconsistencies = _build_inconsistency_samples(variants)

        columns.append({
            "column": col,
            "has_leading_trailing_whitespace": has_ws,
            "whitespace_row_count": whitespace_row_count,
            "mixed_case_categories": mixed_case_categories,
            "unique_value_variants": unique_value_variants,
            "sample_inconsistencies": sample_inconsistencies,
        })

    has_issues = [
        c for c in columns
        if c["has_leading_trailing_whitespace"] or c["mixed_case_categories"]
    ]

    return {
        "columns": columns,
        "columns_with_issues": has_issues,
        "total_string_issues": len(has_issues),
    }


def _find_case_variants(series: pd.Series) -> dict:
    """
    Find groups of values that are likely the same category written differently.
    Returns {canonical_form: [list of variant spellings found]}.
    """
    # Lowercase-stripped version of each unique value
    unique_vals = series.str.strip().unique().tolist()
    lower_map = {}  # lower_key -> list of actual values

    for val in unique_vals:
        key = val.lower().strip()
        if key not in lower_map:
            lower_map[key] = []
        if val not in lower_map[key]:
            lower_map[key].append(val)

    # Only return groups with more than one variant
    variants = {}
    for key, vals in lower_map.items():
        if len(vals) > 1:
            # Use title-cased version as canonical label
            canonical = key.title()
            variants[canonical] = vals

    return variants


def _build_inconsistency_samples(variants: dict) -> list[str]:
    """Build human-readable description strings for inconsistencies."""
    samples = []
    for canonical, vals in list(variants.items())[:5]:
        variants_str = ", ".join(f'"{v}"' for v in vals[:4])
        samples.append(f'"{canonical}" appears as: {variants_str}')
    return samples

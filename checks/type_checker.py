"""
checks/type_checker.py
Detects columns where the stored pandas dtype doesn't match the inferred type.
Example: column stored as object but 95% of values are numeric.
"""

import pandas as pd
import numpy as np


def check_type_consistency(df: pd.DataFrame) -> dict:
    """
    Compare stored pandas dtype vs inferred type for each column.

    Returns:
        dict with key:
            columns: list of dicts with:
                column, inferred_type, pandas_type, is_mismatch, sample_mixed_values
    """
    columns = []

    for col in df.columns:
        pandas_type = str(df[col].dtype)
        inferred_type = _infer_type(df[col])
        is_mismatch = _is_type_mismatch(df[col], pandas_type, inferred_type)

        sample_mixed = []
        if is_mismatch:
            sample_mixed = _get_mixed_samples(df[col], inferred_type)

        columns.append({
            "column": col,
            "inferred_type": inferred_type,
            "pandas_type": pandas_type,
            "is_mismatch": is_mismatch,
            "sample_mixed_values": sample_mixed,
        })

    mismatches = [c for c in columns if c["is_mismatch"]]

    return {
        "columns": columns,
        "mismatch_count": len(mismatches),
        "mismatched_columns": mismatches,
    }


def _infer_type(series: pd.Series) -> str:
    """Infer the most likely intended type of a series."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "float"

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        non_null = series.dropna().astype(str)
        if len(non_null) == 0:
            return "unknown"

        # Check if mostly numeric
        numeric_count = pd.to_numeric(
            non_null.str.replace(",", "").str.replace(r"[KEShs$£€]", "", regex=True).str.strip(),
            errors="coerce"
        ).notna().sum()

        numeric_ratio = numeric_count / len(non_null)
        if numeric_ratio >= 0.9:
            return "numeric"
        if numeric_ratio >= 0.5:
            return "mixed_numeric_text"

        # Check if mostly dates
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            date_count = pd.to_datetime(non_null, errors="coerce").notna().sum()
        date_ratio = date_count / len(non_null)
        if date_ratio >= 0.8:
            return "datetime"

        # Check if boolean-like
        unique_vals = set(non_null.str.lower().unique())
        bool_vals = {"true", "false", "yes", "no", "1", "0", "y", "n"}
        if unique_vals.issubset(bool_vals):
            return "boolean"

        return "text"

    return "unknown"


def _is_type_mismatch(series: pd.Series, pandas_type: str, inferred_type: str) -> bool:
    """Return True when the stored type clearly doesn't match what the data should be."""
    if pandas_type == "object" and inferred_type in ("numeric", "integer", "float", "datetime"):
        return True
    if pandas_type in ("int64", "int32", "float64") and inferred_type in ("text",):
        return False  # Numbers stored as numbers — that's fine
    if inferred_type == "mixed_numeric_text":
        return True
    return False


def _get_mixed_samples(series: pd.Series, inferred_type: str) -> list[str]:
    """Return up to 5 example values that demonstrate the type mismatch."""
    non_null = series.dropna().astype(str)
    if inferred_type in ("numeric", "mixed_numeric_text"):
        # Find values that are NOT parseable as numbers
        non_numeric = non_null[
            pd.to_numeric(
                non_null.str.replace(",", "").str.strip(),
                errors="coerce"
            ).isna()
        ]
        samples = non_numeric.head(5).tolist()
        if not samples:
            samples = non_null.head(5).tolist()
        return samples
    return non_null.head(5).tolist()

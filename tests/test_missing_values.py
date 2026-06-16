"""Tests for checks/missing_values.py"""

import pandas as pd
import pytest
from checks.missing_values import check_missing


def test_clean_dataframe_returns_ok():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    result = check_missing(df)
    assert result["total_missing_cells"] == 0
    assert result["missing_pct_overall"] == 0.0
    for col in result["columns"]:
        assert col["severity"] == "ok"


def test_critical_severity_above_50_pct():
    data = {"col_a": [None] * 60 + [1] * 40}  # 60% missing
    df = pd.DataFrame(data)
    result = check_missing(df)
    col = next(c for c in result["columns"] if c["column"] == "col_a")
    assert col["severity"] == "critical"
    assert col["missing_pct"] == pytest.approx(60.0, abs=0.1)


def test_warning_severity_between_10_and_50_pct():
    data = {"col_b": [None] * 25 + ["val"] * 75}  # 25% missing
    df = pd.DataFrame(data)
    result = check_missing(df)
    col = next(c for c in result["columns"] if c["column"] == "col_b")
    assert col["severity"] == "warning"


def test_ok_severity_below_10_pct():
    data = {"col_c": [None] * 5 + ["val"] * 95}  # 5% missing
    df = pd.DataFrame(data)
    result = check_missing(df)
    col = next(c for c in result["columns"] if c["column"] == "col_c")
    assert col["severity"] == "ok"


def test_missing_pct_overall_calculated_correctly():
    # 2 columns × 4 rows = 8 cells, 2 missing = 25%
    df = pd.DataFrame({"a": [1, None, 3, 4], "b": [None, 2, 3, 4]})
    result = check_missing(df)
    assert result["total_missing_cells"] == 2
    assert result["missing_pct_overall"] == pytest.approx(25.0, abs=0.1)


def test_columns_over_threshold():
    df = pd.DataFrame({
        "low_missing": [None] + [1] * 99,       # 1% — not over threshold
        "high_missing": [None] * 30 + [1] * 70, # 30% — over threshold
    })
    result = check_missing(df)
    assert "high_missing" in result["columns_over_threshold"]
    assert "low_missing" not in result["columns_over_threshold"]


def test_results_sorted_descending():
    df = pd.DataFrame({
        "many_missing": [None] * 50 + [1] * 50,
        "few_missing":  [None] * 5  + [1] * 95,
    })
    result = check_missing(df)
    pcts = [c["missing_pct"] for c in result["columns"]]
    assert pcts == sorted(pcts, reverse=True)

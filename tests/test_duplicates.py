"""Tests for checks/duplicates.py"""

import pandas as pd
import pytest
from checks.duplicates import check_duplicates


def test_no_duplicates_returns_zero():
    df = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    result = check_duplicates(df)
    assert result["exact_duplicate_rows"] == 0
    assert result["duplicate_pct"] == 0.0
    assert result["severity"] == "ok"


def test_three_exact_duplicates_counted():
    base = pd.DataFrame({"id": [1, 2, 3], "name": ["Alice", "Bob", "Charlie"]})
    dupes = base.iloc[[0, 1, 2]]  # all three rows duplicated
    df = pd.concat([base, dupes], ignore_index=True)
    result = check_duplicates(df)
    assert result["exact_duplicate_rows"] == 3


def test_duplicate_pct_calculated_correctly():
    base = pd.DataFrame({"id": list(range(10))})
    extra = base.iloc[:2]  # 2 duplicates out of 12 total ≈ 16.7%
    df = pd.concat([base, extra], ignore_index=True)
    result = check_duplicates(df)
    expected_pct = round(2 / 12 * 100, 2)
    assert result["duplicate_pct"] == pytest.approx(expected_pct, abs=0.1)


def test_severity_critical_above_5_pct():
    base = pd.DataFrame({"id": list(range(10))})
    extras = pd.concat([base.iloc[[0]]] * 6, ignore_index=True)  # 6 duplicates → > 5%
    df = pd.concat([base, extras], ignore_index=True)
    result = check_duplicates(df)
    assert result["severity"] == "critical"


def test_severity_warning_between_1_and_5_pct():
    # 1 duplicate out of ~50 rows ≈ 2%
    base = pd.DataFrame({"id": list(range(50))})
    extra = base.iloc[[0]]
    df = pd.concat([base, extra], ignore_index=True)
    result = check_duplicates(df)
    assert result["severity"] == "warning"


def test_severity_ok_below_1_pct():
    # 0 duplicates
    df = pd.DataFrame({"id": list(range(100))})
    result = check_duplicates(df)
    assert result["severity"] == "ok"


def test_duplicate_sample_not_empty_when_dupes_exist():
    base = pd.DataFrame({"id": [1, 2, 3]})
    extras = pd.concat([base.iloc[[0, 1]]], ignore_index=True)
    df = pd.concat([base, extras], ignore_index=True)
    result = check_duplicates(df)
    assert not result["duplicate_sample"].empty


def test_empty_dataframe_returns_ok():
    df = pd.DataFrame()
    result = check_duplicates(df)
    assert result["exact_duplicate_rows"] == 0
    assert result["severity"] == "ok"

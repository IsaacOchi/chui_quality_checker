"""Tests for checks/numeric_checker.py"""

import pandas as pd
import pytest
from checks.numeric_checker import check_numerics


def test_all_positive_returns_no_negatives():
    df = pd.DataFrame({"amount": [100.0, 250.5, 3000.0, 50.0, 12000.0]})
    result = check_numerics(df)
    if result["columns"]:
        col = next((c for c in result["columns"] if c["column"] == "amount"), None)
        if col:
            assert col["negative_count"] == 0


def test_negative_values_detected():
    df = pd.DataFrame({"amount": [100.0, -50.0, 200.0, -30.0, 500.0]})
    result = check_numerics(df)
    col = next(c for c in result["columns"] if c["column"] == "amount")
    assert col["negative_count"] == 2


def test_currency_symbol_rows_detected():
    df = pd.DataFrame({"amount_kes": ["KES 1,200", "KES 3,500", "500", "KES 800", "250"]})
    result = check_numerics(df)
    assert result["columns"], "Expected at least one numeric column result"
    col = next((c for c in result["columns"] if c["column"] == "amount_kes"), None)
    assert col is not None, "amount_kes column should be flagged as numeric candidate"
    assert col["currency_symbol_rows"] >= 3


def test_kes_symbol_appears_in_global_list():
    df = pd.DataFrame({"price": ["KES 500", "KES 1200", "KES 350", "400", "KES 750"]})
    result = check_numerics(df)
    assert "KES" in result["currency_symbols_detected"]


def test_outlier_detection():
    # Normal values around 1000, one extreme outlier at 1,000,000
    normal = [1000.0] * 98
    df = pd.DataFrame({"revenue": normal + [1_000_000.0, 1_100_000.0]})
    result = check_numerics(df)
    col = next((c for c in result["columns"] if c["column"] == "revenue"), None)
    assert col is not None
    assert col["outlier_count"] >= 1


def test_clean_numeric_column_no_issues():
    df = pd.DataFrame({"clean_amount": [i * 100.0 for i in range(1, 51)]})
    result = check_numerics(df)
    col = next((c for c in result["columns"] if c["column"] == "clean_amount"), None)
    if col:
        assert col["currency_symbol_rows"] == 0
        assert col["negative_count"] == 0


def test_total_numeric_issues_sums_correctly():
    df = pd.DataFrame({
        "amount": [100.0, -50.0, 200.0],          # 1 negative
        "price": ["KES 100", "200", "KES 300"],   # 2 currency rows
    })
    result = check_numerics(df)
    assert result["total_numeric_issues"] >= 3

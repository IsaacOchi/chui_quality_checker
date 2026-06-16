"""Tests for checks/date_checker.py"""

import pandas as pd
import pytest
from checks.date_checker import detect_date_columns, check_date_formats


def test_consistent_dmy_format():
    df = pd.DataFrame({"transaction_date": ["01/03/2024", "15/06/2023", "28/12/2022"] * 20})
    date_cols = detect_date_columns(df)
    assert "transaction_date" in date_cols

    result = check_date_formats(df, ["transaction_date"])
    col = result["columns"][0]
    assert col["is_consistent"] is True
    assert len(col["formats_found"]) == 1


def test_inconsistent_mixed_date_formats():
    # Mix of DD/MM/YYYY and YYYY-MM-DD
    values = (["15/06/2023"] * 50) + (["2023-06-15"] * 50)
    df = pd.DataFrame({"date": values})
    date_cols = detect_date_columns(df)
    assert "date" in date_cols

    result = check_date_formats(df, ["date"])
    col = result["columns"][0]
    assert col["is_consistent"] is False
    assert len(col["formats_found"]) >= 2


def test_non_date_column_not_detected():
    df = pd.DataFrame({"product_name": ["Pembe Flour", "Bidco Oil", "Tusker Beer"] * 30})
    date_cols = detect_date_columns(df)
    assert "product_name" not in date_cols


def test_numeric_id_column_not_detected_as_date():
    df = pd.DataFrame({"customer_id": list(range(1, 101))})
    date_cols = detect_date_columns(df)
    assert "customer_id" not in date_cols


def test_iso_date_column_detected():
    df = pd.DataFrame({"created_at": ["2024-01-15", "2024-02-28", "2023-12-31"] * 20})
    date_cols = detect_date_columns(df)
    assert "created_at" in date_cols


def test_mon_yy_format_detected():
    df = pd.DataFrame({"visit_date": ["3-Jan-23", "15-Feb-23", "28-Mar-23"] * 20})
    date_cols = detect_date_columns(df)
    assert "visit_date" in date_cols
    result = check_date_formats(df, ["visit_date"])
    col = result["columns"][0]
    assert col["is_consistent"] is True

"""
reports/quality_score.py
Aggregates findings from all check modules into a weighted 0–100 quality score.

Scoring weights:
    Missing values:       up to -30 points
    Duplicates:           up to -25 points
    Date inconsistencies: up to -20 points
    Numeric anomalies:    up to -15 points
    Type mismatches:      up to -10 points
    String quality:        (no dedicated deduction — folded into type/other)

Total possible deductions: -100 (floor at 0)
"""


def calculate_score(
    missing_result: dict,
    duplicate_result: dict,
    date_result: dict,
    numeric_result: dict,
    type_result: dict,
    string_result: dict,
) -> dict:
    """
    Aggregate check results into a 0–100 score.

    Returns:
        dict with keys:
            score (int 0-100)
            grade (str: A/B/C/D/F)
            grade_label (str: Excellent/Good/Fair/Poor/Critical)
            breakdown (dict: check_name -> {points_deducted, reason})
            summary_sentence (str)
    """
    breakdown = {}
    total_deducted = 0

    # --- Missing values: up to -30 ---
    missing_pct = missing_result.get("missing_pct_overall", 0)
    critical_cols = sum(
        1 for c in missing_result.get("columns", []) if c["severity"] == "critical"
    )
    missing_deduction = _scale(missing_pct, max_val=40, max_points=20)
    missing_deduction += min(critical_cols * 5, 10)
    missing_deduction = min(missing_deduction, 30)
    breakdown["missing_values"] = {
        "points_deducted": missing_deduction,
        "reason": f"{missing_pct:.1f}% of all cells are missing; {critical_cols} column(s) are >50% empty",
    }
    total_deducted += missing_deduction

    # --- Duplicates: up to -25 ---
    dup_pct = duplicate_result.get("duplicate_pct", 0)
    dup_severity = duplicate_result.get("severity", "ok")
    if dup_severity == "critical":
        dup_deduction = _scale(dup_pct, max_val=20, max_points=20) + 5
    elif dup_severity == "warning":
        dup_deduction = _scale(dup_pct, max_val=5, max_points=15)
    else:
        dup_deduction = 0
    dup_deduction = min(dup_deduction, 25)
    breakdown["duplicates"] = {
        "points_deducted": dup_deduction,
        "reason": f"{duplicate_result.get('exact_duplicate_rows', 0)} duplicate rows ({dup_pct:.1f}% of total)",
    }
    total_deducted += dup_deduction

    # --- Date inconsistencies: up to -20 ---
    date_cols = date_result.get("columns", [])
    inconsistent_date_cols = sum(1 for c in date_cols if not c.get("is_consistent", True))
    if inconsistent_date_cols == 0:
        date_deduction = 0
        date_reason = "All date columns use consistent formats"
    else:
        date_deduction = min(inconsistent_date_cols * 7, 20)
        date_reason = f"{inconsistent_date_cols} date column(s) contain mixed formats"
    breakdown["date_formats"] = {
        "points_deducted": date_deduction,
        "reason": date_reason,
    }
    total_deducted += date_deduction

    # --- Numeric anomalies: up to -15 ---
    num_issues = numeric_result.get("total_numeric_issues", 0)
    currency_symbols = numeric_result.get("currency_symbols_detected", [])
    num_cols = numeric_result.get("columns", [])
    critical_num_cols = sum(1 for c in num_cols if c.get("severity") == "critical")

    if currency_symbols:
        num_deduction = min(5 + critical_num_cols * 4, 15)
        num_reason = f"Currency symbols ({', '.join(currency_symbols)}) found in numeric columns; {num_issues} total numeric issues"
    elif num_issues > 0:
        num_deduction = min(num_issues // 10 + critical_num_cols * 3, 15)
        num_reason = f"{num_issues} numeric anomalies detected (negatives, outliers)"
    else:
        num_deduction = 0
        num_reason = "No numeric anomalies found"

    breakdown["numeric_issues"] = {
        "points_deducted": num_deduction,
        "reason": num_reason,
    }
    total_deducted += num_deduction

    # --- Type mismatches: up to -10 ---
    mismatch_count = type_result.get("mismatch_count", 0)
    if mismatch_count == 0:
        type_deduction = 0
        type_reason = "All columns have consistent data types"
    else:
        type_deduction = min(mismatch_count * 3, 10)
        type_reason = f"{mismatch_count} column(s) have type mismatches (e.g. numbers stored as text)"
    breakdown["type_mismatches"] = {
        "points_deducted": type_deduction,
        "reason": type_reason,
    }
    total_deducted += type_deduction

    # --- Final score ---
    score = max(0, 100 - int(total_deducted))
    grade, grade_label = _grade(score)

    # Build issues list for summary sentence
    issues = []
    if missing_deduction >= 10:
        issues.append(f"{missing_pct:.0f}% missing data")
    if dup_deduction >= 5:
        issues.append(f"{duplicate_result.get('exact_duplicate_rows', 0)} duplicate rows")
    if date_deduction >= 7:
        issues.append(f"{inconsistent_date_cols} date column(s) with mixed formats")
    if num_deduction >= 5:
        issues.append("currency symbols in numeric fields")
    if type_deduction >= 3:
        issues.append(f"{mismatch_count} type mismatch(es)")

    if issues:
        issues_str = "; ".join(issues)
        summary_sentence = f"Your data scored {score}/100 ({grade_label}). Main issues: {issues_str}."
    else:
        summary_sentence = f"Your data scored {score}/100 ({grade_label}). No major quality issues detected."

    return {
        "score": score,
        "grade": grade,
        "grade_label": grade_label,
        "breakdown": breakdown,
        "summary_sentence": summary_sentence,
    }


def _scale(value: float, max_val: float, max_points: int) -> int:
    """Scale a value between 0 and max_val linearly to 0–max_points."""
    if max_val <= 0:
        return 0
    ratio = min(value / max_val, 1.0)
    return int(ratio * max_points)


def _grade(score: int) -> tuple[str, str]:
    if score >= 90:
        return "A", "Excellent"
    elif score >= 75:
        return "B", "Good"
    elif score >= 60:
        return "C", "Fair"
    elif score >= 40:
        return "D", "Poor"
    else:
        return "F", "Critical"

"""
sample_data/generate_sample.py
Generates dirty_mpesa_sample.csv — a 30,000-row synthetic M-Pesa transaction file
with deliberately injected data quality problems for demonstrating the Chui Quality Checker.

Run:  python sample_data/generate_sample.py
Output: sample_data/dirty_mpesa_sample.csv
"""

import os
import random
import csv
from datetime import datetime, timedelta

# ── Kenyan name pools by community ───────────────────────────────────────────
KIKUYU_FIRST = ["Wanjiku", "Kamau", "Njeri", "Mwangi", "Wambui", "Gitau",
                "Wairimu", "Kariuki", "Nyambura", "Kiprotich", "Wachira", "Njoroge"]
LUO_FIRST    = ["Akinyi", "Odhiambo", "Otieno", "Adhiambo", "Owino", "Auma",
                "Ochieng", "Awino", "Ogola", "Akoth", "Odero", "Onyango"]
KAMBA_FIRST  = ["Mutua", "Ndinda", "Musyoka", "Mwende", "Kimani", "Nzula",
                "Mumo", "Syombua", "Kioko", "Muthiani", "Ndoti", "Mulwa"]
KALENJIN_FIRST = ["Chebet", "Kipchoge", "Chepkoech", "Kibet", "Rotich", "Kiplangat",
                  "Jelimo", "Bett", "Koech", "Cherono", "Sang", "Langat"]

SURNAMES = ["Kamau", "Otieno", "Mutua", "Koech", "Odhiambo", "Mwangi",
            "Ndinda", "Akinyi", "Gitau", "Chebet", "Musyoka", "Njoroge",
            "Owino", "Rotich", "Wambui", "Kibet", "Ogola", "Kariuki"]

ALL_FIRST = KIKUYU_FIRST + LUO_FIRST + KAMBA_FIRST + KALENJIN_FIRST

TRANSACTION_TYPES = ["Sale", "Refund", "Transfer"]
STATUSES = ["Completed", "Pending", "Failed", "Reversed"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def random_name():
    return f"{random.choice(ALL_FIRST)} {random.choice(SURNAMES)}"


def random_phone_dirty():
    """Return a Kenyan phone number in one of four inconsistent formats."""
    base = f"7{random.randint(10, 99)}{random.randint(100000, 999999)}"
    fmt = random.randint(0, 3)
    if fmt == 0:
        return f"0{base}"            # 07XXXXXXXX
    elif fmt == 1:
        return f"+254{base}"         # +2547XXXXXXXX
    elif fmt == 2:
        return base                   # 7XXXXXXXX
    else:
        return f"01{random.randint(10000000, 99999999)}"  # 01XXXXXXXXX


def random_date_dirty(start: datetime, end: datetime) -> str:
    """Return a date string in one of three inconsistent formats."""
    delta = (end - start).days
    dt = start + timedelta(days=random.randint(0, delta))
    fmt = random.randint(0, 2)
    if fmt == 0:
        return dt.strftime("%d/%m/%Y")     # DD/MM/YYYY
    elif fmt == 1:
        return dt.strftime("%Y-%m-%d")     # YYYY-MM-DD
    else:
        return dt.strftime("%-d-%b-%y")    # D-Mon-YY  e.g. 3-Jan-23


def random_transaction_type_dirty():
    choices = ["Sale", "SALE", "sale", "Refund", "refund", "Transfer", "TRANSFER"]
    return random.choice(choices)


def random_amount_kes(inject_problem: str = None):
    """Return amount_kes, optionally with an injected problem."""
    amount = round(random.uniform(50, 450_000), 2)
    if inject_problem == "missing":
        return ""
    elif inject_problem == "negative":
        return str(-round(random.uniform(50, 5000), 2))
    elif inject_problem == "kes_prefix":
        return f"KES {amount:,.2f}"
    else:
        return str(amount)


# ── Main generation ───────────────────────────────────────────────────────────

def generate(output_path: str, n_rows: int = 30_000, seed: int = 42):
    random.seed(seed)

    start_date = datetime(2023, 1, 1)
    end_date   = datetime(2024, 6, 30)

    # Pre-calculate injection indices
    total = n_rows

    # 350 exact duplicates — we'll store source rows and duplicate them at the end
    n_duplicates   = 350
    n_missing_amt  = 200
    n_negative_amt = 150
    n_kes_prefix   = 100

    # Assign problem slots
    missing_indices  = set(random.sample(range(total - n_duplicates), n_missing_amt))
    remaining        = [i for i in range(total - n_duplicates) if i not in missing_indices]
    negative_indices = set(random.sample(remaining, n_negative_amt))
    remaining2       = [i for i in remaining if i not in negative_indices]
    kes_indices      = set(random.sample(remaining2, n_kes_prefix))

    rows = []
    dup_source_indices = random.sample(range(total - n_duplicates), n_duplicates)

    for i in range(total - n_duplicates):
        problem = None
        if i in missing_indices:
            problem = "missing"
        elif i in negative_indices:
            problem = "negative"
        elif i in kes_indices:
            problem = "kes_prefix"

        row = {
            "transaction_id"  : f"TXN{100000 + i:07d}",
            "date"            : random_date_dirty(start_date, end_date),
            "sender_name"     : random_name(),
            "sender_phone"    : random_phone_dirty(),
            "receiver_name"   : random_name(),
            "amount_kes"      : random_amount_kes(problem),
            "transaction_type": random_transaction_type_dirty(),
            "status"          : random.choice(STATUSES),
        }
        rows.append(row)

    # Add duplicate rows
    for src_idx in dup_source_indices:
        rows.append(dict(rows[src_idx]))

    # Shuffle so duplicates aren't at the end
    random.shuffle(rows)

    # Write CSV
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    fieldnames = ["transaction_id", "date", "sender_name", "sender_phone",
                  "receiver_name", "amount_kes", "transaction_type", "status"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # ── Manifest ─────────────────────────────────────────────────────────────
    print("=" * 60)
    print("  CHUI SAMPLE DATA MANIFEST — dirty_mpesa_sample.csv")
    print("=" * 60)
    print(f"  Total rows written    : {len(rows):,}")
    print(f"  Clean rows            : {total - n_duplicates - n_missing_amt - n_negative_amt - n_kes_prefix:,}")
    print()
    print("  ── Injected problems ──────────────────────────────────")
    print(f"  Exact duplicate rows  : {n_duplicates}  (same transaction_id, all fields identical)")
    print(f"  Missing amount_kes    : {n_missing_amt}  (blank cells)")
    print(f"  Negative amount_kes   : {n_negative_amt}  (e.g. -1250.00)")
    print(f"  'KES ' prefix in amt  : {n_kes_prefix}  (e.g. 'KES 3,200.00' — text, not number)")
    print()
    print("  ── Format inconsistencies (by design) ─────────────────")
    print("  Phone formats         : 07XXXXXXXX | +2547XXXXXXXX | 7XXXXXXXX | 01XXXXXXXXX")
    print("  Date formats          : DD/MM/YYYY | YYYY-MM-DD | D-Mon-YY")
    print("  Transaction type      : Sale | SALE | sale | Refund | refund | etc.")
    print()
    print(f"  Output: {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    import sys
    out = os.path.join(os.path.dirname(__file__), "dirty_mpesa_sample.csv")
    generate(out)

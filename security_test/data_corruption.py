"""
Attack 1: Data Poisoning via CSV Manipulation
Runs BEFORE and AFTER fix. Saves both outputs to results/.
"""

import pandas as pd
import sys, os, io
sys.path.insert(0, os.path.abspath(".."))  # so we can import scoring_engine

from Scoring_engine import score_revenue, score_inventory, score_customer

RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)


def make_poisoned_csv():
    """Build a malicious CSV in memory — no file rotation involved."""
    rows = []
    for i in range(10):
        rows.append({
            "order_id": f"ORD-{i:04d}",
            "order_date": "2024-11-04",
            "customer_id": f"C{i:03d}",
            "customer_city": "Karachi",
            "product_name": "Wireless Earbuds",
            "category": "Electronics",
            "quantity": -50 if i < 2 else 2,           # A1-2: negative quantity
            "unit_price_pkr": 999999999 if i < 3 else 4000,  # A1-1: extreme price
            "payment_method": "COD",
            "courier": "TCS",
            "is_return": "maybe" if i < 5 else False,  # A1-3: invalid boolean
            "return_reason": "",
            "delivery_days": 2,
        })

    # A1-4: Duplicate 5 rows with same order_id
    for _ in range(5):
        rows.append({**rows[0], "customer_id": "C999"})

    return pd.DataFrame(rows)


def make_clean_csv():
    """Same structure but with valid data."""
    rows = []
    for i in range(50):  # Enough orders to be statistically valid
        rows.append({
            "order_id": f"ORD-{i:04d}",
            "order_date": "2024-11-04",
            "customer_id": f"C{i % 20:03d}",
            "customer_city": "Karachi",
            "product_name": "Wireless Earbuds",
            "category": "Electronics",
            "quantity": 2,
            "unit_price_pkr": 4000,
            "payment_method": "COD",
            "courier": "TCS",
            "is_return": False,
            "return_reason": "",
            "delivery_days": 2,
        })
    return pd.DataFrame(rows)


def apply_sanitisation(df):
    """The fix from the Phase 5 guide."""
    df = df.drop_duplicates(subset="order_id")
    df["is_return"] = df["is_return"].map({
        True: True, False: False,
        "True": True, "False": False,
        "true": True, "false": False,
        "maybe": False,  # gets caught
        1: True, 0: False
    }).fillna(False)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0).clip(lower=0, upper=100)
    df["unit_price_pkr"] = pd.to_numeric(df["unit_price_pkr"], errors="coerce").fillna(0).clip(lower=0, upper=50000)
    return df


def capture_score(df, label):
    """Run scoring and return a readable string of results."""
    revenue = score_revenue(df, df)   # passing same df for both weeks (demo only)
    inventory = score_inventory(df)
    customer = score_customer(df, df)

    lines = [
        f"=== {label} ===",
        f"Row count           : {len(df)}",
        f"Revenue score       : {revenue['score']}/25",
        f"Net revenue PKR     : {revenue['raw_data'].get('net_revenue', 'N/A')}",
        f"Inventory score     : {inventory['score']}/25",
        f"Customer score      : {customer['score']}/25",
        f"is_return uniques   : {df['is_return'].unique().tolist()}",
        f"quantity min/max    : {df['quantity'].min()} / {df['quantity'].max()}",
        f"price min/max       : {df['unit_price_pkr'].min()} / {df['unit_price_pkr'].max()}",
        f"Duplicate order_ids : {df.duplicated(subset='order_id').sum()}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    poisoned = make_poisoned_csv()
    before_text = capture_score(poisoned, "BEFORE FIX — Poisoned CSV")

    sanitised = apply_sanitisation(poisoned.copy())
    after_text = capture_score(sanitised, "AFTER FIX — Sanitised CSV")

    with open(f"{RESULTS}/A1_before.txt", "w") as f:
        f.write(before_text)
    with open(f"{RESULTS}/A1_after.txt", "w") as f:
        f.write(after_text)

    print(before_text)
    print()
    print(after_text)
    print(f"\n✅ Proof saved to security_tests/results/")
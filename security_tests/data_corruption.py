import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Scoring_engine import (
    calculate_revenue_health,
    calculate_inventory_health,
    calculate_customer_health,
    calculate_operations_health
)

RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)


def make_poisoned_csv():
    """
    Simulates a CSV that arrived from an external order management system.
    Three realistic problems embedded:
    - is_return exported as strings ("TRUE"/"FALSE") instead of booleans
    - 40 duplicate order_ids (export ran twice, someone appended the files)
    - 3 orders with PKR 75,000 price (above our 50k cap, but not obviously fake)
    """
    rows = []

    # 60 normal-looking orders
    products = [
        ("Wireless Earbuds",  4500, "Electronics"),
        ("Phone Case",         700, "Accessories"),
        ("USB-C Cable",        700, "Accessories"),
        ("Screen Protector",   450, "Accessories"),
        ("Laptop Sleeve",     1800, "Accessories"),
        ("Portable Power Bank",3500, "Electronics"),
    ]
    couriers = ["TCS", "Leopards", "M&P"]
    cities   = ["Karachi", "Lahore", "Islamabad", "Peshawar"]

    for i in range(60):
        product, price, cat = products[i % len(products)]
        is_ret = (i % 10 == 0)   # every 10th order is a return
        rows.append({
            "order_id"      : f"ORD-{i:04d}",
            "order_date"    : "2024-11-04",
            "customer_id"   : f"C{(i % 25):03d}",
            "customer_city" : cities[i % len(cities)],
            "product_name"  : product,
            "category"      : cat,
            "quantity"      : 2,
            "unit_price_pkr": price,
            "payment_method": "COD" if i % 3 == 0 else "Digital",
            "courier"       : couriers[i % len(couriers)],
            # ← Attack A: string booleans instead of real booleans
            "is_return"     : "TRUE" if is_ret else "FALSE",
            "return_reason" : "Damaged on arrival" if is_ret else "",
            "delivery_days" : 3,
        })

    # Attack B: 40 duplicates (simulates export-then-append mistake)
    # Take first 40 rows and append them again with same order_id
    for i in range(40):
        rows.append({**rows[i]})

    # Attack C: 3 orders with above-cap price (realistic premium product)
    for i in range(3):
        rows.append({
            "order_id"      : f"ORD-PREM-{i:04d}",
            "order_date"    : "2024-11-04",
            "customer_id"   : f"C{(i + 50):03d}",
            "customer_city" : "Karachi",
            "product_name"  : "Laptop Sleeve",
            "category"      : "Accessories",
            "quantity"      : 1,
            "unit_price_pkr": 75000,   # above 50k cap, not obviously fake
            "payment_method": "Digital",
            "courier"       : "TCS",
            "is_return"     : "FALSE",
            "return_reason" : "",
            "delivery_days" : 2,
        })

    return pd.DataFrame(rows)


def apply_sanitisation(df):
    # Fix A: normalise string booleans
    df["is_return"] = df["is_return"].map({
        True: True,   False: False,
        "TRUE": True, "FALSE": False,
        "True": True, "False": False,
        "true": True, "false": False,
        1: True,      0: False
    }).fillna(False)

    # Fix B: remove duplicate orders
    df = df.drop_duplicates(subset="order_id")

    # Fix C: cap price at realistic maximum
    df["unit_price_pkr"] = pd.to_numeric(
        df["unit_price_pkr"], errors="coerce"
    ).fillna(0).clip(lower=0, upper=50000)

    return df


def capture_score(df, label):
    try:
        rev  = calculate_revenue_health(df, df)
        inv  = calculate_inventory_health(df, df)
        cust = calculate_customer_health(df, df)
        ops  = calculate_operations_health(df, df)

        # Pull return count manually to show the string boolean problem
        try:
            return_count = df["is_return"].sum()
        except TypeError:
            return_count = "FAILED — is_return contains strings, not booleans"

        lines = [
            f"=== {label} ===",
            f"Total rows (before dedup) : {len(df)}",
            f"Duplicate order_ids       : {df.duplicated(subset='order_id').sum()}",
            f"is_return unique values   : {df['is_return'].unique().tolist()}",
            f"Returns counted by .sum() : {return_count}",
            f"Max price in data         : PKR {df['unit_price_pkr'].max():,.0f}",
            f"Revenue score             : {rev['score']}/25",
            f"Inventory score           : {inv['score']}/25",
            f"Customer score            : {cust['score']}/25",
            f"Operations score          : {ops['score']}/25",
            f"TOTAL                     : {rev['score']+inv['score']+cust['score']+ops['score']}/100",
        ]
        return "\n".join(lines)

    except Exception as e:
        return (
            f"=== {label} ===\n"
            f"Total rows                : {len(df)}\n"
            f"is_return unique values   : {df['is_return'].unique().tolist()}\n"
            f"Duplicate order_ids       : {df.duplicated(subset='order_id').sum()}\n"
            f"Max price in data         : PKR {df['unit_price_pkr'].max():,.0f}\n\n"
            f"SYSTEM CRASHED\n"
            f"Error: {type(e).__name__}: {e}\n\n"
            f"This means a real external CSV with string booleans\n"
            f"would silently deny the business owner their weekly report."
        )


if __name__ == "__main__":
    poisoned    = make_poisoned_csv()
    before_text = capture_score(poisoned, "BEFORE FIX — External CSV Attack")

    sanitised   = apply_sanitisation(poisoned.copy())
    after_text  = capture_score(sanitised, "AFTER FIX — Sanitised CSV")

    with open(f"{RESULTS}/A1_before.txt", "w",encoding="utf-8") as f:
        f.write(before_text)
    with open(f"{RESULTS}/A1_after.txt", "w",encoding="utf-8") as f:
        f.write(after_text)

    print(before_text)
    print()
    print(after_text)
    print("\nDone! Proof saved to security_tests/results/")
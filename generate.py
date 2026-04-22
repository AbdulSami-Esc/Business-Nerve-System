# ============================================================
# generate_data.py
# Business Nerve System — Phase 1
#
# PURPOSE:
#   Generate realistic CSV files simulating one Pakistani
#   small e-commerce store's weekly sales transactions.
#
#   FIRST RUN  → creates current_week.csv, last_week.csv,
#                 initial_stock.csv in the project folder
#   LATER RUNS → rotates: current_week becomes last_week,
#                 a fresh current_week is generated with new data
#
# HOW TO RUN:
#   python generate_data.py
#
# OUTPUT (all saved directly in the Business Nerve System folder):
#   current_week.csv
#   last_week.csv
#   initial_stock.csv
# ============================================================

import random
import os
import time
import pandas as pd
from faker import Faker
from datetime import date, timedelta
import shutil

# ── Path setup ───────────────────────────────────────────────
# Always save next to THIS script, not wherever the shell cwd is.
# This means the files land in the Business Nerve System folder
# regardless of where you call the script from.
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
CURRENT_PATH = os.path.join(BASE_DIR, "current_week.csv")
LAST_PATH    = os.path.join(BASE_DIR, "last_week.csv")
STOCK_PATH   = os.path.join(BASE_DIR, "initial_stock.csv")


# ── Seeding strategy ────────────────────────────────────────
# First run uses SEED=42 for a reproducible baseline.
# Every rotation uses a seed derived from the current date so
# each new current_week is statistically different.
FIRST_RUN_SEED = 42


# ── Faker setup ──────────────────────────────────────────────
fake = Faker(['en_PK', 'en_US'])


# ============================================================
# SECTION 1 — STORE CATALOGUE
# ============================================================

PRODUCTS = [
    {
        "name":             "Wireless Earbuds",
        "category":         "Electronics",
        "min_price":        3500,
        "max_price":        5500,
        "initial_stock":    80,
        "return_rate":      0.08,
        "weight_in_orders": 10,
    },
    {
        "name":             "Phone Case",
        "category":         "Accessories",
        "min_price":        400,
        "max_price":        900,
        "initial_stock":    250,
        "return_rate":      0.22,
        "weight_in_orders": 30,
    },
    {
        "name":             "Screen Protector",
        "category":         "Accessories",
        "min_price":        300,
        "max_price":        600,
        "initial_stock":    300,
        "return_rate":      0.18,
        "weight_in_orders": 20,
    },
    {
        "name":             "USB-C Charging Cable",
        "category":         "Electronics",
        "min_price":        500,
        "max_price":        900,
        "initial_stock":    200,
        "return_rate":      0.10,
        "weight_in_orders": 22,
    },
    {
        "name":             "Portable Power Bank",
        "category":         "Electronics",
        "min_price":        2500,
        "max_price":        4500,
        "initial_stock":    55,
        "return_rate":      0.07,
        "weight_in_orders": 8,
    },
    {
        "name":             "Laptop Sleeve",
        "category":         "Accessories",
        "min_price":        1200,
        "max_price":        2200,
        "initial_stock":    90,
        "return_rate":      0.14,
        "weight_in_orders": 10,
    },
]


# ============================================================
# SECTION 2 — CITY DISTRIBUTION
# ============================================================

CITIES = [
    {"name": "Lahore",     "weight": 35, "local": True},
    {"name": "Karachi",    "weight": 28, "local": False},
    {"name": "Islamabad",  "weight": 18, "local": False},
    {"name": "Faisalabad", "weight": 8,  "local": False},
    {"name": "Rawalpindi", "weight": 5,  "local": False},
    {"name": "Multan",     "weight": 3,  "local": False},
    {"name": "Peshawar",   "weight": 2,  "local": False},
    {"name": "Quetta",     "weight": 1,  "local": False},
]

CITY_NAMES   = [c["name"]   for c in CITIES]
CITY_WEIGHTS = [c["weight"] for c in CITIES]

COURIER_BY_CITY = {
    "Lahore":     ["Leopards", "TCS", "Rider"],
    "Karachi":    ["TCS", "Leopards", "Swyft"],
    "Islamabad":  ["TCS", "Leopards", "Rider"],
    "Faisalabad": ["Leopards", "TCS"],
    "Rawalpindi": ["TCS", "Rider"],
    "Multan":     ["Leopards", "TCS"],
    "Peshawar":   ["TCS", "Leopards"],
    "Quetta":     ["TCS"],
}


# ============================================================
# SECTION 3 — RETURN REASONS
# ============================================================

RETURN_REASONS = {
    "Electronics": [
        "Not charging correctly",
        "Defective unit",
        "Different from description",
        "Sound quality issue",
    ],
    "Accessories": [
        "Wrong model / size",
        "Poor build quality",
        "Different colour received",
        "Changed mind",
    ],
}


# ============================================================
# SECTION 4 — CUSTOMER POOL
# ============================================================

NUM_CUSTOMERS = 60
LOYAL_CUTOFF  = 15

customer_ids     = [f"CUST-{str(i).zfill(3)}" for i in range(1, NUM_CUSTOMERS + 1)]
customer_weights = [4 if i < LOYAL_CUTOFF else 1 for i in range(NUM_CUSTOMERS)]


# ============================================================
# SECTION 5 — HELPER FUNCTIONS
# ============================================================

def pick_product():
    weights = [p["weight_in_orders"] for p in PRODUCTS]
    return random.choices(PRODUCTS, weights=weights, k=1)[0]


def pick_city():
    return random.choices(CITIES, weights=CITY_WEIGHTS, k=1)[0]


def pick_customer():
    return random.choices(customer_ids, weights=customer_weights, k=1)[0]


def generate_delivery_days(city_dict, is_return):
    city_name = city_dict["name"]

    if city_name == "Lahore":
        days = random.randint(1, 2)
    elif city_name in ("Karachi", "Islamabad", "Rawalpindi"):
        days = random.randint(2, 4)
    elif city_name in ("Faisalabad", "Multan"):
        days = random.randint(3, 5)
    else:
        days = random.randint(4, 7)

    if random.random() < 0.10:
        days += random.randint(2, 3)

    if is_return:
        days += random.randint(1, 2)

    return days


def generate_price(product):
    base_price = random.randint(product["min_price"], product["max_price"])
    if random.random() < 0.15:
        discount   = random.uniform(0.10, 0.25)
        base_price = int(base_price * (1 - discount))
    return base_price


def generate_return_info(product, city_dict):
    base_rate = product["return_rate"]
    if city_dict["name"] in ("Quetta", "Peshawar", "Multan"):
        base_rate += 0.08
    is_return = random.random() < base_rate
    reason    = random.choice(RETURN_REASONS[product["category"]]) if is_return else None
    return is_return, reason


def generate_payment_method():
    return random.choices(
        ["Cash on Delivery", "Online Transfer", "Easypaisa", "JazzCash"],
        weights=[72, 14, 8, 6],
        k=1
    )[0]


# ============================================================
# SECTION 6 — ORDER ROW GENERATOR
# ============================================================

def generate_order(order_number, week_start_date):
    product     = pick_product()
    city        = pick_city()
    customer_id = pick_customer()
    is_return, return_reason = generate_return_info(product, city)

    day_weights = [10, 10, 10, 12, 14, 16, 12]
    day_offset  = random.choices(range(7), weights=day_weights, k=1)[0]
    order_date  = week_start_date + timedelta(days=day_offset)

    quantity      = random.choices([1, 2, 3], weights=[65, 28, 7], k=1)[0]
    unit_price    = generate_price(product)
    courier       = random.choice(COURIER_BY_CITY[city["name"]])
    delivery_days = generate_delivery_days(city, is_return)

    return {
        "order_id":        f"ORD-{str(order_number).zfill(4)}",
        "order_date":      order_date.strftime("%Y-%m-%d"),
        "customer_id":     customer_id,
        "customer_city":   city["name"],
        "product_name":    product["name"],
        "category":        product["category"],
        "quantity":        quantity,
        "unit_price_pkr":  unit_price,
        "payment_method":  generate_payment_method(),
        "courier":         courier,
        "is_return":       is_return,
        "return_reason":   return_reason if return_reason else "",
        "delivery_days":   delivery_days,
    }


# ============================================================
# SECTION 7 — DATASET GENERATOR
# ============================================================

def generate_week(week_start_date, order_start_number, num_orders=None):
    if num_orders is None:
        num_orders = random.randint(160, 200)

    rows = [
        generate_order(order_number=order_start_number + i,
                       week_start_date=week_start_date)
        for i in range(num_orders)
    ]
    df = pd.DataFrame(rows)
    return df.sort_values("order_date").reset_index(drop=True)


# ============================================================
# SECTION 8 — STOCK SNAPSHOT
# ============================================================

def generate_stock_snapshot():
    rows = [
        {
            "product_name":  p["name"],
            "category":      p["category"],
            "initial_stock": p["initial_stock"],
        }
        for p in PRODUCTS
    ]
    return pd.DataFrame(rows)


# ============================================================
# SECTION 9 — ROTATION LOGIC
#
# is_first_run()   → True when current_week.csv does not exist
# rotate_files()   → promotes current → last, prints what happened
# ============================================================

def is_first_run():
    """
    Returns True when current_week.csv does not yet exist.
    That is the signal to generate BOTH files from scratch.
    """
    return not os.path.exists(CURRENT_PATH)


def rotate_files():
    """
    Promotes current_week.csv → last_week.csv.
    Deletes the old last_week.csv if it exists.
    Called only on subsequent runs (not on first run).
    """
    if os.path.exists(LAST_PATH):
        os.remove(LAST_PATH)
        print("  [rotate] Deleted old last_week.csv")

    shutil.move(CURRENT_PATH, LAST_PATH)
    print("  [rotate] current_week.csv → last_week.csv")


# ============================================================
# SECTION 10 — SUMMARY PRINTER
# ============================================================

def print_summary(df_last, df_current, df_stock, run_type):
    def net_revenue(df):
        return (
            df[df["is_return"] == False]
            .assign(rev=lambda d: d["quantity"] * d["unit_price_pkr"])
            ["rev"].sum()
        )

    lw_rev = net_revenue(df_last)
    cw_rev = net_revenue(df_current)
    wow    = ((cw_rev - lw_rev) / lw_rev) * 100

    print("\n" + "=" * 60)
    print(f"  DATA GENERATION COMPLETE  ({run_type})")
    print("=" * 60)
    print(f"\n  last_week.csv    → {len(df_last)} orders")
    print(f"  current_week.csv → {len(df_current)} orders")
    print(f"  initial_stock.csv → {len(df_stock)} products")
    print(f"\n  Last week revenue    → PKR {lw_rev:,.0f}")
    print(f"  Current week revenue → PKR {cw_rev:,.0f}")
    print(f"  Week-over-week       → {wow:+.1f}%")

    cw_return_rate = df_current["is_return"].mean() * 100
    print(f"\n  Return rate (current week) → {cw_return_rate:.1f}%")

    print("\n  Orders by city (current week):")
    for city, count in df_current["customer_city"].value_counts().items():
        bar = "█" * (count // 4)
        print(f"    {city:<12} {count:>3}  {bar}")

    avg_del = df_current["delivery_days"].mean()
    print(f"\n  Avg delivery days → {avg_del:.1f}")

    print("\n  Stock remaining after current week sales:")
    units_sold = (
        df_current[df_current["is_return"] == False]
        .groupby("product_name")["quantity"].sum()
    )
    for product in PRODUCTS:
        sold      = units_sold.get(product["name"], 0)
        remaining = product["initial_stock"] - sold
        flag      = "  ← LOW STOCK" if remaining < 20 else ""
        print(f"    {product['name']:<25} {remaining:>3} units{flag}")

    print("\n" + "=" * 60)
    print(f"  Files saved to: {BASE_DIR}")
    print("=" * 60 + "\n")


# ============================================================
# SECTION 11 — ENTRY POINT
# ============================================================

if __name__ == "__main__":

    today = date.today()

    # ── FIRST RUN ────────────────────────────────────────────
    # current_week.csv does not exist yet.
    # Generate both weeks from scratch with a fixed seed so
    # this baseline is always reproducible.
    if is_first_run():
        print("\n[generate_data] First run detected — generating all files.\n")

        random.seed(FIRST_RUN_SEED)
        fake.seed_instance(FIRST_RUN_SEED)

        # last_week = the Monday two weeks ago
        # current_week = the Monday of last week
        # (offsets keep dates realistic without hardcoding)
        current_week_start = today - timedelta(days=today.weekday())        # this Monday
        last_week_start    = current_week_start - timedelta(weeks=1)

        print("  Generating last_week.csv ...")
        df_last = generate_week(
            week_start_date=last_week_start,
            order_start_number=1000,
        )

        # Independent seed for current week
        random.seed(FIRST_RUN_SEED + 1)
        fake.seed_instance(FIRST_RUN_SEED + 1)

        print("  Generating current_week.csv ...")
        df_current = generate_week(
            week_start_date=current_week_start,
            order_start_number=2000,
        )

        # Deliberate 12 % revenue dip so scoring engine has a story
        high_value_idx = df_current[
            df_current["unit_price_pkr"] > 3000
        ].sample(frac=0.12, random_state=FIRST_RUN_SEED).index
        df_current = df_current.drop(high_value_idx).reset_index(drop=True)

        run_type = "FIRST RUN"

    # ── ROTATION RUN ─────────────────────────────────────────
    # current_week.csv already exists.
    # Promote it to last_week, then generate a brand-new
    # current_week with a time-based seed so the data differs
    # every time you run the script.
    else:
        print("\n[generate_data] Existing data found — rotating files.\n")

        # Read the existing current week BEFORE we rotate it away
        df_last = pd.read_csv(CURRENT_PATH)

        rotate_files()   # current_week.csv → last_week.csv

        # Seed from current date so each weekly run is unique
        # but also repeatable on the same calendar day
        rotation_seed = int(today.strftime("%Y%m%d"))
        random.seed(rotation_seed)
        fake.seed_instance(rotation_seed)

        # New current week starts this Monday
        current_week_start = today - timedelta(days=today.weekday())

        print("  Generating new current_week.csv ...")
        df_current = generate_week(
            week_start_date=current_week_start,
            order_start_number=int(today.strftime("%Y%m%d")) % 9000 + 1000,
        )

        run_type = "ROTATION RUN"

    # ── Save files ───────────────────────────────────────────
    df_last.to_csv(LAST_PATH, index=False)
    df_current.to_csv(CURRENT_PATH, index=False)

    df_stock = generate_stock_snapshot()
    df_stock.to_csv(STOCK_PATH, index=False)

    # ── Print summary ────────────────────────────────────────
    print_summary(df_last, df_current, df_stock, run_type)
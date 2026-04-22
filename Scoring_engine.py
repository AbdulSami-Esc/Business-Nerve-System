"""
Business Nerve System - Scoring Engine
Four health modules, each returning (score, alerts, raw_data, dimension).
All EDA insights are captured in raw_data so Phase 3 (LangChain) can use them.
"""

import pandas as pd
import numpy as np

# ============================================================
# CONFIG — all thresholds in one place (replaces config.py)
# ============================================================

WEEKLY_REVENUE_TARGET = 300_000       # PKR
AOV_TARGET = 1_800                    # PKR per order

TARGET_REPEAT_RATE = 0.30             # 30% of unique customers should have >1 order
MAX_ACCEPTABLE_RETURN_RATE = 0.19     # 19% ceiling; above this, points start dropping

TARGET_DELIVERY_DAYS = 3
MAX_AVG_DELIVERY_DAYS = 3.5
OUTLIER_DELIVERY_DAYS = 5

# Initial stock for each product (matches generate_data.py)
INITIAL_STOCK = {
    "Wireless Earbuds":    80,
    "Phone Case":         250,
    "Screen Protector":   300,
    "USB-C Cable":        200,
    "Portable Power Bank":  55,   # intentionally low
    "Laptop Sleeve":       90,
}

LOW_STOCK_THRESHOLD = 15      # absolute units
CRITICAL_DAYS_THRESHOLD = 7   # days of stock remaining


# ============================================================
# MODULE 1 — REVENUE HEALTH (25 pts)
# ============================================================

def calculate_revenue_health(df_current, df_last):
    """
    Sub 1 (10 pts): Net revenue vs weekly target
    Sub 2  (8 pts): Week-over-week % change
    Sub 3  (7 pts): Average Order Value vs target

    EDA insights captured in raw_data:
    - per-product revenue this week and last week
    - which products declined most (EDA Phase 2)
    - flash-sale influence on AOV
    """

    total_score = 0
    alerts = []

    # --- Pre-processing: filter out returned orders ---
    # FIX: each week filtered by its OWN is_return column
    valid_current = df_current[df_current["is_return"] == False].copy()
    valid_last    = df_last[df_last["is_return"] == False].copy()

    # --- Revenue calculation helper ---
    def net_revenue(df):
        return (df["quantity"] * df["unit_price_pkr"]).sum()

    this_revenue = net_revenue(valid_current)
    last_revenue = net_revenue(valid_last)

    # ── Sub-metric 1: Net Revenue vs Target (10 pts) ──────────────────────────
    ratio = this_revenue / WEEKLY_REVENUE_TARGET

    if   ratio >= 1.00: total_score += 10
    elif ratio >= 0.95: total_score += 9
    elif ratio >= 0.90: total_score += 8
    elif ratio >= 0.85: total_score += 7
    elif ratio >= 0.80: total_score += 6
    elif ratio >= 0.75: total_score += 5
    elif ratio >= 0.70: total_score += 4
    elif ratio >= 0.60: total_score += 3
    elif ratio >= 0.50: total_score += 2
    else:               total_score += 1

    if ratio < 0.85:
        shortfall = WEEKLY_REVENUE_TARGET - this_revenue
        alerts.append(
            f"Revenue is PKR {this_revenue:,.0f} this week — "
            f"PKR {shortfall:,.0f} below the PKR {WEEKLY_REVENUE_TARGET:,} target "
            f"({ratio*100:.1f}% of target achieved)."
        )

    # ── Sub-metric 2: Week-over-Week Change (8 pts) ───────────────────────────
    if last_revenue > 0:
        wow_pct = ((this_revenue - last_revenue) / last_revenue) * 100
    else:
        wow_pct = 0.0

    if   wow_pct >=  5.0: total_score += 8
    elif wow_pct >=  0.0: total_score += 6
    elif wow_pct >= -4.9: total_score += 4
    elif wow_pct >= -9.9: total_score += 2
    else:                 total_score += 0

    if wow_pct <= -5.0:
        alerts.append(
            f"Revenue dropped {abs(wow_pct):.1f}% compared to last week "
            f"(PKR {last_revenue:,.0f} → PKR {this_revenue:,.0f}). "
            f"High-value orders above PKR 3,000 appear to be the primary driver of this decline."
        )

    # ── Sub-metric 3: Average Order Value (7 pts) ─────────────────────────────
    # FIX: AOV = revenue / number of orders (rows), not unique customers
    order_count = len(valid_current)
    current_aov = this_revenue / order_count if order_count > 0 else 0

    aov_ratio = current_aov / AOV_TARGET

    if   aov_ratio >= 1.00: total_score += 7
    elif aov_ratio >= 0.85: total_score += 5
    elif aov_ratio >= 0.70: total_score += 3
    else:                   total_score += 0

    if aov_ratio < 0.70:
        alerts.append(
            f"Average Order Value dropped to PKR {current_aov:,.0f} "
            f"(target: PKR {AOV_TARGET:,}). "
            f"Flash-sale discounting or a shift to lower-priced items may be the cause."
        )

    # ── EDA Insight: Per-product revenue breakdown (Phase 2 finding) ──────────
    def product_revenue(df):
        return (
            df.groupby("product_name")
            .apply(lambda x: (x["quantity"] * x["unit_price_pkr"]).sum())
            .rename("revenue")
        )

    prod_rev_current = product_revenue(valid_current)
    prod_rev_last    = product_revenue(valid_last)

    product_delta = pd.DataFrame({
        "this_week":  prod_rev_current,
        "last_week":  prod_rev_last,
    }).fillna(0)
    product_delta["change_pct"] = (
        (product_delta["this_week"] - product_delta["last_week"])
        / product_delta["last_week"].replace(0, np.nan)
        * 100
    ).round(1)

    # ── EDA Insight: Flash-sale AOV impact ────────────────────────────────────
    flash_sale_aov = None
    regular_aov    = None
    if "discount_pct" in valid_current.columns:
        flash     = valid_current[valid_current["discount_pct"] > 0]
        regular   = valid_current[valid_current["discount_pct"] == 0]
        flash_sale_aov = (
            (flash["quantity"] * flash["unit_price_pkr"]).sum() / len(flash)
            if len(flash) > 0 else None
        )
        regular_aov = (
            (regular["quantity"] * regular["unit_price_pkr"]).sum() / len(regular)
            if len(regular) > 0 else None
        )

    raw_data = {
        "net_revenue":         round(this_revenue, 2),
        "last_week_revenue":   round(last_revenue, 2),
        "wow_change_pct":      round(wow_pct, 2),
        "revenue_target":      WEEKLY_REVENUE_TARGET,
        "target_achievement":  round(ratio * 100, 1),
        "aov":                 round(current_aov, 2),
        "aov_target":          AOV_TARGET,
        # EDA Phase 2: per-product revenue table for LangChain to reference
        "product_revenue_delta": product_delta.to_dict(),
        # EDA: flash-sale AOV split
        "flash_sale_aov":      round(flash_sale_aov, 2) if flash_sale_aov else None,
        "regular_aov":         round(regular_aov, 2)    if regular_aov    else None,
    }

    return total_score, alerts, raw_data, "Revenue Health"


# ============================================================
# MODULE 2 — CUSTOMER HEALTH (25 pts)
# ============================================================

def calculate_customer_health(df_current, df_last):
    """
    Sub 1 (10 pts): Repeat customer rate
    Sub 2  (8 pts): Overall return rate
    Sub 3  (7 pts): New vs lost customers (net growth)

    EDA insights captured in raw_data:
    - COD return rate vs digital payment return rate (EDA Phase 2 key finding)
    - Repeat buyer return rate vs one-time buyer return rate (EDA Phase 3)
    - City-level return rate (EDA Phase 2)
    """

    score = 0
    alerts = []

    # ── Sub-metric 1: Repeat Customer Rate (10 pts) ───────────────────────────
    # FIX: nunique() returns an int, no .count() call needed
    orders_per_customer = df_current.groupby("customer_id").size()
    total_unique   = len(orders_per_customer)
    repeat_count   = (orders_per_customer > 1).sum()
    repeat_rate    = repeat_count / total_unique if total_unique > 0 else 0

    ratio = repeat_rate / TARGET_REPEAT_RATE

    if   ratio >= 1.00: score += 10
    elif ratio >= 0.85: score +=  9
    elif ratio >= 0.75: score +=  8
    elif ratio >= 0.65: score +=  7
    elif ratio >= 0.55: score +=  6
    elif ratio >= 0.50: score +=  5
    elif ratio >= 0.40: score +=  4
    elif ratio >= 0.35: score +=  3
    else:               score +=  2

    if repeat_rate < TARGET_REPEAT_RATE * 0.60:
        alerts.append(
            f"Only {repeat_rate*100:.1f}% of customers placed more than one order this week "
            f"(target: {TARGET_REPEAT_RATE*100:.0f}%). "
            f"Loyalty is low — repeat buyers are your most profitable segment."
        )

    # ── Sub-metric 2: Return Rate (8 pts) ─────────────────────────────────────
    # FIX: return_rate is a single float, computed correctly
    total_orders  = len(df_current)
    returned      = df_current["is_return"].sum()          # True == 1
    return_rate   = returned / total_orders if total_orders > 0 else 0

    # Brackets calibrated around EDA findings:
    # normal 17-19%, concern 20-28%, critical above 28%
    if   return_rate <= 0.19: score += 8
    elif return_rate <= 0.22: score += 7
    elif return_rate <= 0.25: score += 6
    elif return_rate <= 0.28: score += 5
    elif return_rate <= 0.31: score += 4
    elif return_rate <= 0.35: score += 3
    elif return_rate <= 0.40: score += 2
    elif return_rate <= 0.45: score += 1
    else:                     score += 0

    if return_rate > 0.28:
        alerts.append(
            f"Return rate reached {return_rate*100:.1f}% this week — "
            f"above the 28% critical threshold. "
            f"Investigate COD orders and high-return products (Phone Case, Earbuds)."
        )

    # ── Sub-metric 3: New vs Lost Customers (7 pts) ───────────────────────────
    ids_current = set(df_current["customer_id"].unique())
    ids_last    = set(df_last["customer_id"].unique())

    new_customers  = ids_current - ids_last
    lost_customers = ids_last    - ids_current
    new_count      = len(new_customers)
    lost_count     = len(lost_customers)
    net_growth     = new_count - lost_count

    # FIX: add to `score`, not `total_score`
    if   net_growth >  0: score += 7
    elif net_growth == 0: score += 5
    elif net_growth >= -3: score += 3
    elif net_growth >= -6: score += 1
    else:                  score += 0

    if net_growth < -5:
        alerts.append(
            f"Customer churn alert: {lost_count} customers left this week, "
            f"only {new_count} joined. Net change: {net_growth}."
        )

    # ── EDA Insight 1: COD vs Digital Payment Return Rate (Phase 2) ───────────
    payment_return = (
        df_current.groupby("payment_method")["is_return"]
        .agg(total="count", returned="sum")
        .assign(return_rate=lambda x: (x["returned"] / x["total"] * 100).round(1))
    )
    cod_return_rate = (
        payment_return.loc["COD", "return_rate"]
        if "COD" in payment_return.index else None
    )

    # ── EDA Insight 2: City-level return rates (Phase 2) ──────────────────────
    city_return = (
        df_current.groupby("customer_city")["is_return"]
        .agg(total="count", returned="sum")
        .assign(return_rate=lambda x: (x["returned"] / x["total"] * 100).round(1))
        [["return_rate"]]
        .to_dict()["return_rate"]
    )

    # ── EDA Insight 3: Repeat vs One-time buyer return rate (Phase 3) ─────────
    buyer_type = df_current.copy()
    buyer_type["buyer_type"] = buyer_type["customer_id"].map(
        lambda cid: "Repeat" if orders_per_customer.get(cid, 0) > 1 else "One-Time"
    )
    buyer_return = (
        buyer_type.groupby("buyer_type")["is_return"]
        .agg(total="count", returned="sum")
        .assign(return_rate=lambda x: (x["returned"] / x["total"] * 100).round(1))
        [["return_rate"]]
        .to_dict()["return_rate"]
    )

    raw_data = {
        "repeat_rate":            round(repeat_rate * 100, 1),
        "repeat_customer_count":  int(repeat_count),
        "total_unique_customers": int(total_unique),
        "return_rate":            round(return_rate * 100, 1),
        "total_returned":         int(returned),
        "new_customers":          new_count,
        "lost_customers":         lost_count,
        "net_growth":             net_growth,
        # EDA Phase 2: COD structural return problem
        "cod_return_rate":        cod_return_rate,
        "payment_return_rates":   payment_return["return_rate"].to_dict(),
        # EDA Phase 2: city breakdown
        "city_return_rates":      city_return,
        # EDA Phase 3: buyer type breakdown
        "buyer_type_return_rates": buyer_return,
    }

    return score, alerts, raw_data, "Customer Health"


# ============================================================
# MODULE 3 — INVENTORY HEALTH (25 pts)
# ============================================================

def calculate_inventory_health(df_current, df_last):
    """
    Sub 1 (10 pts): Remaining stock per product
    Sub 2  (8 pts): Days of stock remaining
    Sub 3  (7 pts): Number of products at risk simultaneously

    EDA insights captured in raw_data:
    - Full inventory table with remaining stock and days remaining (EDA Phase 5)
    - Products below LOW_STOCK_THRESHOLD flagged by name
    """

    score = 0
    alerts = []

    # ── Pre-processing: only count units that were kept ───────────────────────
    sold = (
        df_current[df_current["is_return"] == False]
        .groupby("product_name")["quantity"]
        .sum()
    )

    # ── Build the inventory report table ──────────────────────────────────────
    inventory_rows = []
    sub1_deductions = 0   # deduct from perfect 10
    sub2_deductions = 0   # deduct from perfect 8
    products_at_risk = 0

    for product, start_qty in INITIAL_STOCK.items():
        sold_qty      = int(sold.get(product, 0))
        remaining     = start_qty - sold_qty
        daily_velocity = sold_qty / 7

        if daily_velocity > 0:
            days_remaining = remaining / daily_velocity
        else:
            days_remaining = float("inf")   # didn't sell at all this week

        at_risk = False

        # Sub-metric 1: absolute stock level
        if remaining < 0:
            sub1_deductions += 3
            at_risk = True
            alerts.append(
                f"STOCKOUT: {product} has run out of stock "
                f"(oversold by {abs(remaining)} units). Reorder immediately."
            )
        elif remaining < LOW_STOCK_THRESHOLD:
            sub1_deductions += 2
            at_risk = True
            alerts.append(
                f"Low stock warning: {product} has only {remaining} units left "
                f"— below the {LOW_STOCK_THRESHOLD}-unit safety threshold."
            )

        # Sub-metric 2: days of stock remaining
        if days_remaining < CRITICAL_DAYS_THRESHOLD and days_remaining != float("inf"):
            sub2_deductions += 2
            at_risk = True
            alerts.append(
                f"Critical: {product} will sell out in approximately "
                f"{days_remaining:.1f} days at the current sales rate "
                f"({sold_qty} units/week, {remaining} units remaining)."
            )

        if at_risk:
            products_at_risk += 1

        inventory_rows.append({
            "product":        product,
            "initial_stock":  start_qty,
            "sold_this_week": sold_qty,
            "remaining":      remaining,
            "days_remaining": round(days_remaining, 1) if days_remaining != float("inf") else "∞",
            "at_risk":        at_risk,
        })

    # Assign sub-metric 1 score (max 10, minimum 0)
    score += max(0, 10 - sub1_deductions)

    # Assign sub-metric 2 score (max 8, minimum 0)
    score += max(0, 8 - sub2_deductions)

    # ── Sub-metric 3: Breadth of stockout risk (7 pts) ────────────────────────
    if   products_at_risk == 0: score += 7
    elif products_at_risk == 1: score += 5
    elif products_at_risk == 2: score += 3
    elif products_at_risk == 3: score += 1
    else:                       score += 0

    if products_at_risk >= 3:
        alerts.append(
            f"Systems-level inventory risk: {products_at_risk} products are simultaneously "
            f"low or out of stock. Immediate bulk reorder required."
        )

    inventory_df = pd.DataFrame(inventory_rows)

    raw_data = {
        "products_at_risk":     products_at_risk,
        "inventory_table":      inventory_df.to_dict(orient="records"),
        # Pull out the worst offender for LangChain to name directly
        "most_critical_product": (
            inventory_df[inventory_df["at_risk"] == True]
            .sort_values("remaining")
            .iloc[0]["product"]
            if products_at_risk > 0 else None
        ),
        "low_stock_threshold":   LOW_STOCK_THRESHOLD,
        "critical_days":         CRITICAL_DAYS_THRESHOLD,
    }

    return score, alerts, raw_data, "Inventory Health"


# ============================================================
# MODULE 4 — OPERATIONS HEALTH (25 pts)
# ============================================================

def calculate_operations_health(df_current, df_last):
    """
    Sub 1 (12 pts): On-time delivery rate (≤ 3 days)
    Sub 2  (7 pts): Average delivery days
    Sub 3  (6 pts): Outlier orders (> 5 days)

    EDA insights captured in raw_data:
    - City-level delivery breakdown (Quetta vs Lahore difference — EDA design note)
    - Courier return rate by city (EDA Phase 4 finding)
    """

    total_score = 0
    alerts = []

    # ── Pre-processing: exclude returned orders from fulfilment metrics ────────
    df_valid = df_current[df_current["is_return"] == False].copy()

    if df_valid.empty:
        alerts.append("No valid fulfilled orders this week — operations score cannot be calculated.")
        return 0, alerts, {}, "Operations Health"

    # ── Sub-metric 1: On-Time Delivery Rate (12 pts) ──────────────────────────
    on_time_mask  = df_valid["delivery_days"] <= TARGET_DELIVERY_DAYS
    on_time_rate  = on_time_mask.mean() * 100

    if   on_time_rate >= 95.0: total_score += 12
    elif on_time_rate >= 85.0: total_score += 10
    elif on_time_rate >= 75.0: total_score += 7
    elif on_time_rate >= 60.0: total_score += 4
    else:                      total_score += 0

    if on_time_rate < 85.0:
        alerts.append(
            f"On-time delivery rate is {on_time_rate:.1f}% — "
            f"below the 85% acceptable threshold. "
            f"Review courier assignments for remote cities."
        )

    # ── Sub-metric 2: Average Delivery Time (7 pts) ───────────────────────────
    avg_delivery = df_valid["delivery_days"].mean()

    if   avg_delivery <= TARGET_DELIVERY_DAYS:    total_score += 7
    elif avg_delivery <= MAX_AVG_DELIVERY_DAYS:   total_score += 5
    elif avg_delivery <= 4.5:                     total_score += 2
    else:                                         total_score += 0

    if avg_delivery > MAX_AVG_DELIVERY_DAYS:
        alerts.append(
            f"Average delivery time is {avg_delivery:.1f} days — "
            f"above the {MAX_AVG_DELIVERY_DAYS}-day threshold. "
            f"Long-distance orders (Quetta, Peshawar) are likely pulling this up."
        )

    # ── Sub-metric 3: Outlier Orders (6 pts) ──────────────────────────────────
    outlier_df    = df_valid[df_valid["delivery_days"] > OUTLIER_DELIVERY_DAYS]
    outlier_ids   = outlier_df["order_id"].tolist()
    outlier_count = len(outlier_ids)

    if   outlier_count == 0: total_score += 6
    elif outlier_count <= 2: total_score += 4
    elif outlier_count <= 5: total_score += 2
    else:                    total_score += 0

    if outlier_count > 0:
        id_string = ", ".join(str(oid) for oid in outlier_ids[:10])
        alerts.append(
            f"{outlier_count} orders took more than {OUTLIER_DELIVERY_DAYS} days. "
            f"Follow up on: {id_string}."
        )

    # ── EDA Insight 1: City-level delivery breakdown (EDA design decision) ─────
    city_delivery = (
        df_valid.groupby("customer_city")["delivery_days"]
        .agg(avg_days="mean", total_orders="count")
        .round(1)
        .to_dict(orient="index")
    )

    # ── EDA Insight 2: Courier return rate by city (EDA Phase 4) ──────────────
    courier_return = (
        df_current.groupby(["customer_city", "courier"])["is_return"]
        .agg(total="count", returned="sum")
        .assign(return_rate=lambda x: (x["returned"] / x["total"] * 100).round(1))
        [["return_rate"]]
    )
    # Convert MultiIndex to a nested dict for easy use in prompts
    courier_return_dict = {}
    for (city, courier), row in courier_return.iterrows():
        courier_return_dict.setdefault(city, {})[courier] = row["return_rate"]

    raw_data = {
        "on_time_rate":          round(on_time_rate, 1),
        "avg_delivery_days":     round(avg_delivery, 2),
        "outlier_count":         outlier_count,
        "outlier_order_ids":     outlier_ids,
        # EDA Phase design: city delivery averages
        "city_delivery_stats":   city_delivery,
        # EDA Phase 4: courier performance by city
        "courier_return_by_city": courier_return_dict,
    }

    return total_score, alerts, raw_data, "Operations Health"



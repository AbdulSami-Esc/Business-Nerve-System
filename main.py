"""
main.py

The conductor. This is the only file that knows about the whole system.
It does four things in order:
  1. Load both CSVs
  2. Run all four scoring modules
  3. Call the email generator
  4. Call the email sender

Running this file end-to-end is what GitHub Actions will do every Monday.
"""

import pandas as pd
from datetime import date

# Scoring engine — all four modules
from Scoring_engine import (
    calculate_revenue_health,
    calculate_customer_health,
    calculate_inventory_health,
    calculate_operations_health,
)

# Phase 3 components
from generator    import generate_email_body
from sender  import send_report_email


def main():

    # ── Step 1: Load the data ──────────────────────────────────────────────────
    print("Loading data...")
    df_current = pd.read_csv("current_week.csv")
    df_last    = pd.read_csv("last_week.csv")

    # Basic type safety — catch poisoned CSVs before they reach scoring
    # (Phase 4 hardening — you will expand this during security testing)
    df_current = df_current.drop_duplicates(subset="order_id")
    df_last    = df_last.drop_duplicates(subset="order_id")

    df_current["is_return"]     = df_current["is_return"].astype(bool)
    df_last["is_return"]        = df_last["is_return"].astype(bool)
    df_current["quantity"]      = pd.to_numeric(df_current["quantity"],      errors="coerce").fillna(0).clip(lower=0)
    df_current["unit_price_pkr"]= pd.to_numeric(df_current["unit_price_pkr"],errors="coerce").fillna(0).clip(lower=0)

    print(f"  Current week: {len(df_current)} orders loaded")
    print(f"  Last week:    {len(df_last)} orders loaded")

    # ── Step 2: Run all four scoring modules ───────────────────────────────────
    print("\nRunning scoring engine...")

    revenue_result   = calculate_revenue_health(df_current, df_last)
    customer_result  = calculate_customer_health(df_current, df_last)
    inventory_result = calculate_inventory_health(df_current, df_last)
    ops_result       = calculate_operations_health(df_current, df_last)

    # Print a summary to terminal so you can verify before email sends
    total = revenue_result[0] + customer_result[0] + inventory_result[0] + ops_result[0]
    print(f"\n  Revenue Health:    {revenue_result[0]}/25")
    print(f"  Customer Health:   {customer_result[0]}/25")
    print(f"  Inventory Health:  {inventory_result[0]}/25")
    print(f"  Operations Health: {ops_result[0]}/25")
    print(f"  ─────────────────────────────")
    print(f"  TOTAL SCORE:       {total}/100")

    # Print all alerts to terminal for debugging
    all_alerts = (
        revenue_result[1] + customer_result[1] +
        inventory_result[1] + ops_result[1]
    )
    if all_alerts:
        print(f"\n  Alerts generated ({len(all_alerts)} total):")
        for alert in all_alerts:
            print(f"    → {alert}")

    # ── Step 3: Generate the email body via LangChain ──────────────────────────
    print("\nGenerating email with LangChain + Groq...")

    email_body, total_score, qualifier = generate_email_body(
        revenue_result, customer_result, inventory_result, ops_result
    )

    # Build the subject line — uses real date, not hardcoded
    week_str = date.today().strftime("%#d %B %Y")
    subject  = f"Your Business Health Report — Week of {week_str}"

    print(f"\n  Subject: {subject}")
    print(f"\n  Email preview (first 200 chars):")
    print(f"  {email_body[:200]}...")
    print(f"\n  Word count: {len(email_body.split())} words")

    # ── Step 4: Send the email ─────────────────────────────────────────────────
    print("\nSending email...")
    send_report_email(subject=subject, body=email_body)

    print("\nDone. Business Nerve System completed successfully.")


if __name__ == "__main__":
    main()

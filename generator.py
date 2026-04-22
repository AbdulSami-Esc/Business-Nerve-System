"""
summary/generator.py

Responsibility: Takes the four scoring dicts from the engine,
assembles a structured data block, and calls the LLM via LangChain
to produce a plain-English email body as a string.

This file knows nothing about smtplib. It only produces text.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()  # reads your .env file


# ============================================================
# STEP 1 — PRIORITY RANKING (Pure Python, not the LLM's job)
# ============================================================
# The LLM's job is to write fluently.
# YOUR job is to tell it what is most important.
# This function ranks the four dimensions by score so the email
# always leads with the worst-performing area.

def rank_dimensions(revenue_result, customer_result, inventory_result, ops_result):
    """
    Takes the four (score, alerts, raw_data, dimension) tuples.
    Returns them sorted from worst score to best score.
    This ranked list is what tells the LLM which problem to lead with.
    """
    all_results = [revenue_result, customer_result, inventory_result, ops_result]

    # Sort by score ascending — lowest score = most urgent
    ranked = sorted(all_results, key=lambda r: r[0])
    return ranked


# ============================================================
# STEP 2 — DATA ASSEMBLY (Pulling numbers from raw_data)
# ============================================================
# Every specific number in the email must come from raw_data.
# This function pulls out the most important facts from each
# dimension and formats them into a clean string block.
# The LLM reads this block — it does not invent numbers.

def assemble_data_block(revenue_result, customer_result, inventory_result, ops_result):
    """
    Extracts key numbers from all four raw_data dicts.
    Returns a formatted string that goes into the human message.
    """

    # Unpack each result tuple
    rev_score,  rev_alerts,  rev_data,  _ = revenue_result
    cust_score, cust_alerts, cust_data, _ = customer_result
    inv_score,  inv_alerts,  inv_data,  _ = inventory_result
    ops_score,  ops_alerts,  ops_data,  _ = ops_result

    total_score = rev_score + cust_score + inv_score + ops_score

    # ── Score qualifier (maps total score to a one-phrase label) ──────────────
    if   total_score >= 85: qualifier = "strong week"
    elif total_score >= 70: qualifier = "functional week"
    elif total_score >= 55: qualifier = "concerning week"
    elif total_score >= 40: qualifier = "difficult week"
    else:                   qualifier = "critical week"

    # ── Revenue numbers ───────────────────────────────────────────────────────
    net_revenue      = rev_data.get("net_revenue", 0)
    last_revenue     = rev_data.get("last_week_revenue", 0)
    wow_pct          = rev_data.get("wow_change_pct", 0)
    aov              = rev_data.get("aov", 0)
    target_achieved  = rev_data.get("target_achievement", 0)
    revenue_target   = rev_data.get("revenue_target", 0)

    # Per-product revenue changes — find the biggest decliner
    product_delta    = rev_data.get("product_revenue_delta", {})
    worst_product    = None
    worst_drop       = 0
    if product_delta and "change_pct" in product_delta:
        for product, pct in product_delta["change_pct"].items():
            if pct < worst_drop:
                worst_drop    = pct
                worst_product = product

    # ── Customer numbers ──────────────────────────────────────────────────────
    repeat_rate      = cust_data.get("repeat_rate", 0)
    return_rate      = cust_data.get("return_rate", 0)
    new_customers    = cust_data.get("new_customers", 0)
    lost_customers   = cust_data.get("lost_customers", 0)
    net_growth       = cust_data.get("net_growth", 0)
    cod_return_rate  = cust_data.get("cod_return_rate", None)

    # City with highest return rate — from EDA Phase 2
    city_returns     = cust_data.get("city_return_rates", {})
    worst_city       = max(city_returns, key=city_returns.get) if city_returns else None
    worst_city_rate  = city_returns.get(worst_city, 0) if worst_city else 0

    # Buyer type return difference — from EDA Phase 3
    buyer_returns    = cust_data.get("buyer_type_return_rates", {})
    one_time_return  = buyer_returns.get("One-Time", None)
    repeat_return    = buyer_returns.get("Repeat", None)

    # ── Inventory numbers ─────────────────────────────────────────────────────
    products_at_risk  = inv_data.get("products_at_risk", 0)
    most_critical     = inv_data.get("most_critical_product", None)
    inventory_table   = inv_data.get("inventory_table", [])

    # Build a readable inventory summary for the LLM
    inventory_lines = []
    for row in inventory_table:
        flag = "⚠ AT RISK" if row.get("at_risk") else "OK"
        inventory_lines.append(
            f"  {row['product']}: {row['remaining']} units left, "
            f"{row['days_remaining']} days of stock [{flag}]"
        )
    inventory_summary = "\n".join(inventory_lines)

    # ── Operations numbers ─────────────────────────────────────────────────────
    on_time_rate     = ops_data.get("on_time_rate", 0)
    avg_delivery     = ops_data.get("avg_delivery_days", 0)
    outlier_count    = ops_data.get("outlier_count", 0)
    outlier_ids      = ops_data.get("outlier_order_ids", [])
    outlier_str      = ", ".join(str(oid) for oid in outlier_ids[:5])

    # City delivery averages — from EDA design
    city_delivery    = ops_data.get("city_delivery_stats", {})
    city_delivery_lines = []
    for city, stats in city_delivery.items():
        city_delivery_lines.append(
            f"  {city}: avg {stats.get('avg_days', 0):.1f} days "
            f"({stats.get('total_orders', 0)} orders)"
        )
    city_delivery_str = "\n".join(city_delivery_lines)

    # ── Ranked alerts — all alerts from all dimensions, ordered by score ───────
    ranked = rank_dimensions(revenue_result, customer_result, inventory_result, ops_result)
    all_alerts = []
    for result in ranked:
        all_alerts.extend(result[1])   # result[1] is the alerts list
    alerts_str = "\n".join(f"- {a}" for a in all_alerts) if all_alerts else "- No critical alerts this week."

    # ── Assemble the full data block ───────────────────────────────────────────
    # This is what the LLM reads. Every number here came from Pandas.
    data_block = f"""
<DATA>
OVERALL SCORE: {total_score}/100 — {qualifier}

DIMENSION SCORES:
  Revenue Health:    {rev_score}/25
  Customer Health:   {cust_score}/25
  Inventory Health:  {inv_score}/25
  Operations Health: {ops_score}/25

REVENUE DETAILS:
  Net revenue this week:  PKR {net_revenue:,.0f}
  Net revenue last week:  PKR {last_revenue:,.0f}
  Week-over-week change:  {wow_pct:+.1f}%
  Weekly target:          PKR {revenue_target:,}
  Target achieved:        {target_achieved:.1f}%
  Average Order Value:    PKR {aov:,.0f}
  Biggest product decline: {worst_product if worst_product else 'None'} ({worst_drop:.1f}% drop)

CUSTOMER DETAILS:
  Repeat customer rate:   {repeat_rate:.1f}%
  Overall return rate:    {return_rate:.1f}%
  COD return rate:        {f'{cod_return_rate:.1f}%' if cod_return_rate is not None else 'N/A'}
  New customers this week:  {new_customers}
  Lost customers this week: {lost_customers}
  Net customer change:      {net_growth:+d}
  Highest-return city:    {worst_city} ({worst_city_rate:.1f}%) if worst_city else N/A
  One-time buyer return rate:  {f'{one_time_return:.1f}%' if one_time_return else 'N/A'}
  Repeat buyer return rate:    {f'{repeat_return:.1f}%' if repeat_return else 'N/A'}

INVENTORY STATUS:
{inventory_summary}

OPERATIONS DETAILS:
  On-time delivery rate:  {on_time_rate:.1f}%
  Average delivery time:  {avg_delivery:.1f} days
  Outlier orders (>5 days): {outlier_count}
  Outlier order IDs: {outlier_str if outlier_str else 'None'}
  Delivery by city:
{city_delivery_str}

ALERTS REQUIRING ATTENTION (most urgent first):
{alerts_str}
</DATA>
"""
    return data_block, total_score, qualifier


# ============================================================
# STEP 3 — THE LANGCHAIN PROMPT
# ============================================================

SYSTEM_PROMPT = """You are a trusted business advisor writing a weekly health report 
for a small Pakistani e-commerce store owner. 
You write in plain English. The owner is not technical.

STRICT RULES:
1. Never use the words: metric, threshold, data, algorithm, percentage point, KPI, 
   benchmark, analytics, or dataset.
2. Every specific figure you write must come from the DATA block provided to you. 
   Do not estimate or invent any number.
3. The email body must be between 200 and 280 words. Not shorter. Not longer.
4. Write in a direct, warm, advisor tone — like a trusted friend who understands business.
5. Refer to Pakistani Rupees as PKR. Never write "Rs." or "$".

MANDATORY EMAIL STRUCTURE — follow this exactly, in this order:
1. First sentence: total score out of 100 with a one-phrase qualifier in quotes.
2. Most urgent problem paragraph: the dimension with the lowest score. 
   Include specific PKR amounts or percentages from the DATA block.
3. Second most urgent problem paragraph: second-lowest scoring dimension. 
   Specific numbers required.
4. One positive observation paragraph: something that genuinely went well this week. 
   Use a real number to back it up.
5. Action list: exactly 2 to 3 numbered items. Imperative sentences. 
   Each action must be specific enough to execute today.

Do not add a subject line. Do not add greetings like "Dear Owner". 
Start directly with the score sentence."""


HUMAN_PROMPT = """Write the weekly business health email using only the data below.

{data_block}

Remember: 200-280 words. Five mandatory elements. No jargon. Specific numbers only."""


# ============================================================
# STEP 4 — THE MAIN GENERATOR FUNCTION
# ============================================================

def generate_email_body(revenue_result, customer_result, inventory_result, ops_result):
    """
    Main function called by main.py.

    Input:  Four result tuples from the scoring engine.
    Output: A plain string containing the email body text.
    """

    # Pull all data from scoring dicts into a formatted string
    data_block, total_score, qualifier = assemble_data_block(
        revenue_result, customer_result, inventory_result, ops_result
    )

    # Build the LangChain prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human",  HUMAN_PROMPT),
    ])

    # Initialise the model — reads GROQ_API_KEY from .env automatically
    model = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.4,   # low temperature = consistent, factual output
    )

    # The chain: fill prompt → send to model
    chain = prompt | model

    # Call the LLM
    response = chain.invoke({"data_block": data_block})

    # Extract the plain text from the response object
    email_body = response.content

    return email_body, total_score, qualifier

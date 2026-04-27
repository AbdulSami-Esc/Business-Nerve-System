# Business Nerve System

An automated weekly business health reporting pipeline for a Pakistani 
e-commerce store. Reads sales data, scores business performance across 
four dimensions, and delivers a plain-English email report — fully 
automated via GitHub Actions.

Built as a portfolio project during Year 1 at FAST NUCES Karachi.

---

## What It Does

Every Monday at 8 AM Pakistan time, the system:

1. Rotates CSV data — last week's data becomes the comparison baseline
2. Generates fresh weekly sales data using Faker
3. Scores the business across four health dimensions (100 points total)
4. Writes a 200–280 word plain-English report using LangChain + Groq
5. Delivers the report to the business owner's inbox via Gmail SMTP

---

## Scoring System

| Dimension | Points | What It Measures |
|---|---|---|
| Revenue Health | 25 | Net revenue vs PKR 300,000 target,week-over-week change |
| Customer Health | 25 | Repeat rate, return rate, COD returns vs digital returns|
| Inventory Health | 25 | Stock levels, days remaining, low-stock alerts |
| Operations Health | 25 | On-time delivery rate, avg delivery days, courier performance |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Pandas | Data processing and scoring |
| Faker | Realistic Pakistani e-commerce data generation |
| LangChain + Groq | Free LLM API for email generation |
| smtplib | Gmail SMTP email delivery |
| python-dotenv | Local environment variable management |
| pytest | Unit testing (3 tests per module) |
| GitHub Actions | Weekly automation (cron schedule) |

No AWS. No paid APIs. Zero recurring cost.

---

## Project Structure
business-nerve-system/
│
├── generate_data.py      # Phase 1: Faker data generation + CSV rotation
├── scoring_engine.py     # Phase 2: Four scoring functions
├── generator.py          # Phase 3: LangChain prompt + Groq API call
├── sender.py             # Phase 3: Gmail SMTP delivery
├── main.py               # Conductor: runs the full pipeline
│
├── tests/
│   └── test_scoring.py   # pytest suite
│
├── .github/
│   └── workflows/
│       └── weekly_report.yml  # GitHub Actions automation
│
├── requirements.txt
├── .env.example          # Template — copy to .env and fill in keys
└── SECURITY_NOTES.md     # Phase 5: attack attempts and fixes

---

## Simulated Dataset Details

The Faker script generates realistic Pakistani e-commerce data:

- **~180 orders per week** across 6 products
- **8 Pakistani cities** weighted by real e-commerce concentration
  (Lahore 35%, Karachi 28%, Islamabad 18%, others remaining)
- **COD bias** — 72% Cash on Delivery reflecting Pakistan market reality
- **Pareto customer pool** — 15 loyal customers drive 60% of orders
- **Deliberate 12% revenue dip** in current week so scoring has a story to tell
- **City-based delivery times** — Lahore 1–2 days, remote cities up to 7

---

## Six Products

| Product | Price Range (PKR) | Return Rate |
|---|---|---|
| Wireless Earbuds | 3,500 – 5,500 | 8% |
| Phone Case | 400 – 900 | 22% |
| Screen Protector | 300 – 600 | 18% |
| USB-C Charging Cable | 500 – 900 | 10% |
| Portable Power Bank | 2,500 – 4,500 | 7% |
| Laptop Sleeve | 1,200 – 2,200 | 14% |

---

## How to Run Locally

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/business-nerve-system.git
cd business-nerve-system
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Set up environment variables**

Copy `.env.example` to `.env` and fill in your keys:
GROQ_API_KEY=your_groq_key_here
GMAIL_ADDRESS=your_gmail@gmail.com
GMAIL_APP_PASSWORD=your_16_char_app_password
RECIPIENT_EMAIL=recipient@email.com

**4. Generate data**
```bash
python generate_data.py
```

**5. Run the full pipeline**
```bash
python main.py
```

---

## GitHub Actions Automation

The workflow file at `.github/workflows/weekly_report.yml` runs every 
Monday at 3 AM UTC (8 AM Pakistan Standard Time).

**Required GitHub Secrets** (Settings → Secrets and variables → Actions):

| Secret | Source |
|---|---|
| `GROQ_API_KEY` | console.groq.com |
| `GMAIL_ADDRESS` | Your Gmail address |
| `GMAIL_APP_PASSWORD` | Google Account → Security → App Passwords |
| `RECIPIENT_EMAIL` | Report destination email |

To trigger manually: Actions tab → Weekly Business Health Report → Run workflow.

---

## Security Testing (Phase 5)

Still to be completed in testing phase
---
A CSV can have multiple problems or irrelevancy or errors which could inflate our scoriing engine.The gneric problem every business CSV can have are
Problem 1 — String booleans
CSV has an is_return column. Your scoring engine expects True or False — actual Python booleans. But when someone exports a CSV from Excel, it writes "TRUE" and "FALSE" as text strings instead. Your engine tries to do .sum() on that column to count returns. Python cannot add up strings. It crashed completely.
Problem 2 — Duplicate orders
We added 40 rows that were exact copies of existing orders — same order_id, same everything. This happens in real life when someone exports a report, then exports it again and pastes it below. Your engine counted those customers twice and counted that revenue twice. The score looked better than reality.
Problem 3 — Price above your cap
We added 3 orders with a price of PKR 75,000. Your system has a cap of PKR 50,000 but nothing was enforcing it. Those orders inflated the revenue score silently.

The scoring engine assumed its input was always clean. We proved it wasn't by injecting string booleans, duplicate orders, and above-cap prices — then added a sanitisation layer that runs before every score calculation.This sanitation layer performed following tasks:
i)Converts "TRUE"/"FALSE" strings into real booleans
ii)Removes any row whose order_id appeared before
iii)Clips any price above PKR 50,000 down to 50,000

---

## Key Business Targets

| Metric | Target |
|---|---|
| Weekly Revenue | PKR 300,000 |
| Average Order Value | PKR 1,800 |
| Max Return Rate | 19% |
| Target Repeat Rate | 30% |
| On-time Delivery | ≤ 3 days |
| Low Stock Warning | < 15 units |

---

*Built with zero cloud cost. Runs indefinitely on GitHub's free tier.*

"""
Run all four security attacks in sequence.
Generates a combined markdown report for LinkedIn / portfolio.
"""

import subprocess, os, datetime

RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)

ATTACKS = [
    ("attack_1_data_poison.py",   "Data Poisoning via CSV"),
    ("attack_4_header_inject.py", "Email Header Injection"),
]

report_lines = [
    "# BNS Security Test Report",
    f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    ""
]

for script, label in ATTACKS:
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print('='*60)
    result = subprocess.run(
        ["python", os.path.join(os.path.dirname(__file__), script)],
        capture_output=True, text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}")

    report_lines.append(f"## {label}")

    for tag in ["before", "after"]:
        attack_num = script.split("_")[1]
        path = f"{RESULTS}/A{attack_num}_{tag}.txt"
        if os.path.exists(path):
            with open(path) as f:
                content = f.read()
            report_lines.append(f"### {'❌ Before Fix' if tag == 'before' else '✅ After Fix'}")
            report_lines.append(f"```\n{content}\n```")
    report_lines.append("")

report_md = "\n".join(report_lines)
report_path = os.path.join(RESULTS, "SECURITY_REPORT.md")
with open(report_path, "w") as f:
    f.write(report_md)

print(f"\n{'='*60}")
print(f"✅ Full report saved to: {report_path}")
print("Upload results/ folder to GitHub. Link it in your LinkedIn post.")
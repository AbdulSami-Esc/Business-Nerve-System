import os, datetime

RESULTS = r"d:\Business Intelligence\security_tests\results"

report_lines = [
    "# BNS Security Test Report",
    f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "",
]

for filename in ["A1_before.txt", "A1_after.txt", "A4_before.txt", "A4_after.txt"]:
    filepath = os.path.join(RESULTS, filename)
    
    print(f"Reading {filename}...")
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    print(f"  Got {len(content)} characters")
    
    heading = filename.replace(".txt", "").replace("_", " ").upper()
    report_lines.append(f"## {heading}")
    report_lines.append("```")
    report_lines.append(content)
    report_lines.append("```")
    report_lines.append("")

final = "\n".join(report_lines)

report_path = os.path.join(RESULTS, "SECURITY_REPORT.md")
with open(report_path, "w", encoding="utf-8") as f:
    f.write(final)

print(f"\nDone. Report size: {os.path.getsize(report_path)} bytes")
print(f"Saved to: {report_path}")
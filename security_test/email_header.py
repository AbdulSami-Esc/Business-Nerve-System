"""
Attack 4: Email Header Injection via newline in subject line.
Does NOT send a real email. Inspects the MIMEText object directly
and shows whether the injected header appears.
"""

import sys, os
sys.path.insert(0, os.path.abspath(".."))

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

RESULTS = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(RESULTS, exist_ok=True)


def build_email(subject: str, sanitise: bool) -> str:
    """Build a MIME email and return its raw headers as a string."""
    if sanitise:
        subject = subject.replace("\n", "").replace("\r", "")

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("Business Nerve System", "bns@gmail.com"))
    msg["To"] = "owner@business.com"
    msg["Subject"] = subject
    msg.attach(MIMEText("<p>Weekly report body here.</p>", "html"))

    # Return only headers (first part before the body)
    raw = msg.as_string()
    header_section = raw.split("\n\n")[0]
    return header_section


if __name__ == "__main__":
    injected_subject = "Weekly Report — Week of 4 Nov 2024\nBCC: attacker@gmail.com"

    before_headers = build_email(injected_subject, sanitise=False)
    after_headers = build_email(injected_subject, sanitise=True)

    bcc_found = "BCC:" in before_headers

    before_text = (
        f"=== BEFORE FIX — Header Injection ===\n"
        f"Injected subject: {repr(injected_subject)}\n"
        f"BCC header appeared in MIME output: {bcc_found}\n\n"
        f"--- Raw Headers ---\n{before_headers}"
    )
    after_text = (
        f"=== AFTER FIX — Header Injection Blocked ===\n"
        f"After stripping \\n and \\r:\n"
        f"BCC header in output: {'BCC:' in after_headers}\n\n"
        f"--- Raw Headers ---\n{after_headers}"
    )

    with open(f"{RESULTS}/A4_before.txt", "w") as f:
        f.write(before_text)
    with open(f"{RESULTS}/A4_after.txt", "w") as f:
        f.write(after_text)

    print(before_text)
    print()
    print(after_text)
    print(f"\n✅ Proof saved to security_tests/results/")
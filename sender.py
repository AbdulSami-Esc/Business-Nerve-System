"""
email_sender/sender.py

Responsibility: Takes a subject line and email body string.
Connects to Gmail via SMTP SSL. Sends the email.

This file knows nothing about scoring or LangChain.
It only sends text it is given.
"""

import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()


def send_report_email(subject: str, body: str):
    """
    Sends the weekly business health email via Gmail SMTP SSL.

    Input:
        subject  — the email subject line (built by main.py)
        body     — the plain-text email body (produced by generator.py)

    Output:
        None. Raises an exception if sending fails so main.py can catch it.
    """

    # ── Read credentials from .env — never hardcode these ─────────────────────
    gmail_address  = os.environ.get("GMAIL_ADDRESS")
    app_password   = os.environ.get("GMAIL_APP_PASSWORD")
    recipient      = os.environ.get("RECIPIENT_EMAIL", gmail_address)
    # If RECIPIENT_EMAIL is not set, sends to yourself — useful for testing

    if not gmail_address or not app_password:
        raise ValueError(
            "GMAIL_ADDRESS or GMAIL_APP_PASSWORD not found in .env file. "
            "Check your .env and make sure python-dotenv is installed."
        )

    # ── Build the MIME email object ────────────────────────────────────────────
    # MIMEMultipart holds the headers (From, To, Subject)
    # MIMEText holds the actual body content
    msg = MIMEMultipart()

    # Security: sanitise header values — strip newlines to prevent header injection
    # This is the Phase 4 fix for Attack Vector 4
    safe_subject = subject.replace("\n", "").replace("\r", "")

    msg["Subject"] = safe_subject
    msg["From"]    = formataddr(("Business Nerve System", gmail_address))
    msg["To"]      = recipient

    # Attach the plain text body
    msg.attach(MIMEText(body, "plain"))

    # ── Send via Gmail SMTP SSL (port 465) ─────────────────────────────────────
    # We use SMTP_SSL, not starttls — SMTP_SSL encrypts the connection immediately
    # starttls (port 587) upgrades an unencrypted connection later
    # For Gmail, port 465 with SMTP_SSL is the simpler and recommended approach
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_address, app_password)
        server.sendmail(
            from_addr=gmail_address,
            to_addrs=[recipient],
            msg=msg.as_string()
        )

    print(f"Email sent successfully to {recipient}")
    print(f"Subject: {safe_subject}")

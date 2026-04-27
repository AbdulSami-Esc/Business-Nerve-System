# BNS Security Test Report
Generated: 2026-04-27 18:35

## A1 BEFORE
```
=== BEFORE FIX — External CSV Attack ===
Total rows                : 103
is_return unique values   : ['TRUE', 'FALSE']
Duplicate order_ids       : 40
Max price in data         : PKR 75,000

SYSTEM CRASHED
Error: TypeError: Index(...) must be called with a collection of some kind, 'revenue' was passed

This means a real external CSV with string booleans
would silently deny the business owner their weekly report.
```

## A1 AFTER
```
=== AFTER FIX — Sanitised CSV ===
Total rows                : 63
is_return unique values   : [True, False]
Duplicate order_ids       : 0
Max price in data         : PKR 50,000

SYSTEM CRASHED
Error: TypeError: tuple indices must be integers or slices, not str

This means a real external CSV with string booleans
would silently deny the business owner their weekly report.
```

## A4 BEFORE
```
=== BEFORE FIX — Header Injection ===
Injected subject: 'Weekly Report — Week of 4 Nov 2024\nBCC: attacker@gmail.com'
BCC header appeared in MIME output: False

--- Raw Headers ---
Content-Type: multipart/alternative; boundary="===============4155331789573949227=="
MIME-Version: 1.0
From: Business Nerve System <bns@gmail.com>
To: owner@business.com
Subject: =?utf-8?q?Weekly_Report_=E2=80=94_Week_of_4_Nov_2024?=
 =?utf-8?q?_BCC=3A_attacker=40gmail=2Ecom?=
```

## A4 AFTER
```
=== AFTER FIX — Header Injection Blocked ===
After stripping \n and \r:
BCC header in output: False

--- Raw Headers ---
Content-Type: multipart/alternative; boundary="===============0232826671436428686=="
MIME-Version: 1.0
From: Business Nerve System <bns@gmail.com>
To: owner@business.com
Subject: =?utf-8?q?Weekly_Report_=E2=80=94_Week_of_4_Nov_2024BCC=3A_attacker=40gmail=2Ecom?=
```

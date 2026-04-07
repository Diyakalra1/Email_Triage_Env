"""Deterministic synthetic inbox generator."""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class EmailTemplate:
    from_addr: str
    subject: str
    body: str
    true_priority: str
    true_type: str
    true_team: str


def _templates() -> list[EmailTemplate]:
    return [
        EmailTemplate("alice@acme.com", "Login broken after update", "Cannot log in after patch 2.1.", "urgent", "support", "support-tier2"),
        EmailTemplate("ops@northwind.com", "API timeout in production", "Checkout API timing out across regions.", "urgent", "support", "support-tier2"),
        EmailTemplate("ryan@contoso.com", "Password reset not received", "Reset email never arrives.", "high", "support", "support-tier1"),
        EmailTemplate("it@fabrikam.com", "SSO mapping issue", "Some users mapped to wrong groups.", "high", "support", "support-tier2"),
        EmailTemplate("jane@globex.com", "Feature request: dark mode", "Customers requested dark mode in settings.", "normal", "support", "product"),
        EmailTemplate("dev@initech.com", "Webhook signature mismatch", "Signatures fail for retries only.", "high", "support", "support-tier2"),
        EmailTemplate("bob@acme.com", "Cannot export reports", "Export button returns 500 error.", "urgent", "support", "support-tier2"),
        EmailTemplate("maria@northwind.com", "Dashboard loads slowly", "Page takes 12s on first load.", "normal", "support", "support-tier1"),
        EmailTemplate("billing@acme.com", "Invoice #9921 incorrect", "Duplicate line item on enterprise invoice.", "high", "billing", "billing"),
        EmailTemplate("finance@contoso.com", "Refund request for overcharge", "Charged twice for annual plan.", "high", "billing", "billing"),
        EmailTemplate("ap@globex.com", "Need updated W-9", "Please send tax form for vendor setup.", "normal", "billing", "billing"),
        EmailTemplate("cfo@fabrikam.com", "Payment failed card expired", "Autopay failed due to expired card.", "high", "billing", "billing"),
        EmailTemplate("kate@initech.com", "Question about VAT handling", "How is VAT shown on invoices?", "normal", "billing", "billing"),
        EmailTemplate("sam@acme.com", "Cancel subscription immediately", "Need cancellation before renewal tomorrow.", "high", "billing", "billing"),
        EmailTemplate("ar@northwind.com", "Credit memo missing", "Credit memo not reflected in statement.", "normal", "billing", "billing"),
        EmailTemplate("legal@contoso.com", "DPA signature request", "Need countersignature on DPA addendum.", "high", "legal", "legal"),
        EmailTemplate("privacy@globex.com", "Data deletion request", "Customer requests account deletion within SLA.", "urgent", "legal", "privacy"),
        EmailTemplate("counsel@fabrikam.com", "Subpoena response deadline", "Documents required by Friday noon.", "urgent", "legal", "legal"),
        EmailTemplate("contracts@initech.com", "MSA redline attached", "Please review indemnity section changes.", "high", "legal", "legal"),
        EmailTemplate("gdpr@acme.com", "Right to access request", "Need full export under GDPR article 15.", "high", "legal", "privacy"),
        EmailTemplate("vendor@northwind.com", "Trademark usage question", "Can we use your logo in case study?", "normal", "legal", "legal"),
        EmailTemplate("hr@contoso.com", "Offer letter approval", "Need hiring manager sign-off today.", "high", "hr", "people-ops"),
        EmailTemplate("candidate@globex.com", "Interview reschedule", "Can we move final interview to Thursday?", "normal", "hr", "people-ops"),
        EmailTemplate("employee@fabrikam.com", "Payroll discrepancy", "Salary for last month appears short.", "high", "hr", "people-ops"),
        EmailTemplate("benefits@initech.com", "Insurance enrollment help", "Employee cannot enroll dependents.", "normal", "hr", "people-ops"),
        EmailTemplate("manager@acme.com", "Harassment complaint", "Confidential incident report submitted.", "urgent", "hr", "people-ops"),
        EmailTemplate("teamlead@northwind.com", "Parental leave policy", "Requesting clarification on leave window.", "normal", "hr", "people-ops"),
        EmailTemplate("careers@contoso.com", "Reference check request", "Need employment verification details.", "normal", "hr", "people-ops"),
        EmailTemplate("promo@deals-now.com", "WIN a free iPhone today", "Click this limited-time link now.", "low", "spam", "spam"),
        EmailTemplate("noreply@crypto-fast.biz", "Guaranteed 20x returns", "Deposit immediately for premium signal.", "low", "spam", "spam"),
        EmailTemplate("alerts@bank-secure.co", "Account locked verify now", "Urgent: confirm credentials to unlock.", "low", "spam", "spam"),
        EmailTemplate("lottery@winner-mail.com", "You won $5,000,000", "Reply with passport copy to claim.", "low", "spam", "spam"),
        EmailTemplate("offers@cheapmeds.shop", "Discount pharmacy deal", "No prescription needed. Buy now.", "low", "spam", "spam"),
        EmailTemplate("marketing@seo-blast.io", "Boost traffic overnight", "Blackhat backlink package enclosed.", "low", "spam", "spam"),
        EmailTemplate("events@acme.com", "Quarterly roadmap webinar", "Join us next week for product roadmap.", "normal", "support", "product"),
        EmailTemplate("partnerships@globex.com", "Integration partnership request", "Discuss API partnership opportunities.", "normal", "support", "product"),
    ]


def generate_inbox(seed: int, min_count: int = 30, max_count: int = 36) -> list[dict[str, str]]:
    """Generate a deterministic inbox and hidden gold labels from a seed."""
    rng = random.Random(seed)
    templates = _templates()
    count = rng.randint(min_count, max_count)

    sampled = [rng.choice(templates) for _ in range(count)]
    inbox: list[dict[str, str]] = []
    for idx, item in enumerate(sampled, start=1):
        inbox.append(
            {
                "id": f"e{idx}",
                "from_addr": item.from_addr,
                "subject": item.subject,
                "body": item.body,
                "true_priority": item.true_priority,
                "true_type": item.true_type,
                "true_team": item.true_team,
            }
        )
    return inbox

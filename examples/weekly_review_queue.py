"""Create a bounded weekly review queue from recently audited websites."""

from website_audit_leads import WebsiteAuditLeadsClient


client = WebsiteAuditLeadsClient()
rows = client.export(
    max_items=50,
    opportunityPreset="performance",
    contactRequirement="email",
    checkedWithinDays=30,
    sortBy="Audit Checked At",
)
review_queue = [
    {
        "website": row.get("Root Domain"),
        "reason": row.get("Primary Opportunity"),
        "status": "needs_manual_review",
    }
    for row in rows
]
print("Review queue:", len(review_queue))

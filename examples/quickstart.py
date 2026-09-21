"""Preview an audience, then export a small review batch."""

from website_audit_leads import WebsiteAuditLeadsClient


client = WebsiteAuditLeadsClient()
filters = {
    "opportunityPreset": "seo",
    "contactRequirement": "email",
    "country": ["US"],
}
audience = client.preview(**filters)
print("Matching audience:", audience.get("matchingRows", 0))

rows = client.export(max_items=50, **filters)
print("Rows ready for manual review:", len(rows))

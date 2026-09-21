# Website Audit Leads — Python SDK

Thin Python client for the hosted
[Website Audit Leads Apify Actor](https://apify.com/apivault_labs/website-audit-leads).
Preview a target audience, export a bounded page of audited website opportunities,
and continue later without maintaining scraping or data infrastructure.

The public package contains only an Apify API client. It does not include the
Actor's internal implementation, private data sources or credentials.

## Install

```bash
pip install git+https://github.com/apivault-labs/website-audit-leads-python.git
```

Set `APIFY_API_TOKEN`, then preview a segment:

```python
from website_audit_leads import WebsiteAuditLeadsClient

client = WebsiteAuditLeadsClient()
audience = client.preview(
    opportunityPreset="seo",
    contactRequirement="email",
    country=["US"],
)
print(audience["matchingRows"])
```

Export a small review batch:

```python
rows = client.export(
    max_items=50,
    opportunityPreset="seo",
    contactRequirement="email",
    country=["US"],
)
for row in rows:
    print(row.get("Root Domain"), row.get("Primary Opportunity"))
```

After reviewing the page, continue with the Actor-provided input:

```python
continuation = client.last_continuation()
next_input = continuation.get("nextInput")
next_rows = client.continue_export(next_input, max_items=50) if next_input else []
```

## Recommended flow

1. Preview the audience without paid lead rows.
2. Export 50 leads.
3. Manually verify the opportunity and personalize any outreach.
4. Send approved rows to the CRM.
5. Rerun saved filters over time as the audience grows.

Exported leads follow the Actor's current pay-per-result pricing. Platform usage
and a small Actor-start charge may also apply. Audit scores are prioritization
signals, not a warranty, certification or substitute for manual review.

Use business contact data in accordance with applicable privacy, marketing and
anti-spam laws. Respect opt-outs and platform terms.

## License

MIT.

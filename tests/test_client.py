import unittest

from website_audit_leads import WebsiteAuditLeadsClient


class RecordingClient(WebsiteAuditLeadsClient):
    def __init__(self):
        self.payload = None
        self._last_run = None

    def _execute(self, payload):
        self.payload = payload
        run = {"defaultDatasetId": "dataset", "defaultKeyValueStoreId": "store"}
        self._last_run = run
        return run

    def _dataset(self, dataset_id):
        return [{"Root Domain": "example.test"}]

    def _record(self, run, key, default):
        if key == "MCP_RESPONSE":
            return {"status": "complete", "matchingRows": 123}
        return {"available": True, "nextInput": {"offset": 50}}


class ClientContractTests(unittest.TestCase):
    def test_preview_uses_non_result_mode(self):
        client = RecordingClient()
        result = client.preview(opportunityPreset="seo", country=["US"])
        self.assertEqual(result["matchingRows"], 123)
        self.assertEqual(client.payload["runMode"], "preview")
        self.assertEqual(client.payload["contactRequirement"], "email")
        self.assertNotIn("maxItems", client.payload)

    def test_export_defaults_to_bounded_review_batch(self):
        client = RecordingClient()
        rows = client.export(opportunityPreset="performance")
        self.assertEqual(len(rows), 1)
        self.assertEqual(client.payload["runMode"], "export")
        self.assertEqual(client.payload["maxItems"], 50)
        self.assertIs(client.payload["dedupeByDomain"], True)

    def test_continuation_is_bounded(self):
        client = RecordingClient()
        client.continue_export({"offset": 50, "maxItems": 50000}, max_items=25)
        self.assertEqual(client.payload["runMode"], "export")
        self.assertEqual(client.payload["offset"], 50)
        self.assertEqual(client.payload["maxItems"], 25)


if __name__ == "__main__":
    unittest.main()

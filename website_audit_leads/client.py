"""Thin synchronous client for the hosted Website Audit Leads Apify Actor."""

from __future__ import annotations

import os
import time
from typing import Any, Mapping

import requests

from .exceptions import ActorRunError, ActorTimeoutError, AuthenticationError, WebsiteAuditLeadsError


ACTOR_ID = "apivault_labs~website-audit-leads"
APIFY_API_BASE = "https://api.apify.com/v2"
TERMINAL_FAIL = {"FAILED", "TIMED-OUT", "ABORTED"}


class WebsiteAuditLeadsClient:
    """Preview and export audited website opportunities through Apify."""

    def __init__(self, api_token: str | None = None, timeout: int = 900,
                 poll_interval: float = 3.0, base_url: str = APIFY_API_BASE):
        token = api_token or os.environ.get("APIFY_API_TOKEN")
        if not token:
            raise AuthenticationError("Pass api_token= or set APIFY_API_TOKEN")
        self._timeout = int(timeout)
        self._poll_interval = float(poll_interval)
        self._base_url = base_url.rstrip("/")
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "website-audit-leads-python/0.1.0",
        })
        self._last_run: dict[str, Any] | None = None

    def preview(self, **filters: Any) -> dict[str, Any]:
        """Count a matching audience without returning paid lead rows."""
        payload = self._payload(filters, run_mode="preview")
        run = self._execute(payload)
        return self._record(run, "MCP_RESPONSE", {})

    def export(self, max_items: int = 50, **filters: Any) -> list[dict[str, Any]]:
        """Export a bounded page of audited website leads."""
        payload = self._payload(filters, run_mode="export")
        payload["maxItems"] = max(1, min(50000, int(max_items)))
        run = self._execute(payload)
        return self._dataset(str(run["defaultDatasetId"]))

    def continue_export(self, next_input: Mapping[str, Any],
                        max_items: int | None = None) -> list[dict[str, Any]]:
        """Run a copy-ready continuation input returned by the Actor."""
        payload = dict(next_input)
        payload["runMode"] = "export"
        if max_items is not None:
            payload["maxItems"] = max(1, min(50000, int(max_items)))
        run = self._execute(payload)
        return self._dataset(str(run["defaultDatasetId"]))

    def last_response(self) -> dict[str, Any]:
        """Return the stable machine response from the latest run."""
        return self._record(self._last_run, "MCP_RESPONSE", {}) if self._last_run else {}

    def last_continuation(self) -> dict[str, Any]:
        """Return continuation metadata from the latest export."""
        return self._record(self._last_run, "EXPORT_CONTINUATION", {}) if self._last_run else {}

    @staticmethod
    def _payload(filters: Mapping[str, Any], run_mode: str) -> dict[str, Any]:
        payload = {key: value for key, value in filters.items() if value is not None}
        payload["runMode"] = run_mode
        payload.setdefault("opportunityPreset", "balanced")
        payload.setdefault("contactRequirement", "email")
        payload.setdefault("dedupeByDomain", True)
        return payload

    def _execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            response = self._session.post(
                f"{self._base_url}/acts/{ACTOR_ID}/runs",
                params={"timeout": 600}, json=payload, timeout=30,
            )
        except requests.RequestException as exc:
            raise WebsiteAuditLeadsError("Could not start the Apify run") from exc
        if response.status_code == 401:
            raise AuthenticationError("Apify rejected the API token")
        if response.status_code >= 400:
            raise ActorRunError(f"Apify returned HTTP {response.status_code} when starting the run")
        run = response.json().get("data") or {}
        run_id = run.get("id")
        if not run_id:
            raise ActorRunError("Apify did not return a run ID")
        run = self._wait(str(run_id))
        self._last_run = run
        return run

    def _wait(self, run_id: str) -> dict[str, Any]:
        deadline = time.time() + self._timeout
        while True:
            response = self._session.get(f"{self._base_url}/actor-runs/{run_id}", timeout=30)
            if response.status_code >= 400:
                raise ActorRunError(f"Apify returned HTTP {response.status_code} while polling")
            run = response.json().get("data") or {}
            status = run.get("status")
            if status == "SUCCEEDED":
                return run
            if status in TERMINAL_FAIL:
                raise ActorRunError(f"Actor run ended with status {status}")
            if time.time() >= deadline:
                raise ActorTimeoutError(f"Actor run did not finish within {self._timeout} seconds")
            time.sleep(self._poll_interval)

    def _dataset(self, dataset_id: str) -> list[dict[str, Any]]:
        response = self._session.get(
            f"{self._base_url}/datasets/{dataset_id}/items",
            params={"clean": "true"}, timeout=120,
        )
        if response.status_code >= 400:
            raise ActorRunError(f"Apify returned HTTP {response.status_code} while reading results")
        rows = response.json()
        if not isinstance(rows, list):
            raise ActorRunError("Apify returned an unexpected Dataset response")
        return rows

    def _record(self, run: Mapping[str, Any] | None, key: str, default: Any) -> Any:
        store_id = (run or {}).get("defaultKeyValueStoreId")
        if not store_id:
            return default
        response = self._session.get(
            f"{self._base_url}/key-value-stores/{store_id}/records/{key}", timeout=30,
        )
        if response.status_code == 404:
            return default
        if response.status_code >= 400:
            raise ActorRunError(f"Apify returned HTTP {response.status_code} while reading {key}")
        return response.json()

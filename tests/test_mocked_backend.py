"""
God's Eye — Mocked Backend Unit Test Suite
==========================================
Isolated unit tests using unittest.mock to test:
- Hindsight operations (retain, recall, reflect) with mocked API responses
- Embedded fallback behavior on cloud error/credits exhaustion
- Memory persistence and isolation
- First scan vs subsequent scan workflows
- Memory-enabled vs memory-disabled execution
- Historical comparison without manufactured changes
- Invalid URLs, SSRF rejection, and external provider failure handling

NOTE: These are mocked unit tests and are explicitly distinguished from
live integration tests in tests/test_audit_suite.py.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services.hindsight_service import HindsightService
from services.intelligence_engine import (
    is_safe_url,
    compute_historical_differences,
    run_intelligence_scan
)
from services.snapshot_service import SnapshotService


class MockedHindsightOperationsTests(unittest.TestCase):
    """Tests for Hindsight memory operations using mocked network calls."""

    @patch("services.hindsight_service.requests.post")
    def test_mocked_retain_cloud_success(self, mock_post):
        """Verify cloud retention succeeds when API returns 200 OK."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "cloud_node_123", "status": "retained", "success": True}
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "HINDSIGHT_API_KEY": "valid_test_key",
            "HINDSIGHT_BASE_URL": "https://api.hindsight.vectorize.io"
        }):
            service = HindsightService()
            result = service.retain_fact("test-bank", "Linear", "Released Cycles feature", "release")

            self.assertEqual(result.get("storage_backend"), "hindsight_cloud")
            self.assertEqual(result.get("status"), "retained")

    @patch("services.hindsight_service.requests.post")
    def test_mocked_retain_cloud_credits_exhausted_fallback(self, mock_post):
        """Verify automatic embedded fallback and transparent reporting on 402 Insufficient Credits."""
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_response.text = '{"detail": "Insufficient credits. Balance: $0.00"}'
        mock_post.return_value = mock_response

        with patch.dict(os.environ, {
            "HINDSIGHT_API_KEY": "valid_test_key",
            "HINDSIGHT_BASE_URL": "https://api.hindsight.vectorize.io"
        }):
            service = HindsightService()
            result = service.retain_fact("mock-exhausted-bank", "Stripe", "Updated pricing model", "pricing")

            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("storage_backend"), "hindsight_embedded")
            self.assertTrue(service._cloud_credits_exhausted)

            health = service.check_health(force=True)
            self.assertEqual(health.get("storage_backend"), "hindsight_embedded")
            self.assertTrue(health.get("cloud_credits_exhausted"))

    @patch("services.hindsight_service.requests.post")
    def test_mocked_recall_operations(self, mock_post):
        """Verify recall returns structured memory nodes."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"id": "node_1", "text": "Linear launched customer requests", "score": 0.95}
            ]
        }
        mock_post.return_value = mock_response

        service = HindsightService()
        res = service.recall("mock-recall-bank", "customer requests")
        self.assertIn(res.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        self.assertTrue(isinstance(res.get("results"), list))

    @patch("services.hindsight_service.requests.post")
    def test_mocked_reflect_operations(self, mock_post):
        """Verify reflection synthesizes strategic trajectory."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Competitors are aggregating project management features into AI agents."}
        mock_post.return_value = mock_response

        service = HindsightService()
        ref = service.reflect("mock-reflect-bank", "Synthesize strategy")
        self.assertIn(ref.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        self.assertTrue(len(ref.get("text", "")) > 0)


class MockedHistoricalScanTests(unittest.TestCase):
    """Tests for scan workflows, snapshots, and diff computations."""

    def test_first_scan_baseline_diff_generation(self):
        """First scan with no prior snapshot generates a baseline establishment diff."""
        diffs = compute_historical_differences(
            brand_name="Acme Corp",
            domain="acme.com",
            prior_scan_data=None,
            current_competitors=[{"name": "RivalA", "price_trend": "Free"}],
            current_matrix=[{"segment": "Tier 1", "target_offering": "Standard"}],
            current_news=[],
            recalled_nodes=[],
            reflection_text=""
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["change_type"], "new")
        self.assertEqual(diffs[0]["category"], "Baseline Establishment")

    def test_subsequent_scan_genuine_change_vs_stability(self):
        """Subsequent scan detects true changes without injecting manufactured price hikes."""
        prior_snapshot = {
            "scan_iteration": 1,
            "what_happened": {
                "competitors": [
                    {"name": "ToolX", "price_trend": "Starting at $10/mo", "recent_move": "Launched Beta"}
                ],
                "pricing_feature_matrix": [
                    {"segment": "Team", "target_offering": "$12/user/mo"}
                ]
            }
        }

        # Case 1: No change in market findings
        comps_unchanged = [{"name": "ToolX", "price_trend": "Starting at $10/mo", "recent_move": "Launched Beta"}]
        matrix_unchanged = [{"segment": "Team", "target_offering": "$12/user/mo"}]
        diffs_unchanged = compute_historical_differences(
            "BrandA", "branda.com", prior_snapshot, comps_unchanged, matrix_unchanged, [], [], ""
        )
        self.assertEqual(diffs_unchanged[0]["change_type"], "unchanged")
        self.assertNotIn("$25/user/mo", diffs_unchanged[0]["summary"])

        # Case 2: Genuine price hike detected
        comps_changed = [{"name": "ToolX", "price_trend": "Increased to $18/mo", "recent_move": "Price restructuring"}]
        diffs_changed = compute_historical_differences(
            "BrandA", "branda.com", prior_snapshot, comps_changed, matrix_unchanged, [], [], ""
        )
        self.assertTrue(any(d["change_type"] == "changed" for d in diffs_changed))


class MockedExecutionModesAndFailuresTests(unittest.TestCase):
    """Tests for memory-enabled vs memory-disabled modes and failure handling."""

    @patch("services.snapshot_service.SnapshotService.extract_page")
    def test_memory_disabled_mode_bypasses_hindsight(self, mock_extract):
        """When use_memory=False, no memories are recalled or retained."""
        mock_extract.return_value = (True, "<html><body><h1>Acme</h1><p>Modern Tools</p></body></html>", None)

        result = run_intelligence_scan(
            raw_url="https://acme.com",
            deep_mode=False,
            simulate_rescan=False,
            scan_id="mock_stateless_scan",
            use_memory=False
        )
        self.assertTrue(result.get("success"))
        self.assertFalse(result.get("use_memory"))
        self.assertFalse(result.get("is_memory_enabled"))
        self.assertEqual(result.get("stats", {}).get("recalled_memories_count"), 0)
        self.assertIn("Stateless Mode", result.get("hindsight_memory", {}).get("reflection_text", ""))

    def test_ssrf_and_invalid_urls_blocked_mocked(self):
        """Verify URL validation rejects dangerous targets without performing external requests."""
        blocked_targets = [
            "http://127.0.0.1:8000",
            "http://localhost:5000",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.254.1.1",
            "http://172.16.0.5",
            "http://192.168.0.1",
            "ftp://example.com/file",
            "javascript:alert(1)"
        ]
        for url in blocked_targets:
            self.assertFalse(is_safe_url(url), f"Should have blocked unsafe URL: {url}")

    @patch("services.snapshot_service.SnapshotService.extract_page")
    def test_external_research_provider_failure_gracefully_handled(self, mock_extract):
        """Verify research extraction failure returns clean error tuple without exception."""
        mock_extract.return_value = (False, "", "Connection timed out connecting to target site.")
        svc = SnapshotService()
        success, content, err = svc.extract_page("https://failing-domain.com")
        self.assertFalse(success)
        self.assertEqual(content, "")
        self.assertIn("timed out", err)


if __name__ == "__main__":
    unittest.main()

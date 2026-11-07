import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

# Ensure workspace root is in path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from app import app
from services.hindsight_service import HindsightService
from services.intelligence_engine import (
    is_safe_url,
    extract_brand_display,
    is_within_last_7_days,
    filter_future_dates,
    compute_historical_differences,
    build_market_share_benchmark,
    build_pricing_trajectory,
    build_hindsight_neural_nodes,
    run_intelligence_scan
)
from services.snapshot_service import SnapshotService


class GodsEyeProductionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.hindsight = HindsightService()

    # 1. Application startup
    def test_01_application_startup(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn("God's Eye", res.text)
        self.assertIn("canvas id=\"irisMarkCanvas\"", res.text)

    # 2. Backend health
    def test_02_backend_health(self):
        res = self.client.get("/api/hindsight/status?force=true")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("healthy"))
        self.assertIn(data.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        # Transparent reporting: never misrepresent embedded as cloud
        if data.get("cloud_credits_exhausted"):
            self.assertEqual(data.get("storage_backend"), "hindsight_embedded")

    # 3. Valid company URL
    def test_03_valid_company_urls(self):
        self.assertTrue(is_safe_url("https://linear.app"))
        self.assertTrue(is_safe_url("https://stripe.com"))
        self.assertTrue(is_safe_url("https://school.bosscoderacademy.com"))
        self.assertTrue(is_safe_url("https://www.bmw.in"))

    # 4. Invalid URL & SSRF prevention
    def test_04_invalid_url_and_ssrf(self):
        unsafe_targets = [
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://169.254.169.254/latest/meta-data",
            "http://10.0.0.1",
            "http://192.168.1.1",
            "file:///etc/passwd",
            "gopher://127.0.0.1"
        ]
        for target in unsafe_targets:
            self.assertFalse(is_safe_url(target), f"Target should be blocked: {target}")
            res = self.client.post("/api/scan", json={"url": target})
            self.assertEqual(res.status_code, 400)

    # 5. Competitor discovery & brand resolution for arbitrary URLs
    def test_05_competitor_discovery_brand_resolution(self):
        self.assertEqual(extract_brand_display("school.bosscoderacademy.com"), "Bosscoder Academy")
        self.assertEqual(extract_brand_display("linear.app"), "Linear")
        self.assertEqual(extract_brand_display("posthog.com"), "PostHog")
        self.assertEqual(extract_brand_display("supabase.com"), "Supabase")
        self.assertEqual(extract_brand_display("bmw.in"), "BMW India")

    # 6. Research provider failure handling
    def test_06_research_provider_failure_handling(self):
        snap_svc = SnapshotService(tavily_api_key="invalid_mock_key")
        success, raw, err = snap_svc.extract_page("https://invalid-unreachable-test-domain-99999.xyz/nonexistent")
        # Should gracefully fail without crashing
        self.assertFalse(success)
        self.assertIsNotNone(err)

    # 7. LLM synthesis failure fallback (no fictional competitors)
    def test_07_llm_synthesis_failure_fallback(self):
        bench = build_market_share_benchmark("TestCo", "testco.com", [])
        self.assertEqual(bench["target"]["name"], "TestCo")
        self.assertTrue(len(bench["all_bars"]) >= 4)
        # Ensure no fictional 'Direct Rival A' hardcoded in dynamic builder
        bar_names = [b["name"] for b in bench["all_bars"]]
        self.assertNotIn("Direct Rival A", bar_names)

    # 8. Hindsight retention
    def test_08_hindsight_retention(self):
        test_bank = "godseye-audit-bank-test"
        now_iso = datetime.now(timezone.utc).isoformat()
        res = self.hindsight.retain_fact(
            bank_id=test_bank,
            brand_name="AuditTestCo",
            content=f"Audit verified observation at {now_iso}",
            fact_type="pricing_event"
        )
        self.assertTrue(res.get("success"))
        self.assertIn(res.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        self.assertTrue(res.get("node_id", "").startswith("node_"))

    # 9. Hindsight recall
    def test_09_hindsight_recall(self):
        test_bank = "godseye-audit-bank-test"
        res = self.hindsight.recall(test_bank, "Audit verified observation")
        self.assertIn(res.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        results = res.get("results", [])
        self.assertTrue(len(results) >= 1)
        self.assertIn("Audit verified observation", results[0]["text"])

    # 10. Hindsight reflection
    def test_10_hindsight_reflection(self):
        test_bank = "godseye-audit-bank-test"
        ref = self.hindsight.reflect(test_bank, "What observations are recorded for AuditTestCo?")
        self.assertIn(ref.get("storage_backend"), ["hindsight_cloud", "hindsight_embedded"])
        self.assertTrue(len(ref.get("text", "")) > 10)

    # 11. Memory persistence across instances
    def test_11_memory_persistence(self):
        new_svc = HindsightService()
        test_bank = "godseye-audit-bank-test"
        memories = new_svc.get_all_memories(test_bank)
        self.assertTrue(len(memories) >= 1)

    # 12. Memory-disabled execution
    def test_12_memory_disabled_execution(self):
        res = run_intelligence_scan(
            raw_url="https://linear.app",
            deep_mode=False,
            simulate_rescan=False,
            scan_id="test_scan_stateless",
            use_memory=False
        )
        self.assertTrue(res.get("success"))
        self.assertFalse(res.get("use_memory"))
        self.assertFalse(res.get("is_memory_enabled"))
        self.assertEqual(res.get("stats", {}).get("recalled_memories_count"), 0)
        self.assertIn("Stateless Mode", res.get("hindsight_memory", {}).get("reflection_text", ""))

    # 13. First scan baseline
    def test_13_first_scan_baseline(self):
        domain = "new-audit-company.com"
        prior_data = None
        diffs = compute_historical_differences(
            brand_name="NewAuditCo",
            domain=domain,
            prior_scan_data=prior_data,
            current_competitors=[],
            current_matrix=[],
            current_news=[],
            recalled_nodes=[],
            reflection_text=""
        )
        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["change_type"], "new")
        self.assertEqual(diffs[0]["category"], "Baseline Establishment")

    # 14. Subsequent scan workflow
    def test_14_subsequent_scan_workflow(self):
        domain = "linear.app"
        meta_path = os.path.join(WORKSPACE_ROOT, ".snapshots", "scans", f"{domain}.json")
        if os.path.exists(meta_path):
            with open(meta_path, "r") as f:
                import json
                data = json.load(f)
            self.assertTrue(data.get("scan_iteration", 0) >= 1)

    # 15. Genuine historical comparison (No manufactured price increases)
    def test_15_genuine_historical_comparison(self):
        prior = {
            "scan_iteration": 1,
            "what_happened": {
                "competitors": [
                    {"name": "CompetitorX", "price_trend": "Stable ($10/mo)", "recent_move": "Initial launch"}
                ],
                "pricing_feature_matrix": [
                    {"segment": "Tier 1", "target_offering": "Free"}
                ]
            }
        }
        # Scenario A: No changes between scans
        cur_comps = [{"name": "CompetitorX", "price_trend": "Stable ($10/mo)", "recent_move": "Initial launch"}]
        cur_matrix = [{"segment": "Tier 1", "target_offering": "Free"}]
        diffs_stable = compute_historical_differences("TestBrand", "test.com", prior, cur_comps, cur_matrix, [], [], "")
        self.assertEqual(diffs_stable[0]["change_type"], "unchanged")
        self.assertNotIn("$25/user/mo", diffs_stable[0]["summary"])

        # Scenario B: Genuine price change detected
        cur_comps_changed = [{"name": "CompetitorX", "price_trend": "Increased to $15/mo", "recent_move": "Price update"}]
        diffs_changed = compute_historical_differences("TestBrand", "test.com", prior, cur_comps_changed, cur_matrix, [], [], "")
        self.assertTrue(any(d["change_type"] == "changed" for d in diffs_changed))
        self.assertIn("CompetitorX Price Trajectory", [d["item"] for d in diffs_changed])

    # 16. News date filtering
    def test_16_news_date_filtering(self):
        today = datetime.now(timezone.utc).date()
        recent_date = (today - timedelta(days=2)).isoformat()
        old_date = (today - timedelta(days=30)).isoformat()
        future_date = (today + timedelta(days=10)).isoformat()

        self.assertTrue(is_within_last_7_days(recent_date, today))
        self.assertFalse(is_within_last_7_days(old_date, today))
        self.assertFalse(is_within_last_7_days(future_date, today))
        self.assertIsNone(filter_future_dates(f"Launch event in Dec {today.year + 1}", today))

    # 17. Empty research results handling
    def test_17_empty_research_results(self):
        diffs = compute_historical_differences("EmptyCo", "empty.com", None, [], [], [], [], "")
        self.assertTrue(len(diffs) > 0)
        self.assertEqual(diffs[0]["category"], "Baseline Establishment")

    # 18. Duplicate scan handling (Deduplication)
    def test_18_duplicate_scan_handling(self):
        test_bank = "godseye-audit-bank-dedup"
        self.hindsight.retain_fact(test_bank, "DedupCo", "Duplicate fact content", "note")
        self.hindsight.retain_fact(test_bank, "DedupCo", "Duplicate fact content", "note")
        all_m = self.hindsight.get_all_memories(test_bank)
        # Identical content should deduplicate to single stable node
        matching = [m for m in all_m if m["content"] == "Duplicate fact content"]
        self.assertEqual(len(matching), 1)

    # 19. Storage persistence
    def test_19_storage_persistence(self):
        scan_dir = os.path.join(WORKSPACE_ROOT, ".snapshots", "scans")
        self.assertTrue(os.path.exists(scan_dir))
        files = os.listdir(scan_dir)
        self.assertTrue(len(files) > 0)

    # 20. Secret exposure check
    def test_20_secret_exposure_checks(self):
        res = self.client.get("/api/hindsight/status")
        text = res.text
        # Ensure API keys are never exposed in JSON responses
        self.assertNotIn(os.getenv("GROQ_API_KEY", "NON_EXISTENT_GROQ"), text)
        self.assertNotIn(os.getenv("TAVILY_API_KEY", "NON_EXISTENT_TAVILY"), text)
        if os.getenv("HINDSIGHT_API_KEY"):
            self.assertNotIn(os.getenv("HINDSIGHT_API_KEY"), text)


if __name__ == "__main__":
    unittest.main()

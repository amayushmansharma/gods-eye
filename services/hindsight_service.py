import os
import json
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import requests
from dotenv import load_dotenv

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_PATH)

LOCAL_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", ".local_memory_bank.json")

class HindsightService:
    """
    Client for Hindsight memory engine.
    Supports self-hosted instances (e.g. http://localhost:8888) as well as cloud endpoints.
    """
    def __init__(self):
        base_url_env = os.getenv("HINDSIGHT_BASE_URL", "").strip()
        # Default to self-hosted localhost:8888 if unspecified or still set to cloud URL
        if not base_url_env or "api.hindsight.vectorize.io" in base_url_env:
            self.base_url = "http://localhost:8888"
        else:
            self.base_url = base_url_env.rstrip("/")

        self.api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.local_storage_path = os.path.abspath(LOCAL_STORAGE_FILE)
        self._known_banks = set()
        self._health_cache: Optional[Dict[str, Any]] = None
        self._health_cache_time: float = 0.0

    def is_configured(self) -> bool:
        return bool(self.base_url)

    def _get_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def check_health(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes a real probe retain and probe recall against Hindsight
        on a dedicated health test bank ('godseye-health-probe').
        Cached for 60 seconds to avoid blocking page load.
        """
        now = time.time()
        if not force and self._health_cache and (now - self._health_cache_time < 60.0):
            cached = dict(self._health_cache)
            cached["cached"] = True
            cached["cache_age_seconds"] = int(now - self._health_cache_time)
            return cached

        if not self.is_configured():
            res = {
                "healthy": False,
                "status": "unconfigured",
                "retain_passed": False,
                "recall_passed": False,
                "error": "Hindsight base URL not configured",
                "latency_ms": 0,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = now
            return res

        t0 = time.time()
        test_bank = "godseye-health-probe"
        now_iso = datetime.now(timezone.utc).isoformat()

        # 1. Ensure test bank exists
        bank_ok, bank_err = self.ensure_bank_exists(test_bank, "Health Probe Bank")
        if not bank_ok:
            latency_ms = int((time.time() - t0) * 1000)
            res = {
                "healthy": False,
                "status": "failed",
                "retain_passed": False,
                "recall_passed": False,
                "error": f"Failed to reach Hindsight at {self.base_url}: {bank_err}",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res

        # 2. Real Retain probe
        try:
            probe_item = {
                "content": f"Health check probe verified at {now_iso}.",
                "timestamp": now_iso,
                "metadata": {"type": "health_probe", "probe_time": str(now_iso)}
            }
            res_retain = requests.post(
                f"{self.base_url}/v1/default/banks/{test_bank}/memories",
                headers=self._get_headers(),
                json={"items": [probe_item]},
                timeout=6
            )
            if res_retain.status_code not in [200, 201, 202]:
                latency_ms = int((time.time() - t0) * 1000)
                err_text = res_retain.text[:200]
                res = {
                    "healthy": False,
                    "status": "failed",
                    "retain_passed": False,
                    "recall_passed": False,
                    "error": f"Retain failed (HTTP {res_retain.status_code}): {err_text}",
                    "latency_ms": latency_ms,
                    "base_url": self.base_url,
                    "provider": "Hindsight"
                }
                self._health_cache = res
                self._health_cache_time = time.time()
                return res
        except requests.exceptions.ConnectionError:
            latency_ms = int((time.time() - t0) * 1000)
            res = {
                "healthy": False,
                "status": "failed",
                "retain_passed": False,
                "recall_passed": False,
                "error": f"Connection refused at {self.base_url}",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            res = {
                "healthy": False,
                "status": "failed",
                "retain_passed": False,
                "recall_passed": False,
                "error": f"Retain error: {str(e)}",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res

        # 3. Real Recall probe
        try:
            res_recall = requests.post(
                f"{self.base_url}/v1/default/banks/{test_bank}/memories/recall",
                headers=self._get_headers(),
                json={"query": "Health check probe verified"},
                timeout=6
            )
            latency_ms = int((time.time() - t0) * 1000)
            if res_recall.status_code != 200:
                err_text = res_recall.text[:200]
                res = {
                    "healthy": False,
                    "status": "failed",
                    "retain_passed": True,
                    "recall_passed": False,
                    "error": f"Recall failed (HTTP {res_recall.status_code}): {err_text}",
                    "latency_ms": latency_ms,
                    "base_url": self.base_url,
                    "provider": "Hindsight"
                }
                self._health_cache = res
                self._health_cache_time = time.time()
                return res

            recalled_results = res_recall.json().get("results", [])
            recalled_id = recalled_results[0].get("id") if recalled_results else "node_created"

            res = {
                "healthy": True,
                "status": "passed",
                "retain_passed": True,
                "recall_passed": True,
                "latency_ms": latency_ms,
                "probe_bank": test_bank,
                "recalled_node_id": recalled_id,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res
        except requests.exceptions.ConnectionError:
            latency_ms = int((time.time() - t0) * 1000)
            res = {
                "healthy": False,
                "status": "failed",
                "retain_passed": True,
                "recall_passed": False,
                "error": f"Recall connection refused at {self.base_url}",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res
        except Exception as e:
            latency_ms = int((time.time() - t0) * 1000)
            res = {
                "healthy": False,
                "status": "failed",
                "retain_passed": True,
                "recall_passed": False,
                "error": f"Recall error: {str(e)}",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "provider": "Hindsight"
            }
            self._health_cache = res
            self._health_cache_time = time.time()
            return res

    def ensure_bank_exists(self, bank_id: str, bank_name: str) -> Tuple[bool, str]:
        """
        Ensures the bank exists in Hindsight. Cached in-memory to avoid redundant PUT calls.
        """
        if bank_id in self._known_banks:
            return True, ""

        if not self.is_configured():
            return False, "Base URL not configured"

        try:
            res = requests.put(
                f"{self.base_url}/v1/default/banks/{bank_id}",
                headers=self._get_headers(),
                json={"name": bank_name},
                timeout=6
            )
            if res.status_code in [200, 201]:
                self._known_banks.add(bank_id)
                return True, ""
            return False, f"HTTP {res.status_code}: {res.text[:150]}"
        except requests.exceptions.ConnectionError:
            return False, f"Connection refused at {self.base_url}"
        except Exception as e:
            return False, str(e)

    def retain_rich_articles(self, bank_id: str, articles: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """
        Retains rich, real article contents into Hindsight.
        Anchors each article's timestamp to its real published_date from Tavily.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        items = []

        for art in articles:
            snippet = art.get("content", "").strip()
            title = art.get("title", "").strip()
            source = art.get("source", "Web Source")
            url = art.get("url", "")
            raw_pub_date = art.get("published_date")

            # Parse real publication date if available
            article_timestamp = now_iso
            if raw_pub_date:
                try:
                    dt = parsedate_to_datetime(raw_pub_date)
                    article_timestamp = dt.isoformat()
                except Exception:
                    article_timestamp = now_iso

            body = f"Article: {title}\nSource: {source}\nContent: {snippet}"
            items.append({
                "content": body,
                "timestamp": article_timestamp,
                "metadata": {
                    "source": str(source),
                    "url": str(url),
                    "brand": str(brand_name),
                    "type": "market_signal"
                }
            })

        if self.is_configured() and items:
            try:
                bank_ok, bank_err = self.ensure_bank_exists(bank_id, f"Gods Eye {brand_name}")
                if not bank_ok:
                    return {"success": False, "error": bank_err, "storage_backend": "error"}
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json={"items": items},
                    timeout=15
                )
                if res.status_code in [200, 201, 202]:
                    data = res.json()
                    data["storage_backend"] = "hindsight"
                    return data
                else:
                    err_msg = f"HTTP {res.status_code}: {res.text[:150]}"
                    print(f"[Hindsight Retain Error] {err_msg}")
                    return {"success": False, "error": err_msg, "storage_backend": "error"}
            except requests.exceptions.ConnectionError:
                err_msg = f"Connection refused at {self.base_url}"
                print(f"[Hindsight Retain Error] {err_msg}")
                return {"success": False, "error": err_msg, "storage_backend": "error"}
            except Exception as e:
                err_msg = str(e)
                print(f"[Hindsight Retain Failed] {err_msg}")
                return {"success": False, "error": err_msg, "storage_backend": "error"}

        return {"success": False, "error": "No items to retain or base URL not configured", "storage_backend": "error"}

    def retain_page_diff(self, bank_id: str, competitor: str, page_type: str, url: str, diff_text: str, timestamp_iso: str, status: str, lines_changed: int) -> Dict[str, Any]:
        """
        Retains a verified page diff directly into Hindsight.
        """
        body = (
            f"Competitor Move Detected: {competitor} ({page_type})\n"
            f"URL: {url}\n"
            f"Status: {status}\n"
            f"Lines Changed: {lines_changed}\n"
            f"Detected At: {timestamp_iso}\n\n"
            f"Diff Content:\n{diff_text}"
        )
        item = {
            "content": body,
            "timestamp": timestamp_iso,
            "metadata": {
                "competitor": str(competitor),
                "page_type": str(page_type),
                "url": str(url),
                "status": str(status),
                "lines_changed": str(lines_changed),
                "type": "page_diff_event"
            }
        }
        if self.is_configured():
            try:
                bank_ok, bank_err = self.ensure_bank_exists(bank_id, f"Gods Eye {competitor}")
                if not bank_ok:
                    return {"success": False, "error": bank_err, "storage_backend": "error"}
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json={"items": [item]},
                    timeout=15
                )
                if res.status_code in [200, 201, 202]:
                    data = res.json()
                    data["storage_backend"] = "hindsight"
                    return data
                else:
                    err_msg = f"HTTP {res.status_code}: {res.text[:150]}"
                    print(f"[Hindsight Retain Diff Error] {err_msg}")
                    return {"success": False, "error": err_msg, "storage_backend": "error"}
            except requests.exceptions.ConnectionError:
                err_msg = f"Connection refused at {self.base_url}"
                print(f"[Hindsight Retain Diff Error] {err_msg}")
                return {"success": False, "error": err_msg, "storage_backend": "error"}
            except Exception as e:
                err_msg = str(e)
                print(f"[Hindsight Retain Diff Failed] {err_msg}")
                return {"success": False, "error": err_msg, "storage_backend": "error"}

        return {"success": False, "error": "Hindsight base URL not configured", "storage_backend": "error"}

    def recall(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Recall memories from Hindsight via multi-strategy search.
        """
        if self.is_configured():
            try:
                bank_ok, bank_err = self.ensure_bank_exists(bank_id, f"Gods Eye {bank_id}")
                if not bank_ok:
                    return {
                        "results": [],
                        "error": bank_err,
                        "storage_backend": "error"
                    }
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories/recall",
                    headers=self._get_headers(),
                    json={"query": query},
                    timeout=10
                )
                if res.status_code == 200:
                    raw_results = res.json().get("results", [])
                    cleaned = []
                    for item in raw_results:
                        ts = item.get("mentioned_at") or item.get("occurred_start") or item.get("timestamp") or "Recorded"
                        cleaned.append({
                            "id": item.get("id", "hindsight-node"),
                            "text": item.get("text", ""),
                            "timestamp": ts,
                            "entities": item.get("entities", []),
                            "scores": item.get("scores", {}),
                            "storage_backend": "hindsight"
                        })
                    return {"results": cleaned, "storage_backend": "hindsight"}
                else:
                    err_msg = f"HTTP {res.status_code}: {res.text[:120]}"
                    print(f"[Hindsight Recall Error] {err_msg}")
                    return {"results": [], "error": err_msg, "storage_backend": "error"}
            except requests.exceptions.ConnectionError:
                err_msg = f"Connection refused at {self.base_url}"
                print(f"[Hindsight Recall Error] {err_msg}")
                return {"results": [], "error": err_msg, "storage_backend": "error"}
            except Exception as e:
                err_msg = str(e)
                print(f"[Hindsight Recall Failed] {err_msg}")
                return {"results": [], "error": err_msg, "storage_backend": "error"}

        return {"results": [], "error": "Hindsight base URL not configured", "storage_backend": "error"}

    def reflect(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Reflect across world facts and observations using Hindsight's native reflect endpoint.
        """
        if self.is_configured():
            try:
                bank_ok, bank_err = self.ensure_bank_exists(bank_id, f"Gods Eye {bank_id}")
                if not bank_ok:
                    return {
                        "text": "",
                        "error": bank_err,
                        "storage_backend": "error"
                    }
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/reflect",
                    headers=self._get_headers(),
                    json={"query": query},
                    timeout=20
                )
                if res.status_code == 200:
                    data = res.json()
                    return {
                        "text": data.get("text", ""),
                        "based_on": data.get("based_on", []),
                        "storage_backend": "hindsight"
                    }
                else:
                    err_msg = f"HTTP {res.status_code}: {res.text[:120]}"
                    print(f"[Hindsight Reflect Error] {err_msg}")
                    return {"text": "", "error": err_msg, "storage_backend": "error"}
            except requests.exceptions.ConnectionError:
                err_msg = f"Connection refused at {self.base_url}"
                print(f"[Hindsight Reflect Error] {err_msg}")
                return {"text": "", "error": err_msg, "storage_backend": "error"}
            except Exception as e:
                err_msg = str(e)
                print(f"[Hindsight Reflect Failed] {err_msg}")
                return {"text": "", "error": err_msg, "storage_backend": "error"}

        return {"text": "", "error": "Hindsight base URL not configured", "storage_backend": "error"}

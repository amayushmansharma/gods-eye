import os
import json
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

LOCAL_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", ".local_memory_bank.json")

class HindsightService:
    """
    Client for Vectorize Hindsight memory engine.
    Connects to Hindsight Cloud (https://api.hindsight.vectorize.io).
    """
    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        self.local_storage_path = os.path.abspath(LOCAL_STORAGE_FILE)
        self._known_banks = set()

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("hsk_"))

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def check_health(self) -> Dict[str, Any]:
        """
        True live health check hitting Hindsight Cloud API /health/ready.
        """
        if not self.is_configured():
            return {"status": "unconfigured", "message": "Missing HINDSIGHT_API_KEY"}
        
        t0 = time.time()
        try:
            res = requests.get(f"{self.base_url}/health/ready", timeout=5)
            latency_ms = int((time.time() - t0) * 1000)
            if res.status_code == 200:
                data = res.json()
                return {
                    "status": "connected",
                    "cloud_healthy": data.get("status") == "healthy",
                    "latency_ms": latency_ms,
                    "provider": "Vectorize Hindsight Cloud"
                }
            return {"status": "error", "code": res.status_code, "latency_ms": latency_ms}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def ensure_bank_exists(self, bank_id: str, bank_name: str) -> bool:
        """
        Ensures the bank exists in Hindsight Cloud. Cached in-memory to avoid redundant PUT calls.
        """
        if bank_id in self._known_banks:
            return True

        if not self.is_configured():
            return False

        try:
            res = requests.put(
                f"{self.base_url}/v1/default/banks/{bank_id}",
                headers=self._get_headers(),
                json={"name": bank_name},
                timeout=8
            )
            if res.status_code in [200, 201]:
                self._known_banks.add(bank_id)
                return True
        except Exception as e:
            print(f"[Hindsight Bank Create Error] {e}")
        return False

    def retain_rich_articles(self, bank_id: str, articles: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """
        Retains rich, real article contents into Hindsight Cloud.
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
                self.ensure_bank_exists(bank_id, f"Gods Eye {brand_name}")
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json={"items": items},
                    timeout=15
                )
                if res.status_code in [200, 201, 202]:
                    data = res.json()
                    data["storage_backend"] = "hindsight_cloud"
                    return data
                else:
                    print(f"[Hindsight Retain Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Retain Failed] {e}")

        # Local fallback
        for it in items:
            entry = {
                "id": f"local-{int(time.time()*1000)}",
                "text": it["content"],
                "timestamp": it["timestamp"],
                "metadata": it["metadata"],
                "storage_backend": "local_disk_fallback"
            }
            self._save_local_bank(bank_id, entry)

        return {"success": True, "bank_id": bank_id, "items_count": len(items), "storage_backend": "local_disk_fallback"}

    def recall(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Recall memories from Hindsight Cloud via multi-strategy search.
        """
        if self.is_configured():
            try:
                self.ensure_bank_exists(bank_id, f"Gods Eye {bank_id}")
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories/recall",
                    headers=self._get_headers(),
                    json={"query": query},
                    timeout=12
                )
                if res.status_code == 200:
                    raw_results = res.json().get("results", [])
                    cleaned = []
                    for item in raw_results:
                        ts = item.get("mentioned_at") or item.get("occurred_start") or item.get("timestamp") or "Recorded"
                        cleaned.append({
                            "id": item.get("id", "cloud-node"),
                            "text": item.get("text", ""),
                            "timestamp": ts,
                            "entities": item.get("entities", []),
                            "scores": item.get("scores", {}),
                            "storage_backend": "hindsight_cloud"
                        })
                    return {"results": cleaned, "storage_backend": "hindsight_cloud"}
                else:
                    print(f"[Hindsight Recall Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Recall Failed] {e}")

        local_items = self._load_local_bank(bank_id)
        return {"results": local_items, "storage_backend": "local_disk_fallback"}

    def reflect(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Reflect across world facts and observations using Hindsight's native reflect endpoint.
        """
        if self.is_configured():
            try:
                self.ensure_bank_exists(bank_id, f"Gods Eye {bank_id}")
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
                        "storage_backend": "hindsight_cloud"
                    }
                else:
                    print(f"[Hindsight Reflect Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Reflect Failed] {e}")

        # Local fallback reflection
        recall_res = self.recall(bank_id, query)
        recalled = recall_res.get("results", [])
        if not recalled:
            return {
                "text": "Baseline market scan committed. Trajectory will emerge across subsequent rescans.",
                "based_on": [],
                "storage_backend": "local_disk_fallback"
            }
        summary_points = [f"• {m.get('text', '')}" for m in recalled[:3]]
        return {
            "text": "Local fallback memory review:\n" + "\n".join(summary_points),
            "based_on": recalled,
            "storage_backend": "local_disk_fallback"
        }

    def _load_local_bank(self, bank_id: str) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(self.local_storage_path):
                with open(self.local_storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get(bank_id, [])
        except Exception:
            pass
        return []

    def _save_local_bank(self, bank_id: str, entry: Dict[str, Any]):
        try:
            data = {}
            if os.path.exists(self.local_storage_path):
                with open(self.local_storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            if bank_id not in data:
                data[bank_id] = []
            data[bank_id].append(entry)
            with open(self.local_storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Hindsight Local] Save error: {e}")

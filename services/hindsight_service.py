import os
import json
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

LOCAL_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "..", ".local_memory_bank.json")

class HindsightService:
    """
    Client for Vectorize Hindsight memory engine.
    Connects to Hindsight Cloud (https://api.hindsight.vectorize.io).
    Fully implements bank lifecycle, retain, recall, and reflect.
    Falls back gracefully to disk persistence with transparent status reporting.
    """
    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        self.local_storage_path = os.path.abspath(LOCAL_STORAGE_FILE)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("hsk_"))

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def ensure_bank_exists(self, bank_id: str, bank_name: str) -> bool:
        """
        Ensures the bank exists in Hindsight Cloud using PUT /v1/default/banks/{bank_id}.
        """
        if not self.is_configured():
            return False
        try:
            res = requests.put(
                f"{self.base_url}/v1/default/banks/{bank_id}",
                headers=self._get_headers(),
                json={"name": bank_name},
                timeout=8
            )
            return res.status_code in [200, 201]
        except Exception as e:
            print(f"[Hindsight Bank Create] {e}")
            return False

    def has_existing_memories(self, bank_id: str) -> bool:
        """
        Queries /memories/list to prevent duplicate seeding.
        """
        if not self.is_configured():
            return len(self._load_local_bank(bank_id)) > 0
        try:
            res = requests.get(
                f"{self.base_url}/v1/default/banks/{bank_id}/memories/list",
                headers=self._get_headers(),
                timeout=8
            )
            if res.status_code == 200:
                items = res.json().get("items", [])
                return len(items) > 0
        except Exception as e:
            print(f"[Hindsight List] {e}")
        return False

    def retain(self, bank_id: str, content: str, timestamp_iso: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retain memory in Vectorize Hindsight Cloud.
        """
        ts = timestamp_iso or datetime.now(timezone.utc).isoformat()
        clean_metadata = {str(k): str(v) for k, v in (metadata or {}).items()}

        if self.is_configured():
            try:
                self.ensure_bank_exists(bank_id, f"Gods Eye {bank_id}")
                payload = {
                    "items": [
                        {
                            "content": content,
                            "timestamp": ts,
                            "metadata": clean_metadata
                        }
                    ]
                }
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json=payload,
                    timeout=12
                )
                if res.status_code in [200, 201, 202]:
                    data = res.json()
                    data["storage_backend"] = "hindsight_cloud"
                    return data
                else:
                    print(f"[Hindsight Retain Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Warning] API retain failed: {e}. Falling back to disk.")

        # Local disk fallback
        entry = {
            "id": f"local-{int(time.time()*1000)}",
            "text": content,
            "timestamp": ts,
            "metadata": clean_metadata,
            "storage_backend": "local_disk_fallback"
        }
        self._save_local_bank(bank_id, entry)
        return {"success": True, "bank_id": bank_id, "items_count": 1, "storage_backend": "local_disk_fallback"}

    def recall(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Recall memories from Hindsight Cloud via multi-strategy search.
        Extracts proper timestamp, entities, and scores.
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
                        ts = item.get("mentioned_at") or item.get("occurred_start") or item.get("timestamp") or "Timestamp recorded"
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
                print(f"[Hindsight Warning] Recall failed: {e}. Checking disk.")

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
                print(f"[Hindsight Warning] Reflect API call failed: {e}")

        # Local fallback reflection
        recall_res = self.recall(bank_id, query)
        recalled = recall_res.get("results", [])
        if not recalled:
            return {
                "text": "Initial scan complete. Baseline market memory recorded.",
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

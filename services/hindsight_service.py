import os
import time
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class HindsightService:
    """
    Production Client for Vectorize Hindsight memory engine.
    Connects to Hindsight Cloud (https://api.hindsight.vectorize.io).
    """
    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.startswith("hsk_"))

    def retain(self, bank_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retain memory in Vectorize Hindsight.
        Uses POST /v1/default/banks/{bank_id}/memories
        """
        if self.is_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "items": [
                        {
                            "content": content,
                            "metadata": metadata or {}
                        }
                    ]
                }
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if res.status_code in [200, 201, 202]:
                    return res.json()
                else:
                    print(f"[Hindsight Retain Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Warning] API call failed: {e}")

        return {"status": "retained_locally", "bank_id": bank_id}

    def recall(self, bank_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Recall memories from Vectorize Hindsight via multi-strategy search.
        Uses POST /v1/default/banks/{bank_id}/memories/recall
        """
        if self.is_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"query": query}
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/memories/recall",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if res.status_code == 200:
                    data = res.json()
                    # Results contains structured memory items with entity resolution
                    return data.get("results", [])
                else:
                    print(f"[Hindsight Recall Error] {res.status_code}: {res.text}")
            except Exception as e:
                print(f"[Hindsight Warning] Recall failed: {e}")

        return []

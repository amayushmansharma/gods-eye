import os
import time
import asyncio
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

load_dotenv()

class HindsightService:
    """
    Client for Vectorize Hindsight memory engine.
    Supports Hindsight Cloud (https://ui.hindsight.vectorize.io) 
    or local self-hosted Hindsight API instances.
    Includes persistent local fallback for demoing before API keys are plugged in.
    """
    def __init__(self):
        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "")
        # In-memory bank for fallback demo state
        self.local_memory_bank: Dict[str, List[Dict[str, Any]]] = {}

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key != "your_api_key_here")

    def retain(self, bank_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Store facts/insights in Hindsight memory bank.
        """
        if self.is_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "content": content,
                    "metadata": metadata or {}
                }
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/retain",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if res.status_code in [200, 201, 202]:
                    return res.json()
            except Exception as e:
                print(f"[Hindsight Warning] API call failed: {e}. Falling back to internal bank.")

        # Local fallback retention
        if bank_id not in self.local_memory_bank:
            self.local_memory_bank[bank_id] = []
        entry = {
            "timestamp": time.time(),
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "content": content,
            "metadata": metadata or {}
        }
        self.local_memory_bank[bank_id].append(entry)
        return {"status": "retained_locally", "entry": entry}

    def recall(self, bank_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant historical memories from Hindsight.
        """
        if self.is_configured():
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                payload = {"query": query}
                res = requests.post(
                    f"{self.base_url}/v1/default/banks/{bank_id}/recall",
                    json=payload,
                    headers=headers,
                    timeout=10
                )
                if res.status_code == 200:
                    return res.json().get("results", [])
            except Exception as e:
                print(f"[Hindsight Warning] API recall failed: {e}. Using local bank.")

        # Local fallback recall
        return self.local_memory_bank.get(bank_id, [])

    def reflect(self, bank_id: str, query: str) -> str:
        """
        Synthesize cross-temporal insights across the memory bank.
        """
        memories = self.recall(bank_id, query)
        if not memories:
            return "No previous historical scans found. This baseline scan has been committed to long-term memory."
        
        # Format memory consolidation
        lines = [f"• [{m.get('date', 'Previous Scan')}]: {m.get('content', '')}" for m in memories[-5:]]
        return "\n".join(lines)

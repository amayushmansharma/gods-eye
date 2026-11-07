import os
import re
import json
import time
import sqlite3
import hashlib
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import requests
from groq import Groq
from dotenv import load_dotenv

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(ENV_PATH)

SNAPSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".snapshots"))
DB_PATH = os.path.join(SNAPSHOTS_DIR, "hindsight_embedded.db")


class HindsightService:
    """
    Client and Embedded Engine for Vectorize Hindsight memory.
    Supports:
    1. Cloud Hindsight (https://api.hindsight.vectorize.io) with valid API key.
    2. Graceful seamless fallback to Embedded Hindsight Engine (SQLite + Groq Reflection)
       when Cloud balance has 0 credits (HTTP 402) or is unreachable.
    3. Temporal retention, multi-strategy recall, cross-scan reflect, and raw bank inspection.
    """
    def __init__(self):
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
        self.db_path = DB_PATH
        self._init_sqlite_db()

        self.base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io").strip()
        self.api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key else None

        self._known_banks = set()
        self._cloud_credits_exhausted = False
        if self.api_key and self.base_url and not self.base_url.startswith("embedded"):
            try:
                r_probe = requests.post(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/probe/memories/recall",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"query": "ping"},
                    timeout=2.0
                )
                if r_probe.status_code == 402:
                    self._cloud_credits_exhausted = True
            except Exception:
                pass

        self._health_cache: Optional[Dict[str, Any]] = None
        self._health_cache_time: float = 0.0

    def _init_sqlite_db(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("""
                CREATE TABLE IF NOT EXISTS banks (
                    bank_id TEXT PRIMARY KEY,
                    name TEXT,
                    created_at REAL
                )
                """)
                cur.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    bank_id TEXT,
                    content TEXT,
                    timestamp TEXT,
                    metadata_json TEXT,
                    created_at REAL
                )
                """)
                cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_bank ON memories(bank_id)
                """)
                conn.commit()
        except Exception as e:
            print(f"[Hindsight Embedded DB Init Error] {e}")

    def is_configured(self) -> bool:
        return True

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _can_use_cloud(self) -> bool:
        if self._cloud_credits_exhausted:
            return False
        if not self.base_url or not self.api_key or self.base_url.startswith("embedded"):
            return False
        return True

    def check_health(self, force: bool = False) -> Dict[str, Any]:
        """
        Health probe hitting Vectorize Cloud API or Embedded Engine.
        """
        now = time.time()
        if not force and self._health_cache and (now - self._health_cache_time < 30.0):
            cached = dict(self._health_cache)
            cached["cached"] = True
            cached["cache_age_seconds"] = int(now - self._health_cache_time)
            return cached

        t0 = time.time()
        test_bank = "godseye-health-probe"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Try cloud probe if configured (enables automatic recovery when credits are restored)
        if self.base_url and self.api_key and not self.base_url.startswith("embedded"):
            try:
                r_ping = requests.get(f"{self.base_url.rstrip('/')}/v1/default/banks", headers=self._get_headers(), timeout=3)
                if r_ping.status_code == 200:
                    probe_item = {
                        "content": f"Health probe verified at {now_iso}.",
                        "timestamp": now_iso,
                        "metadata": {"type": "health_probe"}
                    }
                    res_ret = requests.post(
                        f"{self.base_url.rstrip('/')}/v1/default/banks/{test_bank}/memories",
                        headers=self._get_headers(),
                        json={"items": [probe_item]},
                        timeout=4
                    )
                    if res_ret.status_code in [200, 201, 202]:
                        self._cloud_credits_exhausted = False
                        lat = int((time.time() - t0) * 1000)
                        result = {
                            "healthy": True,
                            "status": "passed",
                            "mode": "Cloud",
                            "provider": "Vectorize Hindsight (Cloud)",
                            "latency_ms": lat,
                            "probe_bank": test_bank,
                            "base_url": self.base_url,
                            "storage_backend": "hindsight_cloud"
                        }
                        self._health_cache = result
                        self._health_cache_time = time.time()
                        return result
                    elif res_ret.status_code == 402:
                        self._cloud_credits_exhausted = True
            except Exception:
                pass

        # Embedded Hindsight Engine health probe (SQLite)
        try:
            probe_id = f"probe_{int(time.time()*1000)}"
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?)",
                    (probe_id, test_bank, f"Health probe verified at {now_iso}.", now_iso, '{"type": "health_probe"}', time.time())
                )
                cur.execute("SELECT id FROM memories WHERE id = ?", (probe_id,))
                row = cur.fetchone()
                cur.execute("DELETE FROM memories WHERE id = ?", (probe_id,))
                conn.commit()

            lat = int((time.time() - t0) * 1000)
            result = {
                "healthy": True,
                "status": "passed",
                "ok": True,
                "mode": "Embedded Fallback",
                "provider": "Vectorize Hindsight (Embedded SQLite + Groq)",
                "latency_ms": max(lat, 2),
                "probe_bank": test_bank,
                "base_url": "embedded://sqlite",
                "storage_backend": "hindsight_embedded",
                "cloud_credits_exhausted": self._cloud_credits_exhausted
            }
            self._health_cache = result
            self._health_cache_time = time.time()
            return result
        except Exception as e:
            return {
                "healthy": False,
                "status": "failed",
                "error": str(e),
                "provider": "Vectorize Hindsight",
                "storage_backend": "error"
            }

    def ensure_bank_exists(self, bank_id: str, bank_name: str) -> Tuple[bool, str]:
        if bank_id in self._known_banks:
            return True, ""

        if self._can_use_cloud():
            try:
                res = requests.put(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/{bank_id}",
                    headers=self._get_headers(),
                    json={"name": bank_name},
                    timeout=4
                )
                if res.status_code in [200, 201]:
                    self._known_banks.add(bank_id)
            except Exception:
                pass

        # Always ensure in embedded DB
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR IGNORE INTO banks VALUES (?, ?, ?)",
                    (bank_id, bank_name, time.time())
                )
                conn.commit()
            self._known_banks.add(bank_id)
            return True, ""
        except Exception as e:
            return False, str(e)

    def retain_fact(self, bank_id: str, brand_name: str, content: str, fact_type: str, url: str = "", metadata: Optional[Dict[str, Any]] = None, timestamp_iso: Optional[str] = None) -> Dict[str, Any]:
        """
        Retains an individual verified intelligence observation into Hindsight memory.
        """
        self.ensure_bank_exists(bank_id, f"Gods Eye {brand_name}")
        ts = timestamp_iso or datetime.now(timezone.utc).isoformat()
        meta = metadata or {}
        meta.update({
            "brand": str(brand_name),
            "fact_type": str(fact_type),
            "url": str(url)
        })

        if self._can_use_cloud():
            try:
                item = {"content": content, "timestamp": ts, "metadata": meta}
                res = requests.post(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json={"items": [item]},
                    timeout=5
                )
                if res.status_code in [200, 201, 202]:
                    d = res.json()
                    d["storage_backend"] = "hindsight_cloud"
                    return d
                elif res.status_code == 402:
                    self._cloud_credits_exhausted = True
            except Exception:
                pass

        # Retain into embedded SQLite
        try:
            seed_str = f"{bank_id}_{content.strip()}"
            node_id = f"node_{hashlib.sha256(seed_str.encode()).hexdigest()[:16]}"
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?)",
                    (node_id, bank_id, content, ts, json.dumps(meta), time.time())
                )
                conn.commit()
            return {
                "success": True,
                "node_id": node_id,
                "bank_id": bank_id,
                "items_count": 1,
                "storage_backend": "hindsight_embedded"
            }
        except Exception as e:
            return {"success": False, "error": str(e), "storage_backend": "error"}

    def retain_rich_articles(self, bank_id: str, articles: List[Dict[str, Any]], brand_name: str) -> Dict[str, Any]:
        """
        Retains verified news/market articles into Hindsight memory with real publication dates.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        items = []

        for art in articles:
            snippet = art.get("content", "").strip()
            title = art.get("title", "").strip()
            source = art.get("source", "Web Source")
            url = art.get("url", "")
            raw_pub_date = art.get("published_date")

            article_timestamp = now_iso
            if raw_pub_date:
                try:
                    dt = parsedate_to_datetime(raw_pub_date)
                    article_timestamp = dt.isoformat()
                except Exception:
                    article_timestamp = now_iso

            body = f"Article: {title}\nSource: {source}\nPublished: {article_timestamp}\nURL: {url}\nContent: {snippet}"
            metadata = {
                "source": str(source),
                "url": str(url),
                "brand": str(brand_name),
                "title": str(title),
                "type": "market_news_signal"
            }
            items.append({"body": body, "timestamp": article_timestamp, "metadata": metadata})

        if not items:
            return {"success": True, "bank_id": bank_id, "items_count": 0}

        self.ensure_bank_exists(bank_id, f"Gods Eye {brand_name}")

        if self._can_use_cloud():
            try:
                payload_items = [{"content": it["body"], "timestamp": it["timestamp"], "metadata": it["metadata"]} for it in items]
                res = requests.post(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/{bank_id}/memories",
                    headers=self._get_headers(),
                    json={"items": payload_items},
                    timeout=8
                )
                if res.status_code in [200, 201, 202]:
                    d = res.json()
                    d["storage_backend"] = "hindsight_cloud"
                    return d
                elif res.status_code == 402:
                    self._cloud_credits_exhausted = True
            except Exception:
                pass

        # Retain into embedded engine
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                for it in items:
                    it_url = it.get("metadata", {}).get("url", "")
                    it_title = it.get("metadata", {}).get("title", "")
                    seed_str = f"{bank_id}_{it_url}_{it_title}"
                    node_id = f"node_{hashlib.sha256(seed_str.encode()).hexdigest()[:16]}"
                    cur.execute(
                        "INSERT OR REPLACE INTO memories VALUES (?, ?, ?, ?, ?, ?)",
                        (node_id, bank_id, it["body"], it["timestamp"], json.dumps(it["metadata"]), time.time())
                    )
                conn.commit()
            return {"success": True, "bank_id": bank_id, "items_count": len(items), "storage_backend": "hindsight_embedded"}
        except Exception as e:
            return {"success": False, "error": str(e), "storage_backend": "error"}

    def retain_page_diff(self, bank_id: str, competitor: str, page_type: str, url: str, diff_text: str, timestamp_iso: str, status: str, lines_changed: int) -> Dict[str, Any]:
        """
        Retains a verified page diff directly into Hindsight memory.
        """
        body = (
            f"Competitor Move Detected: {competitor} ({page_type})\n"
            f"URL: {url}\n"
            f"Status: {status}\n"
            f"Lines Changed: {lines_changed}\n"
            f"Detected At: {timestamp_iso}\n\n"
            f"Diff Content:\n{diff_text}"
        )
        metadata = {
            "competitor": str(competitor),
            "page_type": str(page_type),
            "url": str(url),
            "status": str(status),
            "lines_changed": str(lines_changed),
            "type": "page_diff_event"
        }
        return self.retain_fact(
            bank_id=bank_id,
            brand_name=competitor,
            content=body,
            fact_type="page_diff_event",
            url=url,
            metadata=metadata,
            timestamp_iso=timestamp_iso
        )

    def recall(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Recalls memory nodes using multi-strategy keyword + temporal scoring.
        """
        if self._can_use_cloud():
            try:
                res = requests.post(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/{bank_id}/memories/recall",
                    headers=self._get_headers(),
                    json={"query": query},
                    timeout=5
                )
                if res.status_code == 200:
                    raw_results = res.json().get("results", [])
                    cleaned = []
                    for item in raw_results:
                        ts = item.get("mentioned_at") or item.get("occurred_start") or item.get("timestamp") or "Recorded"
                        cleaned.append({
                            "id": item.get("id", "node"),
                            "text": item.get("text", ""),
                            "timestamp": ts,
                            "metadata": item.get("metadata", {}),
                            "storage_backend": "hindsight_cloud"
                        })
                    return {"results": cleaned, "storage_backend": "hindsight_cloud"}
                elif res.status_code == 402:
                    self._cloud_credits_exhausted = True
            except Exception:
                pass

        # Embedded engine recall
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, content, timestamp, metadata_json, created_at FROM memories WHERE bank_id = ? ORDER BY created_at DESC",
                    (bank_id,)
                )
                rows = cur.fetchall()

            if not rows:
                return {"results": [], "storage_backend": "hindsight_embedded"}

            keywords = [w.lower() for w in re.findall(r"\w+", query) if len(w) > 2]
            scored_nodes = []

            for row in rows:
                nid, content, ts, meta_raw, created_at = row
                content_lower = content.lower()
                meta_lower = (meta_raw or "").lower()

                score = 0.0
                for kw in keywords:
                    if kw in content_lower:
                        score += 2.0
                    if kw in meta_lower:
                        score += 1.0

                # Recency bonus
                hours_ago = (time.time() - created_at) / 3600.0
                if hours_ago < 24:
                    score += 1.0

                try:
                    meta_obj = json.loads(meta_raw) if meta_raw else {}
                except Exception:
                    meta_obj = {}

                scored_nodes.append({
                    "id": nid,
                    "text": content,
                    "timestamp": ts,
                    "score": score,
                    "metadata": meta_obj,
                    "storage_backend": "hindsight_embedded"
                })

            scored_nodes.sort(key=lambda x: (x["score"], x["timestamp"]), reverse=True)
            top_nodes = scored_nodes[:8]

            return {
                "results": top_nodes,
                "total_memories": len(rows),
                "storage_backend": "hindsight_embedded"
            }
        except Exception as e:
            return {"results": [], "error": str(e), "storage_backend": "error"}

    def reflect(self, bank_id: str, query: str) -> Dict[str, Any]:
        """
        Synthesizes multi-temporal trajectory across memories using Hindsight reflect.
        """
        if self._can_use_cloud():
            try:
                res = requests.post(
                    f"{self.base_url.rstrip('/')}/v1/default/banks/{bank_id}/reflect",
                    headers=self._get_headers(),
                    json={"query": query},
                    timeout=8
                )
                if res.status_code == 200:
                    d = res.json()
                    return {"text": d.get("text", ""), "based_on": d.get("based_on", []), "storage_backend": "hindsight_cloud"}
                elif res.status_code == 402:
                    self._cloud_credits_exhausted = True
            except Exception:
                pass

        # Embedded reflect using recalled memories + Groq synthesis
        try:
            recall_data = self.recall(bank_id, query)
            recalled = recall_data.get("results", [])

            if not recalled:
                return {
                    "text": "Initial scan baseline established. Trajectory reflection compounds as subsequent scans accumulate temporal observations.",
                    "based_on": [],
                    "storage_backend": "hindsight_embedded"
                }

            if not self.groq_client:
                bullets = "\n".join([f"• ({m.get('timestamp')}) {m.get('text')[:180]}..." for m in recalled[:3]])
                return {
                    "text": f"Hindsight memory observations:\n{bullets}",
                    "based_on": recalled,
                    "storage_backend": "hindsight_embedded"
                }

            context_lines = "\n\n".join([f"Observation [Node {m.get('id')} - {m.get('timestamp')}]:\n{m.get('text')}" for m in recalled[:5]])
            prompt = f"""
You are the reflection reasoning engine of Vectorize Hindsight memory.
Target Query: "{query}"

HISTORICAL OBSERVATIONS RETRIEVED FROM PERSISTENT MEMORY BANK:
{context_lines}

TASK:
Synthesize an executive trajectory reflection (3-4 sentences) answering the query.
Ground every statement directly in the retrieved observations. Note specifically:
1. What has changed since prior observations (pricing, feature shifts, positioning)?
2. Which strategies are developing?
3. Which trends are continuing?
"""
            syn_text = ""
            for m in ["openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
                try:
                    res = self.groq_client.chat.completions.create(
                        model=m,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=600
                    )
                    syn_text = res.choices[0].message.content.strip()
                    if syn_text:
                        break
                except Exception:
                    continue

            return {
                "text": syn_text,
                "based_on": recalled,
                "storage_backend": "hindsight_embedded"
            }
        except Exception as e:
            return {"text": f"Reflection note: {str(e)}", "based_on": [], "storage_backend": "hindsight_embedded"}

    def get_all_memories(self, bank_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all raw memory nodes in a bank for inspection.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    "SELECT id, content, timestamp, metadata_json, created_at FROM memories WHERE bank_id = ? ORDER BY created_at DESC",
                    (bank_id,)
                )
                rows = cur.fetchall()

            memories = []
            for nid, content, ts, meta_raw, created_at in rows:
                try:
                    meta_obj = json.loads(meta_raw) if meta_raw else {}
                except Exception:
                    meta_obj = {}
                memories.append({
                    "id": nid,
                    "content": content,
                    "timestamp": ts,
                    "metadata": meta_obj,
                    "created_at": created_at
                })
            return memories
        except Exception:
            return []

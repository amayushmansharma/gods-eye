import os
import re
import json
import hashlib
import difflib
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from tavily import TavilyClient

SNAPSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".snapshots"))
MANIFEST_FILE = os.path.join(SNAPSHOTS_DIR, "manifest.json")
SCAN_LOG_FILE = os.path.join(SNAPSHOTS_DIR, "scan_log.jsonl")

# Standard watchlist definition for SaaS competitors
DEFAULT_WATCHLIST = [
    {
        "id": "linear",
        "name": "Linear",
        "domain": "linear.app",
        "pages": [
            {"type": "pricing", "url": "https://linear.app/pricing"},
            {"type": "changelog", "url": "https://linear.app/changelog"}
        ]
    },
    {
        "id": "posthog",
        "name": "PostHog",
        "domain": "posthog.com",
        "pages": [
            {"type": "pricing", "url": "https://posthog.com/pricing"},
            {"type": "changelog", "url": "https://posthog.com/changelog"}
        ]
    },
    {
        "id": "resend",
        "name": "Resend",
        "domain": "resend.com",
        "pages": [
            {"type": "pricing", "url": "https://resend.com/pricing"},
            {"type": "changelog", "url": "https://resend.com/changelog"}
        ]
    }
]

class SnapshotService:
    def __init__(self, tavily_api_key: Optional[str] = None):
        self.snapshots_dir = SNAPSHOTS_DIR
        os.makedirs(self.snapshots_dir, exist_ok=True)
        self.manifest_path = MANIFEST_FILE
        self.scan_log_path = SCAN_LOG_FILE
        self.api_key = tavily_api_key or os.getenv("TAVILY_API_KEY", "")
        self.client = TavilyClient(api_key=self.api_key) if self.api_key else None
        self._ensure_manifest()

    def _ensure_manifest(self):
        if not os.path.exists(self.manifest_path):
            with open(self.manifest_path, "w") as f:
                json.dump({"urls": {}, "competitors": {}}, f, indent=2)

    def _load_manifest(self) -> Dict[str, Any]:
        try:
            with open(self.manifest_path, "r") as f:
                return json.load(f)
        except Exception:
            return {"urls": {}, "competitors": {}}

    def _save_manifest(self, data: Dict[str, Any]):
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_url_slug(self, url: str) -> str:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:10]
        clean_name = re.sub(r"[^a-zA-Z0-9]", "_", url.replace("https://", "").replace("http://", "").rstrip("/"))[:30]
        return f"{clean_name}_{h}"

    def normalize_content(self, raw_text: str) -> str:
        """
        Normalizes raw markdown/HTML extraction:
        - Drops pure image embeds, navigation skip links, cookie notices, generic footers
        - Strips excessive whitespace and blank lines
        - Dedupes consecutive identical lines
        """
        if not raw_text:
            return ""

        drop_regexes = [
            re.compile(r"^\s*\[skip to content.*\]", re.IGNORECASE),
            re.compile(r"^\s*!\[.*?\]\(.*?\)\s*$", re.IGNORECASE),
            re.compile(r"^\s*\[(log in|sign in|sign up|get started|privacy policy|terms of service|cookies)\]", re.IGNORECASE),
            re.compile(r"^\s*(all rights reserved|copyright ©|© \d{4})", re.IGNORECASE),
            re.compile(r"^\s*cookie (settings|preferences|banner|consent)", re.IGNORECASE),
        ]

        lines = raw_text.splitlines()
        filtered = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if any(rx.search(stripped) for rx in drop_regexes):
                continue
            filtered.append(stripped)

        # Deduplicate consecutive identical lines (e.g. repeated buttons/nav items)
        deduped = []
        for l in filtered:
            if not deduped or deduped[-1] != l:
                deduped.append(l)

        return "\n".join(deduped)

    def extract_page(self, url: str) -> Tuple[bool, str, Optional[str]]:
        """
        Fetches live page text using Tavily extract.
        Returns: (success, raw_content, error_message)
        """
        if not self.client:
            return False, "", "Tavily API key is not configured."

        try:
            res = self.client.extract(urls=[url])
            results = res.get("results", [])
            if results and len(results) > 0:
                raw = results[0].get("raw_content", "")
                if raw:
                    return True, raw, None
            failed = res.get("failed_results", [])
            err = f"Tavily extract failed for {url}: {failed}"
            return False, "", err
        except Exception as e:
            return False, "", str(e)

    def get_latest_snapshot(self, url: str) -> Optional[str]:
        slug = self.get_url_slug(url)
        latest_file = os.path.join(self.snapshots_dir, f"{slug}_latest.txt")
        if os.path.exists(latest_file):
            try:
                with open(latest_file, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def save_snapshot(self, url: str, content: str, timestamp_iso: str) -> str:
        slug = self.get_url_slug(url)
        safe_ts = timestamp_iso.replace(":", "-")
        hist_file = os.path.join(self.snapshots_dir, f"{slug}_{safe_ts}.txt")
        latest_file = os.path.join(self.snapshots_dir, f"{slug}_latest.txt")

        with open(hist_file, "w", encoding="utf-8") as f:
            f.write(content)
        with open(latest_file, "w", encoding="utf-8") as f:
            f.write(content)

        return hist_file

    def compute_diff(self, old_text: str, new_text: str, from_date: str, to_date: str) -> Dict[str, Any]:
        """
        Computes deterministic line diff using difflib.
        """
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()

        diff_gen = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"Snapshot ({from_date})",
            tofile=f"Snapshot ({to_date})",
            lineterm=""
        )
        diff_lines = list(diff_gen)

        added = [l for l in diff_lines if l.startswith("+") and not l.startswith("+++")]
        removed = [l for l in diff_lines if l.startswith("-") and not l.startswith("---")]
        total_changed = len(added) + len(removed)

        if total_changed == 0:
            status = "unchanged"
            is_change = False
        elif total_changed > 40:
            status = "possible_page_redesign"
            is_change = True
        else:
            status = "page_diff_detected"
            is_change = True

        return {
            "is_change": is_change,
            "status": status,
            "changed_lines_count": total_changed,
            "added_count": len(added),
            "removed_count": len(removed),
            "added_lines": added,
            "removed_lines": removed,
            "raw_diff": "\n".join(diff_lines)
        }

    def process_url(self, competitor_name: str, page_type: str, url: str) -> Dict[str, Any]:
        """
        Executes a single-page snapshot & diff cycle:
        1. Extracts page via Tavily
        2. Normalizes text
        3. Retrieves previous snapshot if any
        4. Calculates deterministic diff
        5. Saves new snapshot and updates manifest
        """
        now_dt = datetime.now(timezone.utc)
        now_iso = now_dt.isoformat()

        manifest = self._load_manifest()
        url_entry = manifest.get("urls", {}).get(url, {
            "competitor": competitor_name,
            "page_type": page_type,
            "scan_count": 0,
            "history": []
        })

        success, raw_content, error = self.extract_page(url)
        if not success:
            log_record = {
                "timestamp": now_iso,
                "competitor": competitor_name,
                "url": url,
                "page_type": page_type,
                "status": "extract_failed",
                "error": error
            }
            self._append_scan_log(log_record)
            return {
                "url": url,
                "competitor": competitor_name,
                "page_type": page_type,
                "status": "extract_failed",
                "error": error,
                "is_change": False,
                "diff": None
            }

        normalized = self.normalize_content(raw_content)
        previous_snapshot = self.get_latest_snapshot(url)
        scan_count = url_entry.get("scan_count", 0) + 1

        if previous_snapshot is None:
            # Baseline initial run
            self.save_snapshot(url, normalized, now_iso)
            url_entry["scan_count"] = scan_count
            url_entry["baseline_at"] = now_iso
            url_entry["last_scanned_at"] = now_iso
            url_entry["history"].append({
                "timestamp": now_iso,
                "event": "baseline_established",
                "lines_count": len(normalized.splitlines())
            })
            manifest["urls"][url] = url_entry
            self._save_manifest(manifest)

            log_record = {
                "timestamp": now_iso,
                "competitor": competitor_name,
                "url": url,
                "page_type": page_type,
                "scan_count": scan_count,
                "status": "baseline_established",
                "diff_size": 0
            }
            self._append_scan_log(log_record)

            return {
                "url": url,
                "competitor": competitor_name,
                "page_type": page_type,
                "scan_count": scan_count,
                "status": "baseline_established",
                "is_change": False,
                "timestamp": now_iso,
                "diff": None,
                "content_preview": normalized[:500]
            }

        # Compare with previous snapshot
        prev_ts = url_entry.get("last_scanned_at", "prior")
        diff_info = self.compute_diff(previous_snapshot, normalized, prev_ts, now_iso)

        # Save snapshot
        self.save_snapshot(url, normalized, now_iso)
        url_entry["scan_count"] = scan_count
        url_entry["last_scanned_at"] = now_iso
        url_entry["history"].append({
            "timestamp": now_iso,
            "status": diff_info["status"],
            "changed_lines": diff_info["changed_lines_count"]
        })
        manifest["urls"][url] = url_entry
        self._save_manifest(manifest)

        log_record = {
            "timestamp": now_iso,
            "competitor": competitor_name,
            "url": url,
            "page_type": page_type,
            "scan_count": scan_count,
            "status": diff_info["status"],
            "diff_size": diff_info["changed_lines_count"]
        }
        self._append_scan_log(log_record)

        return {
            "url": url,
            "competitor": competitor_name,
            "page_type": page_type,
            "scan_count": scan_count,
            "status": diff_info["status"],
            "is_change": diff_info["is_change"],
            "previous_timestamp": prev_ts,
            "current_timestamp": now_iso,
            "diff": diff_info
        }

    def _append_scan_log(self, record: Dict[str, Any]):
        try:
            with open(self.scan_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            print(f"[Scan Log Error] {e}")

    def get_scan_history(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.scan_log_path):
            return []
        records = []
        try:
            with open(self.scan_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
        except Exception:
            pass
        return records

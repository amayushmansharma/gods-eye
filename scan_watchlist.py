#!/usr/bin/env python3
"""
God's Eye — Standalone Watchlist Scanner
Can be executed manually or scheduled via cron / launchd.
Logs every run to .snapshots/scan_log.jsonl.
"""
import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure root directory is in sys.path
root_dir = os.path.dirname(os.path.abspath(__file__))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

load_dotenv(os.path.join(root_dir, ".env"))

from services.snapshot_service import SnapshotService, DEFAULT_WATCHLIST
from services.hindsight_service import HindsightService

def run_watchlist_scan(watchlist=None) -> list:
    watchlist = watchlist or DEFAULT_WATCHLIST
    snapshot_svc = SnapshotService()
    hindsight = HindsightService()

    now_iso = datetime.now(timezone.utc).isoformat()
    print(f"[{now_iso}] Starting God's Eye Watchlist Scan ({len(watchlist)} competitors)...")

    results = []

    for comp in watchlist:
        c_id = comp["id"]
        c_name = comp["name"]
        bank_id = f"godseye-watchlist-{c_id}"

        print(f"\nScanning {c_name}...")
        for page in comp.get("pages", []):
            p_type = page["type"]
            p_url = page["url"]

            scan_res = snapshot_svc.process_url(c_name, p_type, p_url)
            status = scan_res.get("status")
            is_change = scan_res.get("is_change", False)
            diff_info = scan_res.get("diff")

            hindsight_status = "skipped_unchanged"
            retain_res = None

            if status == "baseline_established":
                # Retain initial baseline marker into Hindsight
                h_res = hindsight.retain_page_diff(
                    bank_id=bank_id,
                    competitor=c_name,
                    page_type=p_type,
                    url=p_url,
                    diff_text=f"Baseline established for {c_name} {p_type}. Content tracked.",
                    timestamp_iso=now_iso,
                    status="baseline_established",
                    lines_changed=0
                )
                hindsight_status = h_res.get("storage_backend", "retained")
                retain_res = h_res
            elif is_change and diff_info:
                # Retain verified real diff into Hindsight
                diff_text = diff_info.get("raw_diff", "")
                changed_lines = diff_info.get("changed_lines_count", 0)

                h_res = hindsight.retain_page_diff(
                    bank_id=bank_id,
                    competitor=c_name,
                    page_type=p_type,
                    url=p_url,
                    diff_text=diff_text,
                    timestamp_iso=now_iso,
                    status=status,
                    lines_changed=changed_lines
                )
                hindsight_status = h_res.get("storage_backend", "retained")
                retain_res = h_res

            scan_res["hindsight_status"] = hindsight_status
            scan_res["hindsight_response"] = retain_res
            results.append(scan_res)

            lines_count = diff_info.get("changed_lines_count", 0) if diff_info else 0
            print(f"  -> {p_type.capitalize()} ({p_url}): {status} | Lines changed: {lines_count} | Hindsight: {hindsight_status}")

    print(f"\nCompleted scan at {datetime.now(timezone.utc).isoformat()}. Total pages processed: {len(results)}")
    return results

if __name__ == "__main__":
    run_watchlist_scan()

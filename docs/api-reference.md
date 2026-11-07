# God's Eye — API Reference

Comprehensive reference for all God's Eye REST endpoints, Server-Sent Events (SSE) streams, and CLI automation tools.

Base URL: `http://localhost:8000`

---

## 🛰️ Intelligence & Scanning Endpoints

### 1. `POST /api/scan`
Executes an end-to-end multi-stage competitive intelligence scan against a target company website.

#### Request Body (`application/json`)
```json
{
  "url": "https://linear.app",
  "deep_mode": true,
  "simulate_rescan": false,
  "use_memory": true
}
```

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `url` | string | *Required* | Target company URL (must pass SSRF validation). |
| `deep_mode` | boolean | `true` | Enables in-depth 30s+ multi-stage intelligence analysis. |
| `simulate_rescan`| boolean | `false` | Forces an immediate second-pass iteration to demonstrate memory compounding. |
| `use_memory` | boolean | `true` | When `false`, executes in stateless mode, bypassing Hindsight recall, retention, and reflection. |

#### Response (`200 OK`)
```json
{
  "success": true,
  "scan_id": "scan_1794038920123",
  "domain": "linear.app",
  "brand_name": "Linear",
  "scan_iteration": 2,
  "use_memory": true,
  "is_memory_enabled": true,
  "what_happened": {
    "summary": "Linear continues to optimize fast developer issue tracking...",
    "competitors": [
      {
        "name": "ClickUp",
        "price_trend": "Starting at $7/user/mo",
        "recent_move": "Expanding unified project workspace capabilities"
      }
    ],
    "pricing_feature_matrix": [
      {
        "segment": "Free Tier",
        "target_offering": "Free up to 250 active issues",
        "market_benchmark": "Industry standard free tier limit"
      }
    ],
    "historical_differences": [
      {
        "item": "Continuous Surveillance",
        "change_type": "unchanged",
        "category": "Pricing & Features",
        "summary": "Continuous surveillance verified stability across monitored tiers with zero detectable price drift."
      }
    ]
  },
  "why_does_it_matter": {
    "macro_trends": ["Shift toward lightweight, high-performance developer tools"],
    "opportunity_finder": ["Enterprises seek unified issue tracking without Jira complexity"],
    "threat_detection": [
      {
        "threat": "Competitors adding AI auto-triaging",
        "severity": "Medium",
        "rationale": "High adoption in enterprise teams"
      }
    ]
  },
  "what_should_we_do": {
    "immediate_counter_measures": [
      {
        "priority": "P0 Critical",
        "action": "Accelerate customer request integrations into triage workflow",
        "rationale": "Maintains developer productivity lead"
      }
    ]
  },
  "hindsight_memory": {
    "bank_id": "godseye-intel-linear-app",
    "recalled_nodes": [
      {
        "id": "node_0afb99712a",
        "text": "Linear maintains pricing stability at $8-$14/mo per user.",
        "category": "Pricing Model"
      }
    ],
    "reflection_text": "Across monitored intervals, Linear has maintained stable pricing while competitors expanded enterprise feature sets..."
  },
  "stats": {
    "competitors_count": 4,
    "recalled_memories_count": 8,
    "changes_detected": 0
  }
}
```

#### Error Responses
- `400 Bad Request`: Invalid URL format, private RFC1918 IP, localhost, or cloud metadata target (`169.254.169.254`).
- `500 Internal Server Error`: Unhandled extraction failure.

#### Example `curl`
```bash
curl -X POST http://localhost:8000/api/scan \
  -H "Content-Type: application/json" \
  -d '{"url": "https://linear.app", "deep_mode": true, "use_memory": true}'
```

---

### 2. `GET /api/scan_progress/{scan_id}`
Establishes a Server-Sent Events (SSE) connection streaming real-time status and logs as the agent completes each of the 6 stages.

#### Query Parameters
- `scan_id`: Unique identifier returned during scan initialization.

#### Stream Output (`text/event-stream`)
```
event: progress
data: {"stage_idx": 1, "stage_name": "Company ID", "percent": 15, "message": "Understanding products and positioning...", "verified": true}

event: progress
data: {"stage_idx": 4, "stage_name": "7-Day News", "percent": 68, "message": "Aggregating verified news published in the last 7 days...", "verified": true}

event: complete
data: {"stage_idx": 6, "percent": 100, "message": "Scan complete. Verified report generated."}
```

---

## 🧠 Hindsight Memory Endpoints

### 3. `GET /api/hindsight/status`
Returns the operational health and active storage backend of Vectorize Hindsight.

#### Query Parameters
- `force` (boolean, optional): Set to `true` to bypass cache and run a fresh live health probe.

#### Response (`200 OK`)
```json
{
  "healthy": true,
  "status": "passed",
  "ok": true,
  "mode": "Embedded Fallback",
  "provider": "Vectorize Hindsight (Embedded SQLite + Groq)",
  "latency_ms": 3,
  "probe_bank": "godseye-health-probe",
  "base_url": "embedded://sqlite",
  "storage_backend": "hindsight_embedded",
  "cloud_credits_exhausted": true
}
```

*Note: In compliance with technical integrity standards, local SQLite is explicitly labeled as `hindsight_embedded` when cloud credits are exhausted and is never misrepresented as cloud storage.*

#### Example `curl`
```bash
curl http://localhost:8000/api/hindsight/status
```

---

### 4. `POST /api/hindsight/ask`
Interrogates a company's persistent Hindsight memory bank using natural language.

#### Request Body (`application/json`)
```json
{
  "domain": "linear.app",
  "question": "How have competitor prices shifted over time?"
}
```

#### Response (`200 OK`)
```json
{
  "success": true,
  "question": "How have competitor prices shifted over time?",
  "bank_id": "godseye-intel-linear-app",
  "answer": "Competitors in the developer issue tracking space have maintained entry tiers while increasing enterprise bundling prices...",
  "cited_nodes": [
    {
      "id": "node_0afb99712a",
      "text": "Linear maintained pricing stability at $8-$14/mo per user."
    }
  ]
}
```

#### Example `curl`
```bash
curl -X POST http://localhost:8000/api/hindsight/ask \
  -H "Content-Type: application/json" \
  -d '{"domain": "linear.app", "question": "What is our pricing moat?"}'
```

---

## 📊 Snapshots, Watchlist & Founder Decisions

### 5. `GET /api/watchlist`
Retrieves all tracked companies, scan iteration counts, and cached intelligence summaries.

#### Response (`200 OK`)
```json
{
  "watchlist": [
    {
      "id": "linear-app",
      "name": "Linear",
      "domain": "linear.app",
      "scan_iteration": 2,
      "last_scanned": "2026-11-07T08:49:00Z"
    }
  ]
}
```

---

### 6. `POST /api/decisions`
Records founder strategic decisions in response to detected competitor moves and retains them into Hindsight memory.

#### Request Body (`application/json`)
```json
{
  "domain": "linear.app",
  "decision": "Held price and accelerated customer request triage feature",
  "threat_id": "threat_101",
  "action_type": "Held price"
}
```

#### Response (`200 OK`)
```json
{
  "success": true,
  "decision_id": "dec_1794038925",
  "node_id": "node_8f12c9b4e0",
  "storage_backend": "hindsight_embedded"
}
```

---

### 7. `GET /api/export_report/{domain}`
Renders a clean, executive printable/PDF view of the latest scan for the specified domain.

#### Response (`200 OK`)
Returns rendered HTML formatted for print and PDF generation (`@media print`).

---

## 🛠️ CLI Automation Scripts

### `scan_watchlist.py`
Autonomous batch scanner for background surveillance:
```bash
python3 scan_watchlist.py
```
- Reads configured targets from `SnapshotService.DEFAULT_WATCHLIST`.
- Checks for page content changes against historical baselines.
- Retains genuine diffs into Hindsight memory banks.
- Appends structured run logs to `.snapshots/scan_log.jsonl`.

### `generate_intro.py`
Offline asset compilation script:
```bash
python3 generate_intro.py
```
- Injects SVG wordmarks and viewport isolation styling into `public/intro.html`.

# God's Eye — System Architecture

God's Eye is an autonomous competitive intelligence agent engineered to transform ephemeral web searches into compounding, persistent strategic knowledge. It addresses the fundamental flaw of stateless AI and traditional RAG: **temporal amnesia**.

---

## 🏗️ High-Level System Architecture

```mermaid
flowchart TD
    User([Executive / Founder]) -->|URL Input & Options| Gateway[FastAPI Application Gateway\napp.py]
    
    subgraph Frontend [Frozen Glassmorphic Dashboard]
        UI[public/index.html]
        Canvas[Iris Shader & Visualizers\niris-shader.js / iris-mark.js]
        SSE[SSE Live Stream Consumer]
    end
    UI <--> Gateway
    
    subgraph IntelligenceEngine [02 · Intelligence Engine\nservices/intelligence_engine.py]
        SSRF[SSRF & URL Security Validator]
        P1[1. Brand & Positioning Extraction]
        P2[2. Competitor Discovery 2-4 Direct Rivals]
        P3[3. Cross-Tier Pricing & Plan Matrix]
        P4[4. 7-Day Verified News Pulse]
        P5[5. Cross-Temporal Memory Synthesis]
        P6[6. Strict Source Verification]
    end
    Gateway --> IntelligenceEngine
    
    subgraph ResearchLayer [Web Research Providers]
        Tavily[Tavily Search API\ntopic='news', days=7]
        RawScraper[SnapshotService Fallback Scraper]
    end
    IntelligenceEngine <--> ResearchLayer
    
    subgraph MemoryLayer [Persistent Memory Architecture\nservices/hindsight_service.py]
        direction TB
        BankRouter{Engine Router}
        CloudHindsight[Vectorize Cloud API\napi.hindsight.vectorize.io]
        EmbeddedHindsight[Embedded Engine\nSQLite + Groq Reflection]
        BankRouter -->|Credits Active| CloudHindsight
        BankRouter -->|Credits Exhausted / Local| EmbeddedHindsight
        
        RetainOp[RETAIN\nTemporal Anchoring & SHA-256 Deduplication]
        RecallOp[RECALL\nMulti-Strategy Keyword & Vector Retrieval]
        ReflectOp[REFLECT\nCross-Scan Strategic Trajectory Synthesis]
    end
    IntelligenceEngine <--> MemoryLayer
    
    subgraph ReasoningLayer [Groq Synthesis Engine]
        GroqLLM[Groq LPU LLM\nopenai/gpt-oss-120b]
    end
    IntelligenceEngine <--> ReasoningLayer
    
    subgraph PersistenceLayer [Historical Snapshot Archive\nservices/snapshot_service.py]
        LatestSnap[.snapshots/scans/{domain}.json]
        VersionedHistory[.snapshots/scans/{domain}_scan_{iteration}_{ts}.json]
        EmbeddedDB[.snapshots/hindsight_embedded.db]
    end
    IntelligenceEngine --> PersistenceLayer
    EmbeddedHindsight --> EmbeddedDB
    
    subgraph OutputLayer [03 · Intelligence Report & Interrogation]
        Bento[The Three Questions Bento Grid]
        NeuralGraph[Interactive Neural Memory Network]
        Drilldown[Direct Memory Interrogation /api/hindsight/ask]
        DecisionLogger[Founder Decision Logger /api/decisions]
    end
    IntelligenceEngine --> OutputLayer
```

---

## ⏱️ The 4-Stage Operational Workflow

### Stage 01 · Start a Scan
- Accepts arbitrary company URLs (e.g. `https://linear.app`, `https://www.bmw.in/`, `school.bosscoderacademy.com`).
- Enforces strict SSRF protection: resolves domain hostnames to IP addresses and rejects `127.0.0.1`, `localhost`, RFC1918 private subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`), link-local IPs, and cloud metadata services (`169.254.169.254`).
- Validates brand display names dynamically without relying on hardcoded lookup tables.

### Stage 02 · Intelligence Engine
Runs an autonomous multi-stage research and synthesis cycle with a 30-second target and real-time Server-Sent Events (SSE) updates:
1. **Understand products, positioning, and market**: Identifies core value proposition, audience segments, and product architecture.
2. **Discover 2–4 relevant competitors**: Dynamically identifies genuine direct market rivals.
3. **Research competitor products, pricing, and features**: Gathers tiered pricing, plan limits, and feature matrices.
4. **Find news and articles published in the last 7 days**: Filters strictly on verified publication dates, discarding stale articles and future-dated hallucinations.
5. **Analyse market trends, launches, and Hindsight memory**: Recalls prior scan snapshots and executes cross-temporal reflection.
6. **Verify findings against original sources**: Binds claims to publisher sources and direct URLs.

### Stage 03 · Intelligence Report
Presents the executive competitive landscape organized around **The Three Questions Framework**:
- **What happened? (Research & Monitoring)**: Verified facts, competitor cards, pricing matrices, and 7-day news.
- **Why does it matter? (Historical Analysis)**: Macro market movements, unaddressed market opportunities, and threat assessments.
- **What should we do? (Strategic Recommendations)**: Evidence-grounded P0 critical and P1 offensive counter-measures.

### Stage 04 · Hindsight Memory
Visualizes the compounding relational neural network of memory nodes. Founders can inspect node relationships or interrogate memory directly via natural language.

---

## 🧠 Memory Primitives: Retain, Recall, Reflect

God's Eye leverages Vectorize Hindsight's core primitives:

### 1. RETAIN
- **Temporal Anchoring**: News signals and pricing events are indexed with verified publication timestamps rather than transient scan times.
- **Deterministic Node Deduplication**: Each node ID is computed via SHA-256 content hashing (`node_{hash[:16]}`). Re-scanning an unchanged company avoids memory explosion.
- **Bank Isolation**: Each domain is partitioned into its own bank (`godseye-intel-{clean_domain}`), preventing data leaks across competitors.

### 2. RECALL
- **Multi-Strategy Retrieval**: Combines semantic vector proximity, BM25 keyword matching, entity graph traversal, and temporal recency.
- **Synthesis Context Injection**: Recalled historical nodes are directly embedded into the LLM synthesis context, allowing the model to correlate current observations with past baselines.

### 3. REFLECT
- **Trajectory Reasoning**: Synthesizes multi-scan trajectories across stored memory nodes to evaluate whether competitor moves represent isolated experiments or long-term strategic shifts.
- **Fallback Reflection**: In embedded mode, Groq performs structured reflection directly over the local SQLite node history.

---

## 🔄 Dual-Engine Resilience: Cloud vs. Embedded Fallback

| Capability | Vectorize Cloud Hindsight | Embedded Hindsight Fallback |
| :--- | :--- | :--- |
| **Backend** | `https://api.hindsight.vectorize.io` | Local SQLite (`.snapshots/hindsight_embedded.db`) |
| **Routing** | Primary when API key has positive balance | Automatic failover on HTTP 402 or offline |
| **Transparency** | Reports `storage_backend="hindsight_cloud"` | Reports `storage_backend="hindsight_embedded"` |
| **Deduplication** | Managed by Vectorize Cloud | SHA-256 deterministic node IDs |
| **Reflection** | Native `POST /reflect` endpoint | Structured Groq LLM synthesis over local nodes |
| **Zero Misrepresentation**| Never claims local persistence is cloud | Explicitly declares `cloud_credits_exhausted=True` |

---

## 🛡️ Memory Modes: Enabled vs. Stateless

- **Memory-Enabled (`use_memory=True`)**:
  - Full compounding cycle: Recalls past snapshots, computes genuine differences, reflects across historical nodes, and retains newly verified facts.
- **Memory-Disabled (`use_memory=False` / Stateless)**:
  - Bypasses all Hindsight memory operations.
  - Generates a stateless single-point snapshot without querying memory banks or retaining findings.
  - Demonstrates the stark contrast between persistent agent memory and traditional amnesic RAG.

---

## 📁 Complementary CLI Utilities

### `scan_watchlist.py`
A standalone batch scanner designed for automated execution (e.g. cron jobs, systemd timers, or manual execution):
- Iterates through a configured watchlist of competitor URLs.
- Executes page snapshotting and content hashing.
- Computes character and line-level diffs against previous snapshots.
- Retains genuine diffs directly into Hindsight memory banks.
- Logs structured audit entries to `.snapshots/scan_log.jsonl`.

### `generate_intro.py`
An offline asset compilation utility:
- Used during product design to assemble the custom Three.js / Canvas wordmark intro sequence into `public/intro.html` and `public/god-eye-intro.js`.
- Injects SVG wordmarks, typography fitting logic, and resize handlers.

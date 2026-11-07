# Why We Stopped Doing One-Shot Scrapes and Built an Agent That Never Forgets

Every product marketer, strategist, and founder has the same Monday morning ritual: opening 15 browser tabs, checking competitor pricing pages, scanning product updates, and trying to remember what changed since last month.

When we set out to automate this, the initial prototype followed the standard 2024 AI recipe: give an LLM a web crawler, feed it competitor HTML snippets, and ask it for a summary.

It was fundamentally limited.

The agent could describe what competitors like Jira, Asana, or Mercedes-Benz offered *that morning*. But it couldn’t tell us how feature packaging had evolved over time, or correlate a recent price change with an enterprise bundling shift. A stateless agent has zero sense of trajectory.

To solve this, we redesigned our pipeline around **God's Eye**—a competitive intelligence system powered by persistent [agent memory](https://vectorize.io/what-is-agent-memory). Here is how the system hangs together, why we chose [Vectorize Hindsight](https://github.com/vectorize-io/hindsight), and the engineering lessons learned along the way.

---

## The Technical Flaw of Stateless RAG

When engineers attempt to give memory to an LLM, their default tool is traditional Retrieval-Augmented Generation (RAG): chunk historical crawl logs, dump them into a vector database with pgvector, and cosine-similarity search against the current query.

In real-world competitive monitoring, naive RAG falls apart:

1. **Temporal Blindness:** When a competitor changes their pricing tiers or feature packaging, cosine similarity rates both historical and current chunks as highly relevant because they share identical terminology. The LLM blends old and new tiers because it cannot determine which fact supersedes the other.
2. **Entity Fragmentation:** Market data is an evolving graph of entities—products, integrations, API tiers, and enterprise terms—shifting states over time.
3. **Context Bloat:** Stuffing raw crawl logs into system prompts quickly exceeds practical latency budgets and degrades model attention.

We needed a dedicated memory layer that structures discrete world facts, tracks entity relationships, and provides temporal retrieval primitives. That led us to [Hindsight](https://hindsight.vectorize.io/) and its three foundational memory operations: `retain`, `recall`, and `reflect`.

---

## System Architecture: The Three Memory Primitives

God's Eye connects live web search via Tavily (`topic="news"`), fast structured extraction via Groq (`openai/gpt-oss-120b`), and persistent memory on **Vectorize Hindsight**:

```
                       ┌───────────────────────────┐
                       │     Target Domain URL     │
                       │ (e.g. BMW India, Linear)  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │ 02 · Intelligence Engine  │
                       │ (6-Stage 30s+ Deep Scan)  │
                       └──────┬─────────────┬──────┘
                              │             │
           1. Live Web News   │             │ 2. Memory Recall & Reflect
              via Tavily API  │             │    via Hindsight Memory API
                              ▼             ▼
                       ┌───────────────────────────┐
                       │   Groq Reasoning Engine   │
                       │   (openai/gpt-oss-120b)   │
                       └─────────────┬─────────────┘
                                     │
           3. Retain verified moves  │
              into Hindsight Memory  ▼
                       ┌───────────────────────────┐
                       │ 03 · Intelligence Report  │
                       │    (The 3 Questions)      │
                       └───────────────────────────┘
```

### 1. Ingestion with Real Publication Anchors (`retain`)
When God's Eye scans a brand, it extracts verified articles from Tavily. Instead of using the scan time as the timestamp, each article is anchored to its actual `published_date`:

```python
# Retaining verified articles into Hindsight with verified publication dates
payload = {
    "items": [
        {
            "content": f"Article: {title}\nSource: {source}\nContent: {snippet}",
            "timestamp": published_date_iso,
            "metadata": {
                "source": str(source),
                "url": str(url),
                "brand": str(brand_name),
                "type": "market_signal"
            }
        }
    ]
}
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/memories",
    headers=headers,
    json=payload
)
```

To avoid memory pollution, God's Eye maintains an explicit URL registry per bank. On rescans, it diffs incoming articles against previously stored URLs and retains only newly discovered articles.

### 2. Multi-Strategy Retrieval (`recall`)
To evaluate current market signals against prior context, God's Eye queries the bank using Hindsight's parallel recall:

```python
# Querying historical observations from Hindsight
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/memories/recall",
    headers=headers,
    json={"query": f"What competitor price shifts and moves were observed for {brand_name}?"}
)
historical_nodes = res.json().get("results", [])
```

Behind this call, Hindsight coordinates semantic vector similarity, BM25 keyword matching, entity graph traversal, and temporal recency filtering.

### 3. Native Cross-Temporal Synthesis (`reflect`)
The core reasoning capability comes from Hindsight's native `POST /reflect` endpoint. Instead of requiring the LLM to manually compare raw text chunks, Hindsight reflects across world facts and observations directly:

```python
# Synthesizing trajectory natively in Hindsight
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/reflect",
    headers=headers,
    json={"query": f"Synthesize the competitive moves, pricing trajectory, and market shifts for {brand_name} across all stored memories."}
)
reflection = res.json().get("text", "")
```

---

## The Three Core Questions Framework

Rather than dumping unstructured web text, God's Eye synthesizes intelligence around three essential executive questions:

1. **What happened?** (Research & Monitoring)
   - Automatically discovers 2–4 direct rivals across segments.
   - Extracts side-by-side pricing tiers and plan limits.
   - Pulls 7-day verified news with real publication dates.
   - All items tagged as `[VERIFIED FACT]`.

2. **Why does it matter?** (Historical Analysis & Trend Detection)
   - Discovers macro market shifts and EV/AI localization trends.
   - Opportunity Finder highlights gaps competitors aren't addressing.
   - Threat Detection flags aggressive rival moves with severity rankings (`High`, `Medium`, `Moderate`).
   - All items tagged as `[INFERRED STRATEGY]`.

3. **What should we do?** (Strategic Recommendations)
   - Prescribes evidence-backed counter-measures (`P0 Critical`, `P1 Offensive`).
   - Interactive Decision Logger lets founders record strategic actions (Held price, Matched, Launched campaign, Ignored) which are retained into Hindsight memory.
   - All items tagged as `[STRATEGIC ACTION]`.

---

## Real-World Verification: What Happens Across Scans

Here is how the system behaves on live targets like Linear (`linear.app`) or BMW India (`bmw.in`):

* **Scan #1 (Baseline Anchor):** God's Eye discovers direct rivals, extracts current tier pricing, and indexes 7-day verified news articles via Tavily. It anchors these observations into Hindsight bank `godseye-intel-{domain}` and archives a baseline snapshot on disk.
* **Scan #2 (Recall & Reflect):** Running a subsequent scan recalls the stored memory nodes and executes Hindsight `reflect()`. Crucially, rather than manufacturing fake price hikes or arbitrary changes, God's Eye compares the fresh web findings against the historical snapshot. When verifiable changes have occurred (such as promotional discounts or tier restructuring), Hindsight synthesizes the strategic trajectory and recommends evidence-backed counter-measures. If the market is stable, continuous surveillance accurately confirms baseline stability.
* **The "Without Memory" Delta:** When executing in **Without Memory (Stateless AI)** mode, the agent bypasses Hindsight. It has zero memory of prior scans, historical trend analysis is completely disabled, and its ability to detect market trajectory disappears.

---

## What Didn't Work & Engineering Lessons

Building this architecture highlighted several practical dead ends:

1. **Hallucinated Memory Seeding:** In early iterations, we considered using an LLM to generate "sample historical events" for new brands. The LLM hallucinated arbitrary numbers that contaminated Hindsight's reflection output. We removed all synthetic seeding and made Scan #1 an authentic, grounded baseline anchor.
2. **Manufactured Diff Traps:** Many competitive demos insert fake price increases ($20 to $25) on subsequent scans to make the UI look active. We replaced this with a strict snapshot diff engine: changes are reported only when backed by genuine evidence from the web.
3. **Duplicate Ingestion on Rescans:** Without content-based hashing, running a scan twice stored duplicate observations. We implemented SHA-256 deterministic node IDs so rescans maintain a clean, compounding memory bank.
4. **Resilience & Storage Transparency:** When third-party cloud services encounter network disruptions or credit limits, silent failure breaks agent reliability. We built a local embedded engine (SQLite + Groq reflection) that activates seamlessly while transparently reporting its active backend.

---

## Conclusion

Stateless AI tools provide one-off snapshots; competitive strategy requires trajectory. By structuring memory around Hindsight's `retain`, `recall`, and `reflect` primitives, God's Eye turns ephemeral web search into persistent, compounding market intelligence.

* Explore the project implementation on GitHub: [https://github.com/ayushmansharma/gods-eye](https://github.com/ayushmansharma/gods-eye)
* Learn more about memory architectures at [Vectorize agent memory](https://vectorize.io/what-is-agent-memory) and inspect the [Hindsight GitHub repo](https://github.com/vectorize-io/hindsight).

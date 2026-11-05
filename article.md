# Why We Stopped Doing One-Shot Scrapes and Built an Agent That Never Forgets

Every product marketer and founder I know has the same Monday morning ritual: opening 15 browser tabs, checking competitor pricing pages, scanning product updates, and trying to remember what changed since last month.

When we set out to automate this, the initial prototype followed the standard 2024 AI recipe: give an LLM a web crawler, feed it competitor HTML snippets, and ask it for a summary.

It was fundamentally limited.

The agent could describe what competitors like Jira, Asana, or ClickUp offered *that morning*. But it couldn’t tell us how feature packaging had evolved over time, or correlate a recent database infrastructure shift with an enterprise pricing pivot. A stateless agent has no sense of trajectory.

To solve this, we redesigned our pipeline around **God's Eye**—a competitive intelligence system powered by persistent [agent memory](https://vectorize.io/what-is-agent-memory). Here is how the system hangs together, why we chose [Hindsight](https://github.com/vectorize-io/hindsight), and the engineering lessons learned along the way.

---

## The Technical Flaw of Stateless RAG

When engineers attempt to give memory to an LLM, their default tool is traditional Retrieval-Augmented Generation (RAG): chunk historical scrape logs, dump them into a vector database with pgvector, and cosine-similarity search against the current query.

In real-world competitive monitoring, naive RAG falls apart:

1. **Temporal Blindness:** When a competitor changes their pricing tiers or feature packaging, cosine similarity rates both historical and current chunks as highly relevant because they share identical terminology. The LLM blends old and new tiers because it cannot determine which fact supersedes the other.
2. **Entity Fragmentation:** Market data is an evolving graph of entities—products, integrations, API tiers, and enterprise terms—shifting states over time.
3. **Context Bloat:** Stuffing raw crawl logs into system prompts quickly exceeds practical latency budgets and degrades model attention.

We needed a dedicated memory layer that structures discrete world facts, tracks entity relationships, and provides temporal retrieval primitives. That led us to the [Hindsight documentation](https://hindsight.vectorize.io/) and its three foundational memory operations: `retain`, `recall`, and `reflect`.

---

## System Architecture: The Three Memory Primitives

God's Eye connects live news search via Tavily (`topic="news"`), structured extraction via Groq (`openai/gpt-oss-120b`), and persistent memory on **Vectorize Hindsight Cloud**:

```
                       ┌───────────────────────────┐
                       │     Target Domain URL     │
                       │   (e.g., https://linear.app)│
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │     FastAPI Pipeline      │
                       └──────┬─────────────┬──────┘
                              │             │
           1. Live Web News   │             │ 2. Memory Recall & Reflect
              via Tavily API  │             │    via Hindsight Cloud API
                              ▼             ▼
                       ┌───────────────────────────┐
                       │   Groq Reasoning Engine   │
                       │   (openai/gpt-oss-120b)   │
                       └─────────────┬─────────────┘
                                     │
           3. Retain new articles    │
              into Hindsight Cloud   ▼
                       ┌───────────────────────────┐
                       │   Executive Bento UI      │
                       │   (Glassmorphic HTML5)    │
                       └───────────────────────────┘
```

### 1. Ingestion with Real Publication Anchors (`retain`)
When God's Eye scans a brand, it extracts verified articles from Tavily. Instead of using the scan time as the timestamp, each article is anchored to its actual `published_date`:

```python
# Retaining real articles into Hindsight Cloud with verified publication dates
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

To avoid memory pollution, we maintain a local URL registry (`.scan_metadata.json`) per bank. On rescans, God's Eye diffs incoming articles against previously stored URLs and retains only newly discovered articles.

### 2. Multi-Strategy Retrieval (`recall`)
To evaluate current market signals against prior context, God's Eye queries the bank using Hindsight's parallel recall:

```python
# Querying historical observations from Hindsight Cloud
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/memories/recall",
    headers=headers,
    json={"query": f"What competitor price shifts and moves were observed for {brand_name}?"}
)
historical_nodes = res.json().get("results", [])
```

Behind this call, Hindsight coordinates semantic vector similarity, BM25 keyword matching, entity graph traversal, and temporal filtering.

### 3. Native Cross-Temporal Synthesis (`reflect`)
The core reasoning capability comes from Hindsight's native `POST /reflect` endpoint. Instead of requiring the LLM to manually compare raw text chunks, Hindsight reflects across world facts and observations directly:

```python
# Synthesizing trajectory natively in Hindsight Cloud
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/reflect",
    headers=headers,
    json={"query": f"Synthesize the competitive moves, pricing trajectory, and market shifts for {brand_name}."}
)
reflection = res.json().get("text", "")
```

---

## Real-World Verification: What Actually Happens Across Scans

Here is how the system behaves on a live target like Linear (`linear.app`):

* **Scan 1 (Baseline Anchor):** God's Eye discovers 5 verified news articles via Tavily covering database scaling, product workflow integration, and competitor benchmarks. It anchors these articles into Hindsight Cloud bank `godseye-bank-linear-app`. The system honestly reports: *"Scan #1: Baseline market anchor established. Retained 5 verified news articles."*
* **Scan 2 (Recall & Reflect):** Running a rescan diffs the URLs. Because all 5 URLs are already indexed, God's Eye retains 0 duplicate chunks. It queries Hindsight's `recall()` to pull the 5 stored memory nodes and executes `reflect()`. Hindsight synthesizes: *"Linear's pricing and competitive strategy throughout 2025 and 2026 reflect a transition toward value-added feature bundling, focusing on developer ergonomics while enterprise incumbents compete on heavy customization."*
* **Interactive Interrogation:** An executive can directly query the bank: *"What are competitor vulnerabilities based on recent moves?"* God's Eye queries Hindsight's reflection engine and returns actionable counter-measures grounded in the stored articles.

---

## What Didn't Work & Engineering Limitations

Building this architecture highlighted several practical dead ends:

1. **Hallucinated Memory Seeding:** In early iterations, we tried using an LLM to generate "sample historical events" for new brands. This was a mistake: the LLM hallucinated arbitrary numbers that contaminated Hindsight's reflection output. We removed all synthetic seeding and made Scan #1 an explicit, authentic baseline anchor.
2. **Duplicate Ingestion on Rescans:** Without URL deduplication, running a scan twice in a row stored identical articles twice. We added an explicit URL registry in `.scan_metadata.json` so rescans only retain genuinely new articles.
3. **Domain Collisions:** Initially, bank IDs used simple prefixes (`clean_domain.split('.')[0]`), which caused `mail.google.com` and `mail.com` to collide. Sanitizing the full domain (`clean_domain.replace('.', '-')`) resolved the collision.

---

## Conclusion

Stateless AI tools provide one-off snapshots; competitive strategy requires trajectory. By structuring memory around Hindsight's `retain`, `recall`, and `reflect` primitives, God's Eye turns ephemeral web search into persistent, compounding market intelligence.

* Explore the project implementation on GitHub.
* Learn more about memory architectures at [Vectorize agent memory](https://vectorize.io/what-is-agent-memory) and inspect the [Hindsight GitHub repo](https://github.com/vectorize-io/hindsight).

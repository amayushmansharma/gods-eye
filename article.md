# Why We Stopped Doing One-Shot Scrapes and Built an Agent That Never Forgets

Every product marketer and founder I know has the same Monday morning ritual: opening 15 browser tabs, checking competitor pricing pages, scanning press releases, and trying to remember what changed since last month.

When we set out to automate this, the initial prototype followed the standard 2024 AI recipe: give an LLM a web crawler, feed it competitor HTML snippets, and ask it for a summary.

It was fundamentally limited.

The agent could describe what Mercedes or Audi charged *that morning*. But it couldn’t tell us that Mercedes had increased sedan prices by 2.4% over the preceding weeks, or that Audi’s sudden discount incentive was an aggressive counter-move to our recent electric vehicle deliveries. A stateless agent has no sense of trajectory.

To solve this, we redesigned our pipeline around **God's Eye**—a competitive intelligence system powered by persistent [agent memory](https://vectorize.io/what-is-agent-memory). Here is how the system hangs together, why we chose [Hindsight](https://github.com/vectorize-io/hindsight), and the engineering lessons learned along the way.

---

## The Technical Flaw of Stateless RAG

When engineers attempt to give memory to an LLM, their default tool is traditional Retrieval-Augmented Generation (RAG): chunk historical scrape logs, dump them into a vector database with pgvector, and cosine-similarity search against the current query.

In real-world competitive monitoring, naive RAG falls apart:

1. **Temporal Blindness:** When a competitor changes their entry pricing from \$49 to \$79, cosine similarity rates both chunks as highly relevant because they share identical vocabulary. The LLM frequently hallucinates or blends the numbers because it cannot determine which fact supersedes the other.
2. **Entity Fragmentation:** Market data is an evolving graph of entities—manufacturers, sub-brands, executive hires, and price tiers—shifting states over time.
3. **Context Bloat:** Stuffing raw scrape logs into system prompts quickly exceeds practical latency budgets and degrades model attention.

We needed a dedicated memory layer that structures discrete world facts, tracks entity relationships, and provides temporal retrieval primitives. That led us to the [Hindsight documentation](https://hindsight.vectorize.io/) and its three foundational memory operations: `retain`, `recall`, and `reflect`.

---

## System Architecture: The Three Memory Primitives

God's Eye connects live web search via Tavily, fast extraction via Groq (`openai/gpt-oss-120b`), and persistent memory on **Vectorize Hindsight Cloud**:

```
                       ┌───────────────────────────┐
                       │     Target Domain URL     │
                       │   (e.g., https://bmw.in)  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │     FastAPI Pipeline      │
                       └──────┬─────────────┬──────┘
                              │             │
           1. Live Web Search │             │ 2. Memory Recall & Reflect
              via Tavily API  │             │    via Hindsight Cloud API
                              ▼             ▼
                       ┌───────────────────────────┐
                       │   Groq Reasoning Engine   │
                       │   (openai/gpt-oss-120b)   │
                       └─────────────┬─────────────┘
                                     │
           3. Retain new snapshot    │
              into Hindsight Cloud   ▼
                       ┌───────────────────────────┐
                       │   Executive Bento UI      │
                       │   (Glassmorphic HTML5)    │
                       └───────────────────────────┘
```

### 1. Ingestion with Temporal Anchors (`retain`)
When God's Eye scans a brand, it extracts core competitor movements and commits them to an isolated Hindsight memory bank (`godseye-bank-{slug}`) with explicit ISO-8601 timestamps:

```python
# Retaining market observations with timestamps into Hindsight Cloud
payload = {
    "items": [
        {
            "content": (
                f"God's Eye scanned {brand_name}. Tracked competitors: {rivals_list}. "
                f"Key shift: Mercedes-Benz published revised luxury pricing (+2.4%) while "
                f"Audi initiated aggressive lease incentives."
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": {"url": url, "brand": brand_name}
        }
    ]
}
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/memories",
    headers=headers,
    json=payload
)
```

Hindsight parses the payload into structured facts and links entities rather than storing raw text strings.

### 2. Multi-Strategy Retrieval (`recall`)
To evaluate what is currently happening against prior context, God's Eye queries the bank using Hindsight's parallel recall:

```python
# Querying historical observations from Hindsight Cloud
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/memories/recall",
    headers=headers,
    json={"query": f"What competitor price shifts and moves were observed for {brand_name}?"}
)
historical_nodes = res.json().get("results", [])
```

Behind the scenes, Hindsight coordinates semantic vector similarity, BM25 keyword matching, entity graph traversal, and temporal filtering.

### 3. Native Cross-Temporal Synthesis (`reflect`)
The biggest breakthrough came from adopting Hindsight's `POST /reflect` endpoint. Instead of having an LLM manually compare two JSON blobs, Hindsight reflects across world facts and mental models natively:

```python
# Synthesizing cross-temporal trajectory directly in Hindsight Cloud
res = requests.post(
    f"{HINDSIGHT_BASE_URL}/v1/default/banks/{bank_id}/reflect",
    headers=headers,
    json={"query": f"Summarize the competitive moves and pricing trajectory for {brand_name}."}
)
reflection = res.json().get("text", "")
```

---

## Real-World Behavior: From Snapshot to Trajectory

By seeding and tracking dated scans within Hindsight Cloud, the difference in agent output becomes clear:

* **Scan 1 (Baseline Ingestion):** The agent crawls the target and records current list prices. Without memory, it can only report: *"Mercedes-Benz and Audi operate in the luxury sedan and SUV space."*
* **Scan 2 (Temporal Delta):** When rescan data arrives, Hindsight recalls the prior baseline and correlates: *"Mercedes-Benz increased luxury sedan prices by 2.4%, while Audi introduced a ₹2.5 Lakh discount incentive on competing models."*
* **Interrogation (Memory In Action):** An executive can directly query the bank: *"What is Audi's biggest vulnerability right now?"* Hindsight's reflection engine correlates Audi's discounting with tariff pressure on imported EVs, delivering an actionable counter-strategy grounded in stored facts.

---

## What Didn't Work & Engineering Limitations

Building this architecture highlighted several practical dead ends:

1. **Raw Scrape Poisoning:** We initially tried piping full HTML directly into the memory layer. This resulted in context bloat—navigation menus, cookie banners, and footers polluted the memory graph. We had to filter data through Tavily and Groq to extract clean entity assertions before retaining them.
2. **Silent API Failures:** In early testing, network hiccups or invalid keys caused the memory layer to fail silently. We implemented persistent on-disk fallback storage so the system can gracefully queue observations when offline.
3. **Entity Disambiguation:** Automakers frequently use sub-brands (e.g. *Mercedes-EQ*, *Audi e-tron*, *BMW i*). Pure keyword matching split observations across different names; configuring entity resolution in Hindsight was necessary to tie sub-brand pricing back to the parent OEM.

---

## Conclusion

Stateless AI tools provide snapshots; competitive strategy requires trajectory. By structuring memory around Hindsight's `retain`, `recall`, and `reflect` primitives, God's Eye turns ephemeral web crawls into persistent, compounding market intelligence.

* Explore the project implementation on GitHub.
* Learn more about memory architectures at [Vectorize agent memory](https://vectorize.io/what-is-agent-memory) and inspect the [Hindsight GitHub repo](https://github.com/vectorize-io/hindsight).

# God's Eye 👁️
### Autonomous Market Intelligence Powered by Persistent Agent Memory

> **God's Eye** is a competitive intelligence pipeline that tracks competitor moves, pricing shifts, and industry announcements over time. Instead of relying on stateless web scrapes that forget past context, God's Eye integrates **[Vectorize Hindsight](https://github.com/vectorize-io/hindsight)** to retain market events, recall past observations, and reflect on multi-week strategic shifts.

---

## ⚡ The Problem: Stateless Crawls Forget Trajectory
Standard web scrapers and AI search tools take a one-shot snapshot. They tell you what a competitor charges today, but they have no memory of:
- What the competitor charged two weeks ago.
- When their marketing messaging shifted from "Performance" to "Electric Luxury".
- How pricing changes correlate with recent promotional announcements.

Without persistent memory, every new scan starts from zero.

---

## 🧠 Architecture & Hindsight Memory Primitives
God's Eye connects live web search via Tavily, fast LLM extraction via Groq (`openai/gpt-oss-120b`), and long-term memory via **Vectorize Hindsight Cloud**:

```
                       ┌───────────────────────────┐
                       │     User / Target URL     │
                       │   (e.g., https://bmw.in)  │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │     FastAPI Web Server    │
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

God's Eye utilizes all three core Hindsight operations:
1. **`retain()`**: Ingests new market events and competitor pricing moves with ISO-8601 timestamps into a dedicated memory bank (`POST /v1/default/banks/{bank_id}/memories`).
2. **`recall()`**: Retrieves relevant past competitor observations using multi-strategy parallel search (`POST /v1/default/banks/{bank_id}/memories/recall`).
3. **`reflect()`**: Synthesizes cross-temporal shifts across world facts and observations directly on Hindsight Cloud (`POST /v1/default/banks/{bank_id}/reflect`).

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
cd gods-eye
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your API keys:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

### 3. Launch God's Eye
```bash
python3 app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🎯 Verification & Demo Walkthrough
1. **Enter URL:** Input `https://www.bmw.in` in the glass pill command bar.
2. **Observe Pipeline Telemetry:** Real-time search fetches verified recent articles via Tavily, while the Hindsight bridge recalls stored memory nodes.
3. **Inspect Real Hindsight Reflection:** View the actual output from Hindsight Cloud's `/reflect` endpoint summarizing price changes and market moves.
4. **Interrogate the Memory Bank:** Use the bottom interrogation bar to ask specific questions (e.g. *"What is Audi's biggest vulnerability right now?"*) and receive answers grounded in Hindsight's retrieved memory nodes.

---

## 📚 Built With
- **Memory Engine:** [Vectorize Hindsight](https://hindsight.vectorize.io/) Cloud API
- **Inference:** [Groq](https://groq.com/) (`openai/gpt-oss-120b`)
- **Web Signals:** [Tavily Search API](https://tavily.com/)
- **Backend:** FastAPI, Python 3.9+
- **Frontend:** HTML5, Tailwind CSS, Lucide Icons, Glassmorphism

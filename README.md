# God's Eye 👁️
### Autonomous Market Intelligence Powered by Persistent Agent Memory

> **God's Eye** is an autonomous competitive intelligence system that monitors competitor moves, pricing shifts, and announcements across time. Unlike one-shot scrapers that forget historical context, God's Eye uses **[Vectorize Hindsight](https://github.com/vectorize-io/hindsight)** to retain market events, compute multi-month strategic trends, and synthesize executive counter-measures.

---

## ⚡ The Problem: Stateless Intelligence Fails
Standard competitive intelligence tools perform one-off web crawls. They can tell you what a competitor charges *today*, but they have zero memory of:
- What the competitor charged 30 days ago.
- When their messaging pivoted from "Performance" to "Enterprise".
- Which job postings from 2 months ago foreshadowed yesterday's product launch.

Without persistent memory, every scan starts from zero.

---

## 🧠 The Architecture: Memory as the Star
God's Eye leverages the **Hindsight Memory Engine** (`retain`, `recall`, `reflect`) across four parallel retrieval strategies:

```
                          ┌───────────────────────────┐
                          │     User / Target URL     │
                          │   (e.g., https://bmw.in)  │
                          └─────────────┬─────────────┘
                                        │
                                        ▼
                          ┌───────────────────────────┐
                          │   God's Eye Multi-Agent   │
                          │      Research Worker      │
                          └──────┬─────────────┬──────┘
                                 │             │
                Extracts Brand & │             │ Scrapes Recent News
             Discovers 2-4 Rivals│             │ & Price Movements
                                 ▼             ▼
                          ┌───────────────────────────┐
                          │  Hindsight Memory Bridge  │
                          └─────────────┬─────────────┘
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
  [ 1. RETAIN ]                  [ 2. RECALL ]                [ 3. REFLECT ]
  Commits current market         Multi-strategy retrieval     Synthesizes cross-temporal
  snapshot to persistent         (Semantic + Temporal + BM25  trends & flags strategic
  memory bank                    + Graph entities)            counter-measures
```

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
cd gods-eye
pip install fastapi uvicorn requests python-dotenv
```

### 2. Configure Environment (Optional for Hindsight Cloud)
Create a `.env` file:
```env
HINDSIGHT_API_KEY=your_hindsight_api_key_or_memhack99
HINDSIGHT_BASE_URL=https://api.hindsight.vectorize.io
GROQ_API_KEY=your_groq_api_key
```
*(God's Eye includes a local persistent fallback bank so you can test and demo instantly without API keys).*

### 3. Launch God's Eye
```bash
python3 app.py
```
Open **[http://localhost:8000](http://localhost:8000)** in your browser.

---

## 🎯 60-Second Demo Walkthrough
1. **Enter URL:** Input `https://www.bmw.in` in the glass pill command bar.
2. **Observe 30s Multi-Agent Telemetry:** Watch the real-time agent log stream as God's Eye profiles the brand, isolates rivals (Mercedes-Benz, Audi, Volvo), ingests the 7-day pulse, and recalls past observations.
3. **The 'Aha!' Moment:** View the **Hindsight Memory Radar** highlighting how Mercedes shifted messaging from 'Performance' to 'Electric Luxury' over 30 days and Audi reacted with ₹2.5L discounts.
4. **Actionable Playbook:** Review P0 and P1 executive actions to exploit the competitive window.

---

## 📚 Built With
- **Memory Layer:** [Vectorize Hindsight](https://hindsight.vectorize.io/)
- **Frontend:** Glassmorphism UI (Tailwind CSS, Lucide Icons, Custom Refraction Shaders)
- **Backend:** FastAPI, Python Async Engine

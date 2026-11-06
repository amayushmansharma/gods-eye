# God's Eye 👁️
### Autonomous Competitor Intelligence Powered by Persistent Agent Memory

> **God's Eye** is a competitive intelligence pipeline that tracks competitor moves, pricing shifts, and changelog releases over time. Instead of relying on stateless web scrapes that forget past context, God's Eye integrates **[Vectorize Hindsight](https://github.com/vectorize-io/hindsight)** to retain market events, recall past observations, and reflect on strategic shifts.

---

## ⚡ The Problem: Stateless Crawls Forget Trajectory
Standard web scrapers and AI search tools take a one-shot snapshot. They tell you what a competitor charges today, but they have no memory of:
- What the competitor charged two weeks ago.
- When their tier pricing or feature bundling changed.
- Which features were launched across recent changelog releases.

Without persistent memory, every new scan starts from zero.

---

## 🧠 Architecture & Hindsight Memory Primitives
God's Eye connects live web extraction via Tavily, deterministic Python snapshot diffing, fast LLM extraction via Groq (`openai/gpt-oss-120b`), and long-term memory via **Hindsight**:

```
                       ┌───────────────────────────┐
                       │   Competitor Watchlist    │
                       │   (Pricing & Changelog)   │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │     FastAPI Web Server    │
                       └──────┬─────────────┬──────┘
                              │             │
           1. Live Extraction │             │ 2. Memory Recall & Reflect
              via Tavily API  │             │    via Hindsight API
                              ▼             ▼
                       ┌───────────────────────────┐
                       │  Deterministic Python     │
                       │  Snapshot & Diff Engine   │
                       └─────────────┬─────────────┘
                                     │
           3. Retain verified diff   │
              into Hindsight Memory  ▼
                       ┌───────────────────────────┐
                       │    Executive Bento UI     │
                       │   (Glassmorphic HTML5)    │
                       └───────────────────────────┘
```

God's Eye utilizes all three core Hindsight operations:
1. **`retain()`**: Ingests new verified page diffs and market events with ISO-8601 timestamps into a dedicated memory bank (`POST /v1/default/banks/{bank_id}/memories`).
2. **`recall()`**: Retrieves relevant past competitor observations using multi-strategy search (`POST /v1/default/banks/{bank_id}/memories/recall`).
3. **`reflect()`**: Synthesizes cross-temporal shifts across observations directly via Hindsight (`POST /v1/default/banks/{bank_id}/reflect`).

---

## 🐳 Running Hindsight Locally

You can run self-hosted Hindsight locally using the official Docker container:

```bash
docker run -it --pull always --name hindsight --restart unless-stopped \
  --shm-size=1g --stop-timeout 75 \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_PROVIDER=groq \
  -e HINDSIGHT_API_LLM_API_KEY=YOUR_GROQ_API_KEY \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

Once running, point God's Eye to your local instance in `.env`:
```env
HINDSIGHT_BASE_URL=http://localhost:8888
# HINDSIGHT_API_KEY can be left blank or omitted for local unauthenticated instances
```

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
cd gods-eye
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your credentials:
```env
HINDSIGHT_BASE_URL=http://localhost:8888
HINDSIGHT_API_KEY=
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
1. **Health Telemetry:** Startup probe verifies live retain and recall against the Hindsight server. If unreachable, a visible warning banner displays the exact connection error.
2. **Watchlist Bento View:** Inspect monitored competitors (Linear, PostHog, Resend) across pricing and changelog endpoints.
3. **Trigger Scan:** Click **Run Scan Now** to fetch live pages, normalize content, execute deterministic diffs, and retain newly observed changes into Hindsight memory banks.
4. **Interrogate the Memory Bank:** Use the interrogation console to ask strategic questions (e.g. *"Compare Linear and PostHog pricing models based on recent memory"*) and receive answers grounded in Hindsight's native `reflect()` endpoint.

---

## 📚 Built With
- **Memory Engine:** [Hindsight](https://github.com/vectorize-io/hindsight) (Self-Hosted / Cloud)
- **Inference:** [Groq](https://groq.com/) (`openai/gpt-oss-120b`)
- **Web Signals:** [Tavily Extract API](https://tavily.com/)
- **Backend:** FastAPI, Python 3.9+
- **Frontend:** HTML5, Tailwind CSS, Lucide Icons, Glassmorphism

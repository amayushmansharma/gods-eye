# God's Eye — 3-Minute Demo Video Walkthrough Script

Use this script to record your screen using **QuickTime (`Cmd + Shift + 5`)**, **Loom**, or **OBS**.
Upload to YouTube as an Unlisted or Public video.

---

## 🎬 5 High-Performing YouTube Titles:
1. `Why AI Agents Need Memory: Building a Market Intelligence Pipeline with Hindsight`
2. `I Connected an AI Agent to Persistent Memory (Here's What Happened)`
3. `How We Built God's Eye: Tracking Competitor Trajectory with Hindsight & Groq`
4. `Stop Building Stateless AI: Giving Agents Long-Term Memory with Hindsight`
5. `The Problem with One-Shot Web Scrapers: Why Agent Memory Changes Everything`

---

## ⏱️ Video Script & Visual Cues (Total: ~3 Minutes)

### [00:00 – 00:30] PART 1: Quick Intro & The Problem
* **On Screen:** Start on the God's Eye landing page (`http://localhost:8000`). Show the clean dark eclipse background and glass pill search bar. Point to the top header showing `Hindsight Cloud: Connected`.
* **Narration:**
  > *"Hey everyone, I'm Ayushman. If you look at most AI agents today, they suffer from complete amnesia. You ask an agent to check a competitor's website, and it gives you a snapshot of what they sell today. But run it next week or next month, and it has zero memory of past pricing, past promotions, or messaging changes.*
  > 
  > *To fix this, we built **God's Eye**—a competitive intelligence pipeline powered by **Vectorize Hindsight** for persistent long-term memory."*

---

### [00:30 – 01:10] PART 2: Scan #1 — Establishing the Baseline Anchor
* **On Screen:** Click the `linear.app` preset chip in the search bar and hit Enter. Watch the pipeline log stream.
* **Narration:**
  > *"Let's test this with Linear (`linear.app`). Instead of a basic scraper, God's Eye runs an automated pipeline:*
  > * *First, it pulls verified news articles via the Tavily news search API, capturing real publication dates.*
  > * *Second, because this is our first time scanning Linear, it establishes a baseline memory bank in Hindsight Cloud.*
  > * *Third, it retains the actual full article contents into Hindsight Cloud so entity resolution has real substance to work on.*
  > * *Finally, Groq's 120B model structures the competitor landscape.*
  > 
  > *Notice the badge: **Scan #1 (Baseline Ingestion)**. It stored 5 verified articles into Hindsight Cloud."*

---

### [01:10 – 02:00] PART 3: Scan #2 — Real Memory Recall & Reflection
* **On Screen:** Click the blue **"Rescan (Test Memory Recall)"** button in the header.
* **Narration:**
  > *"Now, watch what happens when we run a rescan. I'll click 'Rescan'.*
  > 
  > *God's Eye checks our local URL registry and sees that all 5 articles are already indexed, so it retains zero duplicate memories.*
  > 
  > *Instead, it calls Hindsight's `recall()` to pull the stored memory nodes and executes Hindsight Cloud's native `reflect()` endpoint.*
  > 
  > *Look at the **Live Hindsight Cloud reflect() Output**: Hindsight synthesizes Linear's pricing and competitive strategy, noting how feature bundling and developer ergonomics differentiate it from enterprise rivals like Jira. That cross-temporal insight only exists because Hindsight remembered Scan #1."*

---

### [02:00 – 02:35] PART 4: Interrogating the Memory Bank
* **On Screen:** Scroll down to the **"Interrogate God's Eye Memory Bank"** section. Click the chip: *"What are our competitors' biggest vulnerabilities right now?"* and hit Interrogate.
* **Narration:**
  > *"We also built an interactive interrogation bar so an executive can question the memory bank directly. Watch: I'll ask 'What are our competitors' biggest vulnerabilities right now?'*
  > 
  > *God's Eye queries Hindsight's reflection engine, correlates competitor feature moves against stored memories, and returns an actionable executive counter-strategy in under two seconds."*

---

### [02:35 – 03:00] PART 5: Key Takeaway & Wrap-Up
* **On Screen:** Scroll back to the top overview.
* **Narration:**
  > *"My biggest lesson building this: stateless agents give you snapshots, but strategy requires trajectory. By using Hindsight's `retain`, `recall`, and `reflect` primitives, we turned a simple web crawler into an agent that actually compounds intelligence over time.*
  > 
  > *Check out the code in the GitHub repo below, read our technical article on Dev.to, and explore Vectorize Hindsight. Thanks for watching!"*

---

## 🎨 YouTube Thumbnail Prompt (For NanoBanana / Ideogram):
> `Cinematic futuristic executive AI intelligence room, high-contrast dark aesthetic, glowing holographic cybernetic eye looking at financial market graphs, sleek glassmorphism UI, minimal text "AI THAT NEVER FORGETS", 8k resolution, 16:9 aspect ratio.`

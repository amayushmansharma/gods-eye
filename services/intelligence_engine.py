import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient
from services.hindsight_service import HindsightService

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
hindsight = HindsightService()

SCAN_META_PATH = os.path.join(os.path.dirname(__file__), "..", ".scan_metadata.json")

def _load_all_scan_metadata() -> Dict[str, Any]:
    try:
        if os.path.exists(SCAN_META_PATH):
            with open(SCAN_META_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_all_scan_metadata(data: Dict[str, Any]):
    try:
        with open(SCAN_META_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Scan Metadata Save Error] {e}")

def get_scan_metadata(bank_id: str) -> Dict[str, Any]:
    all_meta = _load_all_scan_metadata()
    return all_meta.get(bank_id, {
        "scan_count": 0,
        "stored_urls": [],
        "first_scanned_at": None,
        "last_scanned_at": None
    })

def record_scan_metadata(bank_id: str, new_urls: List[str]) -> Dict[str, Any]:
    all_meta = _load_all_scan_metadata()
    meta = all_meta.get(bank_id, {
        "scan_count": 0,
        "stored_urls": [],
        "first_scanned_at": datetime.now(timezone.utc).isoformat(),
        "last_scanned_at": None
    })
    meta["scan_count"] += 1
    meta["last_scanned_at"] = datetime.now(timezone.utc).isoformat()
    # Add new URLs avoiding duplicates
    existing_urls = set(meta.get("stored_urls", []))
    for u in new_urls:
        if u and u not in existing_urls:
            meta.setdefault("stored_urls", []).append(u)
    all_meta[bank_id] = meta
    _save_all_scan_metadata(all_meta)
    return meta

def analyze_domain(url: str) -> Dict[str, Any]:
    """
    God's Eye Market Intelligence Pipeline:
    1. Ingests live news via Tavily with topic='news' and real published_date.
    2. Maintains explicit local scan count and URL registry per bank to prevent duplicate memories.
    3. Retains only NEW articles into Hindsight, anchored to their real publication dates.
    4. If scan > 1, recalls prior memories and executes Hindsight's reflect() endpoint.
    5. Structures competitor matrix via Groq 120B.
    """
    clean_domain = url.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    # Prevent domain collisions: mail.google.com -> godseye-bank-mail-google-com
    bank_id = f"godseye-bank-{clean_domain.replace('.', '-')}"
    brand_display_name = clean_domain.split(".")[0].capitalize() if "bmw" not in clean_domain else "BMW India"

    # 1. Fetch live web news signals via Tavily (topic='news' for real publish dates)
    search_query = f"{clean_domain} competitors pricing product announcements 2026"
    raw_articles = []
    is_live_search_success = False

    try:
        tavily_res = tavily_client.search(
            query=search_query,
            topic="news",
            search_depth="advanced",
            include_answer=True,
            max_results=5
        )
        results = tavily_res.get("results", [])
        if results:
            is_live_search_success = True
            for r in results:
                raw_articles.append({
                    "title": r.get("title", "Market Update"),
                    "url": r.get("url", f"https://{clean_domain}"),
                    "content": r.get("content", ""),
                    "source": r.get("url", "").split("/")[2] if "//" in r.get("url", "") else clean_domain,
                    "published_date": r.get("published_date")
                })
    except Exception as e:
        print(f"[Tavily News Warning] {e}")

    # Fallback only if Tavily completely fails
    if not raw_articles:
        raw_articles = [
            {
                "title": f"Market analysis and competitive review for {brand_display_name}",
                "url": f"https://{clean_domain}",
                "content": f"Product positioning, market moves, and competitor offerings for {clean_domain}.",
                "source": clean_domain,
                "published_date": None
            }
        ]

    # 2. Check explicit scan counter and diff URLs
    prior_meta = get_scan_metadata(bank_id)
    prior_scan_count = prior_meta["scan_count"]
    is_baseline_scan = (prior_scan_count == 0)
    current_scan_number = prior_scan_count + 1

    stored_urls = set(prior_meta.get("stored_urls", []))
    new_articles = [a for a in raw_articles if a["url"] not in stored_urls] if is_live_search_success else []

    # 3. Retain ONLY new verified articles into Hindsight (skip if already stored or placeholder)
    newly_retained_count = 0
    if is_live_search_success and new_articles:
        retain_res = hindsight.retain_rich_articles(bank_id, new_articles, brand_display_name)
        newly_retained_count = retain_res.get("items_count", len(new_articles))
        storage_backend = retain_res.get("storage_backend", "hindsight")
    else:
        storage_backend = "hindsight" if hindsight.is_configured() else "local_disk_fallback"

    # Update metadata registry
    updated_meta = record_scan_metadata(bank_id, [a["url"] for a in new_articles])

    # 4. Recall and Reflect from Hindsight
    if is_baseline_scan:
        recalled_nodes = []
        reflection_text = (
            f"Scan #1 (Baseline Anchor): Ingested {newly_retained_count} verified news articles into Hindsight "
            f"for bank '{bank_id}'. Stored with real publication dates to serve as historical benchmark."
        )
        cumulative_diffs = [
            f"Scan #1: Baseline market anchor established for {brand_display_name}.",
            f"Retained {newly_retained_count} verified news articles in Hindsight.",
            "Subsequent scans will diff new signals against this baseline."
        ]
    else:
        # Multi-scan active! Recall prior memories and run Hindsight reflect
        recall_data = hindsight.recall(bank_id, f"What competitor price shifts and moves were observed for {brand_display_name}?")
        recalled_nodes = recall_data.get("results", [])
        storage_backend = recall_data.get("storage_backend", storage_backend)

        reflect_data = hindsight.reflect(
            bank_id=bank_id,
            query=f"Synthesize the competitive moves, pricing trajectory, and market shifts for {brand_display_name} across all stored memories."
        )
        reflection_text = reflect_data.get("text", "Memory recall completed across stored scans.")
        
        diff_summary = f"{len(new_articles)} new articles detected since last scan." if len(new_articles) > 0 else "0 new articles (all live web URLs already retained in memory)."
        cumulative_diffs = [
            f"Scan #{current_scan_number}: {diff_summary}",
            f"Recalled {len(recalled_nodes)} historical memory nodes from Hindsight.",
            f"Cross-temporal reflect executed across {len(updated_meta.get('stored_urls', []))} total retained articles."
        ]

    # 5. Extract structured competitors using Groq 120B
    web_text_block = "\n\n".join([f"- {a['title']} ({a['source']}): {a['content'][:250]}" for a in raw_articles])
    
    prompt = f"""
You are the analytics parser for God's Eye.
Target Domain: {url}
Target Brand: {brand_display_name}

LIVE WEB ARTICLES (FROM TAVILY):
{web_text_block}

HINDSIGHT MEMORY CONTEXT:
{reflection_text}

TASK:
Extract and return a strictly valid JSON object with:
1. brand_name: Clean formal name (e.g. BMW India, Stripe, Linear)
2. industry: The exact industry segment
3. competitors: An array of 2 to 4 direct competitors identified in the web snippets or memory. For each competitor:
   - name: Company name
   - focus: Market focus / segment
   - recent_move: Concrete move identified in the web snippets or memory
   - price_trend: Pricing action (e.g. '+2.4%', 'Stable', 'Freemium', 'Discounted')
   - sentiment: General sentiment
   - threat_level: 'High', 'Medium', or 'Moderate'
4. strategic_recommendations: Array of 2 executive counter-measures:
   - priority: 'P0 Critical' or 'P1 Offensive'
   - action: Concrete business or marketing move
   - rationale: Grounded in competitor movements

Return ONLY valid JSON.
"""

    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You are a competitive intelligence parser. Output strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        parsed = json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[Groq Parsing Error] {e}")
        parsed = {
            "brand_name": brand_display_name,
            "industry": "Commercial Sector",
            "competitors": [
                {
                    "name": raw_articles[0].get("source", "Primary Rival"),
                    "focus": "Core Segment",
                    "recent_move": raw_articles[0].get("title", "Market move noted"),
                    "price_trend": "Monitored",
                    "sentiment": "Neutral",
                    "threat_level": "Medium"
                }
            ],
            "strategic_recommendations": [
                {
                    "priority": "P0 Critical",
                    "action": f"Monitor competitor pricing and value propositions for {brand_display_name}.",
                    "rationale": "Counter emerging market moves."
                }
            ]
        }

    # 6. Build verified news pulse with real URLs
    verified_news_pulse = []
    for art in raw_articles[:4]:
        pub_tag = f"Published: {art['published_date'][:16]}" if art.get("published_date") else "Recent News"
        verified_news_pulse.append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "tag": pub_tag,
            "snippet": art["content"][:140] + "..." if len(art["content"]) > 140 else art["content"]
        })

    return {
        "brand_name": parsed.get("brand_name", brand_display_name),
        "target_url": url,
        "industry": parsed.get("industry", "Global Sector"),
        "scanned_at": time.strftime("%B %d, %Y - %H:%M:%S UTC"),
        "is_baseline_scan": is_baseline_scan,
        "scan_iteration": current_scan_number,
        "new_articles_count": len(new_articles),
        "total_tracked_urls": len(updated_meta.get("stored_urls", [])),
        "competitors": parsed.get("competitors", []),
        "news_pulse": verified_news_pulse,
        "hindsight_bank": {
            "bank_id": bank_id,
            "storage_backend": storage_backend,
            "prior_memories_count": len(recalled_nodes),
            "newly_retained_items": newly_retained_count,
            "actual_memory_nodes": recalled_nodes,
            "hindsight_reflection_text": reflection_text,
            "cumulative_diffs": cumulative_diffs
        },
        "strategic_recommendations": parsed.get("strategic_recommendations", [])
    }

def query_memory_drilldown(bank_id: str, brand_name: str, question: str) -> Dict[str, Any]:
    """
    Direct Interrogation into Hindsight Memory:
    Calls Hindsight's reflect endpoint directly for true memory-grounded answers.
    """
    reflect_res = hindsight.reflect(bank_id=bank_id, query=question)
    hindsight_answer = reflect_res.get("text", "")

    prompt = f"""
You are God's Eye strategic advisor for {brand_name}.
A user asked: "{question}"

HINDSIGHT MEMORY ENGINE ANSWER (GROUNDED IN RETRIEVED FACTS):
{hindsight_answer}

INSTRUCTIONS:
Provide a clear, direct, 2-paragraph executive response that highlights what Hindsight's memory bank records show and recommends an actionable counter-move.
"""
    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        final_answer = response.choices[0].message.content
    except Exception:
        final_answer = hindsight_answer

    return {
        "question": question,
        "answer": final_answer,
        "bank_id": bank_id,
        "storage_backend": reflect_res.get("storage_backend", "hindsight_cloud")
    }

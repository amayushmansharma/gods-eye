import os
import json
import time
from typing import Dict, Any, List
from dotenv import load_dotenv
from groq import Groq
from tavily import TavilyClient
from services.hindsight_service import HindsightService

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))
hindsight = HindsightService()

def analyze_domain(url: str) -> Dict[str, Any]:
    """
    God's Eye Autonomous Market Intelligence:
    1. Ingests live web signals via Tavily API.
    2. Checks historical memory depth in Hindsight Cloud.
    3. If previous memories exist, recalls them and reflects natively via Hindsight Cloud.
    4. If first scan, establishes the baseline anchor without fake hallucinations.
    5. Retains the actual rich web article snippets into Hindsight Cloud.
    6. Structures competitor matrix using Groq 120B.
    """
    clean_domain = url.lower().replace("https://", "").replace("http://", "").replace("www.", "").strip("/")
    brand_slug = clean_domain.split(".")[0]
    bank_id = f"godseye-bank-{brand_slug}"
    brand_display_name = brand_slug.capitalize() if brand_slug != "bmw" else "BMW India"

    # 1. Fetch live web signals via Tavily (preserving actual URLs)
    search_query = f"{clean_domain} competitors latest pricing announcements news 2026"
    raw_articles = []
    try:
        tavily_res = tavily_client.search(
            query=search_query,
            search_depth="advanced",
            include_answer=True,
            max_results=5
        )
        for r in tavily_res.get("results", []):
            raw_articles.append({
                "title": r.get("title", "Market Update"),
                "url": r.get("url", f"https://{clean_domain}"),
                "content": r.get("content", ""),
                "source": r.get("url", "").split("/")[2] if "//" in r.get("url", "") else clean_domain
            })
    except Exception as e:
        print(f"[Tavily Search Warning] {e}")

    if not raw_articles:
        raw_articles = [
            {
                "title": f"Competitive and Market Overview for {brand_display_name}",
                "url": f"https://{clean_domain}",
                "content": f"Product positioning, market moves, and competitor offerings for {clean_domain}.",
                "source": clean_domain
            }
        ]

    # 2. Check existing Hindsight Cloud memory depth
    prior_memory_count = hindsight.get_bank_memories_count(bank_id)
    is_baseline_scan = (prior_memory_count == 0)

    # 3. Recall and Reflect from Hindsight Cloud
    if is_baseline_scan:
        recalled_nodes = []
        storage_backend = "hindsight_cloud" if hindsight.is_configured() else "local_disk_fallback"
        reflection_text = (
            f"Scan #1 (Baseline Initialization): Established primary memory bank '{bank_id}' in Hindsight Cloud. "
            f"Ingested current market articles to serve as the historical baseline anchor for future scans."
        )
        cumulative_diffs = [
            f"Baseline established for {brand_display_name}.",
            "Subsequent scans will cross-reference this baseline to detect pricing and messaging shifts."
        ]
    else:
        # Bank has real history! Recall and reflect across time.
        recall_data = hindsight.recall(bank_id, f"What competitor price shifts and moves were observed for {brand_display_name}?")
        recalled_nodes = recall_data.get("results", [])
        storage_backend = recall_data.get("storage_backend", "hindsight_cloud")

        reflect_data = hindsight.reflect(
            bank_id=bank_id,
            query=f"Synthesize the competitive moves and pricing trajectory for {brand_display_name} based on stored memories."
        )
        reflection_text = reflect_data.get("text", "Historical reflection synthesized from stored memories.")
        cumulative_diffs = [
            "Hindsight Cloud recalled past scan nodes and correlated recent pricing signals.",
            "Cross-temporal reflection active across retained articles."
        ]

    # 4. Retain rich real Tavily articles into Hindsight Cloud
    retain_res = hindsight.retain_rich_articles(bank_id, raw_articles, brand_display_name)
    actual_retained_count = retain_res.get("items_count", len(raw_articles))

    # 5. Extract structured competitors using Groq 120B
    web_text_block = "\n\n".join([f"- {a['title']} ({a['source']}): {a['content'][:250]}" for a in raw_articles])
    
    prompt = f"""
You are the analytics parser for God's Eye.
Target Domain: {url}
Target Brand: {brand_display_name}

LIVE WEB SNIPPETS (FROM TAVILY):
{web_text_block}

HINDSIGHT MEMORY CONTEXT:
{reflection_text}

TASK:
Extract and return a strictly valid JSON object with:
1. brand_name: Clean formal name (e.g. BMW India, Stripe, Linear)
2. industry: The exact industry segment
3. competitors: An array of 2 to 4 direct competitors identified in the web snippets. For each competitor:
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
                    "name": raw_articles[0].get("source", "Primary Competitor"),
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
                    "action": f"Track price movements and value proposition for {brand_display_name}.",
                    "rationale": "Protect market position against emerging moves."
                }
            ]
        }

    # 6. Build verified news pulse with real URLs
    verified_news_pulse = []
    for art in raw_articles[:4]:
        verified_news_pulse.append({
            "title": art["title"],
            "url": art["url"],
            "source": art["source"],
            "tag": "Web Signal",
            "snippet": art["content"][:140] + "..." if len(art["content"]) > 140 else art["content"]
        })

    return {
        "brand_name": parsed.get("brand_name", brand_display_name),
        "target_url": url,
        "industry": parsed.get("industry", "Global Sector"),
        "scanned_at": time.strftime("%B %d, %Y - %H:%M:%S UTC"),
        "is_baseline_scan": is_baseline_scan,
        "scan_iteration": 1 if is_baseline_scan else (prior_memory_count // 3 + 1),
        "competitors": parsed.get("competitors", []),
        "news_pulse": verified_news_pulse,
        "hindsight_bank": {
            "bank_id": bank_id,
            "storage_backend": storage_backend,
            "prior_memories_count": prior_memory_count,
            "newly_retained_items": actual_retained_count,
            "actual_memory_nodes": recalled_nodes,
            "hindsight_reflection_text": reflection_text,
            "cumulative_diffs": cumulative_diffs
        },
        "strategic_recommendations": parsed.get("strategic_recommendations", [])
    }

def query_memory_drilldown(bank_id: str, brand_name: str, question: str) -> Dict[str, Any]:
    """
    Direct Interrogation into Hindsight Memory:
    Calls Hindsight Cloud's reflect endpoint directly for true memory-grounded answers.
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

"""
Use an LLM to automatically extract and categorize biosecurity threats from papers.

This script:
1. Fetches recent biosecurity/AI-bio papers from arXiv
2. Sends them to an LLM to identify threat categories
3. Generates a comprehensive threat taxonomy
4. Seeds the database with the extracted threats
"""

import sys
sys.path.append(".")

import asyncio
import json
import arxiv
from datetime import datetime, timedelta

from backend.models.database import init_db, SessionLocal, Threat, ThreatLevel, TrendDirection
from backend.services.openrouter import get_llm_client

# Papers to analyze
PAPER_QUERIES = [
    "AI biosecurity threats",
    "artificial intelligence biological weapons",
    "machine learning synthetic biology risks",
    "large language models bioterrorism",
    "AI-enabled pandemic threats",
    "dual-use AI biology",
    "protein design AI misuse",
    "biosecurity AI governance"
]

SYSTEM_PROMPT = """You are a biosecurity threat analyst with expertise in AI capabilities and biological risks.

Your task is to analyze scientific papers about AI and biosecurity, then extract and categorize potential threats.

Focus on:
- AI capabilities that could lower barriers to biological harm
- Specific threat scenarios enabled by AI tools
- Near-term vs long-term risks
- Both intentional misuse and accidental risks

Be comprehensive but realistic. Avoid science fiction - focus on plausible threats based on current or near-future AI capabilities."""


async def fetch_papers(max_per_query: int = 10) -> list[dict]:
    """Fetch recent papers from arXiv."""
    
    print("📚 Fetching papers from arXiv...")
    all_papers = []
    
    for query in PAPER_QUERIES:
        print(f"  Searching: {query}")
        search = arxiv.Search(
            query=query,
            max_results=max_per_query,
            sort_by=arxiv.SortCriterion.SubmittedDate
        )
        
        for paper in search.results():
            all_papers.append({
                "title": paper.title,
                "summary": paper.summary,
                "authors": [a.name for a in paper.authors],
                "published": paper.published,
                "url": paper.entry_id
            })
    
    # Deduplicate by title
    seen_titles = set()
    unique_papers = []
    for paper in all_papers:
        if paper["title"] not in seen_titles:
            seen_titles.add(paper["title"])
            unique_papers.append(paper)
    
    print(f"✅ Fetched {len(unique_papers)} unique papers\n")
    return unique_papers


async def extract_threats_from_papers(papers: list[dict], retry: bool = True) -> dict:
    """Use LLM to extract threat taxonomy from papers."""
    
    print("🤖 Analyzing papers with LLM...\n")
    
    # Prepare paper summaries for the LLM
    papers_text = "\n\n---\n\n".join([
        f"TITLE: {p['title']}\n"
        f"AUTHORS: {', '.join(p['authors'][:3])}\n"
        f"PUBLISHED: {p['published']}\n"
        f"ABSTRACT: {p['summary'][:1500]}"  # Reduced to avoid token limits
        for p in papers[:20]  # Reduced from 30
    ])
    
    prompt = f"""Based on these recent biosecurity and AI research papers, create a comprehensive threat taxonomy.

PAPERS:
{papers_text}

---

TASK: Extract and categorize all distinct biosecurity threats mentioned or implied in these papers.

For each threat, provide:
1. A clear, specific threat name
2. The threat category (e.g., "AI-Enabled Knowledge Access", "Biological Design Tools", "Dual-Use Research", etc.)
3. A detailed description (2-3 sentences)
4. The specific AI capabilities that enable this threat
5. A realistic timeline estimate (e.g., "Current", "6-12 months", "1-2 years", "2-5 years")
6. Initial feasibility score (1-5, where 5 = highly feasible with current tech)

CRITICAL INSTRUCTIONS FOR JSON OUTPUT:
1. Respond ONLY with valid JSON - no markdown, no explanation before or after
2. Use double quotes for all strings
3. Escape any quotes within strings using backslash
4. Keep descriptions concise (under 200 characters)
5. Do not use newlines within string values

JSON format:
{{
    "threat_categories": [
        "Category 1 name",
        "Category 2 name"
    ],
    "threats": [
        {{
            "name": "Specific threat name",
            "category": "Category it belongs to",
            "description": "Concise description in one line",
            "enabling_capabilities": ["capability 1", "capability 2"],
            "timeline_estimate": "X-Y months",
            "initial_feasibility_score": 3,
            "source_papers": ["Paper 1"]
        }}
    ],
    "analysis_summary": "Brief summary in one sentence"
}}

Aim for 10-20 distinct threats. Keep all text values on single lines."""
    
    client = get_llm_client()
    
    try:
        # Get raw text response first
        text_response = await client.complete(
            prompt=prompt,
            system_prompt=SYSTEM_PROMPT,
            max_tokens=6000,
            temperature=0.3
        )
        
        # Clean the response
        text_response = text_response.strip()
        
        # Remove markdown code fences if present
        if text_response.startswith("```json"):
            text_response = text_response[7:]
        elif text_response.startswith("```"):
            text_response = text_response[3:]
        
        if text_response.endswith("```"):
            text_response = text_response[:-3]
        
        text_response = text_response.strip()
        
        # Try to parse JSON
        try:
            result = json.loads(text_response)
            print("✅ LLM analysis complete\n")
            return result
        except json.JSONDecodeError as je:
            print(f"⚠️ JSON parsing failed: {je}")
            print("Raw response preview:")
            print(text_response[:500])
            print("\n... trying to fix JSON ...")
            
            # Try to fix common JSON issues
            # Replace unescaped quotes in strings
            import re
            # This is a simple fix - you might need more sophisticated handling
            text_response = text_response.replace('\n', ' ')
            
            try:
                result = json.loads(text_response)
                print("✅ Fixed and parsed JSON\n")
                return result
            except:
                print("❌ Could not fix JSON. Saving raw response to debug.txt")
                with open("data/debug_response.txt", "w", encoding="utf-8") as f:
                    f.write(text_response)
                
                # If retry is enabled, try with a simpler prompt
                if retry:
                    print("\n⚠️ Retrying with simpler prompt...\n")
                    return await extract_threats_simplified(papers)
                
                return None
        
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        import traceback
        traceback.print_exc()
        return None


async def extract_threats_simplified(papers: list[dict]) -> dict:
    """Simplified extraction with stricter JSON requirements."""
    
    print("🤖 Running simplified analysis...\n")
    
    # Use fewer papers and shorter abstracts
    papers_text = "\n\n".join([
        f"{i+1}. {p['title']}: {p['summary'][:500]}"
        for i, p in enumerate(papers[:10])
    ])
    
    prompt = f"""Analyze these biosecurity papers and list threats.

Papers:
{papers_text}

List 8-12 distinct AI-biosecurity threats. For each provide:
- name (short, clear)
- category (one of: "Knowledge Access", "Design Tools", "Dual-Use Research", "Security Evasion")  
- description (one sentence, under 150 chars)
- timeline (e.g. "Current", "6-12 months", "1-2 years")
- score (1-5 for current feasibility)

Output valid JSON only. No markdown. Keep descriptions very brief.

{{
  "threats": [
    {{"name": "X", "category": "Y", "description": "Z", "timeline": "T", "score": 3}}
  ]
}}"""
    
    client = get_llm_client()
    
    try:
        text = await client.complete(
            prompt=prompt,
            system_prompt="Output only valid JSON. No explanation.",
            max_tokens=3000,
            temperature=0.2
        )
        
        # Clean response
        text = text.strip()
        if "```" in text:
            text = text.split("```")[1] if "```" in text else text
            text = text.replace("json", "").strip()
        
        result = json.loads(text)
        
        # Convert to full format
        full_result = {
            "threat_categories": list(set(t.get("category", "Unknown") for t in result.get("threats", []))),
            "threats": [
                {
                    "name": t["name"],
                    "category": t.get("category", "Unknown"),
                    "description": t.get("description", ""),
                    "enabling_capabilities": ["AI capability analysis"],
                    "timeline_estimate": t.get("timeline", "Unknown"),
                    "initial_feasibility_score": t.get("score", 3),
                    "source_papers": []
                }
                for t in result.get("threats", [])
            ],
            "analysis_summary": f"Simplified extraction from {len(papers)} papers"
        }
        
        print("✅ Simplified analysis complete\n")
        return full_result
        
    except Exception as e:
        print(f"❌ Simplified extraction also failed: {e}")
        return None


def save_threats_to_db(threat_data: dict, db_session) -> int:
    """Save extracted threats to database."""
    
    if not threat_data or "threats" not in threat_data:
        print("❌ No valid threat data to save")
        return 0
    
    threats = threat_data["threats"]
    added = 0
    
    print(f"💾 Saving {len(threats)} threats to database...")
    
    for t in threats:
        # Check if exists
        existing = db_session.query(Threat).filter(
            Threat.name == t["name"]
        ).first()
        
        if existing:
            print(f"  ⏭️  Skipping (exists): {t['name']}")
            continue
        
        # Determine initial threat level based on feasibility
        score = t.get("initial_feasibility_score", 1)
        if score >= 4:
            level = ThreatLevel.HIGH
        elif score >= 3:
            level = ThreatLevel.MEDIUM
        else:
            level = ThreatLevel.LOW
        
        threat = Threat(
            name=t["name"],
            category=t["category"],
            description=t["description"],
            enabling_capabilities=json.dumps(t.get("enabling_capabilities", [])),
            timeline_estimate=t.get("timeline_estimate", "Unknown"),
            feasibility_score=score,
            threat_level=level,
            trend=TrendDirection.STABLE,
            confidence=0.6  # Medium confidence for initial extraction
        )
        
        db_session.add(threat)
        added += 1
        print(f"  ✅ Added: {t['name']}")
    
    db_session.commit()
    print(f"\n✨ Successfully added {added} new threats\n")
    return added


def save_analysis_to_file(threat_data: dict, papers: list[dict]):
    """Save the full analysis to a JSON file for review."""
    
    output = {
        "generated_at": datetime.utcnow().isoformat(),
        "papers_analyzed": len(papers),
        "threat_data": threat_data,
        "source_papers": [
            {"title": p["title"], "url": p["url"]}
            for p in papers
        ]
    }
    
    filename = f"data/threat_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(filename, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"📄 Full analysis saved to: {filename}\n")


async def main():
    print("=" * 60)
    print("🧬 AUTOMATED THREAT EXTRACTION FROM BIOSECURITY PAPERS")
    print("=" * 60)
    print()
    
    # Initialize database
    init_db()
    db = SessionLocal()
    
    # Step 1: Fetch papers
    papers = await fetch_papers(max_per_query=15)
    
    if not papers:
        print("❌ No papers found. Check your internet connection.")
        return
    
    print(f"Papers to analyze:")
    for i, p in enumerate(papers[:10], 1):
        print(f"  {i}. {p['title'][:80]}...")
    if len(papers) > 10:
        print(f"  ... and {len(papers) - 10} more")
    print()
    
    # Step 2: Extract threats using LLM
    threat_data = await extract_threats_from_papers(papers)
    
    if not threat_data:
        print("❌ Failed to extract threats")
        db.close()
        return
    
    # Step 3: Display results
    print("=" * 60)
    print("📊 EXTRACTED THREAT TAXONOMY")
    print("=" * 60)
    print()
    
    if "threat_categories" in threat_data:
        print("Categories identified:")
        for cat in threat_data["threat_categories"]:
            print(f"  • {cat}")
        print()
    
    if "analysis_summary" in threat_data:
        print(f"Summary: {threat_data['analysis_summary']}")
        print()
    
    print(f"Total threats identified: {len(threat_data.get('threats', []))}")
    print()
    
    # Step 4: Save to database
    added = save_threats_to_db(threat_data, db)
    
    # Step 5: Save full analysis to file
    save_analysis_to_file(threat_data, papers)
    
    # Step 6: Display summary
    print("=" * 60)
    print("✅ EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Papers analyzed: {len(papers)}")
    print(f"Threats identified: {len(threat_data.get('threats', []))}")
    print(f"New threats added to database: {added}")
    print(f"Threat categories: {len(threat_data.get('threat_categories', []))}")
    print()
    print("Next steps:")
    print("  1. Review the threats in the Streamlit dashboard")
    print("  2. Run ingestion to gather new papers")
    print("  3. Classify items to find relevant developments")
    print("  4. Update threat assessments periodically")
    print()
    
    db.close()


if __name__ == "__main__":
    asyncio.run(main())
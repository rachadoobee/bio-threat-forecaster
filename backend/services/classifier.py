from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.openrouter import get_llm_client
from backend.models.database import SourceItem, Threat

CLASSIFICATION_SYSTEM_PROMPT = """You are a biosecurity threat analyst with expertise in AI capabilities and biological risks.

Your task is to analyze content and determine:
1. Whether the AI capabilities relate to any biosecurity threat categories
2. The potential impact on threat timelines
3. Specific capabilities that are advancing that will have an affect on the listed biosecurity threats

Be comprehensive but realistic. Avoid science fiction - focus on plausible threats based on current or near-future AI capabilities. You can flag items that will have biosecurity relevance."""


def build_classification_prompt(item: SourceItem, threats: list[Threat]) -> str:
    threat_list = "\n".join([
        f"- \"{t.name}\" (Category: {t.category})"
        for t in threats
    ])
    
    return f"""Analyze this content for biosecurity relevance:

TITLE: {item.title}

CONTENT:
{item.content or "No content available"}

AUTHORS: {item.authors or "Unknown"}
PUBLISHED: {item.published_date or "Unknown"}

---

THREAT CATEGORIES TO CHECK (use EXACT names from this list):
{threat_list}

---

IMPORTANT: For "related_threat_names", you MUST use the EXACT threat names from the list above (copy them exactly as shown in quotes).

Respond with JSON:
{{
    "is_relevant": true/false,
    "relevance_score": 0.0-1.0,
    "impact_level": "none" | "incremental" | "significant" | "step_change",
    "related_threat_names": ["exact threat name 1", "exact threat name 2"],
    "capabilities_identified": ["capability 1", "capability 2"],
    "reasoning": "Brief explanation of relevance and impact"
}}"""


async def classify_item(db: Session, item: SourceItem) -> dict:
    """Classify a source item for biosecurity relevance."""
    
    # Get all active threats
    threats = db.query(Threat).all()
    if not threats:
        return {"error": "No threats defined in taxonomy"}
    
    # Build prompt and call LLM
    client = get_llm_client()
    prompt = build_classification_prompt(item, threats)
    
    result = await client.complete_json(prompt, CLASSIFICATION_SYSTEM_PROMPT)
    
    # Update item with classification
    item.is_relevant = 1 if result.get("is_relevant") else 0
    item.relevance_score = result.get("relevance_score", 0)
    item.impact_level = result.get("impact_level", "none")
    item.classification_reasoning = result.get("reasoning", "")
    item.capabilities_identified = str(result.get("capabilities_identified", []))
    item.classified_at = datetime.utcnow()
    
    # Link to related threats (fuzzy matching)
    if result.get("related_threat_names"):
        for tname in result["related_threat_names"]:
            # Try exact match first
            threat = db.query(Threat).filter(Threat.name == tname).first()
            
            # If no exact match, try fuzzy matching
            if not threat:
                # Try partial match (case-insensitive)
                threat = db.query(Threat).filter(
                    Threat.name.ilike(f"%{tname}%")
                ).first()
            
            if threat and threat not in item.related_threats:
                item.related_threats.append(threat)
                print(f"  🔗 Linked to threat: {threat.name}")
    
    db.commit()
    db.refresh(item)
    
    return result


async def classify_unprocessed(db: Session, limit: int = 10) -> list[dict]:
    """Classify all unprocessed items."""
    
    items = db.query(SourceItem).filter(
        SourceItem.classified_at.is_(None)
    ).limit(limit).all()
    
    results = []
    for item in items:
        try:
            res = await classify_item(db, item)
            results.append({"item_id": item.id, "title": item.title, "result": res})
        except Exception as e:
            results.append({"item_id": item.id, "title": item.title, "error": str(e)})
    
    return results
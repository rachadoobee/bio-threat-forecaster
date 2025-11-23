from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.services.openrouter import get_llm_client
from backend.models.database import SourceItem, Threat

CLASSIFICATION_SYSTEM_PROMPT = """You are an AI and bio-security analyst expert assessing scientific papers and announcements for emerging AI capabilities and their relevance to future biological threats.

Your task is to analyze content and determine:
1. Whether it relates to any biosecurity threat categories
2. The potential impact on threat timelines
3. Specific capabilities that are advancing

Be precise and conservative. You can flag items that have may have biosecurity relevance."""


def build_classification_prompt(item: SourceItem, threats: list[Threat]) -> str:
    threat_list = "\n".join([
        f"- {t.name} ({t.category}): {t.description}"
        for t in threats
    ])
    
    return f"""Analyze this content for biosecurity relevance:

TITLE: {item.title}

CONTENT:
{item.content or "No content available"}

AUTHORS: {item.authors or "Unknown"}
PUBLISHED: {item.published_date or "Unknown"}

---

THREAT CATEGORIES TO CHECK:
{threat_list}

---

Respond with JSON:
{{
    "is_relevant": true/false,
    "relevance_score": 0.0-1.0,
    "impact_level": "none" | "incremental" | "significant" | "step_change",
    "related_threat_names": ["threat name 1", "threat name 2"],
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
    
    # Link to related threats
    if result.get("related_threat_names"):
        for tname in result["related_threat_names"]:
            threat = db.query(Threat).filter(Threat.name == tname).first()
            if threat and threat not in item.related_threats:
                item.related_threats.append(threat)
    
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
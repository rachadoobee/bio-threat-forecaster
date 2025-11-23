from datetime import datetime
from sqlalchemy.orm import Session

from backend.models.database import Threat, SourceItem, ThreatUpdate, ThreatLevel, TrendDirection
from backend.services.openrouter import get_llm_client

UPDATE_SYSTEM_PROMPT = """You are a biosecurity threat analyst. Based on recent developments, you assess how threat levels and timelines should be updated.

Be conservative but responsive to genuine capability advances. Consider:
- Does this represent real progress or incremental research?
- How much does this lower barriers for malicious actors?
- What timeline implications does this have?"""


def build_update_prompt(threat: Threat, recent_items: list[SourceItem]) -> str:
    items_text = "\n\n".join([
        f"TITLE: {i.title}\nIMPACT: {i.impact_level}\nCAPABILITIES: {i.capabilities_identified}\nREASONING: {i.classification_reasoning}"
        for i in recent_items
    ])
    
    return f"""Assess whether this threat's status should be updated based on recent developments.

THREAT: {threat.name}
CATEGORY: {threat.category}
DESCRIPTION: {threat.description}
ENABLING CAPABILITIES: {threat.enabling_capabilities}

CURRENT STATUS:
- Feasibility Score: {threat.feasibility_score}/5
- Threat Level: {threat.threat_level.value if threat.threat_level else 'low'}
- Trend: {threat.trend.value if threat.trend else 'stable'}
- Timeline Estimate: {threat.timeline_estimate}

RECENT RELEVANT DEVELOPMENTS:
{items_text}

---

Respond with JSON:
{{
    "should_update": true/false,
    "new_feasibility_score": 1.0-5.0,
    "new_threat_level": "low" | "medium" | "high" | "critical",
    "new_trend": "stable" | "increasing" | "rapidly_increasing" | "decreasing",
    "new_timeline_estimate": "e.g., 6-12 months",
    "confidence": 0.0-1.0,
    "reasoning": "Explanation for the assessment"
}}"""


async def update_threat_assessment(db: Session, threat_id: int) -> dict:
    """Update a threat's assessment based on recent relevant items."""
    
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        return {"error": "Threat not found"}
    
    # Get recent relevant items (last 30 days, relevant only)
    recent_items = [
        item for item in threat.source_items
        if item.is_relevant and item.classified_at
    ][-10:]  # Last 10 relevant items
    
    if not recent_items:
        return {"message": "No recent relevant items to assess"}
    
    client = get_llm_client()
    prompt = build_update_prompt(threat, recent_items)
    result = await client.complete_json(prompt, UPDATE_SYSTEM_PROMPT)
    
    if not result.get("should_update"):
        return {"message": "No update needed", "reasoning": result.get("reasoning")}
    
    # Log the update
    update_log = ThreatUpdate(
        threat_id=threat.id,
        previous_score=threat.feasibility_score,
        new_score=result.get("new_feasibility_score"),
        previous_level=threat.threat_level.value if threat.threat_level else None,
        new_level=result.get("new_threat_level"),
        reasoning=result.get("reasoning")
    )
    db.add(update_log)
    
    # Apply updates
    threat.feasibility_score = result.get("new_feasibility_score", threat.feasibility_score)
    threat.threat_level = ThreatLevel(result.get("new_threat_level", "low"))
    threat.trend = TrendDirection(result.get("new_trend", "stable"))
    threat.timeline_estimate = result.get("new_timeline_estimate", threat.timeline_estimate)
    threat.confidence = result.get("confidence", threat.confidence)
    threat.last_updated = datetime.utcnow()
    
    db.commit()
    db.refresh(threat)
    
    return {
        "updated": True,
        "threat": threat.name,
        "new_level": threat.threat_level.value,
        "new_score": threat.feasibility_score,
        "reasoning": result.get("reasoning")
    }


async def update_all_threats(db: Session) -> list[dict]:
    """Update assessments for all threats."""
    
    threats = db.query(Threat).all()
    results = []
    
    for threat in threats:
        try:
            res = await update_threat_assessment(db, threat.id)
            results.append({"threat": threat.name, "result": res})
        except Exception as e:
            results.append({"threat": threat.name, "error": str(e)})
    
    return results


def get_threat_dashboard(db: Session) -> list[dict]:
    """Get current status of all threats for dashboard."""
    
    threats = db.query(Threat).all()
    
    return [
        {
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "description": t.description,
            "feasibility_score": t.feasibility_score,
            "threat_level": t.threat_level.value if t.threat_level else "low",
            "trend": t.trend.value if t.trend else "stable",
            "timeline_estimate": t.timeline_estimate,
            "confidence": t.confidence,
            "last_updated": t.last_updated.isoformat() if t.last_updated else None,
            "recent_items_count": len([i for i in t.source_items if i.is_relevant])
        }
        for t in threats
    ]
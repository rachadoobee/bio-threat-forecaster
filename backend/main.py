from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json

from config import get_settings
from backend.models.database import init_db, get_db, Threat, DataSource, SourceItem, ThreatLevel, TrendDirection
from backend.services.ingestion import run_ingestion, add_manual_item
from backend.services.classifier import classify_item, classify_unprocessed
from backend.services.threat_tracker import update_threat_assessment, update_all_threats, get_threat_dashboard

settings = get_settings()
app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()


# ============ Pydantic Schemas ============

class ThreatCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    enabling_capabilities: Optional[list[str]] = None
    timeline_estimate: Optional[str] = None

class ThreatResponse(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str]
    feasibility_score: float
    threat_level: str
    trend: str
    timeline_estimate: Optional[str]
    confidence: float

class SourceCreate(BaseModel):
    name: str
    source_type: str  # "rss", "arxiv", "manual"
    url: Optional[str] = None
    category: Optional[str] = None

class ManualItemCreate(BaseModel):
    title: str
    content: str
    url: Optional[str] = None
    authors: Optional[str] = None


# ============ Threat Endpoints ============

@app.get("/api/threats")
async def list_threats(db: Session = Depends(get_db)):
    """Get all threats with current status."""
    return get_threat_dashboard(db)

@app.post("/api/threats")
async def create_threat(threat: ThreatCreate, db: Session = Depends(get_db)):
    """Create a new threat category."""
    db_threat = Threat(
        name=threat.name,
        category=threat.category,
        description=threat.description,
        enabling_capabilities=json.dumps(threat.enabling_capabilities) if threat.enabling_capabilities else None,
        timeline_estimate=threat.timeline_estimate,
        feasibility_score=1.0,
        threat_level=ThreatLevel.LOW,
        trend=TrendDirection.STABLE,
        confidence=0.5
    )
    db.add(db_threat)
    db.commit()
    db.refresh(db_threat)
    return {"id": db_threat.id, "name": db_threat.name}

@app.get("/api/threats/{threat_id}")
async def get_threat(threat_id: int, db: Session = Depends(get_db)):
    """Get a specific threat with related items."""
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    if not threat:
        raise HTTPException(status_code=404, detail="Threat not found")
    
    # Get all related items (relevant only)
    related_items = [
        {
            "id": i.id,
            "title": i.title,
            "url": i.url,
            "authors": i.authors,
            "published_date": i.published_date.isoformat() if i.published_date else None,
            "impact_level": i.impact_level,
            "relevance_score": i.relevance_score,
            "classification_reasoning": i.classification_reasoning,
            "capabilities_identified": i.capabilities_identified,
            "fetched_at": i.fetched_at.isoformat() if i.fetched_at else None
        }
        for i in threat.source_items if i.is_relevant
    ]
    
    return {
        "id": threat.id,
        "name": threat.name,
        "category": threat.category,
        "description": threat.description,
        "feasibility_score": threat.feasibility_score,
        "threat_level": threat.threat_level.value if threat.threat_level else "low",
        "trend": threat.trend.value if threat.trend else "stable",
        "timeline_estimate": threat.timeline_estimate,
        "confidence": threat.confidence,
        "enabling_capabilities": json.loads(threat.enabling_capabilities) if threat.enabling_capabilities else [],
        "related_papers": sorted(related_items, key=lambda x: x.get("relevance_score", 0), reverse=True),
        "related_papers_count": len(related_items)
    }

@app.post("/api/threats/{threat_id}/update")
async def trigger_threat_update(threat_id: int, db: Session = Depends(get_db)):
    """Trigger an assessment update for a specific threat."""
    return await update_threat_assessment(db, threat_id)

@app.post("/api/threats/update-all")
async def trigger_all_updates(db: Session = Depends(get_db)):
    """Update assessments for all threats."""
    return await update_all_threats(db)


# ============ Source Endpoints ============

@app.get("/api/sources")
async def list_sources(db: Session = Depends(get_db)):
    """List all data sources."""
    sources = db.query(DataSource).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "type": s.source_type,
            "url": s.url,
            "is_active": bool(s.is_active),
            "last_fetched": s.last_fetched.isoformat() if s.last_fetched else None
        }
        for s in sources
    ]

@app.post("/api/sources")
async def create_source(source: SourceCreate, db: Session = Depends(get_db)):
    """Add a new data source."""
    db_source = DataSource(
        name=source.name,
        source_type=source.source_type,
        url=source.url,
        category=source.category
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return {"id": db_source.id, "name": db_source.name}


# ============ Ingestion Endpoints ============

@app.post("/api/ingest")
async def trigger_ingestion(db: Session = Depends(get_db)):
    """Run ingestion from all active sources."""
    return await run_ingestion(db)

@app.post("/api/ingest/manual")
async def add_manual(item: ManualItemCreate, db: Session = Depends(get_db)):
    """Manually add an item for classification."""
    new_item = await add_manual_item(
        db, item.title, item.content, item.url, item.authors
    )
    return {"id": new_item.id, "title": new_item.title}


# ============ Classification Endpoints ============

@app.post("/api/classify/{item_id}")
async def classify_single(item_id: int, db: Session = Depends(get_db)):
    """Classify a specific item."""
    item = db.query(SourceItem).filter(SourceItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return await classify_item(db, item)

@app.post("/api/classify")
async def classify_batch(limit: int = 10, db: Session = Depends(get_db)):
    """Classify unprocessed items."""
    return await classify_unprocessed(db, limit)


# ============ Items Endpoints ============

@app.get("/api/items")
async def list_items(
    relevant_only: bool = False,
    unclassified_only: bool = False,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List source items."""
    query = db.query(SourceItem)
    
    if relevant_only:
        query = query.filter(SourceItem.is_relevant == 1)
    if unclassified_only:
        query = query.filter(SourceItem.classified_at.is_(None))
    
    items = query.order_by(SourceItem.fetched_at.desc()).limit(limit).all()
    
    return [
        {
            "id": i.id,
            "title": i.title,
            "url": i.url,
            "is_relevant": bool(i.is_relevant) if i.is_relevant is not None else None,
            "impact_level": i.impact_level,
            "classified": i.classified_at is not None,
            "fetched_at": i.fetched_at.isoformat() if i.fetched_at else None
        }
        for i in items
    ]


# ============ Health Check ============

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME}
import feedparser
import arxiv
import httpx
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from backend.models.database import DataSource, SourceItem


async def fetch_rss_feed(db: Session, source: DataSource) -> list[SourceItem]:
    """Fetch items from an RSS feed."""
    
    feed = feedparser.parse(source.url)
    new_items = []
    
    for entry in feed.entries[:20]:  # Limit to 20 most recent
        # Check if already exists
        existing = db.query(SourceItem).filter(
            SourceItem.url == entry.get("link")
        ).first()
        
        if existing:
            continue
        
        # Parse date
        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            pub_date = datetime(*entry.published_parsed[:6])
        
        item = SourceItem(
            source_id=source.id,
            title=entry.get("title", "Untitled"),
            url=entry.get("link"),
            content=entry.get("summary", ""),
            authors=entry.get("author", ""),
            published_date=pub_date,
            fetched_at=datetime.utcnow()
        )
        db.add(item)
        new_items.append(item)
    
    source.last_fetched = datetime.utcnow()
    db.commit()
    
    return new_items


async def fetch_arxiv(db: Session, source: DataSource, query: str, max_results: int = 20) -> list[SourceItem]:
    """Fetch papers from arXiv API."""
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    new_items = []
    
    for paper in search.results():
        # Check if exists
        existing = db.query(SourceItem).filter(
            SourceItem.url == paper.entry_id
        ).first()
        
        if existing:
            continue
        
        item = SourceItem(
            source_id=source.id,
            title=paper.title,
            url=paper.entry_id,
            content=paper.summary,
            authors=", ".join([a.name for a in paper.authors[:5]]),
            published_date=paper.published,
            fetched_at=datetime.utcnow()
        )
        db.add(item)
        new_items.append(item)
    
    source.last_fetched = datetime.utcnow()
    db.commit()
    
    return new_items


async def fetch_webpage(url: str) -> Optional[str]:
    """Fetch content from a webpage."""
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=30.0, follow_redirects=True)
        resp.raise_for_status()
        return resp.text


async def add_manual_item(
    db: Session,
    title: str,
    content: str,
    url: Optional[str] = None,
    authors: Optional[str] = None,
    source_name: str = "Manual Entry"
) -> SourceItem:
    """Manually add an item for classification."""
    
    # Get or create manual source
    source = db.query(DataSource).filter(
        DataSource.name == source_name,
        DataSource.source_type == "manual"
    ).first()
    
    if not source:
        source = DataSource(
            name=source_name,
            source_type="manual",
            category="manual"
        )
        db.add(source)
        db.commit()
        db.refresh(source)
    
    item = SourceItem(
        source_id=source.id,
        title=title,
        url=url,
        content=content,
        authors=authors,
        published_date=datetime.utcnow(),
        fetched_at=datetime.utcnow()
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item


async def run_ingestion(db: Session) -> dict:
    """Run ingestion for all active sources."""
    
    sources = db.query(DataSource).filter(DataSource.is_active == 1).all()
    results = {"fetched": 0, "sources_processed": 0, "errors": []}
    
    for source in sources:
        try:
            if source.source_type == "rss":
                items = await fetch_rss_feed(db, source)
                results["fetched"] += len(items)
            elif source.source_type == "arxiv":
                # URL contains the query for arxiv sources
                items = await fetch_arxiv(db, source, source.url)
                results["fetched"] += len(items)
            
            results["sources_processed"] += 1
        except Exception as e:
            results["errors"].append({"source": source.name, "error": str(e)})
    
    return results
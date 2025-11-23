from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime, ForeignKey, Enum, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

from config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ThreatLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TrendDirection(enum.Enum):
    STABLE = "stable"
    INCREASING = "increasing"
    RAPIDLY_INCREASING = "rapidly_increasing"
    DECREASING = "decreasing"

# Association table for many-to-many relationship
item_threat_association = Table(
    'item_threat_association', Base.metadata,
    Column('item_id', Integer, ForeignKey('source_items.id')),
    Column('threat_id', Integer, ForeignKey('threats.id'))
)

class Threat(Base):
    """A biosecurity threat category to track."""
    __tablename__ = "threats"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False)
    category = Column(String(100))  # e.g., "AI-Enabled Knowledge", "Biological Design"
    description = Column(Text)
    
    # Current assessment
    feasibility_score = Column(Float, default=1.0)  # 1-5 scale
    threat_level = Column(Enum(ThreatLevel), default=ThreatLevel.LOW)
    trend = Column(Enum(TrendDirection), default=TrendDirection.STABLE)
    timeline_estimate = Column(String(100))  # e.g., "12-24 months"
    confidence = Column(Float, default=0.5)  # 0-1
    
    # Enabling capabilities (JSON string for simplicity)
    enabling_capabilities = Column(Text)  # JSON list of capability strings
    
    # Metadata
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    source_items = relationship("SourceItem", secondary=item_threat_association, back_populates="related_threats")

class DataSource(Base):
    """A data source to monitor (RSS feed, API, etc.)."""
    __tablename__ = "data_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    source_type = Column(String(50))  # "rss", "arxiv", "api", "manual"
    url = Column(String(500))
    category = Column(String(100))  # e.g., "preprints", "news", "announcements"
    
    is_active = Column(Integer, default=1)
    last_fetched = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    items = relationship("SourceItem", back_populates="source")

class SourceItem(Base):
    """An individual item from a data source (paper, article, announcement)."""
    __tablename__ = "source_items"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey('data_sources.id'))
    
    title = Column(String(500), nullable=False)
    url = Column(String(500))
    content = Column(Text)  # Abstract or full text
    authors = Column(String(500))
    published_date = Column(DateTime)
    
    # Classification results
    is_relevant = Column(Integer)  # 0/1, null if not yet classified
    relevance_score = Column(Float)  # 0-1
    impact_level = Column(String(50))  # "incremental", "significant", "step_change"
    classification_reasoning = Column(Text)
    capabilities_identified = Column(Text)  # JSON list
    
    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)
    classified_at = Column(DateTime)
    
    # Relationships
    source = relationship("DataSource", back_populates="items")
    related_threats = relationship("Threat", secondary=item_threat_association, back_populates="source_items")

class ThreatUpdate(Base):
    """Historical log of threat assessment changes."""
    __tablename__ = "threat_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(Integer, ForeignKey('threats.id'))
    
    previous_score = Column(Float)
    new_score = Column(Float)
    previous_level = Column(String(50))
    new_level = Column(String(50))
    
    trigger_item_id = Column(Integer, ForeignKey('source_items.id'))
    reasoning = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
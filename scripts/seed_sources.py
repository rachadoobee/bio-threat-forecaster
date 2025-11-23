"""Seed the database with useful biosecurity data sources."""

import sys
sys.path.append(".")

from backend.models.database import init_db, SessionLocal, DataSource

# SOURCES = [
#     # arXiv categories
#     # {
#     #     "name": "arXiv - Quantitative Biology",
#     #     "source_type": "arxiv",
#     #     "url": "q-bio",
#     #     "category": "preprints"
#     # },
#     # {
#     #     "name": "arXiv - Machine Learning + Biology",
#     #     "source_type": "arxiv",
#     #     "url": "cs.LG AND biology",
#     #     "category": "preprints"
#     # },
#     # {
#     #     "name": "arXiv - AI + Protein",
#     #     "source_type": "arxiv",
#     #     "url": "protein structure prediction",
#     #     "category": "preprints"
#     # },
#     # {
#     #     "name": "arXiv - Genomics ML",
#     #     "source_type": "arxiv",
#     #     "url": "genomics machine learning",
#     #     "category": "preprints"
#     # },
#         {
#         "name": "arXiv - Artificial Intelligence",
#         "source_type": "arxiv",
#         "url": "cs.AI",
#         "category": "preprints"
#     },
    
#     # # RSS Feeds - Biosecurity News
#     # {
#     #     "name": "STAT News - Health",
#     #     "source_type": "rss",
#     #     "url": "https://www.statnews.com/feed/",
#     #     "category": "news"
#     # },
#     # {
#     #     "name": "Nature Biotechnology",
#     #     "source_type": "rss",
#     #     "url": "https://www.nature.com/nbt.rss",
#     #     "category": "journals"
#     # },
#     # {
#     #     "name": "Science - Biology",
#     #     "source_type": "rss",
#     #     "url": "https://www.science.org/action/showFeed?type=subject&feed=rss&subject=biology",
#     #     "category": "journals"
#     # },
    
#     # # AI Lab Blogs (these may need adjustment based on actual RSS availability)
#     # {
#     #     "name": "DeepMind Blog",
#     #     "source_type": "rss",
#     #     "url": "https://deepmind.com/blog/feed/basic/",
#     #     "category": "ai_labs"
#     # },
#     # {
#     #     "name": "OpenAI Blog",
#     #     "source_type": "rss",
#     #     "url": "https://openai.com/blog/rss/",
#     #     "category": "ai_labs"
#     # },
    
#     # # biorXiv
#     # {
#     #     "name": "bioRxiv - Synthetic Biology",
#     #     "source_type": "rss",
#     #     "url": "http://connect.biorxiv.org/biorxiv_xml.php?subject=synthetic-biology",
#     #     "category": "preprints"
#     # },
#     # {
#     #     "name": "bioRxiv - Bioinformatics",
#     #     "source_type": "rss",
#     #     "url": "http://connect.biorxiv.org/biorxiv_xml.php?subject=bioinformatics",
#     #     "category": "preprints"
#     # },
# ]


SOURCES = [
    {
        "name": "arXiv - Artificial Intelligence",
        "source_type": "arxiv",
        "url": "https://arxiv.org/list/cs.AI/recent",
        "category": "preprints"
    },
    {
        "name": "IEEE Xplore - Artificial Intelligence",
        "source_type": "journal_database",
        "url": "https://ieeexplore.ieee.org/browse/subjects/4096",
        "category": "peer-reviewed journals"
    },
    {
        "name": "ACM Digital Library - Artificial Intelligence",
        "source_type": "journal_database",
        "url": "https://dl.acm.org/subject/artificial-intelligence",
        "category": "peer-reviewed journals"
    },
    {
        "name": "Springer Nature - Artificial Intelligence",
        "source_type": "publisher_platform",
        "url": "https://www.springer.com/journal/10462",
        "category": "academic journals"
    },
    {
        "name": "bioRxiv - Machine Learning & AI",
        "source_type": "preprint",
        "url": "https://www.biorxiv.org/collection/machine-learning-artificial-intelligence",
        "category": "preprints"
    },
    {
        "name": "Nature - Artificial Intelligence",
        "source_type": "journal",
        "url": "https://www.nature.com/subjects/artificial-intelligence",
        "category": "peer-reviewed journals"
    }
]


def seed_sources():
    init_db()
    db = SessionLocal()
    
    added = 0
    for src in SOURCES:
        # Check if exists
        existing = db.query(DataSource).filter(DataSource.name == src["name"]).first()
        if existing:
            print(f"Skipping (exists): {src['name']}")
            continue
        
        source = DataSource(**src)
        db.add(source)
        added += 1
        print(f"Added: {src['name']}")
    
    db.commit()
    db.close()
    
    print(f"\nSeeded {added} new sources")


if __name__ == "__main__":
    seed_sources()
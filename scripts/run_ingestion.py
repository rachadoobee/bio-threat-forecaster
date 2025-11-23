"""Run a manual ingestion and classification cycle."""

import sys
sys.path.append(".")

import asyncio
from backend.models.database import init_db, SessionLocal
from backend.services.ingestion import run_ingestion
from backend.services.classifier import classify_unprocessed
from backend.services.threat_tracker import update_all_threats


async def main():
    init_db()
    db = SessionLocal()
    
    print("=" * 50)
    print("BIOSECURITY THREAT FORECASTER - INGESTION CYCLE")
    print("=" * 50)
    
    # Step 1: Fetch from sources
    print("\n[1/3] Fetching from data sources...")
    ingest_result = await run_ingestion(db)
    print(f"  - Sources processed: {ingest_result['sources_processed']}")
    print(f"  - Items fetched: {ingest_result['fetched']}")
    if ingest_result['errors']:
        print(f"  - Errors: {ingest_result['errors']}")
    
    # Step 2: Classify new items
    print("\n[2/3] Classifying new items...")
    classify_results = await classify_unprocessed(db, limit=20)
    relevant_count = sum(1 for r in classify_results if r.get("result", {}).get("is_relevant"))
    print(f"  - Items classified: {len(classify_results)}")
    print(f"  - Relevant items: {relevant_count}")
    
    # Step 3: Update threat assessments
    print("\n[3/3] Updating threat assessments...")
    update_results = await update_all_threats(db)
    updated_count = sum(1 for r in update_results if r.get("result", {}).get("updated"))
    print(f"  - Threats assessed: {len(update_results)}")
    print(f"  - Threats updated: {updated_count}")
    
    print("\n" + "=" * 50)
    print("CYCLE COMPLETE")
    print("=" * 50)
    
    db.close()


if __name__ == "__main__":
    asyncio.run(main())
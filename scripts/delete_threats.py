"""Delete threat categories from the database."""

import sys
sys.path.append(".")

from backend.models.database import init_db, SessionLocal, Threat

def list_threats():
    """List all threats with their IDs."""
    db = SessionLocal()
    threats = db.query(Threat).all()
    
    if not threats:
        print("No threats found in database.")
        return
    
    print("\nCurrent threats:")
    print("=" * 80)
    for t in threats:
        print(f"ID: {t.id} | {t.name}")
        print(f"   Category: {t.category}")
        print(f"   Score: {t.feasibility_score}/5")
        print()
    
    db.close()


def delete_threat_by_id(threat_id: int):
    """Delete a specific threat by ID."""
    db = SessionLocal()
    threat = db.query(Threat).filter(Threat.id == threat_id).first()
    
    if not threat:
        print(f"❌ Threat with ID {threat_id} not found")
        db.close()
        return
    
    name = threat.name
    db.delete(threat)
    db.commit()
    print(f"✅ Deleted: {name}")
    db.close()


def delete_by_name_pattern(pattern: str):
    """Delete all threats matching a name pattern."""
    db = SessionLocal()
    threats = db.query(Threat).filter(Threat.name.like(f"%{pattern}%")).all()
    
    if not threats:
        print(f"❌ No threats found matching: {pattern}")
        db.close()
        return
    
    print(f"Found {len(threats)} threats matching '{pattern}':")
    for t in threats:
        print(f"  - {t.name}")
    
    confirm = input("\nDelete these? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        for t in threats:
            db.delete(t)
        db.commit()
        print(f"✅ Deleted {len(threats)} threats")
    else:
        print("❌ Cancelled")
    
    db.close()


def delete_all_threats():
    """Delete ALL threats (use with caution!)."""
    db = SessionLocal()
    count = db.query(Threat).count()
    
    if count == 0:
        print("No threats to delete")
        db.close()
        return
    
    print(f"⚠️  WARNING: This will delete ALL {count} threats!")
    confirm = input("Type 'DELETE ALL' to confirm: ").strip()
    
    if confirm == "DELETE ALL":
        db.query(Threat).delete()
        db.commit()
        print(f"✅ Deleted all {count} threats")
    else:
        print("❌ Cancelled")
    
    db.close()


def interactive_menu():
    """Interactive menu for deleting threats."""
    init_db()
    
    while True:
        print("\n" + "=" * 80)
        print("THREAT MANAGEMENT")
        print("=" * 80)
        print("1. List all threats")
        print("2. Delete threat by ID")
        print("3. Delete threats by name pattern")
        print("4. Delete ALL threats")
        print("5. Exit")
        print()
        
        choice = input("Select option (1-5): ").strip()
        
        if choice == "1":
            list_threats()
        
        elif choice == "2":
            threat_id = input("Enter threat ID to delete: ").strip()
            try:
                delete_threat_by_id(int(threat_id))
            except ValueError:
                print("❌ Invalid ID")
        
        elif choice == "3":
            pattern = input("Enter name pattern to search (e.g., 'Example'): ").strip()
            delete_by_name_pattern(pattern)
        
        elif choice == "4":
            delete_all_threats()
        
        elif choice == "5":
            print("Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        if sys.argv[1] == "list":
            init_db()
            list_threats()
        elif sys.argv[1] == "delete-all":
            init_db()
            delete_all_threats()
        elif sys.argv[1] == "delete-id" and len(sys.argv) > 2:
            init_db()
            delete_threat_by_id(int(sys.argv[2]))
        else:
            print("Usage:")
            print("  python scripts/delete_threats.py              # Interactive mode")
            print("  python scripts/delete_threats.py list         # List all threats")
            print("  python scripts/delete_threats.py delete-id 5  # Delete threat with ID 5")
            print("  python scripts/delete_threats.py delete-all   # Delete all threats")
    else:
        # Interactive mode
        interactive_menu()
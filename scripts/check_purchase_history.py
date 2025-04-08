import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models.purchase_history import PurchaseHistory

def check_purchase_history():
    """Check purchase history records in the database"""
    db = SessionLocal()
    try:
        # Get all purchase history records
        records = db.query(PurchaseHistory).all()
        
        if not records:
            print("No purchase history records found.")
            return
        
        print(f"Found {len(records)} purchase history records:")
        for record in records:
            print(f"Flight: {record.flight_number}, Class: {record.class_type}")
            print(f"Daily purchases: {record.daily_purchases}")
            print("-" * 50)
    finally:
        db.close()

if __name__ == "__main__":
    check_purchase_history() 
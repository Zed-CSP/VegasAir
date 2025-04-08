import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import SessionLocal, engine
from backend.models.base import Base
from backend.models.flight import Flight
from backend.models.seat import Seat
from backend.models.purchase_history import PurchaseHistory
from backend.utils.constants import create_seats

def init_db():
    # Create tables
    Base.metadata.drop_all(bind=engine)  # Drop all tables first
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Create a sample flight
        flight = Flight(
            flight_number="001"
        )
        db.add(flight)
        db.commit()
        db.refresh(flight)
        
        # Create seats for the flight using the shared function
        create_seats(
            flight_id=flight.id,
            db=db,
            num_rows=20,  # 20 rows for initial setup
            first_class_rows=4,
            business_class_rows=8,
            extra_legroom_rows=[9, 10],  # Different extra legroom rows for initial setup
            first_class_price=500.0,
            business_class_price=300.0,
            economy_class_price=150.0,
            window_aisle_extra=10.0,
            legroom_extra=10.0,
            batch_size=120  # Add seats in batches of 120 for better performance
        )
        
        db.commit()
        print(f"Database initialized with flight {flight.flight_number}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.") 
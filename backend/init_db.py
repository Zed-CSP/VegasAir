import sys
import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal, engine
from backend.models.base import Base
from backend.models.flight import Flight
from backend.models.seat import Seat
from backend.models.purchase_history import PurchaseHistory

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
        
        # Create seats for the flight
        seat_letters = ["A", "B", "C", "D", "E", "F"]
        seats = []
        
        for row in range(1, 21):  # 20 rows
            for letter in seat_letters:
                # Determine seat characteristics
                is_window = letter in ["A", "F"]
                is_aisle = letter in ["C", "D"]
                is_middle = letter in ["B", "E"]
                
                # Determine class type (first 4 rows are first class, next 4 are business, rest are economy)
                if row <= 4:
                    class_type = "first"
                    base_price = 500.0
                    is_extra_legroom = True  # All first class seats have extra legroom
                elif row <= 8:
                    class_type = "business"
                    base_price = 300.0
                    is_extra_legroom = True  # All business class seats have extra legroom
                else:
                    class_type = "economy"
                    base_price = 150.0
                    # Only specific economy rows have extra legroom
                    is_extra_legroom = row == 9 or row == 10
                
                seat = Seat(
                    flight_id=flight.id,
                    row_number=row,
                    seat_letter=letter,
                    is_occupied=False,
                    class_type=class_type,
                    is_window=is_window,
                    is_aisle=is_aisle,
                    is_middle=is_middle,
                    is_extra_legroom=is_extra_legroom,
                    base_price=base_price,
                    sale_price=0,  # Initially 0
                    days_until_departure=120  # Default 120 days until departure
                )
                seats.append(seat)
        
        db.add_all(seats)
        db.commit()
        
        print(f"Database initialized with flight {flight.flight_number} and {len(seats)} seats.")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.") 
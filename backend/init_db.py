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
from backend.services.bot_service import bot_service

def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Check if we already have data
        existing_flight = db.query(Flight).first()
        if existing_flight:
            print("Database already initialized. Skipping.")
            return
        
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
                
                # Determine class type (first 2 rows are first class, next 3 are business, rest are economy)
                if row <= 4:
                    class_type = "first"
                    base_price = 500.0
                elif row <= 8:
                    class_type = "business"
                    base_price = 300.0
                else:
                    class_type = "economy"
                    base_price = 150.0
                
                # Determine if extra legroom (last row)
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
        
        # Convert seats to dictionary format for bot service
        seat_dicts = [{
            'id': seat.id,
            'row_number': seat.row_number,
            'seat_letter': seat.seat_letter,
            'is_occupied': seat.is_occupied,
            'class_type': seat.class_type,
            'is_window': seat.is_window,
            'is_aisle': seat.is_aisle,
            'is_middle': seat.is_middle,
            'is_extra_legroom': seat.is_extra_legroom,
            'base_price': seat.base_price,
            'sale_price': seat.sale_price,
            'days_until_departure': seat.days_until_departure
        } for seat in seats]
        
        # Start bots for the flight
        bot_service.start_bots(flight.id, seat_dicts)
        print(f"Bots started automatically for flight {flight.id}")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialization complete.") 
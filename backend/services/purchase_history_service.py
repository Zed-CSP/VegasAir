from collections import defaultdict
from typing import Dict, List
from sqlalchemy.orm import Session

from backend.db.database import SessionLocal
from backend.models.flight import Flight
from backend.models.seat import Seat
from backend.models.purchase_history import PurchaseHistory

class PurchaseHistoryService:
    """Service to handle flight purchase history data collection and storage"""
    
    @staticmethod
    def collect_and_store_purchase_data(flight_id: int):
        """
        Collect purchase data for a completed flight and store it in the purchase_history table.
        This should be called when a flight's countdown timer reaches zero.
        """
        db = SessionLocal()
        try:
            # Get the flight
            flight = db.query(Flight).filter(Flight.id == flight_id).first()
            if not flight:
                print(f"Error: Flight {flight_id} not found")
                return
            
            # Get all seats for the flight
            seats = db.query(Seat).filter(Seat.flight_id == flight_id).all()
            
            # Initialize data structures to collect purchase data by class
            class_purchases: Dict[str, Dict[int, int]] = {
                'first': defaultdict(int),
                'business': defaultdict(int),
                'economy': defaultdict(int)
            }
            
            # Collect purchase data
            for seat in seats:
                if seat.is_occupied and seat.days_until_departure is not None:
                    # Round to nearest day
                    day = min(120, max(0, seat.days_until_departure))
                    class_purchases[seat.class_type][day] += 1
            
            # Create purchase history records for each class
            for class_type, purchases in class_purchases.items():
                # Convert defaultdict to regular dict for JSON storage
                daily_data = {str(day): count for day, count in purchases.items()}
                
                # Create the purchase history record
                history = PurchaseHistory(
                    flight_number=flight.flight_number,
                    class_type=class_type,
                    daily_purchases=daily_data,
                    departure_date=flight.departure_date
                )
                db.add(history)
            
            db.commit()
            print(f"Purchase history data collected and stored for flight {flight.flight_number}")
            
        except Exception as e:
            print(f"Error collecting purchase history data: {e}")
            db.rollback()
        finally:
            db.close()

# Global instance
purchase_history_service = PurchaseHistoryService() 
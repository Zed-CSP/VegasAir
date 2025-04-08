from typing import TypedDict, Dict
from backend.db.database import SessionLocal
from backend.models.flight import Flight
from backend.models.seat import Seat

class FlightStatus(TypedDict):
    hours_remaining: int
    is_active: bool

def create_seats(
    flight_id: int, 
    db,
    num_rows: int = 30,
    first_class_rows: int = 4,
    business_class_rows: int = 8,
    extra_legroom_rows: list[int] = [1, 15, 16],
    first_class_price: float = 500,
    business_class_price: float = 300,
    economy_class_price: float = 150,
    window_aisle_extra: float = 10,
    legroom_extra: float = 10,
    batch_size: int = None
) -> None:
    """
    Create all seats for a given flight.
    
    Args:
        flight_id: The ID of the flight to create seats for
        db: The database session to use
        num_rows: Total number of rows in the aircraft
        first_class_rows: Number of rows for first class
        business_class_rows: Number of rows for business class
        extra_legroom_rows: List of row numbers that have extra legroom
        first_class_price: Base price for first class seats
        business_class_price: Base price for business class seats
        economy_class_price: Base price for economy class seats
        window_aisle_extra: Extra charge for window/aisle seats
        legroom_extra: Extra charge for extra legroom seats
        batch_size: If set, seats will be added in batches of this size
    """
    rows = range(1, num_rows + 1)
    seat_letters = ['A', 'B', 'C', 'D', 'E', 'F']
    seats = []
    
    for row in rows:
        for letter in seat_letters:
            # Determine seat class
            if row <= first_class_rows:
                class_type = "first"
                base_price = first_class_price
            elif row <= business_class_rows:
                class_type = "business"
                base_price = business_class_price
            else:
                class_type = "economy"
                base_price = economy_class_price
            
            # Determine seat properties
            is_window = letter in ['A', 'F']
            is_middle = letter in ['B', 'E']
            is_aisle = letter in ['C', 'D']
            is_extra_legroom = row in extra_legroom_rows
            
            # Add extra for window/aisle and extra legroom
            if is_window or is_aisle:
                base_price += window_aisle_extra
            if is_extra_legroom:
                base_price += legroom_extra
            
            # Create the seat
            seat = Seat(
                flight_id=flight_id,
                row_number=row,
                seat_letter=letter,
                is_occupied=False,
                class_type=class_type,
                is_window=is_window,
                is_aisle=is_aisle,
                is_middle=is_middle,
                is_extra_legroom=is_extra_legroom,
                base_price=base_price,
                days_until_departure=120  # Start with 120 days until departure
            )
            
            if batch_size:
                seats.append(seat)
                if len(seats) >= batch_size:
                    db.add_all(seats)
                    seats = []
            else:
                db.add(seat)
    
    # Add any remaining seats if using batch mode
    if batch_size and seats:
        db.add_all(seats)

def create_next_flight(previous_flight_number: str = None) -> int:
    """
    Create a new flight with the next flight number and all its seats.
    Returns the new flight ID.
    """
    db = SessionLocal()
    try:
        # If no previous flight number, start with 001
        if not previous_flight_number:
            next_flight_number = "001"
        else:
            # Increment the flight number
            next_num = int(previous_flight_number) + 1
            next_flight_number = f"{next_num:03d}"  # Format as 3 digits with leading zeros
        
        # Create the new flight
        new_flight = Flight(flight_number=next_flight_number)
        db.add(new_flight)
        db.flush()  # This gets us the new flight ID
        
        # Create seats for the flight using the dedicated function
        create_seats(new_flight.id, db)
        
        db.commit()
        print(f"Created new flight {next_flight_number} with ID {new_flight.id}")
        return new_flight.id
        
    except Exception as e:
        print(f"Error creating next flight: {e}")
        db.rollback()
        return None
    finally:
        db.close()

class FlightStateManager:
    def __init__(self):
        self.flight_states: Dict[int, FlightStatus] = {}

    def update_hours_remaining(self, flight_id: int, hours: int):
        if flight_id not in self.flight_states:
            self.flight_states[flight_id] = {"hours_remaining": hours, "is_active": True}
        else:
            self.flight_states[flight_id]["hours_remaining"] = hours

    def get_hours_remaining(self, flight_id: int) -> int:
        return self.flight_states.get(flight_id, {}).get("hours_remaining", 0)

    def is_flight_active(self, flight_id: int) -> bool:
        return self.flight_states.get(flight_id, {}).get("is_active", False)

    def set_flight_inactive(self, flight_id: int):
        if flight_id in self.flight_states:
            self.flight_states[flight_id]["is_active"] = False

# Global instance
flight_state_manager = FlightStateManager() 
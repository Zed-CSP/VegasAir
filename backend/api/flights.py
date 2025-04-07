from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models.flight import Flight
from models.seat import Seat

router = APIRouter()

@router.get("/flights/", response_model=List[dict])
def get_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()
    return [{"id": flight.id, "flight_number": flight.flight_number} for flight in flights]

@router.get("/flights/{flight_id}/seats", response_model=List[dict])
def get_flight_seats(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    seats = db.query(Seat).filter(Seat.flight_id == flight_id).all()
    return [
        {
            "id": seat.id,
            "row_number": seat.row_number,
            "seat_letter": seat.seat_letter,
            "is_occupied": seat.is_occupied,
            "class_type": seat.class_type,
            "is_window": seat.is_window,
            "is_aisle": seat.is_aisle,
            "is_middle": seat.is_middle,
            "is_extra_legroom": seat.is_extra_legroom,
            "base_price": seat.base_price,
            "sale_price": seat.sale_price,
            "days_until_departure": seat.days_until_departure
        }
        for seat in seats
    ] 
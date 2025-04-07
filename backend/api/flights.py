from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import asyncio
from datetime import datetime, timedelta

from database import get_db, SessionLocal
from models.flight import Flight
from models.seat import Seat
from ws_manager import manager

router = APIRouter()

@router.get("/flights/", response_model=List[dict])
def get_flights(db: Session = Depends(get_db)):
    flights = db.query(Flight).all()
    return [{"id": flight.id, "flight_number": flight.flight_number} for flight in flights]

@router.get("/flights/{flight_id}", response_model=dict)
def get_flight(flight_id: int, db: Session = Depends(get_db)):
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Get the first seat to get the days_until_departure
    seat = db.query(Seat).filter(Seat.flight_id == flight_id).first()
    days_until_departure = seat.days_until_departure if seat else 0
    
    return {
        "id": flight.id,
        "flight_number": flight.flight_number,
        "days_until_departure": days_until_departure
    }

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

@router.websocket("/ws/flight/{flight_id}")
async def websocket_endpoint(websocket: WebSocket, flight_id: int):
    await manager.connect(websocket, flight_id)
    
    # Start a background task to update the countdown timer
    asyncio.create_task(update_countdown(flight_id, websocket))
    
    try:
        while True:
            # Wait for messages from the client
            data = await websocket.receive_json()
            
            # Handle seat updates
            if data.get("type") == "SEAT_UPDATE":
                seat_data = data.get("seat", {})
                seat_id = seat_data.get("id")
                
                if seat_id:
                    # Update the seat in the database
                    db = SessionLocal()
                    try:
                        seat = db.query(Seat).filter(Seat.id == seat_id).first()
                        if seat:
                            # Update seat properties
                            for key, value in seat_data.items():
                                if hasattr(seat, key):
                                    setattr(seat, key, value)
                            
                            db.commit()
                            
                            # Broadcast the update to all clients
                            await manager.broadcast_to_flight(flight_id, {
                                "type": "SEAT_UPDATE",
                                "seat": {
                                    "id": seat.id,
                                    "is_occupied": seat.is_occupied,
                                    "sale_price": seat.sale_price
                                }
                            })
                    finally:
                        db.close()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, flight_id)

async def update_countdown(flight_id: int, websocket: WebSocket):
    """Background task to update the countdown timer"""
    db = SessionLocal()
    try:
        # Get the first seat to get the days_until_departure
        seat = db.query(Seat).filter(Seat.flight_id == flight_id).first()
        if not seat:
            return
        
        days_until_departure = seat.days_until_departure
        
        # Send initial countdown
        await websocket.send_json({
            "type": "TIME_UPDATE",
            "days_until_departure": days_until_departure
        })
        
        # Update the countdown every hour
        while True:
            await asyncio.sleep(3600)  # Sleep for 1 hour
            
            # Update days_until_departure in the database
            seat.days_until_departure = max(0, seat.days_until_departure - 1)
            db.commit()
            
            # Broadcast the update to all clients
            await manager.broadcast_to_flight(flight_id, {
                "type": "TIME_UPDATE",
                "days_until_departure": seat.days_until_departure
            })
            
            # If we've reached 0 days, stop updating
            if seat.days_until_departure <= 0:
                break
    finally:
        db.close() 
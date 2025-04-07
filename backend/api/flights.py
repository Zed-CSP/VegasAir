from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import asyncio
from datetime import datetime, timedelta

from database import get_db, SessionLocal
from models.flight import Flight
from models.seat import Seat
from ws_manager import manager
from services.countdown_service import countdown_service

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
    
    # Get the days until departure from the database
    db = SessionLocal()
    try:
        seat = db.query(Seat).filter(Seat.flight_id == flight_id).first()
        days_until_departure = seat.days_until_departure if seat else 0
        
        # Start the countdown timer for this flight if it's not already running
        countdown_service.start_timer(flight_id, days_until_departure)
        
        # Register a callback to send updates to this client
        async def send_time_update(days, hours):
            try:
                await websocket.send_json({
                    "type": "TIME_UPDATE",
                    "days_until_departure": days,
                    "hours": hours
                })
            except Exception as e:
                print(f"Error sending time update: {e}")
        
        countdown_service.register_callback(flight_id, send_time_update)
        
        # Send initial time update with current values from the service
        if flight_id in countdown_service._hours_remaining:
            total_hours = countdown_service._hours_remaining[flight_id]
            days = total_hours // 24
            hours = total_hours % 24
            await websocket.send_json({
                "type": "TIME_UPDATE",
                "days_until_departure": days,
                "hours": hours
            })
    finally:
        db.close()
    
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
                            
                            # If the seat is being purchased, record the days until departure
                            if seat_data.get("is_occupied") and not seat.is_occupied:
                                # Get the current days and hours from the countdown service
                                if flight_id in countdown_service._hours_remaining:
                                    total_hours = countdown_service._hours_remaining[flight_id]
                                    days_left = total_hours // 24
                                    # Store the days left at the time of purchase
                                    seat.days_until_departure = days_left
                                    print(f"Seat {seat_id} purchased with {days_left} days until departure")
                            
                            db.commit()
                            
                            # Broadcast the update to all clients
                            await manager.broadcast_to_flight(flight_id, {
                                "type": "SEAT_UPDATE",
                                "seat": {
                                    "id": seat.id,
                                    "is_occupied": seat.is_occupied,
                                    "sale_price": seat.sale_price,
                                    "days_until_departure": seat.days_until_departure
                                }
                            })
                    finally:
                        db.close()
            
    except WebSocketDisconnect:
        # Unregister the callback when the client disconnects
        countdown_service.unregister_callback(flight_id, send_time_update)
        manager.disconnect(websocket, flight_id) 
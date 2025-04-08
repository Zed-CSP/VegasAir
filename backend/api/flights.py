from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List
import asyncio
from datetime import datetime, timedelta

from backend.db.database import get_db, SessionLocal
from backend.models.flight import Flight
from backend.models.seat import Seat
from backend.websocket.ws_manager import manager
from backend.utils.constants import flight_state_manager
from backend.services.countdown_service import countdown_service
from backend.services.bot_service import bot_service

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
    try:
        # Accept the connection first
        await websocket.accept()
        print(f"WebSocket connection accepted for flight {flight_id}")
        
        # Then connect to the manager
        await manager.connect(websocket, flight_id)
        print(f"WebSocket connection established for flight {flight_id}")
        
        # Get the days until departure from the database
        db = SessionLocal()
        try:
            # Get all seats for the flight
            seats = db.query(Seat).filter(Seat.flight_id == flight_id).all()
            if not seats:
                print(f"No seats found for flight {flight_id}")
                await websocket.close()
                return
            
            days_until_departure = seats[0].days_until_departure
            
            # Send initial time update with current values from the service
            if flight_state_manager.is_flight_active(flight_id):
                total_hours = flight_state_manager.get_hours_remaining(flight_id)
                days = total_hours // 24
                hours = total_hours % 24
                await websocket.send_json({
                    "type": "TIME_UPDATE",
                    "days_until_departure": days,
                    "hours": hours
                })
        finally:
            db.close()
        
        # Keep the connection alive and handle messages
        while True:
            try:
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
                                })
                        finally:
                            db.close()
            except WebSocketDisconnect:
                print(f"WebSocket disconnected for flight {flight_id}")
                manager.disconnect(websocket, flight_id)
                break
            except Exception as e:
                print(f"Error in WebSocket connection for flight {flight_id}: {e}")
                # Don't break the loop for other errors, just log them
    except Exception as e:
        print(f"Error establishing WebSocket connection for flight {flight_id}: {e}")
        try:
            await websocket.close()
        except:
            pass

@router.post("/flights/{flight_id}/start", response_model=dict)
def start_flight(flight_id: int, db: Session = Depends(get_db)):
    """Start the timer and bots for a flight"""
    # Check if the flight exists
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    # Get seats for the flight
    seats = db.query(Seat).filter(Seat.flight_id == flight_id).all()
    if not seats:
        raise HTTPException(status_code=404, detail="No seats found for this flight")
    
    # Get days until departure from the first seat
    days_until_departure = seats[0].days_until_departure
    
    # Start the countdown timer
    countdown_service.start_timer(flight_id, days_until_departure * 24)  # Convert days to hours
    
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
    bot_service.start_bots(flight_id, seat_dicts)
    
    return {
        "message": f"Started timer and bots for flight {flight.flight_number}",
        "flight_id": flight_id,
        "days_until_departure": days_until_departure
    } 
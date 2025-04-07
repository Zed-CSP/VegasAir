from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import engine, SessionLocal
from backend.models.base import Base
from backend.models.flight import Flight
from backend.models.seat import Seat
from backend.api import flights
from backend.services.bot_service import bot_service
from backend.services.countdown_service import countdown_service

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(flights.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.on_event("startup")
async def startup_event():
    """Start bots and countdown timers for all flights on application startup"""
    db = SessionLocal()
    try:
        # Get all flights
        flights = db.query(Flight).all()
        
        for flight in flights:
            # Get seats for the flight
            seats = db.query(Seat).filter(Seat.flight_id == flight.id).all()
            
            if seats:
                # Start countdown timer for the flight
                days_until_departure = seats[0].days_until_departure
                countdown_service.start_timer(flight.id, days_until_departure * 24)  # Convert days to hours
                
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
                print(f"Started bots and countdown timer for flight {flight.id}")
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """Stop all bots and countdown timers on application shutdown"""
    # Get all flight IDs from the database
    db = SessionLocal()
    try:
        flights = db.query(Flight).all()
        for flight in flights:
            # Stop bots and countdown timer
            bot_service.stop_bots(flight.id)
            countdown_service.stop_timer(flight.id)
            print(f"Stopped bots and countdown timer for flight {flight.id}")
    finally:
        db.close() 
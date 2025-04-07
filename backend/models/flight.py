from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Flight(BaseModel):
    """Flight model representing airline flights"""
    __tablename__ = "flights"

    flight_number = Column(String(3), unique=True, index=True)  # Format: 001, 002, etc.
    departure_airport = Column(String, index=True)
    arrival_airport = Column(String, index=True)
    departure_time = Column(DateTime, index=True)
    arrival_time = Column(DateTime, index=True)
    
    # Relationship to seats
    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
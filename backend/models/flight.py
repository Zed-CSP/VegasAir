from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import BaseModel

class Flight(BaseModel):
    """Flight model representing airline flights"""
    __tablename__ = "flights"

    flight_number = Column(String(3), unique=True, index=True)  # Format: 001, 002, etc.
    
    # Relationship to seats
    seats = relationship("Seat", back_populates="flight", cascade="all, delete-orphan")
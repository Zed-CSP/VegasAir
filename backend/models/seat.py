from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.models.base import BaseModel
import sqlalchemy

class Seat(BaseModel):
    """Seat model representing individual seats in a flight"""
    __tablename__ = "seats"

    flight_id = Column(Integer, ForeignKey("flights.id"))
    row_number = Column(Integer)  # 1-20
    seat_letter = Column(String(1))  # A, B, C, D, E, F
    class_type = Column(String)  # economy, business, first
    is_occupied = Column(Boolean, default=False)
    is_window = Column(Boolean)
    is_aisle = Column(Boolean)
    is_middle = Column(Boolean)
    is_extra_legroom = Column(Boolean)
    
    base_price = Column(Float)
    sale_price = Column(Float)
    days_until_departure = Column(Integer)
    
    # Relationship to flight
    flight = relationship("Flight", back_populates="seats")
    
    # Composite unique constraint for flight_id + row_number + seat_letter + is_occupied
    __table_args__ = (
        sqlalchemy.UniqueConstraint('flight_id', 'row_number', 'seat_letter', 'is_occupied', name='unique_seat_per_flight'),
    )
from sqlalchemy import Column, Integer, String, JSON, DateTime
from backend.models.base import Base

class PurchaseHistory(Base):
    """Model for storing flight purchase time series data"""
    __tablename__ = "purchase_history"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String, index=True)
    class_type = Column(String)  # first, business, or economy
    daily_purchases = Column(JSON)  # Store 120 days of purchase data as JSON
    departure_date = Column(DateTime, nullable=False, index=True)  # Add departure date

    def __repr__(self):
        return f"<PurchaseHistory(flight={self.flight_number}, class={self.class_type}, departure={self.departure_date})" 
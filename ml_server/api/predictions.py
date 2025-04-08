from fastapi import APIRouter, HTTPException
from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from ..services.demand_forecasting import DemandForecaster

router = APIRouter()
forecaster = DemandForecaster()

@router.post("/demand/{flight_id}")
async def forecast_demand(flight_id: str, days_ahead: Optional[int] = 30):
    """
    Generate demand forecast for a specific flight.
    
    Args:
        flight_id: The ID of the flight to forecast
        days_ahead: Number of days to forecast (default: 30)
        
    Returns:
        Dictionary containing forecast data
    """
    try:
        # Generate dummy historical data for testing
        # In production, this would come from your database
        dates = pd.date_range(
            start=datetime.now() - timedelta(days=90),
            end=datetime.now(),
            freq='D'
        )
        historical_data = pd.DataFrame({
            'date': dates,
            'demand': np.random.normal(100, 20, len(dates))  # Dummy demand data
        })
        
        # Generate forecast
        forecast_df = forecaster.generate_forecast(historical_data, days_ahead)
        
        return {
            "flight_id": flight_id,
            "forecast": forecast_df.to_dict(orient='records'),
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/models/status")
async def get_model_status():
    """
    Get the status of all forecasting models.
    
    Returns:
        Dictionary containing model statuses
    """
    return {
        "arima": {
            "status": "ready",
            "last_trained": datetime.now().isoformat()
        },
        "prophet": {
            "status": "ready",
            "last_trained": datetime.now().isoformat()
        },
        "lstm": {
            "status": "ready",
            "last_trained": datetime.now().isoformat()
        }
    } 
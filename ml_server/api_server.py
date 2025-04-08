from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from run_ml_server import predict

app = FastAPI(title="ML Service API")

class ForecastRequest(BaseModel):
    historical_data: List[Dict[str, Any]]
    forecast_horizon: int

@app.post("/predict")
async def create_prediction(request: ForecastRequest):
    # Submit task to Celery
    task = predict.delay(request.historical_data, request.forecast_horizon)
    
    return {
        "task_id": task.id,
        "status": "processing"
    }

@app.get("/predict/{task_id}")
async def get_prediction(task_id: str):
    task = predict.AsyncResult(task_id)
    
    if task.ready():
        result = task.get()
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        return result
    else:
        return {
            "status": "processing",
            "task_id": task_id
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 
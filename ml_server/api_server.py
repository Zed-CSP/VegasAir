from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
from run_ml_server import predict
from celery.result import AsyncResult
import logging

app = FastAPI(title="ML Service API")
logger = logging.getLogger(__name__)

class ForecastRequest(BaseModel):
    historical_data: List[Dict[str, Any]]
    forecast_horizon: int

class TaskResponse(BaseModel):
    task_id: str
    status: str

class ForecastResponse(BaseModel):
    status: str
    forecast: List[Dict[str, Any]] = None
    error: str = None

@app.post("/predict", response_model=TaskResponse)
async def create_prediction(request: ForecastRequest, background_tasks: BackgroundTasks):
    try:
        # Submit task to RabbitMQ queue
        task = predict.apply_async(
            args=[request.historical_data, request.forecast_horizon],
            queue='prediction_queue',
            routing_key='prediction'
        )
        logger.info(f"Submitted prediction task {task.id} to queue")
        
        return TaskResponse(
            task_id=task.id,
            status="processing"
        )
    except Exception as e:
        logger.error(f"Error submitting prediction task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/predict/{task_id}", response_model=ForecastResponse)
async def get_prediction(task_id: str):
    try:
        task = AsyncResult(task_id)
        
        if not task.ready():
            return ForecastResponse(
                status="processing"
            )
            
        result = task.get()
        if result['status'] == 'error':
            return ForecastResponse(
                status='error',
                error=result['error']
            )
            
        return ForecastResponse(
            status='success',
            forecast=result['forecast']
        )
    except Exception as e:
        logger.error(f"Error retrieving prediction result: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO)
    logger.info("ML API Server starting up")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001) 
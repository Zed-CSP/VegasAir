from celery import Celery
from demand_forecasting import DemandForecaster
import logging

# Configure Celery
app = Celery('ml_tasks',
             broker='redis://localhost:6379/0',
             backend='redis://localhost:6379/0')

# Configure Celery settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,  # Process one task at a time for ML workloads
    worker_max_tasks_per_child=1,  # Restart worker after each task to prevent memory leaks
    task_time_limit=3600,  # 1 hour timeout for long-running ML tasks
)

# Initialize forecaster
forecaster = DemandForecaster()

@app.task(name='predict')
def predict(historical_data, forecast_horizon):
    try:
        forecast = forecaster.generate_forecast(historical_data, forecast_horizon)
        return {
            'status': 'success',
            'forecast': forecast
        }
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        return {
            'status': 'error',
            'error': str(e)
        }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Start Celery worker
    app.worker_main(['worker', '--loglevel=info']) 
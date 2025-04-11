from celery import Celery
from demand_forecasting import DemandForecaster
import logging
from kombu import Exchange, Queue
import numpy as np
from typing import List, Dict, Any

# Define exchanges and queues
ml_exchange = Exchange('ml_exchange', type='direct')
prediction_queue = Queue('prediction_queue', exchange=ml_exchange, routing_key='prediction')

# Configure Celery with RabbitMQ
app = Celery('ml_tasks',
             broker='amqp://guest:guest@localhost:5672//',
             backend='rpc://')

# Configure Celery settings for high throughput
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_queues=(prediction_queue,),
    task_default_queue='prediction_queue',
    task_default_exchange='ml_exchange',
    task_default_routing_key='prediction',
    worker_prefetch_multiplier=4,  # Increased for better throughput
    worker_max_tasks_per_child=100,  # Increased for better performance
    task_time_limit=300,  # Reduced to 5 minutes
    task_soft_time_limit=240,  # Soft limit of 4 minutes
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_pool_limit=None,  # No limit on broker connections
    broker_heartbeat=10,  # More frequent heartbeats
    result_expires=3600,  # Results expire after 1 hour
    worker_concurrency=4  # Number of worker processes
)

# Initialize forecaster with caching
class CachedForecaster:
    def __init__(self):
        self._forecaster = DemandForecaster()
        self._cache = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
    def generate_forecast(self, historical_data: List[Dict[str, Any]], forecast_horizon: int) -> Dict[str, Any]:
        # Create cache key from data characteristics
        cache_key = self._create_cache_key(historical_data, forecast_horizon)
        
        # Check cache
        if cache_key in self._cache:
            self._cache_hits += 1
            return self._cache[cache_key]
            
        self._cache_misses += 1
        
        # Generate new forecast
        forecast = self._forecaster.generate_forecast(historical_data, forecast_horizon)
        
        # Cache the result
        self._cache[cache_key] = forecast
        
        # Maintain cache size
        if len(self._cache) > 1000:  # Limit cache size
            self._clean_cache()
            
        return forecast
    
    def _create_cache_key(self, historical_data: List[Dict[str, Any]], forecast_horizon: int) -> str:
        # Create a cache key based on data characteristics
        if not historical_data:
            return f"empty_{forecast_horizon}"
            
        # Use key data points to create cache key
        latest_data = historical_data[-1]
        return f"{latest_data['timestamp']}_{forecast_horizon}"
    
    def _clean_cache(self):
        # Remove oldest 20% of cache entries
        cache_size = len(self._cache)
        items = sorted(self._cache.items(), key=lambda x: x[0])
        for key, _ in items[:int(cache_size * 0.2)]:
            del self._cache[key]
    
    def get_stats(self):
        return {
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_size': len(self._cache)
        }

forecaster = CachedForecaster()

@app.task(name='predict', bind=True, max_retries=3, rate_limit='100/s')
def predict(self, historical_data: List[Dict[str, Any]], forecast_horizon: int) -> Dict[str, Any]:
    try:
        forecast = forecaster.generate_forecast(historical_data, forecast_horizon)
        return {
            'status': 'success',
            'forecast': forecast,
            'cache_stats': forecaster.get_stats()
        }
    except Exception as e:
        logging.error(f"Prediction error: {str(e)}")
        try:
            self.retry(countdown=2 ** self.request.retries)
        except self.MaxRetriesExceededError:
            return {
                'status': 'error',
                'error': str(e)
            }

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # Start multiple worker processes
    app.worker_main(['worker', '--loglevel=info', '-Q', 'prediction_queue', '--concurrency=4']) 
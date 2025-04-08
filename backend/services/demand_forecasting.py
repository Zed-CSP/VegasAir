import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Tuple
import json

class DemandForecaster:
    """Service to handle demand forecasting using multiple models"""
    
    def __init__(self):
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        
    def prepare_data(self, purchase_history: List[Dict]) -> pd.DataFrame:
        """
        Convert purchase history data into a pandas DataFrame suitable for forecasting.
        """
        # Combine all purchase data into a single time series
        all_data = []
        for record in purchase_history:
            daily_data = record['daily_purchases']
            class_type = record['class_type']
            flight_number = record['flight_number']
            
            # Convert string keys to integers and sort by day
            daily_data = {int(k): v for k, v in daily_data.items()}
            sorted_data = sorted(daily_data.items())
            
            # Add to the dataset
            for day, purchases in sorted_data:
                all_data.append({
                    'day': day,
                    'purchases': purchases,
                    'class_type': class_type,
                    'flight_number': flight_number
                })
        
        # Convert to DataFrame
        df = pd.DataFrame(all_data)
        return df
    
    def fit_arima(self, data: pd.Series) -> Dict:
        """
        Fit ARIMA model and return forecasts.
        """
        try:
            # Fit ARIMA model (p=1, d=1, q=1) as a starting point
            model = ARIMA(data, order=(1, 1, 1))
            results = model.fit()
            
            # Generate forecasts for next 30 days
            forecast = results.forecast(steps=30)
            
            return {
                'model': 'ARIMA',
                'forecast': forecast.tolist(),
                'confidence_intervals': None  # I'll add this later
            }
        except Exception as e:
            print(f"Error fitting ARIMA model: {e}")
            return None
    
    def fit_prophet(self, data: pd.Series) -> Dict:
        """
        Fit Prophet model and return forecasts.
        """
        try:
            # Prepare data for Prophet
            df = pd.DataFrame({
                'ds': pd.date_range(start='2024-01-01', periods=len(data)),
                'y': data.values
            })
            
            # Fit Prophet model
            model = Prophet(daily_seasonality=True)
            model.fit(df)
            
            # Generate forecasts
            future = model.make_future_dataframe(periods=30)
            forecast = model.predict(future)
            
            return {
                'model': 'Prophet',
                'forecast': forecast['yhat'].tail(30).tolist(),
                'confidence_intervals': {
                    'lower': forecast['yhat_lower'].tail(30).tolist(),
                    'upper': forecast['yhat_upper'].tail(30).tolist()
                }
            }
        except Exception as e:
            print(f"Error fitting Prophet model: {e}")
            return None
    
    def create_lstm_sequences(self, data: np.array, lookback: int = 7) -> Tuple[np.array, np.array]:
        """
        Create sequences for LSTM model.
        """
        X, y = [], []
        for i in range(len(data) - lookback):
            X.append(data[i:(i + lookback)])
            y.append(data[i + lookback])
        return np.array(X), np.array(y)
    
    def fit_lstm(self, data: pd.Series) -> Dict:
        """
        Fit LSTM model and return forecasts.
        """
        try:
            # Scale the data
            scaled_data = self.scaler.fit_transform(data.values.reshape(-1, 1))
            
            # Create sequences
            X, y = self.create_lstm_sequences(scaled_data)
            
            # Reshape for LSTM [samples, timesteps, features]
            X = X.reshape((X.shape[0], X.shape[1], 1))
            
            # Create and fit LSTM model
            model = tf.keras.Sequential([
                tf.keras.layers.LSTM(50, activation='relu', input_shape=(7, 1)),
                tf.keras.layers.Dense(1)
            ])
            
            model.compile(optimizer='adam', loss='mse')
            model.fit(X, y, epochs=50, batch_size=32, verbose=0)
            
            # Generate forecasts
            last_sequence = scaled_data[-7:]
            forecast_scaled = []
            
            for _ in range(30):
                next_pred = model.predict(last_sequence.reshape(1, 7, 1))
                forecast_scaled.append(next_pred[0, 0])
                last_sequence = np.roll(last_sequence, -1)
                last_sequence[-1] = next_pred
            
            # Inverse transform the forecasts
            forecast = self.scaler.inverse_transform(np.array(forecast_scaled).reshape(-1, 1))
            
            return {
                'model': 'LSTM',
                'forecast': forecast.flatten().tolist(),
                'confidence_intervals': None  # I'll add this later
            }
        except Exception as e:
            print(f"Error fitting LSTM model: {e}")
            return None
    
    def generate_forecasts(self, purchase_history: List[Dict]) -> Dict:
        """
        Generate forecasts using all models.
        """
        # Prepare data
        df = self.prepare_data(purchase_history)
        
        # Generate forecasts for each class type
        forecasts = {}
        for class_type in ['first', 'business', 'economy']:
            class_data = df[df['class_type'] == class_type]['purchases']
            if len(class_data) > 0:
                forecasts[class_type] = {
                    'arima': self.fit_arima(class_data),
                    'prophet': self.fit_prophet(class_data),
                    'lstm': self.fit_lstm(class_data)
                }
        
        return forecasts

# Global instance
demand_forecaster = DemandForecaster() 
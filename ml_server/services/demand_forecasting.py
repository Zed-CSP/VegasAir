import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from sklearn.preprocessing import MinMaxScaler
from typing import Dict, List, Tuple

class DemandForecaster:
    def __init__(self):
        self.scaler = MinMaxScaler()
        self.lstm_model = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize all forecasting models."""
        # Initialize LSTM model
        self.lstm_model = Sequential([
            LSTM(50, return_sequences=True, input_shape=(30, 1)),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(1)
        ])
        self.lstm_model.compile(optimizer='adam', loss='mse')
    
    def _prepare_lstm_data(self, data: pd.DataFrame, lookback: int = 30) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for LSTM model."""
        scaled_data = self.scaler.fit_transform(data[['demand']])
        X, y = [], []
        for i in range(len(scaled_data) - lookback):
            X.append(scaled_data[i:(i + lookback), 0])
            y.append(scaled_data[i + lookback, 0])
        return np.array(X), np.array(y)
    
    def generate_forecast(self, historical_data: pd.DataFrame, days_ahead: int) -> pd.DataFrame:
        """
        Generate demand forecasts using multiple models.
        
        Args:
            historical_data: DataFrame with 'date' and 'demand' columns
            days_ahead: Number of days to forecast
            
        Returns:
            DataFrame with forecasts from each model
        """
        # Prepare data
        data = historical_data.copy()
        data.set_index('date', inplace=True)
        
        # ARIMA forecast
        arima_model = ARIMA(data['demand'], order=(5,1,0))
        arima_results = arima_model.fit()
        arima_forecast = arima_results.forecast(steps=days_ahead)
        
        # Prophet forecast
        prophet_data = data.reset_index().rename(columns={'date': 'ds', 'demand': 'y'})
        prophet_model = Prophet()
        prophet_model.fit(prophet_data)
        future_dates = prophet_model.make_future_dataframe(periods=days_ahead)
        prophet_forecast = prophet_model.predict(future_dates)
        
        # LSTM forecast
        X, y = self._prepare_lstm_data(data.reset_index())
        if len(X) > 0:
            self.lstm_model.fit(X, y, epochs=50, batch_size=32, verbose=0)
            last_sequence = X[-1:]
            lstm_forecast = []
            for _ in range(days_ahead):
                next_pred = self.lstm_model.predict(last_sequence, verbose=0)
                lstm_forecast.append(next_pred[0, 0])
                last_sequence = np.roll(last_sequence, -1)
                last_sequence[0, -1] = next_pred[0, 0]
            lstm_forecast = self.scaler.inverse_transform(np.array(lstm_forecast).reshape(-1, 1))
        else:
            lstm_forecast = np.zeros(days_ahead)
        
        # Combine forecasts
        forecast_dates = pd.date_range(
            start=data.index[-1] + pd.Timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )
        
        forecast_df = pd.DataFrame({
            'date': forecast_dates,
            'arima_forecast': arima_forecast,
            'prophet_forecast': prophet_forecast['yhat'].values[-days_ahead:],
            'lstm_forecast': lstm_forecast.flatten()
        })
        
        # Calculate ensemble forecast (simple average)
        forecast_df['ensemble_forecast'] = forecast_df[
            ['arima_forecast', 'prophet_forecast', 'lstm_forecast']
        ].mean(axis=1)
        
        return forecast_df 
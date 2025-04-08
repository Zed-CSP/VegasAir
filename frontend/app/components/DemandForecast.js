'use client';

import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';

const DemandForecast = () => {
  const [forecastData, setForecastData] = useState(null);
  const [selectedClass, setSelectedClass] = useState('first');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchForecasts = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/demand-forecast');
        const data = await response.json();
        setForecastData(data.forecasts);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch forecast data');
        setLoading(false);
      }
    };

    fetchForecasts();
  }, []);

  if (loading) return <div>Loading forecasts...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!forecastData) return <div>No forecast data available</div>;

  // Prepare data for the selected class
  const classData = forecastData[selectedClass];
  if (!classData) return <div>No data available for {selectedClass} class</div>;

  // Combine all model forecasts into a single dataset for comparison
  const chartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    ARIMA: classData.arima?.forecast[i] || 0,
    Prophet: classData.prophet?.forecast[i] || 0,
    LSTM: classData.lstm?.forecast[i] || 0,
    ...(classData.prophet?.confidence_intervals && {
      'Prophet Lower': classData.prophet.confidence_intervals.lower[i],
      'Prophet Upper': classData.prophet.confidence_intervals.upper[i],
    })
  }));

  return (
    <div className="demand-forecast">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Demand Forecast
        </h2>
        <div style={{ marginBottom: '15px' }}>
          <label style={{ marginRight: '10px' }}>Select Class:</label>
          <select 
            value={selectedClass}
            onChange={(e) => setSelectedClass(e.target.value)}
            style={{
              padding: '8px',
              borderRadius: '4px',
              border: '1px solid var(--border-color)'
            }}
          >
            <option value="first">First Class</option>
            <option value="business">Business Class</option>
            <option value="economy">Economy Class</option>
          </select>
        </div>
      </div>

      <div style={{ width: '100%', height: '400px' }}>
        <ResponsiveContainer>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="day" 
              label={{ 
                value: 'Days in Future', 
                position: 'insideBottom', 
                offset: -5 
              }}
            />
            <YAxis 
              label={{ 
                value: 'Predicted Purchases', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            <Tooltip />
            <Legend />
            <Line 
              type="monotone" 
              dataKey="ARIMA" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="Prophet" 
              stroke="#82ca9d" 
              strokeWidth={2}
              dot={false}
            />
            <Line 
              type="monotone" 
              dataKey="LSTM" 
              stroke="#ffc658" 
              strokeWidth={2}
              dot={false}
            />
            {classData.prophet?.confidence_intervals && (
              <>
                <Line 
                  type="monotone" 
                  dataKey="Prophet Lower" 
                  stroke="#82ca9d" 
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="Prophet Upper" 
                  stroke="#82ca9d" 
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  dot={false}
                />
              </>
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DemandForecast; 
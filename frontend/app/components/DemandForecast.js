'use client';

import React, { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  ComposedChart
} from 'recharts';

const DemandForecast = () => {
  const [forecastData, setForecastData] = useState(null);
  const [selectedClass, setSelectedClass] = useState('first');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showSaleProjections, setShowSaleProjections] = useState(true);

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

  // Calculate sale projections based on forecast and pricing
  const getSaleProjections = () => {
    // Base prices for each class
    const basePrices = {
      first: 1200,
      business: 800,
      economy: 400
    };
    
    // Calculate projected revenue for each day
    return Array.from({ length: 30 }, (_, i) => {
      // Use the ensemble forecast (average of all models)
      const forecastValue = (
        (classData.arima?.forecast[i] || 0) +
        (classData.prophet?.forecast[i] || 0) +
        (classData.lstm?.forecast[i] || 0)
      ) / 3;
      
      // Calculate projected revenue
      const projectedRevenue = forecastValue * basePrices[selectedClass];
      
      return {
        day: i + 1,
        projectedRevenue
      };
    });
  };

  // Combine all model forecasts and sale projections into a single dataset
  const chartData = Array.from({ length: 30 }, (_, i) => ({
    day: i + 1,
    ARIMA: classData.arima?.forecast[i] || 0,
    Prophet: classData.prophet?.forecast[i] || 0,
    LSTM: classData.lstm?.forecast[i] || 0,
    ...(classData.prophet?.confidence_intervals && {
      'Prophet Lower': classData.prophet.confidence_intervals.lower[i],
      'Prophet Upper': classData.prophet.confidence_intervals.upper[i],
    }),
    ...(showSaleProjections && {
      'Projected Revenue': getSaleProjections()[i].projectedRevenue
    })
  }));

  // Format currency for tooltip
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="demand-forecast">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Demand Forecast & Sale Projections
        </h2>
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          marginBottom: '15px',
          flexWrap: 'wrap'
        }}>
          <div>
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
          <div>
            <label style={{ marginRight: '10px' }}>
              <input 
                type="checkbox" 
                checked={showSaleProjections}
                onChange={(e) => setShowSaleProjections(e.target.checked)}
                style={{ marginRight: '5px' }}
              />
              Show Sale Projections
            </label>
          </div>
        </div>
      </div>

      <div style={{ width: '100%', height: '500px' }}>
        <ResponsiveContainer>
          <ComposedChart data={chartData}>
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
              yAxisId="left"
              label={{ 
                value: 'Predicted Purchases', 
                angle: -90, 
                position: 'insideLeft' 
              }}
            />
            {showSaleProjections && (
              <YAxis 
                yAxisId="right" 
                orientation="right"
                label={{ 
                  value: 'Projected Revenue ($)', 
                  angle: 90, 
                  position: 'insideRight' 
                }}
              />
            )}
            <Tooltip 
              formatter={(value, name) => {
                if (name === 'Projected Revenue') {
                  return [formatCurrency(value), name];
                }
                return [value, name];
              }}
            />
            <Legend />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="ARIMA" 
              stroke="#8884d8" 
              strokeWidth={2}
              dot={false}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="Prophet" 
              stroke="#82ca9d" 
              strokeWidth={2}
              dot={false}
            />
            <Line 
              yAxisId="left"
              type="monotone" 
              dataKey="LSTM" 
              stroke="#ffc658" 
              strokeWidth={2}
              dot={false}
            />
            {classData.prophet?.confidence_intervals && (
              <>
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="Prophet Lower" 
                  stroke="#82ca9d" 
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  dot={false}
                />
                <Line 
                  yAxisId="left"
                  type="monotone" 
                  dataKey="Prophet Upper" 
                  stroke="#82ca9d" 
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  dot={false}
                />
              </>
            )}
            {showSaleProjections && (
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="Projected Revenue" 
                stroke="#ff7300" 
                strokeWidth={3}
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DemandForecast; 
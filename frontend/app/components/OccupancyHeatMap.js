'use client';

import React from 'react';

const OccupancyHeatMap = () => {
  return (
    <div className="occupancy-heatmap">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Occupancy Heat Map
        </h2>
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          marginBottom: '15px',
          flexWrap: 'wrap'
        }}>
          <div>
            <label style={{ marginRight: '10px' }}>View Mode:</label>
            <select 
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="occupancy">Occupancy Rate</option>
              <option value="pricing">Price Optimization</option>
              <option value="booking">Booking Patterns</option>
            </select>
          </div>
          <div>
            <label style={{ marginRight: '10px' }}>Time Scale:</label>
            <select 
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="day">Daily</option>
              <option value="week">Weekly</option>
              <option value="month">Monthly</option>
            </select>
          </div>
        </div>
      </div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        height: '400px',
        color: 'var(--text-secondary)',
        fontSize: '1.1rem'
      }}>
        Occupancy Heat Map Coming Soon
      </div>
    </div>
  );
};

export default OccupancyHeatMap; 
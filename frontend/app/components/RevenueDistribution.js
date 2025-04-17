'use client';

import React from 'react';

const RevenueDistribution = () => {
  return (
    <div className="revenue-distribution">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Revenue Distribution
        </h2>
        <div style={{ 
          display: 'flex', 
          gap: '20px', 
          marginBottom: '15px',
          flexWrap: 'wrap'
        }}>
          <div>
            <label style={{ marginRight: '10px' }}>View By:</label>
            <select 
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="class">Seat Class</option>
              <option value="pricing">Pricing Type</option>
              <option value="timing">Booking Period</option>
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
        Revenue Distribution Chart Coming Soon
      </div>
    </div>
  );
};

export default RevenueDistribution; 
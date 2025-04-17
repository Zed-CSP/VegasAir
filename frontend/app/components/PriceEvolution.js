'use client';

import React from 'react';

const PriceEvolution = () => {
  return (
    <div className="price-evolution">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Price Evolution Timeline
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
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="all">All Classes</option>
              <option value="first">First Class</option>
              <option value="business">Business</option>
              <option value="economy">Economy</option>
            </select>
          </div>
          <div>
            <label style={{ marginRight: '10px' }}>Time Range:</label>
            <select 
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="7">Last 7 Days</option>
              <option value="30">Last 30 Days</option>
              <option value="90">Last 90 Days</option>
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
        Price Evolution Chart Coming Soon
      </div>
    </div>
  );
};

export default PriceEvolution; 
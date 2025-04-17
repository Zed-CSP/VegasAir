'use client';

import React from 'react';

const PriceSensitivity = () => {
  return (
    <div className="price-sensitivity">
      <div className="forecast-controls" style={{ marginBottom: '20px' }}>
        <h2 style={{ 
          fontSize: '1.5rem', 
          marginBottom: '15px',
          color: 'var(--primary-color)'
        }}>
          Price Sensitivity Analysis
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
              <option value="first">First Class</option>
              <option value="business">Business</option>
              <option value="economy">Economy</option>
            </select>
          </div>
          <div>
            <label style={{ marginRight: '10px' }}>Analysis Type:</label>
            <select 
              style={{
                padding: '8px',
                borderRadius: '4px',
                border: '1px solid var(--border-color)'
              }}
            >
              <option value="elasticity">Price Elasticity</option>
              <option value="optimal">Optimal Price Points</option>
              <option value="demand">Demand Curve</option>
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
        Price Sensitivity Analysis Coming Soon
      </div>
    </div>
  );
};

export default PriceSensitivity; 
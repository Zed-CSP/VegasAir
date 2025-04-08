'use client';

import { useState, useEffect } from 'react';

const CountdownTimer = ({ daysUntilDeparture, hours, flightNumber }) => {
  return (
    <div className="countdown-timer" style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'flex-start',
      padding: '20px 40px',
      gap: '60px',
      width: '100%',
      maxWidth: '600px'
    }}>
      <h2 
        className="flight-number"
        style={{
          fontSize: '1.5rem',
          fontFamily: "'Orbitron', 'Arial Black', sans-serif",
          fontWeight: '900',
          letterSpacing: '2px',
          textTransform: 'uppercase',
          color: 'var(--primary-color)',
          textShadow: '0 0 10px rgba(0, 102, 204, 0.3)',
          margin: 0,
          lineHeight: '1.4',
          minWidth: 'fit-content'
        }}
      >
        VEGASAIR<br />
        FLIGHT {flightNumber}
      </h2>
      <div style={{ 
        display: 'flex', 
        gap: '20px',
        marginLeft: 'auto'
      }}>
        <div className="countdown-item">
          <div className="countdown-value">{daysUntilDeparture}</div>
          <div className="countdown-label">Days</div>
        </div>
        <div className="countdown-item">
          <div className="countdown-value">{hours}</div>
          <div className="countdown-label">Hours</div>
        </div>
      </div>
    </div>
  );
}

export default CountdownTimer; 